//! Cortex Rust Engine
//!
//! Core implementation of the Bit-Llama model with TTT (Test-Time Training) support.
//! Provides native Rust, Python, and WebAssembly bindings.

#![allow(non_local_definitions)]

// Core modules (Rust 2018+ style)
pub mod device_utils;
pub mod download;
pub mod error;
pub mod eval;
pub mod kernels;
pub mod layers;
pub mod model;
pub mod optim;
pub mod paged_attention;
pub mod scheduler;
pub mod speculative;

#[cfg(feature = "python")]
pub mod python;

// WebAssembly module
#[cfg(feature = "wasm")]
pub mod wasm;

// Primary public API re-exports
pub use eval::{compute_perplexity, PerplexityResult};
pub use layers::{BitLinear, Linear4Bit, RMSNorm, SwiGLU, TTTLayer};
#[cfg(feature = "tokenizers")]
pub use model::Llama;
pub use model::{defaults, ModelConfig};
pub use model::{
    ActivationType, BitLlama, BitLlamaBlock, BitLlamaConfig, GgufLoader, GgufModel, GgufTensorInfo,
    LayerDispatch, ModelArch, ModelType, UnifiedModel,
};

// Alias for backward compatibility
pub use model::TTTLayer as CandleTTTLayer;

// Python module registration
#[cfg(feature = "python")]
use pyo3::prelude::*;

#[cfg(feature = "python")]
#[pymodule]
fn cortex_rust(m: &Bound<'_, PyModule>) -> PyResult<()> {
    m.add_class::<python::PyBitLlama>()?;
    m.add_class::<python::PyTrainer>()?;
    Ok(())
}

// Basic inference function (simplified to work across platforms)
pub fn infer(input: &str) -> Result<String, String> {
    // Placeholder implementation
    // TODO: Adapt core inference for cross-platform support
    let result = format!("Processed input: {}", input);
    Ok(result)
}

#[cfg(test)]
#[path = "tests/attention_test.rs"]
mod attention_test;

#[cfg(test)]
#[path = "tests/isomorphic_test.rs"]
mod isomorphic_test;

#[cfg(test)]
#[path = "tests/bit_linear_test.rs"]
mod bit_linear_test;

#[cfg(test)]
#[path = "tests/ttt_test.rs"]
mod ttt_test;

#[cfg(test)]
#[path = "tests/format_diagnosis.rs"]
mod format_diagnosis;
