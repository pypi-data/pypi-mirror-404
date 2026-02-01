//! Common configuration traits and defaults
//!
//! Shared between rust_engine (BitLlamaConfig) and bit_llama (ProjectConfig)

/// Default values for model configuration
/// Centralized to avoid duplication
pub mod defaults {
    pub const VOCAB_SIZE: usize = 8000;
    pub const HIDDEN_DIM: usize = 256;
    pub const NUM_LAYERS: usize = 4;
    pub const N_HEADS: usize = 8;
    pub const CONTEXT_LEN: usize = 128;
    pub const ROPE_THETA: f64 = 10000.0;
    pub const MAX_POSITION_EMBEDDINGS: usize = 2048;
    pub const INNER_LR: f64 = 0.0;
    pub const LM_HEAD_CPU: bool = false;
}

/// Common model configuration trait
/// Implemented by both BitLlamaConfig and ProjectConfig
pub trait ModelConfig {
    fn vocab_size(&self) -> usize;
    fn hidden_dim(&self) -> usize;
    fn num_layers(&self) -> usize;
    fn n_heads(&self) -> usize;
    fn n_kv_heads(&self) -> usize;
    fn rope_theta(&self) -> f64;
    fn max_position_embeddings(&self) -> usize;
    fn lm_head_cpu(&self) -> bool;
}
