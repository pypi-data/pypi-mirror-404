//! Model Module - BitLlama model architecture
//!
//! This module contains the complete model implementation:
//! - BitLlamaBlock: Single transformer block with TTT + MLP
//! - BitLlama: Full model with embedding, layers, and LM head
//! - BitLlamaConfig: Model configuration
//! - Llama: High-level API with tokenizer
//! - GgufLoader: GGUF format model loader

pub mod block;
pub mod config;
pub mod config_common;
pub mod detector;
pub mod gguf_loader;
pub mod gguf_model;
pub mod llama; // Now a directory with mod.rs
pub mod llama_4bit;
pub mod unified;

pub use block::{BitLlamaBlock, LayerDispatch};
pub use config::{ActivationType, BitLlamaConfig, ModelArch};
pub use config_common::{defaults, ModelConfig};
pub use detector::{ModelArchitecture, ModelDetector, ModelInfo, OptimalConfig, QuantizationType};
pub use gguf_loader::{GgufLoader, TensorInfo as GgufTensorInfo};
pub use gguf_model::GgufModel;
pub use llama::BitLlama;
#[cfg(feature = "tokenizers")]
pub use llama::Llama; // Re-exported from llama/mod.rs (requires tokenizers feature)
pub use llama_4bit::{Llama4Bit, Llama4BitConfig};
pub use unified::{ModelType, UnifiedModel};

// Re-export TTTLayer for backward compatibility alias
pub use crate::layers::TTTLayer;
