//! Llama - High-level API with tokenizer and state management

use candle_core::{DType, Device, Result, Tensor};
use candle_nn::VarBuilder;
use std::path::Path;
use tokenizers::Tokenizer;
use tracing::info;

use rand::distributions::{Distribution, WeightedIndex};
use rand::thread_rng;

use crate::error::BitTTTError;
use crate::model::BitLlamaConfig;

use super::bitllama::BitLlama;
use super::TEMP_MIN;

/// High-level Llama API with tokenizer and state management
pub struct Llama {
    pub model: BitLlama,
    pub tokenizer: Tokenizer,
    pub device: candle_core::Device,
    pub w_states: Vec<Tensor>,
    /// Holds the shared lock on the model file to prevent modification during use
    pub _lock_file: Option<std::fs::File>,
    /// Accumulated experience (Token Count) - "Soul Level"
    pub soul_level: u64,
}

impl Llama {
    pub fn load<P: AsRef<Path>>(
        model_path: P,
        tokenizer_path: P,
        config: BitLlamaConfig,
    ) -> Result<Self> {
        let device = Device::cuda_if_available(0).unwrap_or(Device::Cpu);

        let tokenizer = Tokenizer::from_file(tokenizer_path).map_err(candle_core::Error::wrap)?;

        let file = std::fs::File::open(&model_path)?;

        let vb =
            unsafe { VarBuilder::from_mmaped_safetensors(&[model_path], DType::F32, &device)? };

        let model = BitLlama::load(config, vb)?;
        let w_states = model.new_w_states();

        Ok(Self {
            model,
            tokenizer,
            device,
            w_states,
            _lock_file: Some(file),
            soul_level: 0,
        })
    }

    /// Load with direct safetensors loading (bypasses VarBuilder, preserves U8).
    pub fn load_direct<P: AsRef<Path>>(
        model_path: P,
        tokenizer_path: P,
        config: BitLlamaConfig,
    ) -> Result<Self> {
        let tokenizer = Tokenizer::from_file(&tokenizer_path).map_err(candle_core::Error::wrap)?;

        info!("🚀 [DIRECT] Loading safetensors with U8 preservation...");
        let load_device = Device::Cpu;
        let tensors = candle_core::safetensors::load(&model_path, &load_device)?;

        let u8_count = tensors
            .values()
            .filter(|t| t.dtype() == candle_core::DType::U8)
            .count();
        info!(
            "📊 [DIRECT] Loaded {} tensors ({} U8 preserved)",
            tensors.len(),
            u8_count
        );

        let model = BitLlama::load_direct(config, &tensors)?;

        let device = model.embedding.embeddings().device().clone();
        info!("📍 [DIRECT] Model device: {:?}", device);
        let w_states = model.new_w_states();

        Ok(Self {
            model,
            tokenizer,
            device,
            w_states,
            _lock_file: None,
            soul_level: 0,
        })
    }

    /// Load model automatically from directory (or file path)
    pub fn load_auto<P: AsRef<Path>>(input_path: P) -> Result<Self> {
        let path = input_path.as_ref();
        let dir = if path.is_file() {
            path.parent().unwrap_or(path)
        } else {
            path
        };

        let config_path = dir.join("config.json");
        let tokenizer_path = dir.join("tokenizer.json");

        let mut model_path = dir.join("model.safetensors");
        if !model_path.exists() {
            model_path = dir.join("weight.safetensors");
            if !model_path.exists() {
                return Err(BitTTTError::storage_error(format!(
                    "No model.safetensors or weight.safetensors found in {:?}",
                    dir
                ))
                .into());
            }
        }

        let config_str = std::fs::read_to_string(&config_path).map_err(candle_core::Error::wrap)?;
        let config: BitLlamaConfig =
            serde_json::from_str(&config_str).map_err(candle_core::Error::wrap)?;

        Self::load_direct(model_path, tokenizer_path, config)
    }

    pub fn reset_state(&mut self) -> Result<()> {
        self.model.reset_kv_cache();
        self.soul_level = 0;
        let device = self.device.clone();
        let dim = self.model.config.hidden_dim;
        self.w_states =
            vec![Tensor::zeros((dim, dim), DType::F32, &device)?; self.model.layers.len()];
        Ok(())
    }

    pub fn generate(&mut self, prompt: &str, max_tokens: usize) -> Result<String> {
        let callback = |_token: &str| Ok(true);
        self.stream_completion(prompt, max_tokens, 0.8, callback)
    }

    pub fn stream_completion<F>(
        &mut self,
        prompt: &str,
        max_tokens: usize,
        temp: f64,
        mut callback: F,
    ) -> Result<String>
    where
        F: FnMut(&str) -> anyhow::Result<bool>,
    {
        let tokens = self
            .tokenizer
            .encode(prompt, true)
            .map_err(candle_core::Error::wrap)?;
        let mut token_ids = tokens.get_ids().to_vec();

        let mut output_str = String::from(prompt);

        // Reset KV cache and position before new generation
        self.model.reset_kv_cache();

        // DEBUG: Enable KV bypass mode (F32 path without quantization)
        self.model.set_kv_bypass(true);

        // 1. Prefill: Process all tokens and get logits from the last one
        let mut last_logits = None;
        for &id in &token_ids {
            let input = Tensor::new(&[id], &self.device)?.unsqueeze(0)?;
            last_logits = Some(self.model.forward_one(&input, &mut self.w_states)?);
        }

        // 2. Generate: Use prefill logits for first token, then iterate
        let mut logits = last_logits
            .ok_or_else(|| candle_core::Error::Msg("No tokens to prefill".to_string()))?;
        for _ in 0..max_tokens {
            let logits_squeezed = logits.squeeze(0)?.squeeze(0)?;
            let next_token = if temp < TEMP_MIN {
                let logits_v: Vec<f32> = logits_squeezed.to_vec1()?;
                logits_v
                    .iter()
                    .enumerate()
                    .max_by(|(_, a), (_, b)| a.partial_cmp(b).unwrap())
                    .map(|(i, _)| i as u32)
                    .unwrap()
            } else {
                let scaled = (&logits_squeezed / temp)?;
                let probs = candle_nn::ops::softmax(&scaled, 0)?;
                let probs_v: Vec<f32> = probs.to_vec1()?;

                let probs_clean: Vec<f64> = probs_v
                    .iter()
                    .map(|&p| if p.is_nan() || p < 0.0 { 0.0 } else { p as f64 })
                    .collect();

                match WeightedIndex::new(&probs_clean) {
                    Ok(dist) => dist.sample(&mut thread_rng()) as u32,
                    Err(_) => {
                        let logits_v: Vec<f32> = logits_squeezed.to_vec1()?;
                        logits_v
                            .iter()
                            .enumerate()
                            .max_by(|(_, a), (_, b)| a.partial_cmp(b).unwrap())
                            .map(|(i, _)| i as u32)
                            .unwrap()
                    }
                }
            };

            token_ids.push(next_token);

            let decoded = self
                .tokenizer
                .decode(&[next_token], true)
                .map_err(candle_core::Error::wrap)?;

            if !callback(&decoded).map_err(|e| candle_core::Error::Msg(e.to_string()))? {
                break;
            }
            output_str.push_str(&decoded);

            self.soul_level += 1;

            if next_token == 2 {
                break;
            }

            // Update logits for next iteration
            let input = Tensor::new(&[next_token], &self.device)?.unsqueeze(0)?;
            logits = self.model.forward_one(&input, &mut self.w_states)?;
        }
        Ok(output_str)
    }

    /// TTT Training Update (Learn)
    pub fn learn(&mut self, text: &str) -> Result<()> {
        let tokens = self
            .tokenizer
            .encode(text, true)
            .map_err(candle_core::Error::wrap)?;
        let token_ids = tokens.get_ids().to_vec();

        for &id in &token_ids {
            let input = Tensor::new(&[id], &self.device)?.unsqueeze(0)?;
            let _ = self.model.forward_one(&input, &mut self.w_states)?;
            self.soul_level += 1;
        }
        Ok(())
    }

    /// Save memory (w_states) to file
    pub fn save_memory<P: AsRef<Path>>(&self, path: P) -> Result<()> {
        let w_tensors: std::collections::HashMap<String, Tensor> = self
            .w_states
            .iter()
            .enumerate()
            .map(|(i, t)| (format!("layer_{}", i), t.clone()))
            .collect();

        candle_core::safetensors::save(&w_tensors, path)?;
        Ok(())
    }

    /// Load memory (w_states) from file
    pub fn load_memory<P: AsRef<Path>>(&mut self, path: P) -> Result<()> {
        let vb = unsafe { VarBuilder::from_mmaped_safetensors(&[path], DType::F32, &self.device)? };

        for i in 0..self.w_states.len() {
            if let Ok(t) = vb.get(
                (self.model.config.hidden_dim, self.model.config.hidden_dim),
                &format!("layer_{}", i),
            ) {
                self.w_states[i] = t;
            }
        }

        Ok(())
    }
}
