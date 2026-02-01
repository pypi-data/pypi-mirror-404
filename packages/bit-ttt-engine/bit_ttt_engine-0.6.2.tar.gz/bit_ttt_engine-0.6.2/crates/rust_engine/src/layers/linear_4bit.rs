//! Linear4Bit - 4-bit Quantized Linear Layer
//!
//! このモジュールは4ビット量子化された線形層を実装します。
//! 重みを4ビットに量子化することで、メモリ使用量を削減し、
//! 効率的な推論を実現します。
//!
//! This module implements a 4-bit quantized linear layer.
//! By quantizing weights to 4-bit values, it reduces memory usage
//! and enables efficient inference.
//!
//! # Architecture / アーキテクチャ
//!
//! - **Storage**: Packed weights [out_dim, in_dim/2] as U8 + per-group scales
//! - **Computation**: Unpack → Dequantize → Standard MatMul → Optional Bias
//!
//! # Quantization / 量子化方式
//!
//! ```text
//! Group-wise 4-bit quantization with per-group scaling:
//! scale_g = max(|W_g|) / 15.0  (for group g)
//! W_quant_g = round(clamp(W_g / scale_g, -8, 7))  (4-bit signed range)
//!
//! Storage: 2 weights per byte (4 bits each)
//! ```

use candle_core::{Result, Tensor};
use candle_nn::VarBuilder;
use std::collections::HashMap;
use tracing::debug;

/// 4-bit quantized linear layer.
///
/// 4ビット量子化された線形層。
/// グループごとのスケーリングにより精度を保ちつつメモリ使用量を削減します。
///
/// Stores weights in 4-bit format with group-wise scaling to maintain
/// accuracy while reducing memory usage.
#[derive(Clone, Debug)]
pub struct Linear4Bit {
    /// Packed weights: [out_dim, in_dim/2] as U8
    /// 各バイトに2つの4ビット重みを格納
    pub weight_packed: Tensor,

    /// Per-group scales: [out_dim, n_groups] as F16
    /// グループごとのスケール係数
    pub scales: Tensor,

    /// Optional bias: `[out_dim]`
    pub bias: Option<Tensor>,

    /// Group size for quantization (typically 64 or 128)
    pub group_size: usize,

    /// Input feature dimension
    pub in_features: usize,

    /// Output feature dimension
    pub out_features: usize,
}

impl Linear4Bit {
    /// Create a new Linear4Bit layer with pre-computed packed weights.
    ///
    /// 事前計算されたパック済み重みで新しいLinear4Bit層を作成。
    ///
    /// # Arguments / 引数
    /// - `weight_packed`: Packed weights `[out_dim, in_dim/2]` as U8
    /// - `scales`: Per-group scales `[out_dim, n_groups]` as F16
    /// - `bias`: Optional bias `[out_dim]`
    /// - `group_size`: Size of each quantization group
    /// - `in_features`: Input dimension
    /// - `out_features`: Output dimension
    pub fn new(
        weight_packed: Tensor,
        scales: Tensor,
        bias: Option<Tensor>,
        group_size: usize,
        in_features: usize,
        out_features: usize,
    ) -> Result<Self> {
        // Validate dimensions
        let packed_dims = weight_packed.dims();
        let scales_dims = scales.dims();

        if packed_dims.len() != 2
            || packed_dims[0] != out_features
            || packed_dims[1] != in_features / 2
        {
            return Err(candle_core::Error::Msg(format!(
                "Invalid weight_packed shape: expected [{}, {}], got {:?}",
                out_features,
                in_features / 2,
                packed_dims
            )));
        }

        let n_groups = in_features.div_ceil(group_size);
        if scales_dims.len() != 2 || scales_dims[0] != out_features || scales_dims[1] != n_groups {
            return Err(candle_core::Error::Msg(format!(
                "Invalid scales shape: expected [{}, {}], got {:?}",
                out_features, n_groups, scales_dims
            )));
        }

        if let Some(ref bias_tensor) = bias {
            let bias_dims = bias_tensor.dims();
            if bias_dims.len() != 1 || bias_dims[0] != out_features {
                return Err(candle_core::Error::Msg(format!(
                    "Invalid bias shape: expected [{}], got {:?}",
                    out_features, bias_dims
                )));
            }
        }

        Ok(Self {
            weight_packed,
            scales,
            bias,
            group_size,
            in_features,
            out_features,
        })
    }

    /// Load 4-bit quantized weights from VarBuilder.
    ///
    /// VarBuilderから4ビット量子化重みをロード。
    ///
    /// # Arguments / 引数
    /// - `vb`: VarBuilder for loading weights
    /// - `prefix`: Prefix for weight names (e.g., "layers.0.mlp.gate_proj")
    ///
    /// # Expected files / 期待するファイル
    /// - `{prefix}.weight_4bit`: Packed weights `[out_dim, in_dim/2]` as U8
    /// - `{prefix}.scales_4bit`: Per-group scales `[out_dim, n_groups]` as F16
    /// - `{prefix}.bias` (optional): Bias `[out_dim]`
    pub fn load_4bit(vb: &VarBuilder, prefix: &str) -> Result<Self> {
        debug!("Loading 4bit linear layer with prefix: {}", prefix);

        // Load packed weights
        let weight_4bit_name = format!("{}.weight_4bit", prefix);
        let scales_4bit_name = format!("{}.scales_4bit", prefix);
        let bias_name = format!("{}.bias", prefix);

        let weight_packed = vb.get_with_hints_dtype(
            (), // Shape will be inferred from file
            &weight_4bit_name,
            candle_nn::init::ZERO,
            candle_core::DType::U8,
        )?;

        let scales = vb.get_with_hints_dtype(
            (), // Shape will be inferred from file
            &scales_4bit_name,
            candle_nn::init::ZERO,
            candle_core::DType::F16,
        )?;

        // Try to load bias (optional)
        let bias = match vb.get_with_hints((), &bias_name, candle_nn::init::ZERO) {
            Ok(bias_tensor) => Some(bias_tensor),
            Err(_) => {
                debug!("No bias found for {}, proceeding without bias", prefix);
                None
            }
        };

        // Infer dimensions from loaded tensors
        let packed_dims = weight_packed.dims();
        let scales_dims = scales.dims();

        if packed_dims.len() != 2 || scales_dims.len() != 2 {
            return Err(candle_core::Error::Msg(format!(
                "Invalid tensor dimensions: weight_packed {:?}, scales {:?}",
                packed_dims, scales_dims
            )));
        }

        let out_features = packed_dims[0];
        let in_features = packed_dims[1] * 2; // 2 weights per byte
        let n_groups = scales_dims[1];
        let group_size = in_features.div_ceil(n_groups);

        debug!(
            "Loaded 4bit layer: {}x{}, group_size={}, n_groups={}",
            out_features, in_features, group_size, n_groups
        );

        Self::new(
            weight_packed,
            scales,
            bias,
            group_size,
            in_features,
            out_features,
        )
    }

    /// Load from pre-loaded tensor HashMap (bypasses VarBuilder).
    ///
    /// 事前ロードしたテンソルHashMapから直接ロードします（VarBuilderをバイパス）。
    ///
    /// # Arguments / 引数
    /// - `tensors`: Pre-loaded tensor HashMap
    /// - `prefix`: Prefix for weight names (e.g., "layers.0.mlp.gate_proj")
    /// - `in_dim`: Input dimension
    /// - `out_dim`: Output dimension
    /// - `group_size`: Group size for quantization (use 128 as default)
    /// - `_symmetric`: Whether quantization is symmetric (currently unused)
    /// - `device`: Target device
    pub fn load_direct(
        tensors: &HashMap<String, Tensor>,
        prefix: &str,
        in_dim: usize,
        out_dim: usize,
        _group_size: usize,
        _symmetric: bool,
        device: &candle_core::Device,
    ) -> Result<Self> {
        let weight_4bit_key = format!("{}.weight_4bit", prefix);
        let scales_4bit_key = format!("{}.scales_4bit", prefix);
        let bias_key = format!("{}.bias", prefix);

        // Try to load 4-bit format
        if let (Some(weight_packed), Some(scales)) =
            (tensors.get(&weight_4bit_key), tensors.get(&scales_4bit_key))
        {
            debug!("Loading 4bit format for {}", prefix);

            let weight_packed = weight_packed.to_device(device)?;
            let scales = scales.to_device(device)?;
            let bias = tensors
                .get(&bias_key)
                .map(|t| t.to_device(device))
                .transpose()?;

            let scales_dims = scales.dims();
            let n_groups = scales_dims[1];
            let group_size = in_dim.div_ceil(n_groups);

            return Self::new(weight_packed, scales, bias, group_size, in_dim, out_dim);
        }

        Err(candle_core::Error::Msg(format!(
            "No 4-bit weights found for prefix: {}",
            prefix
        )))
    }

    /// Unpack 4-bit weights to FP32 format.
    ///
    /// 4ビット重みをFP32形式にアンパック。
    ///
    /// # Returns
    /// Unpacked weights tensor [out_features, in_features] as F32
    fn unpack_4bit(&self) -> Result<Tensor> {
        let device = self.weight_packed.device();
        let packed_data = self.weight_packed.to_vec2::<u8>()?;
        let scales_data = self
            .scales
            .to_dtype(candle_core::DType::F32)?
            .to_vec2::<f32>()?;

        let mut unpacked = Vec::with_capacity(self.out_features * self.in_features);

        for (packed_row, scales_row) in packed_data.iter().zip(scales_data.iter()) {
            let mut row = Vec::with_capacity(self.in_features);

            for (in_idx, &packed_byte) in packed_row.iter().enumerate() {
                // Extract two 4-bit weights from each byte
                // Lower 4 bits: first weight
                // Upper 4 bits: second weight
                let w1 = (packed_byte & 0x0F) as i8;
                let w2 = ((packed_byte >> 4) & 0x0F) as i8;

                // Convert unsigned 4-bit (0-15) to signed 4-bit range [-8, 7]
                // Python uses +8 offset: original -8~7 → stored 0~15
                // So we subtract 8 to get back the original value
                let w1_signed = w1 - 8;
                let w2_signed = w2 - 8;

                // Determine which group each weight belongs to
                let pos1 = in_idx * 2;
                let pos2 = in_idx * 2 + 1;

                if pos1 < self.in_features {
                    let group_idx1 = pos1 / self.group_size;
                    let scale1 = scales_row[group_idx1];
                    let dequant1 = w1_signed as f32 * scale1;
                    row.push(dequant1);
                }

                if pos2 < self.in_features {
                    let group_idx2 = pos2 / self.group_size;
                    let scale2 = scales_row[group_idx2];
                    let dequant2 = w2_signed as f32 * scale2;
                    row.push(dequant2);
                }
            }

            // Pad row if necessary (due to packing)
            while row.len() < self.in_features {
                row.push(0.0);
            }
            row.truncate(self.in_features);

            unpacked.extend(row);
        }

        Tensor::from_vec(unpacked, (self.out_features, self.in_features), device)
    }

    /// Forward pass: Y = X @ W^T + b
    ///
    /// 順伝播: Y = X @ W^T + b
    ///
    /// Uses fused 4-bit GEMM for better performance.
    /// Automatically routes to CUDA kernel when input is on GPU.
    ///
    /// # Arguments / 引数
    /// - `input`: Input tensor [..., in_features]
    ///
    /// # Returns / 戻り値
    /// Output tensor [..., out_features]
    pub fn forward(&self, input: &Tensor) -> Result<Tensor> {
        // Handle batch dimensions by flattening
        let (input_2d, original_shape) = if input.rank() > 2 {
            let dims = input.dims();
            let last_dim = dims[dims.len() - 1];
            let batch_size = input.elem_count() / last_dim;
            (input.reshape(&[batch_size, last_dim])?, Some(dims.to_vec()))
        } else {
            (input.clone(), None)
        };

        // Use fused 4-bit GEMM (CPU or CUDA depending on device)
        let output = crate::kernels::matmul_4bit::gemm_4bit(
            &input_2d,
            &self.weight_packed,
            &self.scales,
            self.group_size,
        )?;

        // Add bias if present
        let output = match &self.bias {
            Some(bias) => output.broadcast_add(bias)?,
            None => output,
        };

        // Reshape back to original shape if needed
        if let Some(mut dims) = original_shape {
            let last_idx = dims.len() - 1;
            dims[last_idx] = self.out_features;
            output.reshape(&dims[..])
        } else {
            Ok(output)
        }
    }

    /// Forward pass with weight unpacking (legacy path).
    ///
    /// This method unpacks weights to FP32 before matmul.
    /// Use `forward()` for better performance with fused GEMM.
    pub fn forward_unpack(&self, input: &Tensor) -> Result<Tensor> {
        // Handle batch dimensions by flattening
        let (input_2d, original_shape) = if input.rank() > 2 {
            let dims = input.dims();
            let last_dim = dims[dims.len() - 1];
            let batch_size = input.elem_count() / last_dim;
            (input.reshape(&[batch_size, last_dim])?, Some(dims.to_vec()))
        } else {
            (input.clone(), None)
        };

        // Unpack weights
        let weight = self.unpack_4bit()?;

        // Matrix multiplication: input @ weight^T
        let output = input_2d.matmul(&weight.t()?)?;

        // Add bias if present
        let output = match &self.bias {
            Some(bias) => output.broadcast_add(bias)?,
            None => output,
        };

        // Reshape back to original shape if needed
        if let Some(mut dims) = original_shape {
            let last_idx = dims.len() - 1;
            dims[last_idx] = self.out_features;
            output.reshape(&dims[..])
        } else {
            Ok(output)
        }
    }
}

#[cfg(test)]
mod tests {
    use super::*;
    use candle_core::{Device, Tensor};

    fn create_test_layer() -> Result<Linear4Bit> {
        let device = Device::Cpu;

        // Create test data: 4x8 layer with group_size=4
        let out_features = 4usize;
        let in_features = 8usize;
        let group_size = 4usize;
        let n_groups = in_features.div_ceil(group_size);

        // Create packed weights (random-ish data)
        let weight_packed_data: Vec<u8> = vec![
            0x12, 0x34, 0x56, 0x78, // Row 0: 4 bytes = 8 weights
            0x9A, 0xBC, 0xDE, 0xF0, // Row 1
            0x11, 0x22, 0x33, 0x44, // Row 2
            0x55, 0x66, 0x77, 0x88, // Row 3
        ];
        let weight_packed =
            Tensor::from_vec(weight_packed_data, (out_features, in_features / 2), &device)?;

        // Create scales (2 groups)
        let scales_data = vec![
            [0.1f32, 0.2f32],   // Row 0 scales
            [0.15f32, 0.25f32], // Row 1 scales
            [0.12f32, 0.22f32], // Row 2 scales
            [0.18f32, 0.28f32], // Row 3 scales
        ];
        let scales = Tensor::from_vec(
            scales_data.into_iter().flatten().collect::<Vec<_>>(),
            (out_features, n_groups),
            &device,
        )?
        .to_dtype(candle_core::DType::F16)?;

        // Create bias
        let bias_data = vec![0.1f32, 0.2f32, 0.3f32, 0.4f32];
        let bias = Some(Tensor::from_vec(bias_data, out_features, &device)?);

        Linear4Bit::new(
            weight_packed,
            scales,
            bias,
            group_size,
            in_features,
            out_features,
        )
    }

    #[test]
    fn test_linear_4bit_creation() -> Result<()> {
        let layer = create_test_layer()?;
        assert_eq!(layer.in_features, 8);
        assert_eq!(layer.out_features, 4);
        assert_eq!(layer.group_size, 4);
        assert!(layer.bias.is_some());
        Ok(())
    }

    #[test]
    fn test_linear_4bit_unpack() -> Result<()> {
        let layer = create_test_layer()?;
        let unpacked = layer.unpack_4bit()?;
        let dims = unpacked.dims();
        assert_eq!(dims, [4, 8]); // [out_features, in_features]
        Ok(())
    }

    #[test]
    fn test_linear_4bit_forward() -> Result<()> {
        let layer = create_test_layer()?;
        let device = Device::Cpu;

        // Test 2D input (ensure F32)
        let input_2d = Tensor::randn(0.0f32, 1.0, (2, 8), &device)?;
        let output_2d = layer.forward(&input_2d)?;
        assert_eq!(output_2d.dims(), [2, 4]);

        // Test 3D input (with batch, ensure F32)
        let input_3d = Tensor::randn(0.0f32, 1.0, (3, 5, 8), &device)?;
        let output_3d = layer.forward(&input_3d)?;
        assert_eq!(output_3d.dims(), [3, 5, 4]);

        Ok(())
    }

    #[test]
    fn test_4bit_weight_unpacking() -> Result<()> {
        // Test specific 4-bit unpacking logic
        let device = Device::Cpu;

        // Test byte: 0x12 = 0001 0010
        // Lower 4 bits (first weight): 0010 = 2
        // Upper 4 bits (second weight): 0001 = 1
        let packed_data = vec![0x12u8];
        let weight_packed = Tensor::from_vec(packed_data, (1, 1), &device)?;

        let scales_data = vec![1.0f32, 1.0f32]; // Two groups, scale 1.0
        let scales =
            Tensor::from_vec(scales_data, (1, 2), &device)?.to_dtype(candle_core::DType::F16)?;

        let layer = Linear4Bit::new(
            weight_packed,
            scales,
            None,
            1, // group_size
            2, // in_features (2 weights from 1 byte)
            1, // out_features
        )?;

        let unpacked = layer.unpack_4bit()?;
        let data = unpacked.to_vec2::<f32>()?;

        // packed = 0x12: low nibble = 2, high nibble = 1
        // With -8 offset: 2-8 = -6, 1-8 = -7
        // With scale=1.0: [-6.0, -7.0]
        assert_eq!(data[0][0], -6.0);
        assert_eq!(data[0][1], -7.0);

        Ok(())
    }
}
