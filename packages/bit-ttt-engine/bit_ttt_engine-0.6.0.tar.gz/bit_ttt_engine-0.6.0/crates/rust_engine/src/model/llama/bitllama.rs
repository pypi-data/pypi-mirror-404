//! BitLlama - Low-level model with 1.58-bit quantization support

use candle_core::{DType, Device, IndexOp, Module, Result, Tensor};
use candle_nn::VarBuilder;
use std::collections::HashMap;
use tracing::{debug, info, warn};

use crate::layers::RMSNorm;
use crate::model::{BitLlamaBlock, BitLlamaConfig};

use super::RMS_NORM_EPS;

/// BitLlama model with embedding, layers, and LM head
pub struct BitLlama {
    pub embedding: candle_nn::Embedding,
    pub layers: Vec<BitLlamaBlock>,
    pub norm: RMSNorm,
    pub lm_head: candle_nn::Linear,
    pub kv_caches: Vec<Option<crate::layers::KVCache>>,
    pub current_pos: usize,
    #[allow(dead_code)]
    pub config: BitLlamaConfig,
    /// GPU device used for layers 0..n_gpu_layers (None if CPU-only mode)
    pub gpu_device: Option<Device>,
    /// CPU device for layers n_gpu_layers..num_layers and lm_head (if lm_head_cpu=true)
    pub cpu_device: Device,
    /// Number of layers on GPU (from config.n_gpu_layers)
    pub n_gpu: usize,
}

impl BitLlama {
    pub fn load(cfg: BitLlamaConfig, vb: VarBuilder) -> Result<Self> {
        let main_device = Device::cuda_if_available(0).unwrap_or(Device::Cpu);
        let cpu_device = Device::Cpu;

        let n_gpu = match cfg.n_gpu_layers {
            Some(n) => n,
            None => {
                if main_device.is_cuda() {
                    match crate::device_utils::get_vram_info(0) {
                        Ok((free, total)) => {
                            let (n, est_vram) = cfg.calculate_auto_offload(free);
                            info!(
                                "[Auto-Config] Detected VRAM: {} MB Free / {} MB Total",
                                free / 1024 / 1024,
                                total / 1024 / 1024
                            );
                            info!("[Auto-Config] Strategy: {} Layers on GPU / {} on CPU. (Est: {:.2} MB)", n, cfg.num_layers.saturating_sub(n), est_vram);
                            n
                        }
                        Err(e) => {
                            warn!(
                                "[Auto-Config] Failed to detect VRAM: {}. Defaulting to CPU.",
                                e
                            );
                            0
                        }
                    }
                } else {
                    0
                }
            }
        };

        let io_device = if n_gpu > 0 { &main_device } else { &cpu_device };
        let lm_head_device = if cfg.lm_head_cpu {
            &cpu_device
        } else {
            io_device
        };

        // Support both "model.embed_tokens" (HF) and "embed" (BitLlama Legacy)
        let embedding_raw =
            candle_nn::embedding(cfg.vocab_size, cfg.hidden_dim, vb.pp("model.embed_tokens"))
                .or_else(|_| {
                    candle_nn::embedding(cfg.vocab_size, cfg.hidden_dim, vb.pp("embed"))
                })?;

        let embedding = if io_device.is_cpu() {
            let data = embedding_raw.embeddings().flatten_all()?.to_vec1::<f32>()?;
            let w = Tensor::from_vec(data, (cfg.vocab_size, cfg.hidden_dim), io_device)?;
            candle_nn::Embedding::new(w, cfg.hidden_dim)
        } else {
            candle_nn::Embedding::new(
                embedding_raw.embeddings().to_device(io_device)?,
                cfg.hidden_dim,
            )
        };

        let mut layers = Vec::new();
        for i in 0..cfg.num_layers {
            let target_device = if i < n_gpu { &main_device } else { &cpu_device };

            let layer_vb = if vb
                .contains_tensor(&format!("model.layers.{}.self_attn.q_proj.weight", i))
                || vb.contains_tensor(&format!(
                    "model.layers.{}.post_attention_layernorm.weight",
                    i
                )) {
                vb.pp(format!("model.layers.{}", i))
            } else {
                vb.pp(format!("layers.{}", i))
            };

            let layer = BitLlamaBlock::load(&cfg, layer_vb, target_device)?;
            layers.push(layer);
        }

        let norm = RMSNorm::load(cfg.hidden_dim, RMS_NORM_EPS, vb.pp("model.norm"), io_device)
            .or_else(|_| RMSNorm::load(cfg.hidden_dim, RMS_NORM_EPS, vb.pp("norm_f"), io_device))?;

        let lm_head_raw =
            candle_nn::linear_no_bias(cfg.hidden_dim, cfg.vocab_size, vb.pp("lm_head"))?;

        let lm_head = if lm_head_device.is_cpu() {
            let data = lm_head_raw.weight().flatten_all()?.to_vec1::<f32>()?;
            let w = Tensor::from_vec(data, (cfg.vocab_size, cfg.hidden_dim), lm_head_device)?;
            candle_nn::Linear::new(w, None)
        } else {
            candle_nn::Linear::new(lm_head_raw.weight().to_device(lm_head_device)?, None)
        };

        Ok(Self {
            embedding,
            layers,
            norm,
            lm_head,
            kv_caches: vec![
                Some(crate::layers::KVCache::new(cfg.max_position_embeddings));
                cfg.num_layers
            ],
            current_pos: 0,
            config: cfg,
            gpu_device: if n_gpu > 0 { Some(main_device) } else { None },
            cpu_device,
            n_gpu,
        })
    }

    /// Load directly from pre-loaded tensor HashMap (bypasses VarBuilder).
    pub fn load_direct(cfg: BitLlamaConfig, tensors: &HashMap<String, Tensor>) -> Result<Self> {
        let main_device = Device::cuda_if_available(0).unwrap_or(Device::Cpu);
        let cpu_device = Device::Cpu;

        let n_gpu = match cfg.n_gpu_layers {
            Some(n) => n,
            None => {
                if main_device.is_cuda() {
                    match crate::device_utils::get_vram_info(0) {
                        Ok((free, _total)) => {
                            let (n, _est_vram) = cfg.calculate_auto_offload(free);
                            info!("[DIRECT-LOAD] Auto-Config: {} Layers on GPU", n);
                            n
                        }
                        Err(_) => 0,
                    }
                } else {
                    0
                }
            }
        };

        let io_device = if n_gpu > 0 { &main_device } else { &cpu_device };
        let lm_head_device = if cfg.lm_head_cpu {
            &cpu_device
        } else {
            io_device
        };

        let embed_key = if tensors.contains_key("model.embed_tokens.weight") {
            "model.embed_tokens.weight"
        } else {
            "embed.weight"
        };
        let embed_weight = tensors.get(embed_key).ok_or_else(|| {
            candle_core::Error::Msg(format!("Embedding weight not found: {}", embed_key))
        })?;

        let embed_f32 = embed_weight.to_dtype(candle_core::DType::F32)?;
        let embed_weight = if io_device.is_cpu() {
            let data = embed_f32.flatten_all()?.to_vec1::<f32>()?;
            Tensor::from_vec(data, (cfg.vocab_size, cfg.hidden_dim), io_device)?
        } else {
            embed_f32.to_device(io_device)?
        };
        let embedding = candle_nn::Embedding::new(embed_weight, cfg.hidden_dim);

        let mut layers = Vec::new();
        for i in 0..cfg.num_layers {
            let target_device = if i < n_gpu { &main_device } else { &cpu_device };

            let prefix = if tensors
                .contains_key(&format!("model.layers.{}.input_layernorm.weight", i))
                || tensors.contains_key(&format!(
                    "model.layers.{}.post_attention_layernorm.weight",
                    i
                )) {
                format!("model.layers.{}", i)
            } else {
                format!("layers.{}", i)
            };

            let layer = BitLlamaBlock::load_direct(tensors, &prefix, &cfg, target_device)?;
            layers.push(layer);
        }

        let norm_key = if tensors.contains_key("model.norm.weight") {
            "model.norm.weight"
        } else {
            "norm_f.weight"
        };
        let norm =
            RMSNorm::load_direct(tensors, norm_key, cfg.hidden_dim, RMS_NORM_EPS, io_device)?;

        let lm_head_weight = tensors
            .get("lm_head.weight")
            .ok_or_else(|| candle_core::Error::Msg("lm_head.weight not found".to_string()))?;
        let lm_head_f32 = lm_head_weight.to_dtype(candle_core::DType::F32)?;
        let lm_head_weight = if lm_head_device.is_cpu() {
            let data = lm_head_f32.flatten_all()?.to_vec1::<f32>()?;
            Tensor::from_vec(data, (cfg.vocab_size, cfg.hidden_dim), lm_head_device)?
        } else {
            lm_head_f32.to_device(lm_head_device)?
        };
        let lm_head = candle_nn::Linear::new(lm_head_weight, None);

        info!(
            "✅ [DIRECT-LOAD] Model loaded: {} layers ({} on GPU)",
            cfg.num_layers, n_gpu
        );

        if n_gpu > 0 {
            if let Ok((free, total)) = crate::device_utils::get_vram_info(0) {
                let used = total.saturating_sub(free);
                info!(
                    "📊 [VRAM] After load: {:.0}MB used / {:.0}MB free / {:.0}MB total",
                    used as f64 / 1024.0 / 1024.0,
                    free as f64 / 1024.0 / 1024.0,
                    total as f64 / 1024.0 / 1024.0
                );
            }
        }

        Ok(Self {
            embedding,
            layers,
            norm,
            lm_head,
            kv_caches: vec![
                Some(crate::layers::KVCache::new(cfg.max_position_embeddings));
                cfg.num_layers
            ],
            current_pos: 0,
            config: cfg,
            gpu_device: if n_gpu > 0 { Some(main_device) } else { None },
            cpu_device,
            n_gpu,
        })
    }

    /// Helper to get zero states for TTT
    pub fn new_w_states(&self) -> Vec<Tensor> {
        let device = self.embedding.embeddings().device();
        let dim = self.config.hidden_dim;
        vec![Tensor::zeros((dim, dim), DType::F32, device).unwrap(); self.layers.len()]
    }

    pub fn precompute_packed(&mut self) -> Result<()> {
        for layer in self.layers.iter_mut() {
            layer.precompute_packed()?;
        }
        Ok(())
    }

    pub fn reset_kv_cache(&mut self) {
        self.kv_caches = vec![
            Some(crate::layers::KVCache::new(
                self.config.max_position_embeddings
            ));
            self.layers.len()
        ];
        self.current_pos = 0;
    }

    /// Enable or disable KV cache bypass mode (f32 without quantization)
    /// Useful for debugging quantization-related issues
    pub fn set_kv_bypass(&mut self, bypass: bool) {
        for c in self.kv_caches.iter_mut().flatten() {
            c.set_bypass(bypass);
        }
    }

    /// Main forward pass (dispatches to chunkwise or one)
    #[allow(dead_code)]
    pub fn forward(&mut self, x: &Tensor, w_states: &mut [Tensor]) -> Result<Tensor> {
        let vram_start = if self.n_gpu > 0 {
            crate::device_utils::get_vram_info(0).ok()
        } else {
            None
        };

        let (_b, seq_len) = x.dims2()?;
        let result = if seq_len > 1 {
            let mut last_logits = None;
            for i in 0..seq_len {
                let token = x.i((.., i..i + 1))?;
                last_logits = Some(self.forward_one(&token, w_states)?);
            }
            last_logits.ok_or_else(|| candle_core::Error::Msg("Empty sequence".to_string()))
        } else {
            self.forward_one(x, w_states)
        };

        if let Some((free_start, _total)) = vram_start {
            if let Ok((free_end, total)) = crate::device_utils::get_vram_info(0) {
                let delta = free_start as i64 - free_end as i64;
                debug!(
                    "📊 [VRAM] forward: delta={:+.1}MB (free: {:.0}MB / {:.0}MB)",
                    delta as f64 / 1024.0 / 1024.0,
                    free_end as f64 / 1024.0 / 1024.0,
                    total as f64 / 1024.0 / 1024.0
                );
            }
        }

        result
    }

    pub fn forward_one(&mut self, x: &Tensor, w_states: &mut [Tensor]) -> Result<Tensor> {
        let x = if x.rank() == 1 {
            x.unsqueeze(0)?
        } else {
            x.clone()
        };
        let mut h = self.embedding.forward(&x)?;

        // DEBUG: Log embedding output and position
        static DEBUG_ONCE: std::sync::atomic::AtomicBool = std::sync::atomic::AtomicBool::new(true);
        if DEBUG_ONCE.swap(false, std::sync::atomic::Ordering::SeqCst) {
            if let Ok(h_vec) = h.flatten_all()?.to_vec1::<f32>() {
                tracing::info!(
                    "🔬 [DEBUG] Embed pos={}: first 8 = {:?}",
                    self.current_pos,
                    &h_vec[..8.min(h_vec.len())]
                );
            }
        }

        for (i, layer) in self.layers.iter().enumerate() {
            let target_device: &Device = if i < self.n_gpu {
                self.gpu_device.as_ref().unwrap_or(&self.cpu_device)
            } else {
                &self.cpu_device
            };

            let h_layer = if h.device().same_device(target_device) {
                h.clone()
            } else {
                h.to_device(target_device)?
            };

            let w_state = &w_states[i];
            let cache = &mut self.kv_caches[i];
            let pos = self.current_pos;

            let (h_new, w_new) = layer.forward(&h_layer, w_state, cache, pos)?;

            // DEBUG: Log first layer output
            static DEBUG_LAYER0: std::sync::atomic::AtomicBool =
                std::sync::atomic::AtomicBool::new(true);
            if i == 0 && DEBUG_LAYER0.swap(false, std::sync::atomic::Ordering::SeqCst) {
                if let Ok(h_vec) = h_new.flatten_all()?.to_vec1::<f32>() {
                    tracing::info!(
                        "🔬 [DEBUG] Layer0 out pos={}: first 8 = {:?}",
                        pos,
                        &h_vec[..8.min(h_vec.len())]
                    );
                }
            }

            w_states[i] = w_new;
            h = h_new;
        }

        let norm_device = self.norm.weight.device();
        let h = if h.device().same_device(norm_device) {
            h
        } else {
            h.to_device(norm_device)?
        };

        let h_norm = self.norm.forward(&h)?;

        let lm_head_device = self.lm_head.weight().device();
        let h_norm = if h_norm.device().same_device(lm_head_device) {
            h_norm
        } else {
            h_norm.to_device(lm_head_device)?
        };

        // DEBUG: Log pre-logits hidden state
        static DEBUG_LOGITS: std::sync::atomic::AtomicBool =
            std::sync::atomic::AtomicBool::new(true);
        if DEBUG_LOGITS.swap(false, std::sync::atomic::Ordering::SeqCst) {
            if let Ok(h_vec) = h_norm.flatten_all()?.to_vec1::<f32>() {
                tracing::info!(
                    "🔬 [DEBUG] Pre-logits pos={}: first 8 = {:?}",
                    self.current_pos,
                    &h_vec[..8.min(h_vec.len())]
                );
            }
        }

        let logits = self.lm_head.forward(&h_norm)?;

        // DEBUG: Log logits
        static DEBUG_LOGITS2: std::sync::atomic::AtomicBool =
            std::sync::atomic::AtomicBool::new(true);
        if DEBUG_LOGITS2.swap(false, std::sync::atomic::Ordering::SeqCst) {
            if let Ok(l_vec) = logits.flatten_all()?.to_vec1::<f32>() {
                // Find top 5 logits
                let mut indexed: Vec<(usize, f32)> = l_vec.iter().copied().enumerate().collect();
                indexed.sort_by(|a, b| b.1.partial_cmp(&a.1).unwrap_or(std::cmp::Ordering::Equal));
                tracing::info!(
                    "🔬 [DEBUG] Logits pos={}: top5 = {:?}",
                    self.current_pos,
                    &indexed[..5.min(indexed.len())]
                );
            }
        }

        self.current_pos += 1;

        Ok(logits)
    }

    /// Forward chunkwise (parallel training)
    pub fn forward_chunkwise(
        &self,
        x: &Tensor,
        w_states: &mut [Tensor],
        chunk_size: usize,
    ) -> Result<Tensor> {
        let mut h = self.embedding.forward(x)?;

        for (i, layer) in self.layers.iter().enumerate() {
            let target_device: &Device = if i < self.n_gpu {
                self.gpu_device.as_ref().unwrap_or(&self.cpu_device)
            } else {
                &self.cpu_device
            };

            let h_layer = if h.device().same_device(target_device) {
                h.clone()
            } else {
                h.to_device(target_device)?
            };

            let w_state = if w_states[i].device().same_device(target_device) {
                w_states[i].clone()
            } else {
                w_states[i].to_device(target_device)?
            };

            let (h_new, w_new) = layer.forward_chunkwise(&h_layer, &w_state, chunk_size)?;
            w_states[i] = w_new;
            h = h_new;
        }

        let norm_device = self.norm.weight.device();
        let h = if h.device().same_device(norm_device) {
            h
        } else {
            h.to_device(norm_device)?
        };

        let h_norm = self.norm.forward(&h)?;

        let lm_head_device = self.lm_head.weight().device();
        let h_norm = if h_norm.device().same_device(lm_head_device) {
            h_norm
        } else {
            h_norm.to_device(lm_head_device)?
        };

        let logits = self.lm_head.forward(&h_norm)?;
        Ok(logits)
    }

    /// Helper for Python to check weights
    pub fn collect_tensors(&self) -> std::collections::HashMap<String, Tensor> {
        let mut tensors = std::collections::HashMap::new();
        tensors.insert(
            "embed.weight".to_string(),
            self.embedding.embeddings().clone(),
        );

        for (i, layer) in self.layers.iter().enumerate() {
            let prefix = format!("layers.{}", i);
            tensors.insert(
                format!("{}.norm1.weight", prefix),
                layer.norm1.weight.clone(),
            );

            let get_weight = |l: &crate::layers::AdaptiveBitLinear| -> Option<Tensor> {
                if let Some(legacy) = &l.legacy_linear {
                    Some(legacy.weight.clone())
                } else {
                    l.reconstructed_weight.clone()
                }
            };

            match &layer.core {
                crate::model::block::LayerDispatch::TTT(ttt) => {
                    if let Some(w) = get_weight(&ttt.proj_down) {
                        tensors.insert(format!("{}.ttt.down.weight", prefix), w);
                    }
                    if let Some(w) = get_weight(&ttt.proj_up) {
                        tensors.insert(format!("{}.ttt.up.weight", prefix), w);
                    }
                }
                crate::model::block::LayerDispatch::Attention(attn) => {
                    if let Some(w) = get_weight(&attn.q_proj) {
                        tensors.insert(format!("{}.self_attn.q_proj.weight", prefix), w);
                    }
                    if let Some(w) = get_weight(&attn.k_proj) {
                        tensors.insert(format!("{}.self_attn.k_proj.weight", prefix), w);
                    }
                    if let Some(w) = get_weight(&attn.v_proj) {
                        tensors.insert(format!("{}.self_attn.v_proj.weight", prefix), w);
                    }
                    if let Some(w) = get_weight(&attn.o_proj) {
                        tensors.insert(format!("{}.self_attn.o_proj.weight", prefix), w);
                    }
                }
            }

            tensors.insert(
                format!("{}.norm2.weight", prefix),
                layer.norm2.weight.clone(),
            );

            if let Some(w) = get_weight(&layer.mlp.w1) {
                tensors.insert(format!("{}.mlp.gate_proj.weight", prefix), w);
            }
            if let Some(w) = get_weight(&layer.mlp.w2) {
                tensors.insert(format!("{}.mlp.down_proj.weight", prefix), w);
            }
            if let Some(w) = get_weight(&layer.mlp.w3) {
                tensors.insert(format!("{}.mlp.up_proj.weight", prefix), w);
            }
        }

        tensors.insert("norm_f.weight".to_string(), self.norm.weight.clone());
        tensors.insert("lm_head.weight".to_string(), self.lm_head.weight().clone());

        tensors
    }
}
