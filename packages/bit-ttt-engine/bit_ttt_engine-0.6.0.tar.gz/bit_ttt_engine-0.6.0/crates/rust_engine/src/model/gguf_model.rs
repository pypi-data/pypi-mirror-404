//! GGUF Model - Quantized model inference using GGUF format
//!
//! Loads GGUF models and runs inference. Currently dequantizes all weights
//! to FP32 for computation. Future versions will use quantized matmul.

use candle_core::{DType, Device, Result, Tensor};
use std::path::Path;
use tracing::info;

use super::config::{ActivationType, BitLlamaConfig};
use super::gguf_loader::{tensor_names, GgufLoader};

#[cfg(feature = "flash-attention")]
use crate::layers::flash_attention::{flash_attention, FlashAttentionConfig};

/// GGUF Model for inference
///
/// Note: `device` field is currently unused but reserved for future GPU acceleration.
/// The `#[allow(dead_code)]` suppresses warnings until GPU support is implemented.
#[allow(dead_code)]
pub struct GgufModel {
    /// Model configuration
    pub config: BitLlamaConfig,
    /// Token embeddings
    embed_tokens: Tensor,
    /// Transformer layers
    layers: Vec<GgufLayer>,
    /// Final normalization weight
    norm_weight: Tensor,
    /// LM head weight (transposed: [hidden, vocab])
    lm_head_weight: Tensor,
    /// Device
    device: Device,
    /// RoPE cos cache
    cos_cache: Tensor,
    /// RoPE sin cache
    sin_cache: Tensor,
}

/// Single transformer layer
struct GgufLayer {
    input_norm_weight: Tensor,
    post_norm_weight: Tensor,
    // Attention weights (transposed for matmul)
    q_weight: Tensor,
    k_weight: Tensor,
    v_weight: Tensor,
    o_weight: Tensor,
    // MLP weights (transposed for matmul)
    gate_weight: Tensor,
    up_weight: Tensor,
    down_weight: Tensor,
    // KV cache
    k_cache: Option<Tensor>,
    v_cache: Option<Tensor>,
    // Config
    n_heads: usize,
    n_kv_heads: usize,
    head_dim: usize,
    rms_norm_eps: f64,
    activation: ActivationType,
    // TTT mode (Test-Time Training)
    use_ttt: bool,
    ttt_proj_down: Option<Tensor>,  // [hidden, d_small]
    ttt_proj_up: Option<Tensor>,    // [d_small, hidden]
    ttt_inner_lr: f64,
    ttt_w_state: Option<Tensor>,    // [batch, d_small, d_small]
}

impl GgufModel {
    /// Load a GGUF model (dequantizes all weights to FP32)
    pub fn load<P: AsRef<Path>>(path: P, device: &Device) -> Result<Self> {
        let mut loader =
            GgufLoader::load(&path).map_err(|e| candle_core::Error::Msg(e.to_string()))?;
        let config = loader
            .to_config()
            .map_err(|e| candle_core::Error::Msg(e.to_string()))?;

        info!(
            "🚀 Loading GGUF model: {} layers (dequantizing to FP32)",
            config.num_layers
        );

        // Load embedding
        info!("   📥 Loading embeddings...");
        let embed_tokens = loader
            .tensor(tensor_names::embedding(), device)
            .map_err(|e| candle_core::Error::Msg(e.to_string()))?
            .dequantize(device)?;

        // Load layers
        info!("   📥 Loading layers...");
        let mut layers = Vec::with_capacity(config.num_layers);
        for i in 0..config.num_layers {
            if (i + 1) % 10 == 0 || i == config.num_layers - 1 {
                info!("      Layer {}/{}", i + 1, config.num_layers);
            }
            layers.push(GgufLayer::load(&mut loader, i, &config, device)?);
        }

        // Load output norm
        info!("   📥 Loading output norm...");
        let norm_weight = loader
            .tensor(tensor_names::output_norm(), device)
            .map_err(|e| candle_core::Error::Msg(e.to_string()))?
            .dequantize(device)?;

        // Load lm_head (transpose for efficient matmul: [vocab, hidden] -> [hidden, vocab])
        // For tied embeddings (Gemma), use embed_tokens if output weight doesn't exist
        info!("   📥 Loading lm_head...");
        let lm_head_weight = if loader.has_tensor(tensor_names::output()) {
            loader
                .tensor(tensor_names::output(), device)
                .map_err(|e| candle_core::Error::Msg(e.to_string()))?
                .dequantize(device)?
                .t()? // Transpose
        } else {
            // Tied embeddings: lm_head = embed_tokens.T
            // embed_tokens is [vocab, hidden], need [hidden, vocab] for matmul
            info!("      ℹ️ Using tied embeddings (lm_head = embed_tokens.T)");
            embed_tokens.t()?.contiguous()?
        };

        // Precompute RoPE using head_dim from first layer (handles Gemma2's non-standard head_dim)
        let head_dim = layers
            .first()
            .map(|l| l.head_dim)
            .unwrap_or(config.hidden_dim / config.n_heads);
        let (cos_cache, sin_cache) = compute_rope_cache(
            config.max_position_embeddings,
            head_dim,
            config.rope_theta,
            device,
        )?;

        info!(
            "✅ GGUF model loaded! (head_dim={}, activation={:?})",
            head_dim, config.activation
        );

        Ok(Self {
            config,
            embed_tokens,
            layers,
            norm_weight,
            lm_head_weight,
            device: device.clone(),
            cos_cache,
            sin_cache,
        })
    }

    /// Forward pass
    pub fn forward(&mut self, input_ids: &Tensor, start_pos: usize) -> Result<Tensor> {
        let (batch, seq_len) = input_ids.dims2()?;

        // Embed tokens: gather from embedding table
        // input_ids: [batch, seq] -> flatten to [batch * seq]
        // Then gather from embed_tokens: [vocab, hidden]
        // Result: [batch * seq, hidden] -> reshape to [batch, seq, hidden]
        let flat_ids = input_ids.flatten_all()?;
        let hidden_flat = self.embed_tokens.index_select(&flat_ids, 0)?;
        let mut hidden = hidden_flat.reshape((batch, seq_len, self.config.hidden_dim))?;

        // Get RoPE for this position
        let cos = self.cos_cache.narrow(0, start_pos, seq_len)?;
        let sin = self.sin_cache.narrow(0, start_pos, seq_len)?;

        // Process layers
        for layer in &mut self.layers {
            hidden = layer.forward(&hidden, &cos, &sin, start_pos)?;
        }

        // Final norm
        hidden = rms_norm(&hidden, &self.norm_weight, self.config.rms_norm_eps)?;

        // LM head: flatten to 2D, matmul, reshape back
        let (batch, seq_len, hidden_dim) = hidden.dims3()?;
        let hidden_2d = hidden.reshape((batch * seq_len, hidden_dim))?;
        let logits_2d = hidden_2d.matmul(&self.lm_head_weight)?;
        let vocab_size = self.lm_head_weight.dim(1)?;
        let logits = logits_2d.reshape((batch, seq_len, vocab_size))?;

        Ok(logits)
    }

    /// Reset KV cache
    pub fn reset_cache(&mut self) {
        for layer in &mut self.layers {
            layer.k_cache = None;
            layer.v_cache = None;
        }
    }

    /// Get config
    pub fn config(&self) -> &BitLlamaConfig {
        &self.config
    }

    /// Enable TTT mode for specified layers
    ///
    /// # Arguments
    /// * `layer_indices` - Which layers to enable TTT for (None = all layers)
    /// * `inner_lr` - Learning rate for TTT weight updates
    ///
    /// # Example
    /// ```ignore
    /// // Enable TTT for last 4 layers
    /// let num_layers = model.config().num_layers;
    /// model.enable_ttt(Some((num_layers - 4)..num_layers), 0.01);
    /// ```
    pub fn enable_ttt(&mut self, layer_indices: Option<std::ops::Range<usize>>, inner_lr: f64) {
        let range = layer_indices.unwrap_or(0..self.layers.len());
        for i in range {
            if i < self.layers.len() {
                self.layers[i].use_ttt = true;
                self.layers[i].ttt_inner_lr = inner_lr;
            }
        }
        tracing::info!("TTT enabled for {} layers", self.layers.iter().filter(|l| l.use_ttt).count());
    }

    /// Disable TTT mode for all layers
    pub fn disable_ttt(&mut self) {
        for layer in &mut self.layers {
            layer.use_ttt = false;
        }
    }

    /// Reset TTT state (W matrices) for all layers
    pub fn reset_ttt_state(&mut self) {
        for layer in &mut self.layers {
            layer.ttt_w_state = None;
        }
    }

    /// Check if any layer has TTT enabled
    pub fn is_ttt_enabled(&self) -> bool {
        self.layers.iter().any(|l| l.use_ttt)
    }
}

impl GgufLayer {
    fn load(
        loader: &mut GgufLoader,
        idx: usize,
        config: &BitLlamaConfig,
        device: &Device,
    ) -> Result<Self> {
        // Helper to load and dequantize tensor
        let mut load_tensor = |name: &str| -> Result<Tensor> {
            loader
                .tensor(name, device)
                .map_err(|e| candle_core::Error::Msg(e.to_string()))?
                .dequantize(device)
        };

        // Load norm weights
        let input_norm_weight = load_tensor(&tensor_names::attn_norm(idx))?;
        let post_norm_weight = load_tensor(&tensor_names::ffn_norm(idx))?;

        // Load attention weights (transpose for matmul: [out, in] -> [in, out])
        let q_weight = load_tensor(&tensor_names::attn_q(idx))?.t()?;
        let k_weight = load_tensor(&tensor_names::attn_k(idx))?.t()?;
        let v_weight = load_tensor(&tensor_names::attn_v(idx))?.t()?;
        let o_weight = load_tensor(&tensor_names::attn_output(idx))?.t()?;

        // Load MLP weights (transpose)
        let gate_weight = load_tensor(&tensor_names::ffn_gate(idx))?.t()?;
        let up_weight = load_tensor(&tensor_names::ffn_up(idx))?.t()?;
        let down_weight = load_tensor(&tensor_names::ffn_down(idx))?.t()?;

        // Calculate head_dim from q_weight shape (handles Gemma2 with non-standard head_dim)
        // q_weight is [hidden_dim, n_heads * head_dim] after transpose
        let q_out_dim = q_weight.dims()[1];
        let head_dim = q_out_dim / config.n_heads;

        Ok(Self {
            input_norm_weight,
            post_norm_weight,
            q_weight,
            k_weight,
            v_weight,
            o_weight,
            gate_weight,
            up_weight,
            down_weight,
            k_cache: None,
            v_cache: None,
            n_heads: config.n_heads,
            n_kv_heads: config.n_kv_heads,
            head_dim,
            rms_norm_eps: config.rms_norm_eps,
            activation: config.activation,
            // TTT mode disabled by default
            use_ttt: false,
            ttt_proj_down: None,
            ttt_proj_up: None,
            ttt_inner_lr: 0.01,
            ttt_w_state: None,
        })
    }

    fn forward(
        &mut self,
        hidden: &Tensor,
        cos: &Tensor,
        sin: &Tensor,
        start_pos: usize,
    ) -> Result<Tensor> {
        let (batch, seq_len, hidden_dim) = hidden.dims3()?;

        // Pre-attention norm
        let residual = hidden.clone();
        let hidden = rms_norm(hidden, &self.input_norm_weight, self.rms_norm_eps)?;

        // TTT mode: use Test-Time Training instead of attention
        // Note: Current implementation is experimental. TTT approximates attention
        // but uses self-supervised learning (reconstruction loss) which differs
        // from the language model objective (next token prediction).
        if self.use_ttt {
            let ttt_out = self.ttt_forward(&hidden)?;
            return self.mlp_forward(&residual, &ttt_out, batch, seq_len, hidden_dim);
        }

        // Flatten to 2D for matmul: [batch * seq, hidden]
        let hidden_2d = hidden.reshape((batch * seq_len, hidden_dim))?;

        // Attention projection: [batch*seq, hidden] @ [hidden, proj_dim] -> [batch*seq, proj_dim]
        let q = hidden_2d.matmul(&self.q_weight)?;
        let k = hidden_2d.matmul(&self.k_weight)?;
        let v = hidden_2d.matmul(&self.v_weight)?;

        // Reshape to [batch, seq, heads, head_dim]
        let q = q.reshape((batch, seq_len, self.n_heads, self.head_dim))?;
        let k = k.reshape((batch, seq_len, self.n_kv_heads, self.head_dim))?;
        let v = v.reshape((batch, seq_len, self.n_kv_heads, self.head_dim))?;

        // Transpose to [batch, heads, seq, head_dim]
        let q = q.transpose(1, 2)?.contiguous()?;
        let k = k.transpose(1, 2)?.contiguous()?;
        let v = v.transpose(1, 2)?.contiguous()?;

        // Apply RoPE
        let (q, k) = apply_rotary_emb(&q, &k, cos, sin)?;

        // Use Flash Attention for prefill (no KV cache, longer sequences)
        #[cfg(feature = "flash-attention")]
        let use_flash = self.k_cache.is_none() && seq_len > 64;
        #[cfg(not(feature = "flash-attention"))]
        let use_flash = false;

        let attn_out = if use_flash {
            #[cfg(feature = "flash-attention")]
            {
                // Flash Attention path (prefill only)
                // Repeat KV for GQA before flash attention
                let n_rep = self.n_heads / self.n_kv_heads;
                let k_expanded = repeat_kv(&k, n_rep)?;
                let v_expanded = repeat_kv(&v, n_rep)?;

                // Run flash attention
                let config = FlashAttentionConfig::new(self.head_dim);
                let attn_out = flash_attention(&q, &k_expanded, &v_expanded, &config)?;

                // Update KV cache with original (non-repeated) K, V
                self.k_cache = Some(k);
                self.v_cache = Some(v);

                attn_out
            }
            #[cfg(not(feature = "flash-attention"))]
            {
                unreachable!()
            }
        } else {
            // Standard attention path (decode or small prefill)
            // Update KV cache
            let (k, v) = match (&self.k_cache, &self.v_cache) {
                (Some(k_cache), Some(v_cache)) => {
                    let k = Tensor::cat(&[k_cache, &k], 2)?;
                    let v = Tensor::cat(&[v_cache, &v], 2)?;
                    (k, v)
                }
                _ => (k, v),
            };
            self.k_cache = Some(k.clone());
            self.v_cache = Some(v.clone());

            // Repeat KV for GQA
            let n_rep = self.n_heads / self.n_kv_heads;
            let k = repeat_kv(&k, n_rep)?;
            let v = repeat_kv(&v, n_rep)?;

            // Scaled dot-product attention
            let scale = (self.head_dim as f64).sqrt().recip();
            let attn_weights = (q.matmul(&k.transpose(2, 3)?)? * scale)?;

            // Causal mask
            let kv_len = k.dim(2)?;
            let mask = create_causal_mask(seq_len, kv_len, start_pos, hidden.device())?;
            let attn_weights = attn_weights.broadcast_add(&mask)?;

            // Softmax
            let attn_weights = candle_nn::ops::softmax_last_dim(&attn_weights)?;

            // Attention output
            attn_weights.matmul(&v)?
        };

        // Reshape back to [batch, seq, hidden]
        let attn_out = attn_out.transpose(1, 2)?.contiguous()?.reshape((
            batch,
            seq_len,
            self.n_heads * self.head_dim,
        ))?;

        // Output projection (flatten to 2D, matmul, reshape back)
        let attn_out_2d = attn_out.reshape((batch * seq_len, self.n_heads * self.head_dim))?;
        let attn_out_2d = attn_out_2d.matmul(&self.o_weight)?;
        let attn_out = attn_out_2d.reshape((batch, seq_len, hidden_dim))?;

        // Residual connection
        let hidden = (&residual + &attn_out)?;

        // MLP
        let residual = hidden.clone();
        let hidden = rms_norm(&hidden, &self.post_norm_weight, self.rms_norm_eps)?;

        // Flatten for matmul
        let hidden_2d = hidden.reshape((batch * seq_len, hidden_dim))?;

        // Gated MLP: down(activation(gate(x)) * up(x))
        // SwiGLU (Llama): silu activation
        // GeGLU (Gemma): gelu activation
        let gate = hidden_2d.matmul(&self.gate_weight)?;
        let up = hidden_2d.matmul(&self.up_weight)?;
        let gate_activated = match self.activation {
            ActivationType::SiLU => candle_nn::ops::silu(&gate)?,
            ActivationType::GELU => gate.gelu()?,
        };
        let hidden_2d = (gate_activated * up)?;
        let hidden_2d = hidden_2d.matmul(&self.down_weight)?;

        // Reshape back to 3D
        let hidden = hidden_2d.reshape((batch, seq_len, hidden_dim))?;

        // Residual
        let hidden = (&residual + &hidden)?;

        Ok(hidden)
    }

    /// MLP forward (shared between attention and TTT paths)
    fn mlp_forward(
        &self,
        residual: &Tensor,
        attn_out: &Tensor,
        batch: usize,
        seq_len: usize,
        hidden_dim: usize,
    ) -> Result<Tensor> {
        // Residual connection after attention/TTT
        let hidden = (residual + attn_out)?;

        // MLP
        let residual = hidden.clone();
        let hidden = rms_norm(&hidden, &self.post_norm_weight, self.rms_norm_eps)?;

        // Flatten for matmul
        let hidden_2d = hidden.reshape((batch * seq_len, hidden_dim))?;

        // Gated MLP
        let gate = hidden_2d.matmul(&self.gate_weight)?;
        let up = hidden_2d.matmul(&self.up_weight)?;
        let gate_activated = match self.activation {
            ActivationType::SiLU => candle_nn::ops::silu(&gate)?,
            ActivationType::GELU => gate.gelu()?,
        };
        let hidden_2d = (gate_activated * up)?;
        let hidden_2d = hidden_2d.matmul(&self.down_weight)?;

        // Reshape back to 3D
        let hidden = hidden_2d.reshape((batch, seq_len, hidden_dim))?;

        // Residual
        residual + hidden
    }

    /// TTT forward: Test-Time Training attention replacement
    fn ttt_forward(&mut self, hidden: &Tensor) -> Result<Tensor> {
        use candle_core::D;
        
        let (batch, seq_len, hidden_dim) = hidden.dims3()?;
        let d_small = hidden_dim / 4;
        let device = hidden.device();

        // Initialize TTT weights to approximate Attention behavior
        // Strategy: Use O weight directly for output projection
        // proj_down: identity-like (just for dimensionality reduction)
        // proj_up: O weight subset (maintains learned output distribution)
        if self.ttt_proj_down.is_none() {
            // proj_down: Initialize to preserve information
            // Use orthogonal-like initialization from hidden -> d_small
            // Simple approach: normalized random + small identity component
            let eye_part = if hidden_dim >= d_small {
                // Create a partial identity: [hidden, d_small]
                let mut data = vec![0.0f32; hidden_dim * d_small];
                for i in 0..d_small {
                    data[i * d_small + i] = 1.0;
                }
                Tensor::from_vec(data, (hidden_dim, d_small), device)?
            } else {
                Tensor::zeros((hidden_dim, d_small), DType::F32, device)?
            };
            
            let random_part = Tensor::randn(0.0f32, 0.02f32, (hidden_dim, d_small), device)?;
            let proj_down = (eye_part * 0.5 + random_part)?;
            
            // proj_up: Use O weight for output projection
            // O weight is [n_heads * head_dim, hidden], we want [d_small, hidden]
            // Take first d_small rows
            let o_rows = self.o_weight.dim(0)?;
            let take_rows = d_small.min(o_rows);
            let proj_up = self.o_weight.narrow(0, 0, take_rows)?;
            
            // Pad if needed
            let proj_up = if take_rows < d_small {
                let padding = Tensor::zeros((d_small - take_rows, hidden_dim), DType::F32, device)?;
                Tensor::cat(&[&proj_up, &padding], 0)?
            } else {
                proj_up.contiguous()?
            };
            
            self.ttt_proj_down = Some(proj_down);
            self.ttt_proj_up = Some(proj_up);
        }

        // Initialize W state if not present
        if self.ttt_w_state.is_none() || self.ttt_w_state.as_ref().unwrap().dim(0)? != batch {
            // Identity matrix for each batch element
            let eye = Tensor::eye(d_small, DType::F32, device)?;
            self.ttt_w_state = Some(eye.broadcast_left(batch)?);
        }

        let proj_down = self.ttt_proj_down.as_ref().unwrap();
        let proj_up = self.ttt_proj_up.as_ref().unwrap();
        let mut w_state = self.ttt_w_state.take().unwrap();

        let mut outputs = Vec::with_capacity(seq_len);

        // Token-by-token TTT processing
        for t in 0..seq_len {
            let x_t = hidden.narrow(1, t, 1)?.squeeze(1)?;  // [batch, hidden]

            // Project down: [batch, hidden] @ [hidden, d_small] -> [batch, d_small]
            let feat = x_t.matmul(proj_down)?;

            // L2 normalize
            let norm = feat.sqr()?.sum_keepdim(D::Minus1)?.sqrt()?;
            let feat_norm = feat.broadcast_div(&(&norm + 1e-6)?)?;

            // Predict: W @ feat_norm
            // w_state: [batch, d_small, d_small], feat_norm: [batch, d_small]
            let feat_unsqueezed = feat_norm.unsqueeze(2)?;  // [batch, d_small, 1]
            let pred = w_state.matmul(&feat_unsqueezed)?.squeeze(2)?;  // [batch, d_small]

            // Compute gradient: d(loss)/d(W) = (pred - feat_norm) outer feat_norm
            let error = (&pred - &feat_norm)?;
            let error_unsqueezed = error.unsqueeze(2)?;  // [batch, d_small, 1]
            let feat_unsqueezed_t = feat_norm.unsqueeze(1)?;  // [batch, 1, d_small]
            let grad = error_unsqueezed.matmul(&feat_unsqueezed_t)?;  // [batch, d_small, d_small]

            // Update W: W = W - lr * grad
            w_state = (w_state - grad * self.ttt_inner_lr)?;

            // Project up: [batch, d_small] @ [d_small, hidden] -> [batch, hidden]
            let out = pred.matmul(proj_up)?;
            outputs.push(out);
        }

        // Save updated state
        self.ttt_w_state = Some(w_state);

        // Stack outputs: [seq_len, batch, hidden] -> [batch, seq_len, hidden]
        let stacked = Tensor::stack(&outputs, 0)?;  // [seq_len, batch, hidden]
        stacked.transpose(0, 1)?.contiguous()
    }
}

// ========== Helper functions ==========

/// RMS Normalization
fn rms_norm(x: &Tensor, weight: &Tensor, eps: f64) -> Result<Tensor> {
    let x_f32 = x.to_dtype(DType::F32)?;
    let variance = x_f32.sqr()?.mean_keepdim(2)?;
    let x_normed = x_f32.broadcast_div(&(variance + eps)?.sqrt()?)?;
    x_normed.broadcast_mul(weight)
}

/// Compute RoPE cos/sin cache
fn compute_rope_cache(
    max_len: usize,
    head_dim: usize,
    theta: f64,
    device: &Device,
) -> Result<(Tensor, Tensor)> {
    let half_dim = head_dim / 2;

    let positions: Vec<f32> = (0..max_len).map(|p| p as f32).collect();
    let positions = Tensor::from_vec(positions, (max_len, 1), device)?;

    let freqs: Vec<f32> = (0..half_dim)
        .map(|i| 1.0 / theta.powf(2.0 * i as f64 / head_dim as f64) as f32)
        .collect();
    let freqs = Tensor::from_vec(freqs, (1, half_dim), device)?;

    let angles = positions.matmul(&freqs)?;
    let cos = angles.cos()?;
    let sin = angles.sin()?;

    // Duplicate for full head_dim
    let cos = Tensor::cat(&[&cos, &cos], 1)?;
    let sin = Tensor::cat(&[&sin, &sin], 1)?;

    Ok((cos, sin))
}

/// Apply rotary position embedding
fn apply_rotary_emb(
    q: &Tensor,
    k: &Tensor,
    cos: &Tensor,
    sin: &Tensor,
) -> Result<(Tensor, Tensor)> {
    // cos/sin: [seq_len, head_dim] -> [1, 1, seq_len, head_dim]
    let cos = cos.unsqueeze(0)?.unsqueeze(0)?;
    let sin = sin.unsqueeze(0)?.unsqueeze(0)?;

    let q_embed = (q.broadcast_mul(&cos)? + rotate_half(q)?.broadcast_mul(&sin)?)?;
    let k_embed = (k.broadcast_mul(&cos)? + rotate_half(k)?.broadcast_mul(&sin)?)?;
    Ok((q_embed, k_embed))
}

fn rotate_half(x: &Tensor) -> Result<Tensor> {
    let last_dim = x.dims().len() - 1;
    let half = x.dim(last_dim)? / 2;
    let x1 = x.narrow(last_dim, 0, half)?;
    let x2 = x.narrow(last_dim, half, half)?;
    Tensor::cat(&[&x2.neg()?, &x1], last_dim)
}

/// Repeat KV heads for GQA
fn repeat_kv(x: &Tensor, n_rep: usize) -> Result<Tensor> {
    if n_rep == 1 {
        return Ok(x.clone());
    }
    let (batch, n_kv_heads, seq_len, head_dim) = x.dims4()?;
    x.unsqueeze(2)?
        .expand((batch, n_kv_heads, n_rep, seq_len, head_dim))?
        .reshape((batch, n_kv_heads * n_rep, seq_len, head_dim))
}

/// Create causal mask
fn create_causal_mask(
    q_len: usize,
    kv_len: usize,
    start_pos: usize,
    device: &Device,
) -> Result<Tensor> {
    let mut mask = vec![0.0f32; q_len * kv_len];
    for i in 0..q_len {
        for j in 0..kv_len {
            if j > start_pos + i {
                mask[i * kv_len + j] = f32::NEG_INFINITY;
            }
        }
    }
    Tensor::from_vec(mask, (1, 1, q_len, kv_len), device)
}

#[cfg(test)]
mod tests {
    use super::*;

    #[test]
    fn test_rope_cache() {
        let device = Device::Cpu;
        let (cos, sin) = compute_rope_cache(128, 64, 10000.0, &device).unwrap();
        assert_eq!(cos.dims(), &[128, 64]);
        assert_eq!(sin.dims(), &[128, 64]);
    }

    #[test]
    fn test_causal_mask() {
        let device = Device::Cpu;
        let mask = create_causal_mask(4, 8, 4, &device).unwrap();
        assert_eq!(mask.dims(), &[1, 1, 4, 8]);
    }
}
