//! 4-bit Symmetric Weight Quantization for Efficient Inference
//!
//! このモジュールは、4ビット対称量子化重みを効率的に格納するパッキング機能を提供します。
//! 2つの4ビット重み{-8..7}を1バイトに圧縮し、グループごとのスケーリングをサポートします。
//!
//! This module provides packing functionality for 4-bit symmetric quantized weights.
//! It compresses two 4-bit weights {-8..7} into a single byte with per-group scaling.
//!
//! # Memory Efficiency / メモリ効率
//!
//! ```text
//! FP32:     32 bits/weight
//! FP16:     16 bits/weight
//! INT8:      8 bits/weight
//! INT4:      4 bits/weight → 8x compression vs FP32
//! ```
//!
//! # Quantization Formula / 量子化式
//!
//! ```text
//! scale_group = max(|W_group|) / 7.0
//! Q = clamp(round(W / scale_group), -8, 7)
//! ```
//!
//! # Packing Format / パッキング形式
//!
//! Each byte stores 2 weights in low/high nibbles (4 bits each):
//! ```text
//! byte = low_weight | (high_weight << 4)
//! Signed range: -8..7 → Unsigned storage: 0..15
//! ```

use candle_core::{IndexOp, Result, Tensor};

/// Epsilon for numerical stability during scale calculation.
const EPSILON: f32 = 1e-5;

/// Pack a tensor into 4-bit symmetric quantized format with per-group scaling.
///
/// テンソルをグループごとスケーリング付き4ビット対称量子化形式にパッキングします。
///
/// # Arguments / 引数
/// - `tensor`: Input FP32/FP16 tensor [out_dim, in_dim] / 入力テンソル
/// - `group_size`: Number of elements per group for scaling / スケーリング用グループサイズ
///
/// # Returns / 戻り値
/// - `packed`: Packed tensor [out_dim, in_dim/2] (u8) / パック済みテンソル
/// - `scales`: Per-group scales [out_dim, n_groups] (f32) / グループごとスケール
///
/// # Quantization Process / 量子化プロセス
/// 1. Group weights into chunks of `group_size`
/// 2. Calculate per-group scale: `scale = max(|group|) / 7.0`
/// 3. Quantize: `Q = clamp(round(W / scale), -8, 7)`
/// 4. Pack pairs of weights into bytes
///
/// # Example / 例
/// ```ignore
/// let weights = Tensor::new(&[[1.4, -2.1, 0.7, -0.3]], &Device::Cpu)?; // [1, 4]
/// let (packed, scales) = pack_4bit_symmetric(&weights, 4)?;
/// // packed: [1, 2] (2 bytes for 4 weights)
/// // scales: [1, 1] (1 group)
/// ```
pub fn pack_4bit_symmetric(tensor: &Tensor, group_size: usize) -> Result<(Tensor, Tensor)> {
    let device = tensor.device();
    let dims = tensor.dims();

    if dims.len() != 2 {
        return Err(candle_core::Error::Msg(format!(
            "Expected 2D tensor [out_dim, in_dim], got shape {:?}",
            dims
        )));
    }

    let (out_dim, in_dim) = (dims[0], dims[1]);

    // Calculate padding needed for group alignment
    let pad_size = if in_dim % group_size == 0 {
        0
    } else {
        group_size - (in_dim % group_size)
    };
    let padded_in_dim = in_dim + pad_size;
    let n_groups = padded_in_dim / group_size;

    // Convert to F32 for consistent processing
    let tensor_f32 = tensor.to_dtype(candle_core::DType::F32)?;

    // Flatten tensor to work with 1D logic
    let tensor_2d = if pad_size > 0 {
        // Pad with zeros: [out_dim, in_dim] -> [out_dim, padded_in_dim]
        let zeros_pad = Tensor::zeros((out_dim, pad_size), candle_core::DType::F32, device)?;
        Tensor::cat(&[&tensor_f32, &zeros_pad], 1)?
    } else {
        tensor_f32.clone()
    };

    let mut all_packed_data = Vec::new();
    let mut all_scales = Vec::new();

    // Process each output row
    for row_idx in 0..out_dim {
        let row = tensor_2d.i((row_idx, ..))?; // [padded_in_dim]
        let row_data = row.to_vec1::<f32>()?;

        let mut row_scales = Vec::new();
        let mut row_packed = Vec::new();

        // Process groups within this row
        for group_idx in 0..n_groups {
            let group_start = group_idx * group_size;
            let group_end = (group_start + group_size).min(padded_in_dim);
            let group = &row_data[group_start..group_end];

            // Calculate group scale: max(|group|) / 7.0
            let max_abs = group.iter().map(|&x: &f32| x.abs()).fold(0.0f32, f32::max);
            let scale = (max_abs / 7.0).max(EPSILON);
            row_scales.push(scale);

            // Quantize group: Q = clamp(round(W / scale), -8, 7)
            let mut quantized_group = Vec::new();
            for &weight in group {
                let q = (weight / scale).round().clamp(-8.0, 7.0) as i8;
                quantized_group.push(q);
            }

            // Pack pairs of quantized values into bytes
            // Always pack group_size elements (pad with 0 if odd)
            for i in (0..group_size).step_by(2) {
                let low = if i < quantized_group.len() {
                    quantized_group[i]
                } else {
                    0i8
                };
                let high = if i + 1 < quantized_group.len() {
                    quantized_group[i + 1]
                } else {
                    0i8
                };

                // Convert to unsigned: -8..7 -> 0..15
                let low_unsigned = (low + 8) as u8;
                let high_unsigned = (high + 8) as u8;

                // Pack: low nibble | high nibble
                let packed_byte = low_unsigned | (high_unsigned << 4);
                row_packed.push(packed_byte);
            }
        }

        all_scales.extend(row_scales);
        all_packed_data.extend(row_packed);
    }

    // Create output tensors
    // Each group of group_size produces ceil(group_size/2) bytes
    let bytes_per_group = group_size.div_ceil(2);
    let packed_shape = (out_dim, n_groups * bytes_per_group);
    let scales_shape = (out_dim, n_groups);

    let packed_tensor = Tensor::from_vec(all_packed_data, packed_shape, device)?;
    let scales_tensor = Tensor::from_vec(all_scales, scales_shape, device)?;

    Ok((packed_tensor, scales_tensor))
}

/// Unpack 4-bit symmetric quantized weights back to floating point.
///
/// 4ビット対称量子化重みを浮動小数点に逆量子化します。
///
/// # Arguments / 引数
/// - `packed`: Packed tensor [out_dim, in_dim/2] (u8) / パック済みテンソル
/// - `scales`: Per-group scales [out_dim, n_groups] (f32) / グループごとスケール
/// - `original_shape`: Original tensor shape (out_dim, in_dim) / 元のテンソル形状
/// - `group_size`: Group size used during packing / パッキング時のグループサイズ
///
/// # Returns / 戻り値
/// Unpacked FP32 tensor with original shape / 元の形状のFP32テンソル
///
/// # Process / プロセス
/// 1. Unpack bytes into pairs of 4-bit values
/// 2. Convert unsigned (0..15) back to signed (-8..7)
/// 3. Apply per-group scaling: `W = Q * scale_group`
/// 4. Trim padding to restore original shape
pub fn unpack_4bit_symmetric(
    packed: &Tensor,
    scales: &Tensor,
    original_shape: (usize, usize),
    group_size: usize,
) -> Result<Tensor> {
    let device = packed.device();
    let (out_dim, in_dim) = original_shape;

    // Calculate padded dimensions
    let pad_size = if in_dim % group_size == 0 {
        0
    } else {
        group_size - (in_dim % group_size)
    };
    let padded_in_dim = in_dim + pad_size;
    let n_groups = padded_in_dim / group_size;
    let bytes_per_group = group_size.div_ceil(2);

    // Verify tensor shapes
    let packed_dims = packed.dims();
    let scales_dims = scales.dims();

    if packed_dims != [out_dim, n_groups * bytes_per_group] {
        return Err(candle_core::Error::Msg(format!(
            "Packed tensor shape mismatch: expected [{}, {}], got {:?}",
            out_dim,
            n_groups * bytes_per_group,
            packed_dims
        )));
    }

    if scales_dims != [out_dim, n_groups] {
        return Err(candle_core::Error::Msg(format!(
            "Scales tensor shape mismatch: expected [{}, {}], got {:?}",
            out_dim, n_groups, scales_dims
        )));
    }

    // Flatten and convert types for processing
    let packed_data = packed.flatten_all()?.to_vec1::<u8>()?;
    let scales_f32 = scales.to_dtype(candle_core::DType::F32)?;
    let scales_data = scales_f32.flatten_all()?.to_vec1::<f32>()?;

    let mut result_data: Vec<f32> = Vec::new();

    // Process each output row
    for row_idx in 0..out_dim {
        let mut row_data: Vec<f32> = Vec::new();

        // Process groups within this row
        for group_idx in 0..n_groups {
            let scale = scales_data[row_idx * n_groups + group_idx];
            let group_start_packed =
                (row_idx * n_groups * bytes_per_group) + (group_idx * bytes_per_group);

            // Unpack bytes for this group
            let mut group_weights = Vec::new();
            for byte_idx in 0..bytes_per_group {
                let packed_byte = packed_data[group_start_packed + byte_idx];

                // Unpack nibbles
                let low_unsigned = packed_byte & 0x0F;
                let high_unsigned = (packed_byte >> 4) & 0x0F;

                // Convert back to signed: 0..15 -> -8..7
                let low_signed = (low_unsigned as i8) - 8;
                let high_signed = (high_unsigned as i8) - 8;

                // Dequantize: W = Q * scale
                group_weights.push(low_signed as f32 * scale);
                if group_weights.len() < group_size {
                    group_weights.push(high_signed as f32 * scale);
                }
            }

            // Take only the required number of weights for this group
            let group_size_actual = group_size.min(padded_in_dim - group_idx * group_size);
            row_data.extend(&group_weights[..group_size_actual]);
        }

        // Trim padding to get original in_dim
        if row_data.len() > in_dim {
            row_data.truncate(in_dim);
        }

        result_data.extend(row_data);
    }

    let result_tensor = Tensor::from_vec(result_data, original_shape, device)?;
    Ok(result_tensor)
}

#[cfg(test)]
mod tests {
    use super::*;
    use candle_core::Device;

    /// Helper to compare tensors with tolerance
    fn assert_tensor_approx_eq(a: &Tensor, b: &Tensor, tol: f32) -> Result<()> {
        let a_f32 = a.to_dtype(candle_core::DType::F32)?;
        let b_f32 = b.to_dtype(candle_core::DType::F32)?;
        let a_vec = a_f32.flatten_all()?.to_vec1::<f32>()?;
        let b_vec = b_f32.flatten_all()?.to_vec1::<f32>()?;

        assert_eq!(a_vec.len(), b_vec.len(), "Tensor lengths mismatch");
        for (i, (v1, v2)) in a_vec.iter().zip(b_vec.iter()).enumerate() {
            assert!(
                (v1 - v2).abs() < tol,
                "Mismatch at index {}: {} vs {} (tol {})",
                i,
                v1,
                v2,
                tol
            );
        }
        Ok(())
    }

    #[test]
    fn test_4bit_packing_simple() -> Result<()> {
        let device = Device::Cpu;

        // Simple test: [1, 4] tensor with group_size=4
        let input_data = [7.0, -5.6, 0.0, 3.5];
        let tensor = Tensor::new(&input_data[..], &device)?.reshape((1, 4))?;

        let (packed, scales) = pack_4bit_symmetric(&tensor, 4)?;

        // Verify shapes
        assert_eq!(packed.dims(), &[1, 2]); // 4 weights -> 2 bytes
        assert_eq!(scales.dims(), &[1, 1]); // 1 group

        // Unpack and verify round-trip
        let unpacked = unpack_4bit_symmetric(&packed, &scales, (1, 4), 4)?;

        // Calculate expected error (4-bit quantization can have some loss)
        // 4-bit has only 16 levels, so error up to scale/2 is expected
        assert_tensor_approx_eq(&tensor, &unpacked, 1.0)?; // Tolerance for 4-bit quantization

        Ok(())
    }

    #[test]
    fn test_4bit_packing_multi_group() -> Result<()> {
        let device = Device::Cpu;

        // Test with multiple groups: [2, 6] tensor with group_size=3
        // Each group of 3 weights → ceil(3/2) = 2 bytes
        // 2 groups × 2 bytes = 4 bytes per row
        let input_data = vec![
            1.0, -2.0, 3.0, // Group 1: scale ≈ 3.0/7 ≈ 0.43
            4.0, -1.0, 0.0, // Group 2: scale ≈ 4.0/7 ≈ 0.57
            // Row 2
            -7.0, 2.0, 1.0, // Group 1: scale ≈ 7.0/7 = 1.0
            0.5, -0.2, 3.0, // Group 2: scale ≈ 3.0/7 ≈ 0.43
        ];
        let tensor = Tensor::new(&input_data[..], &device)?.reshape((2, 6))?;

        let (packed, scales) = pack_4bit_symmetric(&tensor, 3)?;

        // Verify shapes
        // group_size=3 → ceil(3/2) = 2 bytes per group, 2 groups = 4 bytes per row
        assert_eq!(packed.dims(), &[2, 4]); // 2 groups × 2 bytes = 4 bytes per row
        assert_eq!(scales.dims(), &[2, 2]); // 2 rows, 2 groups per row

        // Unpack and verify
        let unpacked = unpack_4bit_symmetric(&packed, &scales, (2, 6), 3)?;
        assert_tensor_approx_eq(&tensor, &unpacked, 0.5)?;

        Ok(())
    }

    #[test]
    fn test_4bit_packing_padding() -> Result<()> {
        let device = Device::Cpu;

        // Test padding: [1, 5] tensor with group_size=4 (needs padding to 8)
        let input_data = [1.0, -2.0, 3.0, -4.0, 2.0];
        let tensor = Tensor::new(&input_data[..], &device)?.reshape((1, 5))?;

        let (packed, scales) = pack_4bit_symmetric(&tensor, 4)?;

        // Should pad to 8 elements -> 2 groups of 4
        assert_eq!(packed.dims(), &[1, 4]); // 8 weights -> 4 bytes
        assert_eq!(scales.dims(), &[1, 2]); // 2 groups

        let unpacked = unpack_4bit_symmetric(&packed, &scales, (1, 5), 4)?;

        // Only check the original 5 elements (padding should be ignored)
        let original_slice = tensor.narrow(1, 0, 5)?;
        let unpacked_slice = unpacked.narrow(1, 0, 5)?;
        assert_tensor_approx_eq(&original_slice, &unpacked_slice, 0.5)?;

        Ok(())
    }

    #[test]
    fn test_4bit_quantization_range() -> Result<()> {
        let device = Device::Cpu;

        // Test quantization limits
        let input_data = [10.0f32, -15.0, 0.0, 7.0]; // Values that should saturate
        let tensor = Tensor::new(&input_data[..], &device)?.reshape((1, 4))?;

        let (packed, scales) = pack_4bit_symmetric(&tensor, 4)?;
        let unpacked = unpack_4bit_symmetric(&packed, &scales, (1, 4), 4)?;

        let unpacked_vec = unpacked.flatten_all()?.to_vec1::<f32>()?;

        // Verify quantization clamping (values should be in expected range after scaling)
        let scale = scales.flatten_all()?.to_vec1::<f32>()?[0];
        let max_val = 7.0 * scale; // Max quantized value
        let min_val = -8.0 * scale; // Min quantized value

        for &val in &unpacked_vec {
            assert!(
                val >= min_val - 1e-5 && val <= max_val + 1e-5,
                "Unpacked value {} outside expected range [{}, {}]",
                val,
                min_val,
                max_val
            );
        }

        Ok(())
    }

    #[test]
    fn test_4bit_round_trip_error() -> Result<()> {
        let device = Device::Cpu;

        // Test with realistic weight distribution
        let input_data: Vec<f32> = (0..32).map(|i| (i as f32 - 16.0) * 0.1).collect(); // -1.6 to 1.5
        let tensor = Tensor::new(&input_data[..], &device)?.reshape((4, 8))?;

        let (packed, scales) = pack_4bit_symmetric(&tensor, 8)?;
        let unpacked = unpack_4bit_symmetric(&packed, &scales, (4, 8), 8)?;

        // Calculate mean absolute error
        let tensor_f32 = tensor.to_dtype(candle_core::DType::F32)?;
        let diff = (&tensor_f32 - &unpacked)?;
        let mae = diff.abs()?.mean_all()?.to_scalar::<f32>()?;

        println!("4-bit Round-trip MAE: {:.6}", mae);

        // 4-bit quantization should have reasonable error
        assert!(mae < 0.05, "Round-trip error too high: MAE = {}", mae);

        Ok(())
    }

    #[test]
    fn test_4bit_standalone_functionality() -> Result<()> {
        println!("🧪 Testing 4-bit Packing Functions");
        let device = Device::Cpu;

        // Test 1: Simple case
        println!("Test 1: Simple 4-bit packing...");
        let input_data: Vec<f32> = vec![7.0, -5.6, 0.0, 3.5];
        let tensor = Tensor::new(&input_data[..], &device)?.reshape((1, 4))?;

        let (packed, scales) = pack_4bit_symmetric(&tensor, 4)?;
        assert_eq!(packed.dims(), &[1, 2]); // 4 weights -> 2 bytes
        assert_eq!(scales.dims(), &[1, 1]); // 1 group

        let unpacked = unpack_4bit_symmetric(&packed, &scales, (1, 4), 4)?;
        let unpacked_data = unpacked.flatten_all()?.to_vec1::<f32>()?;

        // Calculate MAE for this case
        let mut total_error = 0.0;
        for i in 0..input_data.len() {
            total_error += (input_data[i] - unpacked_data[i]).abs();
        }
        let mae = total_error / input_data.len() as f32;
        println!("  MAE: {:.6}", mae);
        assert!(mae < 0.5, "MAE too high: {}", mae);

        // Test 2: Multi-group test
        println!("Test 2: Multi-group 4-bit packing...");
        let input_data: Vec<f32> = vec![
            1.0, -2.0, 3.0, // Group 1
            4.0, -1.0, 0.0, // Group 2
            -7.0, 2.0, 1.0, // Group 1
            0.5, -0.2, 3.0, // Group 2
        ];
        let tensor = Tensor::new(&input_data[..], &device)?.reshape((2, 6))?;

        let (packed, scales) = pack_4bit_symmetric(&tensor, 3)?;
        // group_size=3 → ceil(3/2) = 2 bytes per group, 2 groups = 4 bytes per row
        assert_eq!(packed.dims(), &[2, 4]); // 2 groups × 2 bytes = 4 bytes per row
        assert_eq!(scales.dims(), &[2, 2]); // 2 rows, 2 groups per row

        let unpacked = unpack_4bit_symmetric(&packed, &scales, (2, 6), 3)?;
        let diff = (&tensor - &unpacked)?;
        let mae = diff.abs()?.mean_all()?.to_scalar::<f32>()?;
        println!("  MAE: {:.6}", mae);
        assert!(mae < 0.5, "MAE too high: {}", mae);

        // Test 3: Padding test
        println!("Test 3: Padding test...");
        let input_data: Vec<f32> = vec![1.0, -2.0, 3.0, -4.0, 2.0];
        let tensor = Tensor::new(&input_data[..], &device)?.reshape((1, 5))?;

        let (packed, scales) = pack_4bit_symmetric(&tensor, 4)?;
        assert_eq!(packed.dims(), &[1, 4]); // 8 weights (padded) -> 4 bytes
        assert_eq!(scales.dims(), &[1, 2]); // 2 groups

        let unpacked = unpack_4bit_symmetric(&packed, &scales, (1, 5), 4)?;
        let original_slice = tensor.narrow(1, 0, 5)?;
        let unpacked_slice = unpacked.narrow(1, 0, 5)?;
        let diff = (&original_slice - &unpacked_slice)?;
        let mae = diff.abs()?.mean_all()?.to_scalar::<f32>()?;
        println!("  MAE: {:.6}", mae);
        assert!(mae < 0.5, "MAE too high: {}", mae);

        println!("✅ All 4-bit packing tests passed!");
        Ok(())
    }
}
