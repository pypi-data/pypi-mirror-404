//! Layers Module - Core neural network layers
//!
//! This module contains the building blocks for the Bit-Llama architecture:
//! - RMSNorm: Root Mean Square Layer Normalization
//! - BitLinear: 1.58-bit quantized linear layer
//! - SwiGLU: Gated MLP with SiLU activation
//! - TTTLayer: Test-Time Training with online learning

use candle_core::{Result, Tensor};

pub mod adaptive_linear;
pub mod attention;
pub mod bit_linear;
#[cfg(feature = "flash-attention")]
pub mod flash_attention;
pub mod isomorphic;
pub mod kv_cache;
pub mod linear_4bit; // 4-bit quantized linear layer
pub mod rms_norm;
pub mod swiglu;
pub mod ttt;

pub use adaptive_linear::AdaptiveBitLinear;
pub use attention::{BitAttention, KVCache};
pub use bit_linear::BitLinear;
pub use isomorphic::{IsomorphicOffloader, LayerPlacement, MemoryPressure};
pub use kv_cache::QuantizedKVCache;
pub use linear_4bit::Linear4Bit;
pub use rms_norm::RMSNorm;
pub use swiglu::SwiGLU;
pub use ttt::TTTLayer;

#[cfg(feature = "flash-attention")]
pub use flash_attention::{flash_attention, FlashAttentionConfig};

// --- Helper Trait for Robust Operations ---
#[allow(dead_code)]
pub(crate) trait TensorExt {
    fn matmul_robust(&self, rhs: &Tensor) -> Result<Tensor>;
}

impl TensorExt for Tensor {
    fn matmul_robust(&self, rhs: &Tensor) -> Result<Tensor> {
        let lhs = self.contiguous()?;
        let rhs = rhs.contiguous()?;
        let lhs_rank = lhs.rank();

        // [Hybrid Guard] Ensure rhs is on same device as lhs
        let rhs = if rhs.device().same_device(lhs.device()) {
            rhs.clone()
        } else {
            // eprintln!("🚀 [MatMul] Moving tensor {:?} -> {:?}", rhs.device(), lhs.device());
            rhs.to_device(lhs.device())?
        };
        let rhs = &rhs;

        if lhs_rank == 1 {
            lhs.unsqueeze(0)?.matmul(rhs)?.squeeze(0)
        } else if lhs_rank == 2 {
            lhs.matmul(rhs)
        } else {
            let flattened = lhs.flatten(0, lhs_rank - 2)?;
            let out = flattened.matmul(rhs)?;
            let mut new_shape = lhs.dims()[..lhs_rank - 1].to_vec();
            new_shape.push(out.dim(1)?);
            out.reshape(new_shape)
        }
    }
}
