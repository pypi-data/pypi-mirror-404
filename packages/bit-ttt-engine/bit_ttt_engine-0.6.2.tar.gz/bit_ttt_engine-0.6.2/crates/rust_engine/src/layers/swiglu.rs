//! SwiGLU - Gated MLP with SiLU activation

use candle_core::Result;
use candle_core::Tensor;
use candle_nn::VarBuilder;
use std::collections::HashMap;

use super::AdaptiveBitLinear;
use crate::model::config::QuantizationConfig;

/// SwiGLU MLP block (Gate, Down, Up projections)
pub struct SwiGLU {
    pub w1: AdaptiveBitLinear, // Gate
    pub w2: AdaptiveBitLinear, // Down
    pub w3: AdaptiveBitLinear, // Up
}

impl SwiGLU {
    /// Load directly from pre-loaded tensor HashMap (bypasses VarBuilder).
    ///
    /// # Arguments
    /// - `tensors`: Pre-loaded tensors from `candle_core::safetensors::load()`
    /// - `prefix`: Layer prefix (e.g., "model.layers.0.mlp")
    /// - `hidden_dim`: Hidden dimension
    /// - `intermediate_dim`: Intermediate dimension
    /// - `device`: Target device
    /// - `quantization`: Quantization configuration (for 4-bit support)
    pub fn load_direct(
        tensors: &HashMap<String, Tensor>,
        prefix: &str,
        hidden_dim: usize,
        intermediate_dim: usize,
        device: &candle_core::Device,
        quantization: &Option<QuantizationConfig>,
    ) -> Result<Self> {
        let w1 = AdaptiveBitLinear::load_direct(
            tensors,
            &format!("{}.gate_proj", prefix),
            hidden_dim,
            intermediate_dim,
            device,
            quantization,
        )?;
        let w2 = AdaptiveBitLinear::load_direct(
            tensors,
            &format!("{}.down_proj", prefix),
            intermediate_dim,
            hidden_dim,
            device,
            quantization,
        )?;
        let w3 = AdaptiveBitLinear::load_direct(
            tensors,
            &format!("{}.up_proj", prefix),
            hidden_dim,
            intermediate_dim,
            device,
            quantization,
        )?;
        Ok(Self { w1, w2, w3 })
    }

    pub fn load(
        hidden_dim: usize,
        intermediate_dim: usize,
        vb: VarBuilder,
        device: &candle_core::Device,
    ) -> Result<Self> {
        let w1 = AdaptiveBitLinear::load(hidden_dim, intermediate_dim, vb.pp("gate_proj"), device)?;
        let w2 = AdaptiveBitLinear::load(intermediate_dim, hidden_dim, vb.pp("down_proj"), device)?;
        let w3 = AdaptiveBitLinear::load(hidden_dim, intermediate_dim, vb.pp("up_proj"), device)?;
        Ok(Self { w1, w2, w3 })
    }

    pub fn forward(&self, x: &Tensor) -> Result<Tensor> {
        let x_gate = self.w1.forward(x)?;
        let x_up = self.w3.forward(x)?;
        let silu_gate = candle_nn::ops::silu(&x_gate)?;
        let hidden = (silu_gate * x_up)?;
        self.w2.forward(&hidden)
    }

    pub fn precompute_packed(&mut self) -> Result<()> {
        self.w1.precompute_packed()?;
        self.w2.precompute_packed()?;
        self.w3.precompute_packed()?;
        Ok(())
    }
}
