//! BitLlamaConfig - Model configuration

use serde::Deserialize;

#[cfg(feature = "python")]
use pyo3::prelude::*;

/// Quantization configuration for 4-bit models
#[derive(Clone, Debug, Deserialize, serde::Serialize)]
#[cfg_attr(feature = "python", derive(pyo3::FromPyObject))]
pub struct QuantizationConfig {
    #[serde(rename = "type")]
    pub quant_type: String, // "int4" or "int2"
    #[serde(default = "default_group_size")]
    pub group_size: usize,
    #[serde(default)]
    pub symmetric: bool,
}

fn default_group_size() -> usize {
    128
}

/// Model configuration for BitLlama
/// Model architecture type
#[derive(Clone, Copy, Debug, Deserialize, serde::Serialize, PartialEq, Eq)]
#[cfg_attr(feature = "python", pyo3::pyclass(eq, eq_int))]
#[derive(Default)]
pub enum ModelArch {
    #[serde(rename = "ttt")]
    #[default]
    TTT,
    #[serde(rename = "llama")]
    Llama,
    #[serde(rename = "gemma")]
    Gemma,
    #[serde(rename = "gemma2")]
    Gemma2,
}

/// MLP activation function type
#[cfg_attr(feature = "python", pyo3::pyclass(eq, eq_int))]
#[derive(Clone, Copy, Debug, Deserialize, serde::Serialize, PartialEq, Eq, Default)]
pub enum ActivationType {
    #[default]
    SiLU, // Llama, Mistral
    GELU, // Gemma, GPT
}

/// BitLlamaConfig for Python bindings
#[cfg(feature = "python")]
#[pyclass]
#[derive(Clone, Debug, Deserialize, serde::Serialize)]
pub struct BitLlamaConfig {
    #[pyo3(get, set)]
    #[serde(default)]
    pub arch: ModelArch,
    #[pyo3(get, set)]
    pub vocab_size: usize,
    #[pyo3(get, set)]
    #[serde(alias = "hidden_size")]
    pub hidden_dim: usize,
    #[pyo3(get, set)]
    #[serde(alias = "num_hidden_layers")]
    #[serde(alias = "n_layers")]
    pub num_layers: usize,
    #[pyo3(get, set)]
    #[serde(alias = "num_attention_heads")]
    pub n_heads: usize,
    #[pyo3(get, set)]
    #[serde(alias = "num_key_value_heads")]
    pub n_kv_heads: usize,
    #[pyo3(get, set)]
    #[serde(alias = "intermediate_size")]
    pub intermediate_dim: Option<usize>,
    #[pyo3(get, set)]
    #[serde(default)]
    pub inner_lr: f64,
    #[pyo3(get, set)]
    pub n_gpu_layers: Option<usize>,
    #[pyo3(get, set)]
    #[serde(default = "default_rope")]
    pub rope_theta: f64,
    #[pyo3(get, set)]
    #[serde(default = "default_max_pos")]
    pub max_position_embeddings: usize,
    #[pyo3(get, set)]
    #[serde(default)]
    pub lm_head_cpu: bool,
    /// Sliding window size (None = full attention)
    /// When set, only the most recent `sliding_window` tokens are kept in KV cache
    #[pyo3(get, set)]
    #[serde(default)]
    pub sliding_window: Option<usize>,
    /// Number of attention sink tokens to always keep (StreamingLLM)
    /// The first N tokens are never evicted, improving stability for long sequences
    #[pyo3(get, set)]
    #[serde(default)]
    pub attention_sink_size: Option<usize>,
    /// Quantization configuration for 4-bit models
    #[serde(default)]
    pub quantization: Option<QuantizationConfig>,
    /// RMS normalization epsilon (default: 1e-5)
    #[pyo3(get, set)]
    #[serde(default = "default_rms_norm_eps")]
    pub rms_norm_eps: f64,
    /// MLP activation function (default: SiLU for Llama, GELU for Gemma)
    #[pyo3(get, set)]
    #[serde(default)]
    pub activation: ActivationType,
}

/// BitLlamaConfig for Rust-only builds
#[cfg(not(feature = "python"))]
#[derive(Clone, Debug, Deserialize, serde::Serialize)]
pub struct BitLlamaConfig {
    #[serde(default)]
    pub arch: ModelArch,
    pub vocab_size: usize,
    #[serde(alias = "hidden_size")]
    pub hidden_dim: usize,
    #[serde(alias = "num_hidden_layers")]
    #[serde(alias = "n_layers")]
    pub num_layers: usize,
    #[serde(alias = "num_attention_heads")]
    pub n_heads: usize,
    #[serde(alias = "num_key_value_heads")]
    pub n_kv_heads: usize,
    #[serde(alias = "intermediate_size")]
    pub intermediate_dim: Option<usize>,
    #[serde(default)]
    pub inner_lr: f64,
    pub n_gpu_layers: Option<usize>,
    #[serde(default = "default_rope")]
    pub rope_theta: f64,
    #[serde(default = "default_max_pos")]
    pub max_position_embeddings: usize,
    #[serde(default)]
    pub lm_head_cpu: bool,
    /// Sliding window size (None = full attention)
    /// When set, only the most recent `sliding_window` tokens are kept in KV cache
    #[serde(default)]
    pub sliding_window: Option<usize>,
    /// Number of attention sink tokens to always keep (StreamingLLM)
    /// The first N tokens are never evicted, improving stability for long sequences
    #[serde(default)]
    pub attention_sink_size: Option<usize>,
    /// Quantization configuration for 4-bit models
    #[serde(default)]
    pub quantization: Option<QuantizationConfig>,
    /// RMS normalization epsilon (default: 1e-5)
    #[serde(default = "default_rms_norm_eps")]
    pub rms_norm_eps: f64,
    /// MLP activation function (default: SiLU for Llama, GELU for Gemma)
    #[serde(default)]
    pub activation: ActivationType,
}

fn default_rms_norm_eps() -> f64 {
    1e-5
}

fn default_rope() -> f64 {
    10000.0
}
fn default_max_pos() -> usize {
    2048
}

#[cfg(feature = "python")]
#[pymethods]
impl BitLlamaConfig {
    #[new]
    #[pyo3(signature = (vocab_size, hidden_dim, num_layers, inner_lr, lm_head_cpu=None, sliding_window=None, attention_sink_size=None))]
    pub fn new(
        vocab_size: usize,
        hidden_dim: usize,
        num_layers: usize,
        inner_lr: f64,
        lm_head_cpu: Option<bool>,
        sliding_window: Option<usize>,
        attention_sink_size: Option<usize>,
    ) -> Self {
        Self {
            arch: ModelArch::TTT,
            vocab_size,
            hidden_dim,
            num_layers,
            n_heads: hidden_dim / 64,
            n_kv_heads: hidden_dim / 64,
            intermediate_dim: Some(hidden_dim * 4),
            inner_lr,
            n_gpu_layers: None,
            rope_theta: 10000.0,
            max_position_embeddings: 2048,
            lm_head_cpu: lm_head_cpu.unwrap_or(false),
            sliding_window,
            attention_sink_size,
            quantization: None,
            rms_norm_eps: 1e-5,
            activation: ActivationType::SiLU,
        }
    }

    /// Calculate possible offload layers for given VRAM (bytes)
    /// Returns (n_gpu_layers, used_vram_mb)
    pub fn calculate_auto_offload(&self, vram_bytes: usize) -> (usize, f32) {
        let mb = 1024.0 * 1024.0;
        let available_mb = vram_bytes as f64 / mb;

        // Conservative constants
        let base_overhead = 500.0; // Reserve for CUDA context

        // Dynamic layer size calculation based on model dimensions
        // Formula: (hidden_dim^2 * 7 + hidden_dim * intermediate_dim * 3) / 10 / 1024 / 1024
        // This accounts for:
        //   - Attention weights: Q, K, V, O projections (~4 * hidden_dim^2)
        //   - TTT/RNN state weights (~3 * hidden_dim^2)
        //   - MLP weights: gate, up, down projections (~3 * hidden_dim * intermediate_dim)
        //   - /10 for 1.58-bit quantization factor
        let intermediate = self.intermediate_dim.unwrap_or(self.hidden_dim * 4);
        let layer_size = (self.hidden_dim as f64 * self.hidden_dim as f64 * 7.0
            + self.hidden_dim as f64 * intermediate as f64 * 3.0)
            / 10.0
            / mb;

        // KV cache per layer (scales with hidden_dim)
        // Roughly 2 * hidden_dim * max_seq_len * 2 (K + V) * sizeof(f16) / MB
        // For 2048 context: ~hidden_dim * 0.016 MB per layer
        let kv_cache_size = self.hidden_dim as f64 * 0.016;

        if available_mb < base_overhead {
            return (0, 0.0);
        }

        let usable = available_mb - base_overhead;
        let per_layer = layer_size + kv_cache_size;

        let n = (usable / per_layer).floor() as usize;
        let n = n.min(self.num_layers);

        let estimated = base_overhead + (n as f64 * per_layer);

        (n, estimated as f32)
    }
}

/// Implementation for Rust-only builds
#[cfg(not(feature = "python"))]
impl BitLlamaConfig {
    /// Calculate possible offload layers for given VRAM (bytes)
    /// Returns (n_gpu_layers, used_vram_mb)
    pub fn calculate_auto_offload(&self, vram_bytes: usize) -> (usize, f32) {
        let mb = 1024.0 * 1024.0;
        let available_mb = vram_bytes as f64 / mb;

        // Conservative constants
        let base_overhead = 500.0; // Reserve for CUDA context

        // Dynamic layer size calculation based on model dimensions
        // Formula: (hidden_dim^2 * 7 + hidden_dim * intermediate_dim * 3) / 10 / 1024 / 1024
        // This accounts for:
        //   - Attention weights: Q, K, V, O projections (~4 * hidden_dim^2)
        //   - TTT/RNN state weights (~3 * hidden_dim^2)
        //   - MLP weights: gate, up, down projections (~3 * hidden_dim * intermediate_dim)
        //   - /10 for 1.58-bit quantization factor
        let intermediate = self.intermediate_dim.unwrap_or(self.hidden_dim * 4);
        let layer_size = (self.hidden_dim as f64 * self.hidden_dim as f64 * 7.0
            + self.hidden_dim as f64 * intermediate as f64 * 3.0)
            / 10.0
            / mb;

        // KV cache per layer (scales with hidden_dim)
        // Roughly 2 * hidden_dim * max_seq_len * 2 (K + V) * sizeof(f16) / MB
        // For 2048 context: ~hidden_dim * 0.016 MB per layer
        let kv_cache_size = self.hidden_dim as f64 * 0.016;

        if available_mb < base_overhead {
            return (0, 0.0);
        }

        let usable = available_mb - base_overhead;
        let per_layer = layer_size + kv_cache_size;

        let n = (usable / per_layer).floor() as usize;
        let n = n.min(self.num_layers);

        let estimated = base_overhead + (n as f64 * per_layer);

        (n, estimated as f32)
    }
}
