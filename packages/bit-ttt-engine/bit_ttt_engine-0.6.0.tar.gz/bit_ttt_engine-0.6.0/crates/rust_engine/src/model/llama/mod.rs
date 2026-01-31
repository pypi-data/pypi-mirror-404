//! Llama model implementations
//!
//! This module contains:
//! - `BitLlama` - Low-level model with 1.58-bit quantization support
//! - `Llama` - High-level API with tokenizer and state management (requires tokenizers feature)

mod bitllama;
#[cfg(feature = "tokenizers")]
mod llama_fp16;

pub use bitllama::BitLlama;
#[cfg(feature = "tokenizers")]
pub use llama_fp16::Llama;

/// Epsilon for RMSNorm
pub(crate) const RMS_NORM_EPS: f64 = 1e-5;

/// Minimum temperature for sampling
#[allow(dead_code)]
pub(crate) const TEMP_MIN: f64 = 1e-6;
