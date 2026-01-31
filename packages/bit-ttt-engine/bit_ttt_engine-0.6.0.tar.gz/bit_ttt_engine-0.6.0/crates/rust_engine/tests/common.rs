//! Common test utilities for integration tests.
//!
//! This module provides path helpers that work across different environments
//! (Windows, Linux, macOS, Termux, CI).

use std::path::PathBuf;

/// Get the path to the tiny-converted test model.
///
/// # Environment Variable
/// Set `BIT_TEST_MODEL_PATH` to override the default path.
///
/// # Default
/// Falls back to `../../benchmark/tiny-converted` relative to the crate manifest.
#[allow(dead_code)]
pub fn get_test_model_path() -> PathBuf {
    std::env::var("BIT_TEST_MODEL_PATH")
        .map(PathBuf::from)
        .unwrap_or_else(|_| {
            PathBuf::from(env!("CARGO_MANIFEST_DIR")).join("../../benchmark/tiny-converted")
        })
}

/// Get the path to the tiny-converted model.safetensors file.
#[allow(dead_code)]
pub fn get_test_model_safetensors() -> PathBuf {
    get_test_model_path().join("model.safetensors")
}

/// Get the path to the TinyLlama 1.1B converted test model.
///
/// # Environment Variable
/// Set `BIT_TEST_TINYLLAMA_PATH` to override the default path.
///
/// # Default
/// Falls back to `../../benchmark/tinyllama-1.1b-converted` relative to the crate manifest.
#[allow(dead_code)]
pub fn get_tinyllama_model_path() -> PathBuf {
    std::env::var("BIT_TEST_TINYLLAMA_PATH")
        .map(PathBuf::from)
        .unwrap_or_else(|_| {
            PathBuf::from(env!("CARGO_MANIFEST_DIR"))
                .join("../../benchmark/tinyllama-1.1b-converted")
        })
}

/// Get the path to the TinyLlama model.safetensors file.
#[allow(dead_code)]
pub fn get_tinyllama_model_safetensors() -> PathBuf {
    get_tinyllama_model_path().join("model.safetensors")
}

/// Get the path to a GGUF test model.
///
/// # Environment Variable
/// Set `BIT_TEST_GGUF_PATH` to override the default path.
///
/// # Default
/// Falls back to `../../models/tinyllama-1.1b-chat-v1.0.Q4_K_M.gguf` relative to the crate manifest.
#[allow(dead_code)]
pub fn get_gguf_model_path() -> PathBuf {
    std::env::var("BIT_TEST_GGUF_PATH")
        .map(PathBuf::from)
        .unwrap_or_else(|_| {
            PathBuf::from(env!("CARGO_MANIFEST_DIR"))
                .join("../../models/tinyllama-1.1b-chat-v1.0.Q4_K_M.gguf")
        })
}
