//! Model Detection and Auto-Configuration Module
//!
//! Automatically detects model architecture, quantization type,
//! and generates optimal inference settings.

use anyhow::{anyhow, Result};
use serde::{Deserialize, Serialize};
use std::collections::HashMap;
use std::path::Path;

/// Supported model architectures
#[derive(Debug, Clone, Copy, PartialEq, Eq, Serialize, Deserialize)]
pub enum ModelArchitecture {
    Llama,
    Llama2,
    Llama3,
    Mistral,
    Mixtral,
    Phi,
    Phi2,
    Phi3,
    Qwen,
    Qwen2,
    Gemma,
    Gemma2,
    TinyLlama,
    StableLM,
    Unknown,
}

impl ModelArchitecture {
    /// Parse model architecture from string.
    /// Note: This intentionally doesn't implement FromStr as it's infallible
    #[allow(clippy::should_implement_trait)]
    pub fn from_str(s: &str) -> Self {
        let lower = s.to_lowercase();
        if lower.contains("llama-3") || lower.contains("llama3") {
            Self::Llama3
        } else if lower.contains("llama-2") || lower.contains("llama2") {
            Self::Llama2
        } else if lower.contains("tinyllama") {
            Self::TinyLlama
        } else if lower.contains("llama") {
            Self::Llama
        } else if lower.contains("mixtral") {
            Self::Mixtral
        } else if lower.contains("mistral") {
            Self::Mistral
        } else if lower.contains("phi-3") || lower.contains("phi3") {
            Self::Phi3
        } else if lower.contains("phi-2") || lower.contains("phi2") {
            Self::Phi2
        } else if lower.contains("phi") {
            Self::Phi
        } else if lower.contains("qwen2") {
            Self::Qwen2
        } else if lower.contains("qwen") {
            Self::Qwen
        } else if lower.contains("gemma-2") || lower.contains("gemma2") {
            Self::Gemma2
        } else if lower.contains("gemma") {
            Self::Gemma
        } else if lower.contains("stablelm") {
            Self::StableLM
        } else {
            Self::Unknown
        }
    }
}

/// Quantization type
#[derive(Debug, Clone, Copy, PartialEq, Eq, Serialize, Deserialize)]
pub enum QuantizationType {
    FP32,
    FP16,
    BF16,
    Int8,
    Int4,    // 4-bit quantization
    Ternary, // 1.58-bit (-1, 0, +1)
    Mixed,   // Mixed precision
    Unknown,
}

/// Attention type
#[derive(Debug, Clone, Copy, PartialEq, Eq, Serialize, Deserialize)]
pub enum AttentionType {
    MHA, // Multi-Head Attention (n_kv_heads == n_heads)
    GQA, // Grouped Query Attention (n_kv_heads < n_heads)
    MQA, // Multi-Query Attention (n_kv_heads == 1)
}

/// Detected model information
#[derive(Debug, Clone, Serialize, Deserialize)]
pub struct ModelInfo {
    pub name: String,
    pub architecture: ModelArchitecture,
    pub quantization: QuantizationType,
    pub attention_type: AttentionType,

    // Core dimensions
    pub vocab_size: usize,
    pub hidden_size: usize,
    pub intermediate_size: usize,
    pub num_layers: usize,
    pub num_attention_heads: usize,
    pub num_kv_heads: usize,
    pub head_dim: usize,

    // Position encoding
    pub max_position_embeddings: usize,
    pub rope_theta: f64,
    pub rope_scaling: Option<RopeScaling>,

    // Quantization details
    pub group_size: Option<usize>,
    pub bits: Option<usize>,

    // Estimated sizes
    pub estimated_params: u64,
    pub estimated_vram_mb: u64,

    // Raw config for debugging
    pub raw_config: HashMap<String, serde_json::Value>,
}

#[derive(Debug, Clone, Serialize, Deserialize)]
pub struct RopeScaling {
    pub scaling_type: String,
    pub factor: f64,
}

/// Optimal inference configuration
#[derive(Debug, Clone, Serialize, Deserialize)]
pub struct OptimalConfig {
    pub use_flash_attention: bool,
    pub use_paged_attention: bool,
    pub use_kv_cache: bool,
    pub batch_size: usize,
    pub max_context_length: usize,
    pub recommended_temperature: f64,
    pub use_sliding_window: bool,
    pub sliding_window_size: Option<usize>,
    pub n_gpu_layers: usize, // For hybrid CPU/GPU
}

/// Model detector
pub struct ModelDetector;

impl ModelDetector {
    /// Detect model from directory path
    pub fn detect<P: AsRef<Path>>(model_path: P) -> Result<ModelInfo> {
        let path = model_path.as_ref();

        // Find config.json
        let config_path = if path.is_file() {
            path.parent()
                .ok_or_else(|| anyhow!("Cannot get parent directory"))?
                .join("config.json")
        } else {
            path.join("config.json")
        };

        if !config_path.exists() {
            return Err(anyhow!("config.json not found at {:?}", config_path));
        }

        // Parse config
        let config_str = std::fs::read_to_string(&config_path)?;
        let config: HashMap<String, serde_json::Value> = serde_json::from_str(&config_str)?;

        // Detect architecture
        let architecture = Self::detect_architecture(&config);

        // Extract dimensions
        let vocab_size = Self::get_usize(&config, &["vocab_size"]).unwrap_or(32000);
        let hidden_size =
            Self::get_usize(&config, &["hidden_size", "hidden_dim", "d_model"]).unwrap_or(4096);
        let intermediate_size = Self::get_usize(
            &config,
            &["intermediate_size", "intermediate_dim", "ffn_dim"],
        )
        .unwrap_or(hidden_size * 4);
        let num_layers =
            Self::get_usize(&config, &["num_hidden_layers", "num_layers", "n_layer"]).unwrap_or(32);
        let num_attention_heads =
            Self::get_usize(&config, &["num_attention_heads", "n_heads", "n_head"]).unwrap_or(32);
        let num_kv_heads = Self::get_usize(
            &config,
            &["num_key_value_heads", "n_kv_heads", "num_kv_heads"],
        )
        .unwrap_or(num_attention_heads);
        let head_dim = hidden_size / num_attention_heads;

        // Position encoding
        let max_position_embeddings = Self::get_usize(
            &config,
            &["max_position_embeddings", "max_seq_len", "context_length"],
        )
        .unwrap_or(2048);
        let rope_theta = Self::get_f64(&config, &["rope_theta"]).unwrap_or(10000.0);

        // Rope scaling
        let rope_scaling = config.get("rope_scaling").and_then(|v| {
            let obj = v.as_object()?;
            Some(RopeScaling {
                scaling_type: obj.get("type")?.as_str()?.to_string(),
                factor: obj.get("factor")?.as_f64()?,
            })
        });

        // Detect quantization
        let (quantization, group_size, bits) = Self::detect_quantization(&config, path);

        // Determine attention type
        let attention_type = if num_kv_heads == 1 {
            AttentionType::MQA
        } else if num_kv_heads < num_attention_heads {
            AttentionType::GQA
        } else {
            AttentionType::MHA
        };

        // Estimate parameters
        let estimated_params = Self::estimate_params(
            vocab_size,
            hidden_size,
            intermediate_size,
            num_layers,
            num_attention_heads,
            num_kv_heads,
        );

        // Estimate VRAM
        let estimated_vram_mb =
            Self::estimate_vram(estimated_params, &quantization, max_position_embeddings);

        // Get model name
        let name = config
            .get("_name_or_path")
            .or_else(|| config.get("model_type"))
            .and_then(|v| v.as_str())
            .unwrap_or("unknown")
            .to_string();

        Ok(ModelInfo {
            name,
            architecture,
            quantization,
            attention_type,
            vocab_size,
            hidden_size,
            intermediate_size,
            num_layers,
            num_attention_heads,
            num_kv_heads,
            head_dim,
            max_position_embeddings,
            rope_theta,
            rope_scaling,
            group_size,
            bits,
            estimated_params,
            estimated_vram_mb,
            raw_config: config,
        })
    }

    /// Detect architecture from config
    fn detect_architecture(config: &HashMap<String, serde_json::Value>) -> ModelArchitecture {
        // Check architectures field
        if let Some(archs) = config.get("architectures").and_then(|v| v.as_array()) {
            for arch in archs {
                if let Some(arch_str) = arch.as_str() {
                    let lower = arch_str.to_lowercase();
                    if lower.contains("llama") {
                        return ModelArchitecture::Llama;
                    } else if lower.contains("mistral") {
                        return ModelArchitecture::Mistral;
                    } else if lower.contains("phi") {
                        return ModelArchitecture::Phi;
                    } else if lower.contains("qwen") {
                        return ModelArchitecture::Qwen;
                    } else if lower.contains("gemma") {
                        return ModelArchitecture::Gemma;
                    }
                }
            }
        }

        // Check model_type field
        if let Some(model_type) = config.get("model_type").and_then(|v| v.as_str()) {
            return ModelArchitecture::from_str(model_type);
        }

        // Check arch field (our custom format)
        if let Some(arch) = config.get("arch").and_then(|v| v.as_str()) {
            return ModelArchitecture::from_str(arch);
        }

        ModelArchitecture::Unknown
    }

    /// Detect quantization type
    fn detect_quantization(
        config: &HashMap<String, serde_json::Value>,
        model_path: &Path,
    ) -> (QuantizationType, Option<usize>, Option<usize>) {
        // Check explicit quantization field
        if let Some(quant) = config.get("quantization").and_then(|v| v.as_object()) {
            let qtype = quant.get("type").and_then(|v| v.as_str()).unwrap_or("");
            let group_size = quant
                .get("group_size")
                .and_then(|v| v.as_u64())
                .map(|v| v as usize);

            let quantization = match qtype {
                "int4" | "4bit" | "nf4" | "fp4" => QuantizationType::Int4,
                "int8" | "8bit" => QuantizationType::Int8,
                "ternary" | "1.58bit" => QuantizationType::Ternary,
                _ => QuantizationType::Unknown,
            };

            let bits = match quantization {
                QuantizationType::Int4 => Some(4),
                QuantizationType::Int8 => Some(8),
                QuantizationType::Ternary => Some(2), // 1.58 rounds to 2
                _ => None,
            };

            return (quantization, group_size, bits);
        }

        // Check torch_dtype
        if let Some(dtype) = config.get("torch_dtype").and_then(|v| v.as_str()) {
            let quantization = match dtype {
                "float32" | "fp32" => QuantizationType::FP32,
                "float16" | "fp16" => QuantizationType::FP16,
                "bfloat16" | "bf16" => QuantizationType::BF16,
                _ => QuantizationType::Unknown,
            };
            return (quantization, None, None);
        }

        // Try to detect from weight files
        let safetensors_path = if model_path.is_file() {
            model_path.to_path_buf()
        } else {
            model_path.join("model.safetensors")
        };

        if safetensors_path.exists() {
            if let Ok(quantization) = Self::detect_quantization_from_weights(&safetensors_path) {
                return quantization;
            }
        }

        (QuantizationType::Unknown, None, None)
    }

    /// Detect quantization from weight file
    fn detect_quantization_from_weights(
        path: &Path,
    ) -> Result<(QuantizationType, Option<usize>, Option<usize>)> {
        use candle_core::safetensors::MmapedSafetensors;

        let tensors = unsafe { MmapedSafetensors::new(path)? };
        let tensor_list = tensors.tensors();
        let names: Vec<_> = tensor_list.iter().map(|(n, _)| n.clone()).collect();

        // Check for 4-bit quantization markers
        let has_4bit = names
            .iter()
            .any(|n| n.contains("weight_4bit") || n.contains("scales_4bit"));
        if has_4bit {
            return Ok((QuantizationType::Int4, Some(128), Some(4)));
        }

        // Check for ternary quantization markers
        let has_ternary = names
            .iter()
            .any(|n| n.contains("weight_packed") || n.contains("_ternary"));
        if has_ternary {
            return Ok((QuantizationType::Ternary, None, Some(2)));
        }

        // Check tensor names for quantization markers
        // If we got here, no explicit markers found, assume FP16
        let has_any_weight = names.iter().any(|n| n.contains("weight"));
        if has_any_weight {
            // Try to load one tensor and check its dtype
            // For now, assume FP16 if no quantization markers found
            return Ok((QuantizationType::FP16, None, None));
        }

        Ok((QuantizationType::Unknown, None, None))
    }

    /// Get usize value from config with multiple possible keys
    fn get_usize(config: &HashMap<String, serde_json::Value>, keys: &[&str]) -> Option<usize> {
        for key in keys {
            if let Some(val) = config.get(*key) {
                if let Some(n) = val.as_u64() {
                    return Some(n as usize);
                }
            }
        }
        None
    }

    /// Get f64 value from config
    fn get_f64(config: &HashMap<String, serde_json::Value>, keys: &[&str]) -> Option<f64> {
        for key in keys {
            if let Some(val) = config.get(*key) {
                if let Some(n) = val.as_f64() {
                    return Some(n);
                }
            }
        }
        None
    }

    /// Estimate total parameters
    fn estimate_params(
        vocab_size: usize,
        hidden_size: usize,
        intermediate_size: usize,
        num_layers: usize,
        num_attention_heads: usize,
        num_kv_heads: usize,
    ) -> u64 {
        let head_dim = hidden_size / num_attention_heads;

        // Embedding
        let embed_params = vocab_size * hidden_size;

        // Per layer
        let q_params = hidden_size * hidden_size;
        let k_params = hidden_size * (num_kv_heads * head_dim);
        let v_params = hidden_size * (num_kv_heads * head_dim);
        let o_params = hidden_size * hidden_size;
        let attn_params = q_params + k_params + v_params + o_params;

        let mlp_params = hidden_size * intermediate_size * 3; // gate, up, down
        let norm_params = hidden_size * 2; // input_layernorm, post_attention_layernorm

        let layer_params = attn_params + mlp_params + norm_params;

        // LM head (often tied with embeddings)
        let lm_head_params = vocab_size * hidden_size;

        // Final norm
        let final_norm_params = hidden_size;

        (embed_params + layer_params * num_layers + lm_head_params + final_norm_params) as u64
    }

    /// Estimate VRAM usage in MB
    fn estimate_vram(params: u64, quantization: &QuantizationType, max_context: usize) -> u64 {
        let bytes_per_param = match quantization {
            QuantizationType::FP32 => 4.0,
            QuantizationType::FP16 | QuantizationType::BF16 => 2.0,
            QuantizationType::Int8 => 1.0,
            QuantizationType::Int4 => 0.5,
            QuantizationType::Ternary => 0.25, // ~1.58 bits
            QuantizationType::Mixed => 1.5,
            QuantizationType::Unknown => 2.0, // Assume FP16
        };

        let model_mb = (params as f64 * bytes_per_param / 1024.0 / 1024.0) as u64;

        // Add KV cache estimate (rough)
        let kv_cache_mb = (max_context * 128) as u64 / 1024; // Very rough estimate

        // Add overhead
        let overhead_mb = 512;

        model_mb + kv_cache_mb + overhead_mb
    }

    /// Generate optimal configuration for the model
    pub fn generate_optimal_config(info: &ModelInfo, available_vram_mb: u64) -> OptimalConfig {
        let fits_in_vram = info.estimated_vram_mb < available_vram_mb;

        // Determine GPU layers
        let n_gpu_layers = if fits_in_vram {
            info.num_layers
        } else {
            // Calculate how many layers fit
            let layer_size_mb = info.estimated_vram_mb / info.num_layers as u64;
            let available_for_layers = available_vram_mb.saturating_sub(512); // Reserve 512MB
            (available_for_layers / layer_size_mb) as usize
        };

        // Sliding window (Mistral-style)
        let use_sliding_window = matches!(
            info.architecture,
            ModelArchitecture::Mistral | ModelArchitecture::Mixtral
        );
        let sliding_window_size = if use_sliding_window {
            info.raw_config
                .get("sliding_window")
                .and_then(|v| v.as_u64())
                .map(|v| v as usize)
        } else {
            None
        };

        // Flash attention for larger models
        let use_flash_attention = info.num_layers >= 24;

        // Paged attention for long contexts
        let use_paged_attention = info.max_position_embeddings >= 4096;

        // Batch size based on VRAM
        let batch_size = if available_vram_mb >= 24000 {
            8
        } else if available_vram_mb >= 16000 {
            4
        } else if available_vram_mb >= 8000 {
            2
        } else {
            1
        };

        // Context length
        let max_context_length = if fits_in_vram {
            info.max_position_embeddings
        } else {
            // Reduce context for memory
            (info.max_position_embeddings / 2).max(512)
        };

        // Temperature recommendation
        let recommended_temperature = match info.architecture {
            ModelArchitecture::Phi | ModelArchitecture::Phi2 | ModelArchitecture::Phi3 => 0.7,
            _ => 0.8,
        };

        OptimalConfig {
            use_flash_attention,
            use_paged_attention,
            use_kv_cache: true,
            batch_size,
            max_context_length,
            recommended_temperature,
            use_sliding_window,
            sliding_window_size,
            n_gpu_layers,
        }
    }

    /// Print model summary
    pub fn print_summary(info: &ModelInfo) {
        println!("╔══════════════════════════════════════════════════════════════╗");
        println!("║                     MODEL DETECTION REPORT                    ║");
        println!("╠══════════════════════════════════════════════════════════════╣");
        println!("║ Name:          {:47} ║", info.name);
        println!("║ Architecture:  {:47?} ║", info.architecture);
        println!("║ Quantization:  {:47?} ║", info.quantization);
        println!("║ Attention:     {:47?} ║", info.attention_type);
        println!("╠══════════════════════════════════════════════════════════════╣");
        println!("║                        DIMENSIONS                            ║");
        println!("╠══════════════════════════════════════════════════════════════╣");
        println!("║ Vocab Size:    {:>47} ║", info.vocab_size);
        println!("║ Hidden Size:   {:>47} ║", info.hidden_size);
        println!("║ Intermediate:  {:>47} ║", info.intermediate_size);
        println!("║ Layers:        {:>47} ║", info.num_layers);
        println!("║ Attn Heads:    {:>47} ║", info.num_attention_heads);
        println!("║ KV Heads:      {:>47} ║", info.num_kv_heads);
        println!("║ Head Dim:      {:>47} ║", info.head_dim);
        println!("╠══════════════════════════════════════════════════════════════╣");
        println!("║                     POSITION ENCODING                        ║");
        println!("╠══════════════════════════════════════════════════════════════╣");
        println!("║ Max Position:  {:>47} ║", info.max_position_embeddings);
        println!("║ RoPE Theta:    {:>47.1} ║", info.rope_theta);
        if let Some(ref scaling) = info.rope_scaling {
            println!("║ RoPE Scaling:  {:>47} ║", scaling.scaling_type);
            println!("║ Scale Factor:  {:>47.1} ║", scaling.factor);
        }
        println!("╠══════════════════════════════════════════════════════════════╣");
        println!("║                        ESTIMATES                             ║");
        println!("╠══════════════════════════════════════════════════════════════╣");
        println!(
            "║ Parameters:    {:>43.2}B ║",
            info.estimated_params as f64 / 1e9
        );
        println!("║ Est. VRAM:     {:>43} MB ║", info.estimated_vram_mb);
        if let Some(bits) = info.bits {
            println!("║ Bits:          {:>47} ║", bits);
        }
        if let Some(group_size) = info.group_size {
            println!("║ Group Size:    {:>47} ║", group_size);
        }
        println!("╚══════════════════════════════════════════════════════════════╝");
    }

    // ========== GGUF Support ==========

    /// Check if path is a GGUF file
    pub fn is_gguf<P: AsRef<Path>>(path: P) -> bool {
        let path = path.as_ref();
        path.is_file()
            && path
                .extension()
                .map(|ext| ext.to_str() == Some("gguf"))
                .unwrap_or(false)
    }

    /// Detect model from GGUF file
    pub fn detect_gguf<P: AsRef<Path>>(path: P) -> Result<ModelInfo> {
        use super::gguf_loader::GgufLoader;

        let path = path.as_ref();
        if !Self::is_gguf(path) {
            return Err(anyhow!("Not a GGUF file: {:?}", path));
        }

        let mut loader = GgufLoader::load(path)?;
        let config = loader.to_config()?;

        // Get architecture
        let architecture = loader
            .architecture()
            .map(ModelArchitecture::from_str)
            .unwrap_or(ModelArchitecture::Unknown);

        // Detect quantization from tensors
        let quantization = loader.detect_quantization();

        // Determine attention type
        let attention_type = if config.n_kv_heads == 1 {
            AttentionType::MQA
        } else if config.n_kv_heads < config.n_heads {
            AttentionType::GQA
        } else {
            AttentionType::MHA
        };

        // Get model name
        let name = loader.model_name().unwrap_or_else(|| {
            path.file_stem()
                .unwrap_or_default()
                .to_string_lossy()
                .to_string()
        });

        // Estimate parameters
        let intermediate_size = config.intermediate_dim.unwrap_or(config.hidden_dim * 4);
        let estimated_params = Self::estimate_params(
            config.vocab_size,
            config.hidden_dim,
            intermediate_size,
            config.num_layers,
            config.n_heads,
            config.n_kv_heads,
        );

        // Estimate VRAM (for FP32 dequantized, since that's our current implementation)
        let estimated_vram_mb = Self::estimate_vram(
            estimated_params,
            &QuantizationType::FP32,
            config.max_position_embeddings,
        );

        Ok(ModelInfo {
            name,
            architecture,
            quantization,
            attention_type,
            vocab_size: config.vocab_size,
            hidden_size: config.hidden_dim,
            intermediate_size,
            num_layers: config.num_layers,
            num_attention_heads: config.n_heads,
            num_kv_heads: config.n_kv_heads,
            head_dim: config.hidden_dim / config.n_heads,
            max_position_embeddings: config.max_position_embeddings,
            rope_theta: config.rope_theta,
            rope_scaling: None,
            group_size: None,
            bits: match quantization {
                QuantizationType::Int4 => Some(4),
                QuantizationType::Int8 => Some(8),
                _ => None,
            },
            estimated_params,
            estimated_vram_mb,
            raw_config: HashMap::new(),
        })
    }

    /// Auto-detect model from path (GGUF file or directory with config.json)
    pub fn detect_auto<P: AsRef<Path>>(path: P) -> Result<ModelInfo> {
        let path = path.as_ref();
        if Self::is_gguf(path) {
            Self::detect_gguf(path)
        } else {
            Self::detect(path)
        }
    }
}

#[cfg(test)]
mod tests {
    use super::*;

    #[test]
    fn test_architecture_detection() {
        assert_eq!(
            ModelArchitecture::from_str("llama"),
            ModelArchitecture::Llama
        );
        assert_eq!(
            ModelArchitecture::from_str("Llama-2-7b"),
            ModelArchitecture::Llama2
        );
        assert_eq!(
            ModelArchitecture::from_str("Meta-Llama-3-8B"),
            ModelArchitecture::Llama3
        );
        assert_eq!(
            ModelArchitecture::from_str("TinyLlama"),
            ModelArchitecture::TinyLlama
        );
        assert_eq!(
            ModelArchitecture::from_str("mistral"),
            ModelArchitecture::Mistral
        );
        assert_eq!(
            ModelArchitecture::from_str("phi-2"),
            ModelArchitecture::Phi2
        );
    }
}
