//! Unified Model Interface
//!
//! Provides a common interface for different model types (BitLlama, Llama4Bit)
//! to enable seamless switching between quantization formats.

use candle_core::{Device, Result, Tensor};
use std::path::Path;
use tracing::info;

use super::detector::{ModelDetector, QuantizationType};
use super::gguf_model::GgufModel;
use super::llama_4bit::{Llama4Bit, Llama4BitConfig};

#[cfg(feature = "tokenizers")]
use super::llama::Llama;

/// Unified model enum that can hold different model types
#[allow(clippy::large_enum_variant)]
pub enum UnifiedModel {
    /// 1.58-bit TTT or FP16 model with tokenizer
    #[cfg(feature = "tokenizers")]
    BitLlama(Llama),
    /// 4-bit quantized model (no tokenizer bundled)
    FourBit(Llama4Bit),
    /// GGUF format model (llama.cpp compatible)
    Gguf(GgufModel),
}

/// Model type for dispatch
#[derive(Debug, Clone, Copy, PartialEq, Eq)]
pub enum ModelType {
    BitLlama,
    FourBit,
    Gguf,
}

impl UnifiedModel {
    /// Detect model type from path
    pub fn detect_type<P: AsRef<Path>>(path: P) -> Result<ModelType> {
        let path = path.as_ref();

        // Check for GGUF file first
        if ModelDetector::is_gguf(path) {
            info!("🔍 Detected GGUF model");
            return Ok(ModelType::Gguf);
        }

        let dir = if path.is_file() {
            path.parent().unwrap_or(path)
        } else {
            path
        };

        // Try to detect using ModelDetector
        if let Ok(info) = ModelDetector::detect(dir) {
            match info.quantization {
                QuantizationType::Int4 => return Ok(ModelType::FourBit),
                QuantizationType::Ternary => return Ok(ModelType::BitLlama),
                QuantizationType::FP16 | QuantizationType::BF16 | QuantizationType::FP32 => {
                    return Ok(ModelType::BitLlama)
                }
                _ => {}
            }
        }

        // Fallback: Check config.json for quantization field
        let config_path = dir.join("config.json");
        if config_path.exists() {
            if let Ok(config_str) = std::fs::read_to_string(&config_path) {
                if let Ok(config) = serde_json::from_str::<serde_json::Value>(&config_str) {
                    // Check for quantization.type == "int4"
                    if let Some(quant) = config.get("quantization") {
                        if let Some(qtype) = quant.get("type").and_then(|v| v.as_str()) {
                            if qtype == "int4" || qtype == "4bit" || qtype == "nf4" {
                                info!("🔍 Detected 4-bit model from config.json");
                                return Ok(ModelType::FourBit);
                            }
                        }
                    }
                }
            }
        }

        // Fallback: Check safetensors for weight patterns
        let model_path = dir.join("model.safetensors");
        if model_path.exists() {
            if let Ok(info) = detect_from_safetensors(&model_path) {
                return Ok(info);
            }
        }

        // Default to BitLlama (FP16/TTT)
        info!("🔍 Defaulting to BitLlama (FP16/TTT) model type");
        Ok(ModelType::BitLlama)
    }

    /// Load model automatically, detecting type from path
    #[cfg(feature = "tokenizers")]
    pub fn load_auto<P: AsRef<Path>>(path: P) -> Result<Self> {
        let model_type = Self::detect_type(&path)?;

        match model_type {
            ModelType::FourBit => {
                info!("📦 Loading as 4-bit quantized model");
                let model = load_4bit_model(&path)?;
                Ok(UnifiedModel::FourBit(model))
            }
            ModelType::BitLlama => {
                info!("📦 Loading as BitLlama (FP16/TTT) model");
                let model = Llama::load_auto(&path)?;
                Ok(UnifiedModel::BitLlama(model))
            }
            ModelType::Gguf => {
                info!("📦 Loading as GGUF model");
                let device = Device::cuda_if_available(0)?;
                let model = GgufModel::load(&path, &device)?;
                Ok(UnifiedModel::Gguf(model))
            }
        }
    }

    /// Check if model is loaded
    pub fn is_loaded(&self) -> bool {
        true // If we have the enum, we have a model
    }

    /// Get model type
    pub fn model_type(&self) -> ModelType {
        match self {
            #[cfg(feature = "tokenizers")]
            UnifiedModel::BitLlama(_) => ModelType::BitLlama,
            UnifiedModel::FourBit(_) => ModelType::FourBit,
            UnifiedModel::Gguf(_) => ModelType::Gguf,
        }
    }

    /// Generate text (simplified interface)
    #[cfg(feature = "tokenizers")]
    pub fn generate(&mut self, prompt: &str, max_tokens: usize) -> Result<String> {
        match self {
            UnifiedModel::BitLlama(llama) => llama.generate(prompt, max_tokens),
            UnifiedModel::FourBit(_) | UnifiedModel::Gguf(_) => Err(candle_core::Error::Msg(
                "This model requires external tokenizer for generate()".to_string(),
            )),
        }
    }

    /// Forward pass for quantized models (4-bit or GGUF)
    pub fn forward_4bit(&mut self, input_ids: &Tensor, start_pos: usize) -> Result<Tensor> {
        match self {
            #[cfg(feature = "tokenizers")]
            UnifiedModel::BitLlama(_) => Err(candle_core::Error::Msg(
                "Use generate() for BitLlama models".to_string(),
            )),
            UnifiedModel::FourBit(model) => model.forward(input_ids, start_pos),
            UnifiedModel::Gguf(model) => model.forward(input_ids, start_pos),
        }
    }

    /// Reset KV cache
    pub fn reset_cache(&mut self) {
        match self {
            #[cfg(feature = "tokenizers")]
            UnifiedModel::BitLlama(llama) => {
                llama.model.reset_kv_cache();
            }
            UnifiedModel::FourBit(model) => {
                model.clear_kv_cache();
            }
            UnifiedModel::Gguf(model) => {
                model.reset_cache();
            }
        }
    }

    /// Stream completion with callback (BitLlama only)
    #[cfg(feature = "tokenizers")]
    pub fn stream_completion<F>(
        &mut self,
        prompt: &str,
        max_tokens: usize,
        temp: f64,
        callback: F,
    ) -> Result<String>
    where
        F: FnMut(&str) -> anyhow::Result<bool>,
    {
        match self {
            UnifiedModel::BitLlama(llama) => {
                llama.stream_completion(prompt, max_tokens, temp, callback)
            }
            UnifiedModel::FourBit(_) | UnifiedModel::Gguf(_) => Err(candle_core::Error::Msg(
                "Streaming not supported for this model. Use CLI instead.".to_string(),
            )),
        }
    }

    /// Learn from text (TTT online learning, BitLlama only)
    #[cfg(feature = "tokenizers")]
    pub fn learn(&mut self, text: &str) -> Result<()> {
        match self {
            UnifiedModel::BitLlama(llama) => llama.learn(text),
            UnifiedModel::FourBit(_) | UnifiedModel::Gguf(_) => Err(candle_core::Error::Msg(
                "Learning not supported for this model".to_string(),
            )),
        }
    }

    /// Get soul level (BitLlama only)
    #[cfg(feature = "tokenizers")]
    pub fn soul_level(&self) -> u64 {
        match self {
            UnifiedModel::BitLlama(llama) => llama.soul_level,
            UnifiedModel::FourBit(_) | UnifiedModel::Gguf(_) => 0,
        }
    }

    /// Load memory/soul file (BitLlama only)
    #[cfg(feature = "tokenizers")]
    pub fn load_memory<P: AsRef<std::path::Path>>(&mut self, path: P) -> Result<()> {
        match self {
            UnifiedModel::BitLlama(llama) => llama.load_memory(path),
            UnifiedModel::FourBit(_) | UnifiedModel::Gguf(_) => Err(candle_core::Error::Msg(
                "Soul loading not supported for this model".to_string(),
            )),
        }
    }
}

/// Detect model type from safetensors file
fn detect_from_safetensors<P: AsRef<Path>>(path: P) -> Result<ModelType> {
    use candle_core::safetensors::MmapedSafetensors;

    let tensors = unsafe { MmapedSafetensors::new(path)? };
    let tensor_list = tensors.tensors();
    let names: Vec<_> = tensor_list.iter().map(|(n, _)| n.clone()).collect();

    // Check for 4-bit markers (weight_4bit, scales, zeros)
    let has_4bit = names.iter().any(|n| {
        n.contains("weight_4bit")
            || n.contains("scales_4bit")
            || (n.contains("scales") && n.contains("qweight"))
    });
    if has_4bit {
        return Ok(ModelType::FourBit);
    }

    // Check for ternary/TTT markers (weight_packed)
    let has_ternary = names.iter().any(|n| n.contains("weight_packed"));
    if has_ternary {
        return Ok(ModelType::BitLlama);
    }

    // Default to BitLlama
    Ok(ModelType::BitLlama)
}

/// Load 4-bit model from path
#[allow(dead_code)]
fn load_4bit_model<P: AsRef<Path>>(path: P) -> Result<Llama4Bit> {
    let path = path.as_ref();
    let dir = if path.is_file() {
        path.parent().unwrap_or(path)
    } else {
        path
    };

    let config_path = dir.join("config.json");
    let mut model_path = dir.join("model.safetensors");
    if !model_path.exists() {
        model_path = dir.join("weight.safetensors");
    }

    // Load config
    let config_str = std::fs::read_to_string(&config_path)
        .map_err(|e| candle_core::Error::Msg(format!("Failed to read config: {}", e)))?;
    let config: Llama4BitConfig = serde_json::from_str(&config_str)
        .map_err(|e| candle_core::Error::Msg(format!("Failed to parse config: {}", e)))?;

    // Load tensors
    let device = Device::cuda_if_available(0).unwrap_or(Device::Cpu);
    let tensors = candle_core::safetensors::load(&model_path, &device)?;

    // Load model
    Llama4Bit::load(&tensors, config, &device)
}

#[cfg(test)]
mod tests {
    use super::*;

    #[test]
    fn test_detect_type() {
        // This test requires actual model files, so we just check the logic compiles
        let _ = UnifiedModel::detect_type("nonexistent_path");
    }
}
