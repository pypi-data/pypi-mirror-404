//! BitLinear - 1.58-bit Quantized Linear Layer
//!
//! BitLinear層は、BitNet b1.58論文に基づく1.58ビット量子化線形層です。
//! 重みを{-1, 0, +1}の三値に量子化することで、メモリ使用量を大幅に削減し、
//! 乗算をビット演算に置き換えることで高速な推論を実現します。
//!
//! This module implements the BitLinear layer based on the BitNet b1.58 paper.
//! By quantizing weights to ternary values {-1, 0, +1}, it significantly reduces
//! memory usage and replaces multiplications with bit operations for faster inference.
//!
//! # Architecture / アーキテクチャ
//!
//! - **Training (学習時)**: Straight-Through Estimator (STE) で勾配を近似
//! - **Inference (推論時)**: Pre-packed weights で最適化されたカーネルを使用
//!
//! # Quantization / 量子化方式
//!
//! ```text
//! W_quant = round(clamp(W / scale, -1, 1))
//! scale = mean(|W|)
//!
//! Note: Uses BitTTTError for unified error handling across the crate.
//! ```
//!
//! # Dual Kernel Support / デュアルカーネル対応
//!
//! - **CPU**: AVX2/FMA最適化されたSIMDカーネル
//! - **CUDA**: BitNet専用カスタムカーネル

use candle_core::{Device, Result, Tensor};
use candle_nn::VarBuilder;

use crate::error::BitTTTError;
use crate::kernels::packing::PackedTensor;
use crate::kernels::{cpu::BitLinearCpu, cuda::BitLinearCuda};

/// Standard BitLinear layer implementing 1.58-bit quantization.
///
/// 1.58ビット量子化を実装する標準BitLinear層。
/// 推論時はpre-packedウェイトにより最適化されます。
///
/// Optimized for inference with pre-packed weights that enable
/// efficient ternary matrix multiplication on both CPU and CUDA.
#[derive(Clone)]
pub struct BitLinear {
    pub weight: Tensor,
    /// Input feature dimension (retained for introspection/serialization)
    #[allow(dead_code)]
    pub in_features: usize,
    /// Output feature dimension (retained for introspection/serialization)
    #[allow(dead_code)]
    pub out_features: usize,
    /// Simply-packed weights for 1.58-bit kernels (Dual Device Support)
    pub packed_params: Option<PackedTensor>,
}

impl BitLinear {
    /// Load weights from a VarBuilder (checkpoint/safetensors).
    ///
    /// VarBuilderからウェイトをロードします（チェックポイント/safetensorsから）。
    /// mmap使用時のメモリ安全性のため、CPU上では明示的にデータをコピーします。
    ///
    /// # Arguments / 引数
    /// - `in_dim`: Input dimension / 入力次元
    /// - `out_dim`: Output dimension / 出力次元
    /// - `vb`: VarBuilder for loading weights / ウェイトロード用VarBuilder
    /// - `device`: Target device (CPU/CUDA) / ターゲットデバイス
    pub fn load(in_dim: usize, out_dim: usize, vb: VarBuilder, device: &Device) -> Result<Self> {
        let init = candle_nn::init::DEFAULT_KAIMING_NORMAL;
        let weight = vb.get_with_hints((out_dim, in_dim), "weight", init)?;

        // [Plan B] Explicit Mmap Detachment
        let weight = if device.is_cpu() {
            let data = weight.to_vec1::<f32>()?;
            Tensor::from_vec(data, weight.shape(), device)?
        } else {
            weight.to_device(device)?
        };
        Ok(Self {
            weight,
            in_features: in_dim,
            out_features: out_dim,
            packed_params: None,
        })
    }

    /// Load from pre-loaded weight tensor (legacy FP32/FP16 format).
    ///
    /// 事前ロードしたウェイトテンソルからロードします（レガシーFP32/FP16形式）。
    ///
    /// # Arguments / 引数
    /// - `weight`: Weight tensor `[out_dim, in_dim]`
    /// - `in_dim`: Input dimension / 入力次元
    /// - `out_dim`: Output dimension / 出力次元
    /// - `device`: Target device / ターゲットデバイス
    pub fn from_weight_tensor(
        weight: &Tensor,
        in_dim: usize,
        out_dim: usize,
        device: &Device,
    ) -> Result<Self> {
        // Move to device and ensure F32
        let weight = weight
            .to_dtype(candle_core::DType::F32)?
            .to_device(device)?;

        // Verify shape
        let dims = weight.dims();
        if dims != [out_dim, in_dim] {
            return Err(candle_core::Error::Msg(format!(
                "Weight shape mismatch: expected [{}, {}], got {:?}",
                out_dim, in_dim, dims
            )));
        }

        // Deep copy to detach from mmap
        let weight = if device.is_cpu() {
            let data = weight.flatten_all()?.to_vec1::<f32>()?;
            Tensor::from_vec(data, (out_dim, in_dim), device)?
        } else {
            weight
        };

        Ok(Self {
            weight,
            in_features: in_dim,
            out_features: out_dim,
            packed_params: None,
        })
    }

    /// Load from pre-loaded Bit-TTT tensors (weight_packed + scales).
    ///
    /// 事前ロード済みのBit-TTTテンソル（weight_packed + scales）からロードします。
    ///
    /// This is the recommended way to load quantized models, as it avoids
    /// VarBuilder dtype issues with U8 tensors.
    ///
    /// # Arguments / 引数
    /// - `weight_packed`: Packed weights `[out_dim, in_dim/4]` or `[out_dim, in_dim/4, n_bases]` as U8
    /// - `scales`: Per-base scales `[n_bases]` as F32
    /// - `device`: Target device (CPU/CUDA) / ターゲットデバイス
    ///
    /// # Example
    /// ```ignore
    /// let tensors = candle_core::safetensors::load(&path, &device)?;
    /// let packed = tensors.get("layer.weight_packed").unwrap();
    /// let scales = tensors.get("layer.scales").unwrap();
    /// let layer = BitLinear::from_packed_tensors(packed, scales, &device)?;
    /// ```
    pub fn from_packed_tensors(
        weight_packed: &Tensor,
        scales: &Tensor,
        device: &Device,
    ) -> Result<Self> {
        let dims = weight_packed.dims();

        // Extract dimensions from packed tensor
        // [out_dim, in_dim/4] or [out_dim, in_dim/4, n_bases]
        let (out_dim, in_dim, _n_bases) = match dims.len() {
            2 => (dims[0], dims[1] * 4, 1usize),
            3 => (dims[0], dims[1] * 4, dims[2]),
            _ => {
                return Err(candle_core::Error::Msg(format!(
                    "Invalid weight_packed shape: expected 2D or 3D, got {:?}",
                    dims
                )))
            }
        };

        // Move tensors to device and ensure correct dtype
        // VarBuilder.get() may return F32 even for U8 safetensors, so we need to handle this
        let packed_data = if weight_packed.dtype() != candle_core::DType::U8 {
            // Convert F32 weights back to U8 (happens when VarBuilder auto-converts)
            eprintln!(
                "⚠️ [PACKED] Converting {:?} → U8 (VarBuilder dtype issue)",
                weight_packed.dtype()
            );
            weight_packed
                .to_dtype(candle_core::DType::U8)?
                .to_device(device)?
        } else {
            weight_packed.to_device(device)?
        };
        let scales_data = scales
            .to_dtype(candle_core::DType::F32)?
            .to_device(device)?;

        // Create PackedTensor
        let packed_params =
            PackedTensor::from_loaded(packed_data, scales_data, out_dim, in_dim, device)?;

        // Create dummy weight tensor (not used in forward when packed_params exists)
        let weight = Tensor::zeros((out_dim, in_dim), candle_core::DType::F32, device)?;

        Ok(Self {
            weight,
            in_features: in_dim,
            out_features: out_dim,
            packed_params: Some(packed_params),
        })
    }

    /// Load from Bit-TTT quantized format via VarBuilder.
    ///
    /// **Note**: VarBuilder has issues with U8 tensors. Prefer `from_packed_tensors()`.
    ///
    /// Bit-TTT形式の量子化済みウェイトをVarBuilder経由でロード。
    /// **注意**: VarBuilderはU8テンソルに問題があるため、`from_packed_tensors()`を推奨。
    #[allow(dead_code)]
    pub fn load_packed(
        in_dim: usize,
        out_dim: usize,
        n_bases: usize,
        vb: VarBuilder,
        device: &Device,
    ) -> Result<Self> {
        // Try to load packed format
        let packed_shape = if n_bases == 1 {
            vec![out_dim, in_dim / 4]
        } else {
            vec![out_dim, in_dim / 4, n_bases]
        };

        let packed_result = vb.get(packed_shape.as_slice(), "weight_packed");
        let scales_result = vb.get(&[n_bases], "scales");

        match (packed_result, scales_result) {
            (Ok(packed_raw), Ok(scales)) => {
                // Ensure packed data is on correct device and dtype
                let packed_data = packed_raw.to_device(device)?;
                let scales_data = scales
                    .to_dtype(candle_core::DType::F32)?
                    .to_device(device)?;

                // Create PackedTensor from loaded data
                let packed_params =
                    PackedTensor::from_loaded(packed_data, scales_data, out_dim, in_dim, device)?;

                // Create dummy weight tensor (not used in forward when packed_params exists)
                let weight = Tensor::zeros((out_dim, in_dim), candle_core::DType::F32, device)?;

                Ok(Self {
                    weight,
                    in_features: in_dim,
                    out_features: out_dim,
                    packed_params: Some(packed_params),
                })
            }
            _ => {
                // Fallback to regular load for FP32/FP16 weights
                Self::load(in_dim, out_dim, vb, device)
            }
        }
    }

    /// Pre-compute packed weights for optimized inference via Dual Kernels.
    ///
    /// デュアルカーネル用に最適化されたpacked weightsを事前計算します。
    /// この関数は推論前に一度だけ呼び出してください。
    ///
    /// This quantizes the weights to ternary values and packs them into
    /// 2-bit format (4 weights per byte) for efficient SIMD/GPU processing.
    ///
    /// 重みを三値に量子化し、2ビット形式（1バイトあたり4ウェイト）に
    /// パッキングしてSIMD/GPU処理を効率化します。
    pub fn precompute_packed(&mut self) -> Result<()> {
        // This function quantizes the weights and packs them into 2-bit format.
        // It populates `self.packed_params`.
        let packed = PackedTensor::pack(&self.weight)?;
        self.packed_params = Some(packed);
        Ok(())
    }

    /// Forward pass: Y = X @ W^T (with automatic kernel dispatch).
    ///
    /// 順伝播: Y = X @ W^T（自動カーネルディスパッチ付き）。
    ///
    /// # Execution Paths / 実行パス
    ///
    /// 1. **Dual Kernel Path** (推論時推奨): `packed_params`が存在する場合、
    ///    デバイスに応じて最適化カーネル（AVX2/CUDA）を自動選択
    /// 2. **Legacy STE Path** (学習時): Straight-Through Estimatorで勾配を近似
    ///
    /// # Arguments / 引数
    /// - `x`: Input tensor of shape `[..., in_features]`
    ///
    /// # Returns / 戻り値
    /// Output tensor of shape `[..., out_features]`
    pub fn forward(&self, x: &Tensor) -> Result<Tensor> {
        // Handle Rank > 2 inputs (e.g. [Batch, Seq, Hidden]) via flattening
        let (input, original_shape) = if x.rank() > 2 {
            let dims = x.dims();
            let last_dim = dims[dims.len() - 1];
            let flattened_dim = x.elem_count() / last_dim;
            // flatten to [Batch*Seq, Hidden]
            (x.reshape(&[flattened_dim, last_dim])?, Some(dims.to_vec()))
        } else {
            (x.clone(), None)
        };

        // 1. Dual Kernel Path (Fastest, 1.58-bit Native)
        if let Some(packed) = &self.packed_params {
            // Automatic Dispatch based on device
            let result = match input.device() {
                Device::Cpu => {
                    // Use Optimized CPU Kernel (AVX2)
                    BitLinearCpu::forward(&input, packed)
                }
                Device::Cuda(_) => {
                    // Use Custom CUDA Kernel (BitNet)
                    BitLinearCuda::forward(&input, packed)
                }
                _ => {
                    // Fallback to legacy path if kernel not available for device
                    // But we don't have a fallback return here easily without code dupe or rearranging.
                    // For now, let's assume if packed exists, we must use kernel or fail.
                    // Or we can assume packing only happens if supported?
                    return Err(BitTTTError::kernel_error(
                        "Packed params present but Custom Kernel not implemented for this device",
                    )
                    .into());
                }
            }?;

            // Reshape back if needed
            if let Some(mut dims) = original_shape {
                let last_idx = dims.len() - 1;
                let (_total, out_dim) = result.dims2()?;
                dims[last_idx] = out_dim;
                return result.reshape(&dims[..]);
            } else {
                return Ok(result);
            }
        }

        // 3. Legacy Fallback (FP16/FP32 weights - no quantization)
        // Used for pre-quantized models that have been dequantized to FP16
        #[cfg(debug_assertions)]
        tracing::debug!("📦 BitLinear: Using legacy FP path (no STE quantization)");

        // Simple matmul without quantization simulation
        // The weights are already in their final form (FP16/FP32)
        let result = input.matmul(&self.weight.t()?)?;

        // Reshape back if needed
        if let Some(mut dims) = original_shape {
            let last_idx = dims.len() - 1;
            dims[last_idx] = self.out_features;
            result.reshape(&dims[..])
        } else {
            Ok(result)
        }
    }
}
