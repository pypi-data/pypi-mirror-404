//! RMSNorm - Root Mean Square Layer Normalization

use candle_core::{Result, Tensor};
use candle_nn::VarBuilder;
use std::collections::HashMap;

use crate::kernels::fused_ops::rms_norm_cuda;

/// Root Mean Square Normalization layer
pub struct RMSNorm {
    pub weight: Tensor,
    pub eps: f64,
}

impl RMSNorm {
    /// Load directly from pre-loaded tensor HashMap (bypasses VarBuilder).
    ///
    /// # Arguments
    /// - `tensors`: Pre-loaded tensors from `candle_core::safetensors::load()`
    /// - `key`: Full tensor key (e.g., "model.layers.0.input_layernorm.weight")
    /// - `dim`: Dimension
    /// - `eps`: Epsilon for normalization
    /// - `device`: Target device
    pub fn load_direct(
        tensors: &HashMap<String, Tensor>,
        key: &str,
        dim: usize,
        eps: f64,
        device: &candle_core::Device,
    ) -> Result<Self> {
        let weight = tensors
            .get(key)
            .ok_or_else(|| candle_core::Error::Msg(format!("RMSNorm weight not found: {}", key)))?;

        // Deep copy to detach from mmap (convert F16 → F32 if needed)
        let weight_f32 = weight.to_dtype(candle_core::DType::F32)?;
        let weight = if device.is_cpu() {
            let data = weight_f32.to_vec1::<f32>()?;
            Tensor::from_vec(data, (dim,), device)?
        } else {
            weight_f32.to_device(device)?
        };

        Ok(Self { weight, eps })
    }

    pub fn load(
        dim: usize,
        eps: f64,
        vb: VarBuilder,
        device: &candle_core::Device,
    ) -> Result<Self> {
        let weight =
            vb.get_with_hints((dim,), "weight", candle_nn::init::DEFAULT_KAIMING_NORMAL)?;

        // [Plan B] Explicit Mmap Detachment
        // If loading to CPU, we must Deep Copy to allow dropping the Mmap file.
        let weight = if device.is_cpu() {
            let data = weight.to_vec1::<f32>()?;
            Tensor::from_vec(data, weight.shape(), device)?
        } else {
            weight.to_device(device)?
        };
        Ok(Self { weight, eps })
    }

    pub fn forward(&self, x: &Tensor) -> Result<Tensor> {
        // [Hybrid Guard] Ensure weight is on same device as input
        let weight = if self.weight.device().same_device(x.device()) {
            self.weight.clone()
        } else {
            self.weight.to_device(x.device())?
        };

        // Use CUDA-optimized kernel
        rms_norm_cuda(x, &weight, self.eps)
    }
}
