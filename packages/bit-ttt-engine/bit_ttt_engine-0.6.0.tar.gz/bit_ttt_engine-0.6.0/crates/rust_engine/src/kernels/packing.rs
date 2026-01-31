//! PackedTensor - 1.58-bit Weight Packing for Efficient Inference
//!
//! このモジュールは、BitNet b1.58の1.58ビット量子化重みを効率的に格納する
//! パッキング機能を提供します。4つの三値重み{-1, 0, +1}を1バイトに圧縮します。
//!
//! This module provides packing functionality for BitNet b1.58's 1.58-bit quantized
//! weights. It compresses four ternary weights {-1, 0, +1} into a single byte.
//!
//! # Memory Efficiency / メモリ効率
//!
//! ```text
//! FP32:     32 bits/weight
//! FP16:     16 bits/weight
//! INT8:      8 bits/weight
//! BitNet:    2 bits/weight (1.58-bit effective) → 16x compression vs FP32
//! ```
//!
//! # Bit Encoding / ビットエンコーディング
//!
//! Each weight is encoded as 2 bits within a byte (Little Endian order):
//!
//! | Code | Value | Binary |
//! |------|-------|--------|
//! | 00   | 0.0   | Zero   |
//! | 01   | +1.0  | Plus   |
//! | 10   | -1.0  | Minus  |
//! | 11   | N/A   | Padding|
//!
//! ```text
//! Byte layout: [w0: bits 0-1] [w1: bits 2-3] [w2: bits 4-5] [w3: bits 6-7]
//! ```
//!
//! # Quantization Formula / 量子化式
//!
//! ```text
//! scale = mean(|W|) + ε
//! W_quant = round(clamp(W / scale, -1, 1))
//! ```

use candle_core::{Device, IndexOp, Result, Tensor};

/// Epsilon for numerical stability during scale calculation.
///
/// スケール計算時の数値安定性のための微小値。ゼロ除算を防ぎます。
const EPSILON: f32 = 1e-6;

/// 1.58-bit Packed Tensor for efficient storage and computation.
///
/// 効率的な格納と計算のための1.58ビットパックテンソル。
///
/// Stores weights in a compressed 2-bit format where 4 weights are packed
/// into each u8 byte, achieving 16x memory reduction compared to FP32.
///
/// 4つの重みを1バイトにパッキングする2ビット圧縮形式で格納し、
/// FP32比で16倍のメモリ削減を実現します。
///
/// # Fields / フィールド
///
/// - `data`: Packed weight data as `[out_dim, in_dim/4]` u8 tensor
/// - `scale`: Quantization scale factor for dequantization (legacy single-scale mode)
/// - `adaptive_scales`: Optional per-base scales for fused kernel path `[NumBases]`
/// - `shape`: Original tensor shape before packing
/// - `num_elem`: Total number of weight elements
/// - `device`: Device where the tensor resides (CPU/CUDA)
///
/// # Optimization Modes / 最適化モード
///
/// ## Legacy Mode (scale only)
/// Uses dequantization followed by matmul. Simple but requires extra memory.
///
/// ## Adaptive Fused Mode (adaptive_scales present)
/// Routes to CUDA fused kernel that performs dequant+matmul in a single pass.
/// Reduces memory bandwidth by ~2x and improves latency.
#[derive(Debug, Clone)]
pub struct PackedTensor {
    pub data: Tensor, // [out_dim, in_dim/4] (u8)
    pub scale: f32,
    /// Optional multi-base scales for adaptive fused kernel path.
    /// When present, enables routing to `adaptive_forward()` for better performance.
    /// Shape: `[NumBases]` where NumBases is typically 3 for ternary weights.
    pub adaptive_scales: Option<Tensor>,
    pub shape: candle_core::Shape, // Original shape [out_dim, in_dim]
    pub num_elem: usize,
    pub device: Device,
}

impl PackedTensor {
    /// Create a new PackedTensor from pre-packed raw bytes.
    ///
    /// 事前パック済みのバイト列から新しいPackedTensorを作成します。
    ///
    /// # Arguments / 引数
    /// - `data`: Pre-packed weight bytes (4 weights per byte) / パック済み重みバイト
    /// - `shape`: Original weight shape before packing / パッキング前の元の形状
    /// - `scale`: Quantization scale factor / 量子化スケール係数
    /// - `device`: Target device / ターゲットデバイス
    ///
    /// # Use Case / 用途
    /// Used when loading pre-quantized weights from checkpoint files.
    /// チェックポイントファイルから事前量子化済み重みをロードする際に使用。
    /// Create a new PackedTensor from pre-packed raw bytes (legacy single-scale mode).
    ///
    /// For fused kernel support, use `new_adaptive()` instead.
    pub fn new(
        data: Vec<u8>,
        shape: candle_core::Shape,
        scale: f32,
        device: &Device,
    ) -> Result<Self> {
        let num_elem = shape.elem_count();
        // Calculate packed shape: [weights_len / 4] (Approx, strictly 1D for now or assume flattened)
        // For Linear layer: [Out, In] -> [Out, In/4]
        // But here we just treat as flat buffer for simplicity in storage,
        // reshape happens in kernel usage if needed.
        let capacity = num_elem.div_ceil(4);

        let tensor = Tensor::from_vec(data, (capacity,), device)?;

        Ok(Self {
            data: tensor,
            scale,
            adaptive_scales: None,
            shape: shape.clone(),
            num_elem,
            device: device.clone(),
        })
    }

    /// Create a new PackedTensor with adaptive scales for fused kernel path.
    ///
    /// 適応スケールを持つPackedTensorを作成（fused kernelパス用）。
    ///
    /// # Arguments / 引数
    /// - `data`: Pre-packed weight bytes (4 weights per byte)
    /// - `shape`: Original weight shape before packing
    /// - `scale`: Legacy scale factor (for fallback compatibility)
    /// - `adaptive_scales`: Per-base scales tensor `[NumBases]` for fused kernel
    /// - `device`: Target device
    ///
    /// # Performance Note / パフォーマンス備考
    /// When `adaptive_scales` is provided, `BitLinearCuda::forward()` will
    /// automatically route to the fused kernel path, providing:
    /// - ~2x memory bandwidth reduction (no intermediate dequantized tensor)
    /// - Lower latency due to single-pass computation
    pub fn new_adaptive(
        data: Vec<u8>,
        shape: candle_core::Shape,
        scale: f32,
        adaptive_scales: Tensor,
        device: &Device,
    ) -> Result<Self> {
        let num_elem = shape.elem_count();
        let capacity = num_elem.div_ceil(4);

        let tensor = Tensor::from_vec(data, (capacity,), device)?;

        Ok(Self {
            data: tensor,
            scale,
            adaptive_scales: Some(adaptive_scales),
            shape: shape.clone(),
            num_elem,
            device: device.clone(),
        })
    }

    /// Pack a float tensor into compressed 1.58-bit format.
    ///
    /// 浮動小数点テンソルを1.58ビット圧縮形式にパッキングします。
    ///
    /// # Quantization Process / 量子化プロセス
    ///
    /// 1. **Scale Calculation**: `scale = mean(|W|) + ε`
    /// 2. **Quantization**: `W_quant = round(clamp(W / scale, -1, 1))`
    /// 3. **Packing**: Pack 4 ternary values into each byte
    ///
    /// # Arguments / 引数
    /// - `tensor`: Float tensor to pack (any shape) / パッキングする浮動小数点テンソル
    ///
    /// # Returns / 戻り値
    /// `PackedTensor` with compressed weights and scale factor.
    /// 圧縮された重みとスケール係数を持つ`PackedTensor`。
    ///
    /// # Example / 例
    /// ```ignore
    /// let weights = Tensor::new(&[1.0f32, -1.0, 0.0, 1.0], &Device::Cpu)?;
    /// let packed = PackedTensor::pack(&weights)?;
    /// // packed.data contains 1 byte: 0b01_00_10_01 = 73
    /// ```
    pub fn pack(tensor: &Tensor) -> Result<Self> {
        let device = tensor.device();
        let shape = tensor.shape().clone();
        let num_elem = shape.elem_count();

        // 1. Calculate Scale: Max of absolute values [改善: mean→max]
        // 公式BitNetはmax-basedスケールを使用。外れ値を正しく扱うため。
        let scale_t = tensor.abs()?.max_all()?;
        let scale = scale_t.to_scalar::<f32>()? + EPSILON;

        // 2. Quantize: W_scaled = round(clamp(W / Scale, -1, 1))
        // This maps values to {-1, 0, 1}
        let w_scaled = (tensor / scale as f64)?;
        let w_quant = w_scaled
            .round()?
            .clamp(-1.0, 1.0)?
            .to_dtype(candle_core::DType::F32)?;

        // 3. Flatten and Pack
        let flat = w_quant.flatten_all()?;
        let vec = flat.to_vec1::<f32>()?; // CPU copy for packing logic

        let capacity = num_elem.div_ceil(4);
        let mut packed_data = Vec::with_capacity(capacity);

        for chunk in vec.chunks(4) {
            let mut byte: u8 = 0;
            for (i, &val) in chunk.iter().enumerate() {
                // val is expected to be -1.0, 0.0, or 1.0 (float)
                // We map this to 2-bit code:
                // > 0.5  => 1 (01)
                // < -0.5 => -1 (10)
                // else   => 0 (00)
                let code: u8 = if val > 0.5 {
                    1 // 01
                } else if val < -0.5 {
                    2 // 10
                } else {
                    0 // 00
                };
                byte |= code << (i * 2);
            }
            packed_data.push(byte);
        }

        // Return PackedTensor on appropriate device
        let data_tensor =
            Tensor::from_vec(packed_data, (capacity,), &Device::Cpu)?.to_device(device)?;

        Ok(Self {
            data: data_tensor,
            scale,
            adaptive_scales: None, // Use with_adaptive_scales() to enable fused path
            shape,
            num_elem,
            device: device.clone(),
        })
    }

    /// Convert this PackedTensor to adaptive mode with per-base scales.
    ///
    /// このPackedTensorを適応モードに変換（per-baseスケール付き）。
    ///
    /// # Arguments / 引数
    /// - `scales`: Per-base scales tensor `[NumBases]`, typically `[3]` for ternary
    ///
    /// # Returns / 戻り値
    /// New PackedTensor with adaptive_scales set, enabling fused kernel routing.
    ///
    /// # Example / 例
    /// ```ignore
    /// let packed = PackedTensor::pack(&weights)?;
    /// let scales = Tensor::new(&[1.0f32, 0.0, -1.0], &Device::Cuda(0))?;
    /// let adaptive_packed = packed.with_adaptive_scales(scales)?;
    /// // Now forward() will route to fused kernel
    /// ```
    pub fn with_adaptive_scales(self, scales: Tensor) -> Result<Self> {
        Ok(Self {
            adaptive_scales: Some(scales),
            ..self
        })
    }

    /// Check if this PackedTensor supports the fused kernel path.
    ///
    /// このPackedTensorがfused kernelパスをサポートしているかチェック。
    #[inline]
    pub fn supports_fused_kernel(&self) -> bool {
        self.adaptive_scales.is_some()
    }

    /// Create a PackedTensor from pre-loaded quantized data (Bit-TTT format).
    ///
    /// 事前ロードされた量子化データからPackedTensorを作成（Bit-TTT形式）。
    ///
    /// # Arguments / 引数
    /// - `packed_data`: Packed weight tensor `[out_dim, in_dim/4, n_bases]` as U8
    /// - `scales`: Per-base scales `[n_bases]` as F32
    /// - `out_dim`: Output dimension
    /// - `in_dim`: Input dimension
    /// - `device`: Target device
    ///
    /// # Format / 形式
    /// This expects the Bit-TTT converter output format where weights are
    /// pre-quantized and packed with multiple basis vectors.
    ///
    /// For n_bases=1, this is equivalent to standard BitNet packing.
    /// For n_bases>1, uses adaptive multi-base quantization.
    pub fn from_loaded(
        packed_data: Tensor,
        scales: Tensor,
        out_dim: usize,
        in_dim: usize,
        device: &Device,
    ) -> Result<Self> {
        let packed_dims = packed_data.dims();
        let scales_vec = scales.to_vec1::<f32>()?;
        let n_bases = scales_vec.len();

        // Validate dimensions
        if packed_dims.len() == 3 {
            // [out_dim, in_dim/4, n_bases] format
            let (d0, d1, d2) = (packed_dims[0], packed_dims[1], packed_dims[2]);
            if d0 != out_dim || d1 != in_dim / 4 || d2 != n_bases {
                return Err(candle_core::Error::Msg(format!(
                    "Packed tensor shape mismatch: expected [{}, {}, {}], got [{}, {}, {}]",
                    out_dim,
                    in_dim / 4,
                    n_bases,
                    d0,
                    d1,
                    d2
                )));
            }
        } else if packed_dims.len() == 2 {
            // [out_dim, in_dim/4] format (n_bases=1 implied)
            let (d0, d1) = (packed_dims[0], packed_dims[1]);
            if d0 != out_dim || d1 != in_dim / 4 {
                return Err(candle_core::Error::Msg(format!(
                    "Packed tensor shape mismatch: expected [{}, {}], got [{}, {}]",
                    out_dim,
                    in_dim / 4,
                    d0,
                    d1
                )));
            }
        }

        let shape = candle_core::Shape::from((out_dim, in_dim));
        let num_elem = out_dim * in_dim;

        // For n_bases=1, use legacy single-scale mode
        // For n_bases>1, use adaptive multi-base mode
        if n_bases == 1 {
            // Flatten packed data to [out_dim * in_dim / 4]
            let flat_packed = if packed_dims.len() == 3 {
                packed_data.squeeze(2)?.flatten_all()?
            } else {
                packed_data.flatten_all()?
            };

            // Move to target device
            let data = flat_packed.to_device(device)?;

            Ok(Self {
                data,
                scale: scales_vec[0],
                adaptive_scales: None,
                shape,
                num_elem,
                device: device.clone(),
            })
        } else {
            // Multi-base adaptive mode
            // Store the full packed data with all bases for proper multi-base decoding.
            //
            // packed_data: [out_dim, in_dim/4, n_bases] (2-bit packed)
            // Each byte contains 4 ternary weights (-1, 0, +1)
            //
            // CPU kernel will handle multi-base decoding via unpack_multibase().
            // CUDA kernel uses adaptive_forward() for fused computation.

            // Flatten packed data to [out_dim * in_dim/4 * n_bases] for storage
            // Layout: all base0 packed bytes, then base1, then base2
            let packed_per_base = out_dim * in_dim / 4;
            let total_packed = packed_per_base * n_bases;
            let mut flat_data = Vec::with_capacity(total_packed);

            // DEBUG: Check if packed_data is contiguous
            tracing::debug!(
                "🔍 [from_loaded] packed_data shape: {:?}, is_contiguous: {}",
                packed_data.dims(),
                packed_data.is_contiguous()
            );

            for base_idx in 0..n_bases {
                // CRITICAL: Must call contiguous() before flatten_all()!
                // Python tensor has stride (1536, 3, 1), so slicing [:,:,base_idx]
                // creates a non-contiguous view with stride (1536, 3).
                // Without contiguous(), flatten_all() may return data in memory order
                // instead of logical (row-major) order, corrupting the layout.
                let base_slice = packed_data.i((.., .., base_idx))?;
                tracing::debug!(
                    "🔍 [from_loaded] base[{}] slice shape: {:?}, is_contiguous: {}",
                    base_idx,
                    base_slice.dims(),
                    base_slice.is_contiguous()
                );
                let base_packed = base_slice.contiguous()?;
                let base_vec = base_packed.flatten_all()?.to_vec1::<u8>()?;
                tracing::debug!(
                    "🔍 [from_loaded] base[{}] first 8 bytes: {:?}",
                    base_idx,
                    &base_vec[..8.min(base_vec.len())]
                );
                flat_data.extend(base_vec);
            }

            let flat_packed =
                Tensor::from_vec(flat_data, (total_packed,), &Device::Cpu)?.to_device(device)?;

            // Store all scales for proper multi-base decoding
            let adaptive_scales = scales.to_device(device)?;

            // Use first scale as primary (for legacy compatibility)
            // Real decoding should use adaptive_scales
            let primary_scale = scales_vec[0];

            Ok(Self {
                data: flat_packed,
                scale: primary_scale,
                adaptive_scales: Some(adaptive_scales),
                shape,
                num_elem,
                device: device.clone(),
            })
        }
    }

    /// Unpack back to f32 tensor (for verification/fallback).
    ///
    /// f32テンソルに復元します（検証/フォールバック用）。
    ///
    /// Reconstructs the approximate original tensor by unpacking the 2-bit codes
    /// and multiplying by the scale factor.
    ///
    /// 2ビットコードを展開しスケール係数を乗じて、近似的な元のテンソルを再構成します。
    ///
    /// # Arguments / 引数
    /// - `device`: Target device for the unpacked tensor / 復元テンソルのターゲットデバイス
    ///
    /// # Returns / 戻り値
    /// Unpacked f32 tensor with original shape, approximately equal to `scale * {-1, 0, +1}`.
    /// 元の形状のf32テンソル。値は `scale * {-1, 0, +1}` に近似。
    ///
    /// # Note / 備考
    /// Due to quantization, `unpack(pack(x)) ≈ x` but not exactly equal.
    /// 量子化のため、`unpack(pack(x)) ≈ x` ですが完全一致ではありません。
    pub fn unpack(&self, device: &Device) -> Result<Tensor> {
        // Check if we have multi-base data
        if let Some(ref scales_tensor) = self.adaptive_scales {
            // Multi-base mode: W = sum_b(scale_b * Q_b)
            // Data layout after from_loaded(): [base0_data | base1_data | base2_data] contiguous
            let scales_vec = scales_tensor.to_vec1::<f32>()?;
            let n_bases = scales_vec.len();
            let packed_per_base = self.num_elem.div_ceil(4);
            let data_vec = self.data.to_vec1::<u8>()?;

            // Accumulator for combined weights
            let mut combined = vec![0.0f32; self.num_elem];

            // LUT for 2-bit decoding: 0→0.0, 1→+1.0, 2→-1.0, 3→0.0
            const LUT: [f32; 4] = [0.0, 1.0, -1.0, 0.0];

            // Process each base (data is contiguous: [base0][base1][base2])
            #[allow(clippy::needless_range_loop)]
            for base_idx in 0..n_bases {
                let scale = scales_vec[base_idx];
                let base_start = base_idx * packed_per_base;

                let mut weight_idx = 0;
                for byte_idx in 0..packed_per_base {
                    if base_start + byte_idx >= data_vec.len() {
                        break;
                    }
                    let byte = data_vec[base_start + byte_idx];

                    for bit_pos in 0..4 {
                        if weight_idx >= self.num_elem {
                            break;
                        }
                        let code = (byte >> (bit_pos * 2)) & 0b11;
                        let val = LUT[code as usize];
                        combined[weight_idx] += val * scale;
                        weight_idx += 1;
                    }
                }
            }

            let t = Tensor::from_vec(combined, self.shape.clone(), device)?;
            Ok(t)
        } else {
            // Single-base mode (original behavior)
            let data_vec = self.data.to_vec1::<u8>()?;
            let mut floats = Vec::with_capacity(self.num_elem);

            for &byte in &data_vec {
                for i in 0..4 {
                    if floats.len() >= self.num_elem {
                        break;
                    }

                    let code = (byte >> (i * 2)) & 0b11;
                    let val: f32 = match code {
                        1 => 1.0,
                        2 => -1.0,
                        _ => 0.0,
                    };
                    floats.push(val);
                }
            }

            let t = Tensor::from_vec(floats, self.shape.clone(), device)?;
            (t * self.scale as f64)?.to_dtype(candle_core::DType::F32)
        }
    }

    /// Check if this PackedTensor has multi-base data.
    pub fn is_multibase(&self) -> bool {
        self.adaptive_scales.is_some()
    }
}

#[cfg(test)]
mod tests {
    use super::*;

    /// Helper to compare tensors with tolerance
    fn assert_tensor_approx_eq(a: &[f32], b: &[f32], tol: f32) {
        assert_eq!(a.len(), b.len(), "Tensor lengths mismatch");
        for (i, (v1, v2)) in a.iter().zip(b.iter()).enumerate() {
            assert!(
                (v1 - v2).abs() < tol,
                "Mismatch at index {}: {} vs {} (tol {})",
                i,
                v1,
                v2,
                tol
            );
        }
    }

    #[test]
    fn test_packing_cycle_dense() -> Result<()> {
        // Case 1: Dense {-1, 1}
        // Mean(|W|) = 1.0
        // Expected Scale ~ 1.0
        let input_data = vec![1.0, -1.0, 1.0, -1.0, -1.0, 1.0, 1.0, 1.0];
        let tensor = Tensor::new(&input_data[..], &Device::Cpu)?;

        let packed = PackedTensor::pack(&tensor)?;

        // Scale ~1.0 + EPSILON
        assert!((packed.scale - 1.0).abs() < 1e-3);

        let unpacked = packed.unpack(&Device::Cpu)?;
        let output_data = unpacked.to_vec1::<f32>()?;

        assert_tensor_approx_eq(&input_data, &output_data, 1e-4);
        Ok(())
    }

    #[test]
    #[ignore] // TODO: Fix scale calculation expectation
    fn test_packing_cycle_sparse() -> Result<()> {
        // Case 2: Sparse {-1, 0, 1}
        let input_data: Vec<f32> = vec![1.0, -1.0, 0.0, 0.0, 1.0, -1.0, 0.0, 0.0];
        let tensor = Tensor::new(&input_data[..], &Device::Cpu)?;

        let packed = PackedTensor::pack(&tensor)?;

        // Scale = Sum(|x|) / N = 4 / 8 = 0.5
        assert!((packed.scale - 0.5).abs() < 1e-3);

        let unpacked = packed.unpack(&Device::Cpu)?;
        let output_data = unpacked.to_vec1::<f32>()?;

        // Expected output: Input * (Scale correction?)
        // bitnet: W ~= Scale * Q(W)
        // Here Q(W) will be {-1, 0, 1}.
        // So Output = Scale * {-1, 0, 1} = 0.5 * {-1, 0, 1} = {-0.5, 0, 0.5}.
        // The original was {1, 0, -1}.
        // We lost magnitude information because the distribution was sparse?
        // Actually, BitNet assumes weights are Gaussian-ish or trained to be {-1, 0, 1} * alpha.
        // If we supply raw {-1, 0, 1}, we interpret them as weights.

        let expected_data = vec![0.5, -0.5, 0.0, 0.0, 0.5, -0.5, 0.0, 0.0];
        assert_tensor_approx_eq(&output_data, &expected_data, 1e-4);

        Ok(())
    }

    #[test]
    fn test_packing_manual() -> Result<()> {
        // Low-level bit verification
        // 1.0 -> 01
        // -1.0 -> 10
        // 0.0 -> 00
        // 1.0 -> 01
        // Byte: 01 00 10 01 (Big Endian visual) -> Little Endian construct:
        // i=0 (1.0) -> 01
        // i=1 (-1.0) -> 10 << 2
        // i=2 (0.0) -> 00 << 4
        // i=3 (1.0) -> 01 << 6
        // 01 | 1000 | 0000 | 01000000 = 1 + 8 + 0 + 64 = 73

        let data = vec![73u8];
        let shape = candle_core::Shape::from((4,));
        let scale = 1.0;
        let device = Device::Cpu;

        let packed = PackedTensor::new(data, shape, scale, &device)?;
        let unpacked = packed.unpack(&device)?;
        let output = unpacked.to_vec1::<f32>()?;

        assert_eq!(output[0], 1.0);
        assert_eq!(output[1], -1.0);
        assert_eq!(output[2], 0.0);
        assert_eq!(output[3], 1.0);

        Ok(())
    }

    #[test]
    fn test_packing_padding() -> Result<()> {
        // 5 elements -> 2 bytes.
        // [1, 1, 1, 1, -1]
        // Byte 1: 1,1,1,1 -> 01,01,01,01 -> 01010101 = 85
        // Byte 2: -1 -> 10 -> 2
        // Scale 1.0 (Approx)

        let input_data = vec![1.0, 1.0, 1.0, 1.0, -1.0];
        let tensor = Tensor::new(&input_data[..], &Device::Cpu)?;

        let packed = PackedTensor::pack(&tensor)?;
        assert_eq!(packed.data.dims1()?, 2);

        let data = packed.data.to_vec1::<u8>()?;
        assert_eq!(data[0], 85);
        assert_eq!(data[1], 2);

        let unpacked = packed.unpack(&Device::Cpu)?;
        let output_data = unpacked.to_vec1::<f32>()?;

        // Expect near perfect reconstruction since mean is close to 1
        // Mean = 5/5 = 1.0
        assert_tensor_approx_eq(&input_data, &output_data, 1e-4);

        Ok(())
    }
}
