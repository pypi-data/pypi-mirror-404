//! 4-bit Quantized Llama Model
//!
//! Simple implementation for 4-bit quantized inference.

use candle_core::{DType, Device, IndexOp, Result, Tensor};
use std::collections::HashMap;
use tracing::info;

use crate::kernels::fused_ops::{fused_silu_mul_cuda, softmax_cuda};
use crate::kernels::matmul_4bit::{gemm_4bit, gemm_ternary_multibase};
use crate::layers::RMSNorm;
#[cfg(feature = "cuda")]
use crate::paged_attention::{BlockManager, CacheConfig, CacheEngine, PagedKVCache};

const RMS_NORM_EPS: f64 = 1e-5;

/// CUDA-optimized softmax on last dimension
fn softmax_last_dim(x: &Tensor) -> Result<Tensor> {
    softmax_cuda(x)
}

/// Quantization format
#[derive(Debug, Clone, Copy, PartialEq)]
pub enum QuantFormat {
    /// 4-bit symmetric: [out, in/2] packed, [out, n_groups] scales
    FourBit,
    /// Multi-base ternary (1.58-bit): [out, in/4, n_bases] packed, [n_bases] scales
    TernaryMultiBase { n_bases: usize },
}

/// 4-bit Linear layer (also supports Multi-Base Ternary)
pub struct Linear4Bit {
    pub weight_packed: Tensor,
    pub scales: Tensor,
    pub bias: Option<Tensor>,
    pub group_size: usize,
    pub format: QuantFormat,
}

impl Linear4Bit {
    pub fn load(
        tensors: &HashMap<String, Tensor>,
        prefix: &str,
        group_size: usize,
        device: &Device,
    ) -> Result<Self> {
        let weight_key = format!("{}.weight_4bit", prefix);
        let scales_key = format!("{}.scales_4bit", prefix);
        let bias_key = format!("{}.bias", prefix);

        let weight_packed = tensors
            .get(&weight_key)
            .ok_or_else(|| candle_core::Error::Msg(format!("Missing {}", weight_key)))?
            .to_device(device)?;

        let scales = tensors
            .get(&scales_key)
            .ok_or_else(|| candle_core::Error::Msg(format!("Missing {}", scales_key)))?
            .to_device(device)?;

        let bias = tensors
            .get(&bias_key)
            .map(|t| t.to_device(device))
            .transpose()?;

        // Detect format based on tensor shapes
        let w_dims = weight_packed.dims();
        let s_dims = scales.dims();

        let format = if w_dims.len() == 3 && s_dims.len() == 1 {
            // Multi-base ternary: [out, in/4, n_bases], [n_bases]
            let n_bases = w_dims[2];
            info!(
                "  {} detected as TernaryMultiBase (n_bases={})",
                prefix, n_bases
            );
            QuantFormat::TernaryMultiBase { n_bases }
        } else if w_dims.len() == 2 && s_dims.len() == 2 {
            // 4-bit: [out, in/2], [out, n_groups]
            QuantFormat::FourBit
        } else {
            return Err(candle_core::Error::Msg(format!(
                "Unknown quant format for {}: weight {:?}, scales {:?}",
                prefix, w_dims, s_dims
            )));
        };

        Ok(Self {
            weight_packed,
            scales,
            bias,
            group_size,
            format,
        })
    }

    pub fn forward(&self, x: &Tensor) -> Result<Tensor> {
        let output = match self.format {
            QuantFormat::FourBit => {
                gemm_4bit(x, &self.weight_packed, &self.scales, self.group_size)?
            }
            QuantFormat::TernaryMultiBase { n_bases } => {
                gemm_ternary_multibase(x, &self.weight_packed, &self.scales, n_bases)?
            }
        };
        match &self.bias {
            Some(bias) => output.broadcast_add(bias),
            None => Ok(output),
        }
    }

    /// Forward with timing for profiling
    pub fn forward_timed(&self, x: &Tensor, name: &str) -> Result<Tensor> {
        use std::time::Instant;
        let start = Instant::now();
        let output = match self.format {
            QuantFormat::FourBit => {
                gemm_4bit(x, &self.weight_packed, &self.scales, self.group_size)?
            }
            QuantFormat::TernaryMultiBase { n_bases } => {
                gemm_ternary_multibase(x, &self.weight_packed, &self.scales, n_bases)?
            }
        };
        // Sync CUDA to get accurate time
        let _ = output.flatten_all()?.to_vec1::<f32>();
        info!(
            "      [gemm] {}: {:?} ({:?}, shape: {:?} x {:?})",
            name,
            start.elapsed(),
            self.format,
            x.dims(),
            self.weight_packed.dims()
        );
        match &self.bias {
            Some(bias) => output.broadcast_add(bias),
            None => Ok(output),
        }
    }
}

/// Rotary Position Embedding
fn apply_rotary_emb(
    q: &Tensor,
    k: &Tensor,
    cos: &Tensor,
    sin: &Tensor,
) -> Result<(Tensor, Tensor)> {
    let q_embed = (q.broadcast_mul(cos)? + rotate_half(q)?.broadcast_mul(sin)?)?;
    let k_embed = (k.broadcast_mul(cos)? + rotate_half(k)?.broadcast_mul(sin)?)?;
    Ok((q_embed, k_embed))
}

fn rotate_half(x: &Tensor) -> Result<Tensor> {
    let dims = x.dims();
    let last_dim = dims[dims.len() - 1];
    let half = last_dim / 2;
    let x1 = x.narrow(dims.len() - 1, 0, half)?;
    let x2 = x.narrow(dims.len() - 1, half, half)?;
    Tensor::cat(&[&x2.neg()?, &x1], dims.len() - 1)
}

/// KV Cache for attention (legacy version with Tensor::cat)
#[derive(Clone)]
pub struct KVCache {
    pub k: Tensor,
    pub v: Tensor,
}

impl KVCache {
    pub fn new(k: Tensor, v: Tensor) -> Self {
        Self { k, v }
    }

    pub fn append(&self, new_k: &Tensor, new_v: &Tensor) -> Result<Self> {
        let k = Tensor::cat(&[&self.k, new_k], 2)?;
        let v = Tensor::cat(&[&self.v, new_v], 2)?;
        Ok(Self { k, v })
    }
}

/// Pre-allocated KV Cache - avoids per-token memory allocation
///
/// Allocates buffer for max_seq_len upfront, writes via index.
#[derive(Clone)]
pub struct PreallocKVCache {
    pub k: Tensor,      // [batch, heads, max_seq_len, head_dim]
    pub v: Tensor,      // [batch, heads, max_seq_len, head_dim]
    pub seq_len: usize, // Current sequence length
    pub max_seq_len: usize,
}

impl PreallocKVCache {
    /// Create a new pre-allocated cache
    pub fn new(
        batch_size: usize,
        num_heads: usize,
        max_seq_len: usize,
        head_dim: usize,
        dtype: DType,
        device: &Device,
    ) -> Result<Self> {
        let k = Tensor::zeros(
            (batch_size, num_heads, max_seq_len, head_dim),
            dtype,
            device,
        )?;
        let v = Tensor::zeros(
            (batch_size, num_heads, max_seq_len, head_dim),
            dtype,
            device,
        )?;

        Ok(Self {
            k,
            v,
            seq_len: 0,
            max_seq_len,
        })
    }

    /// Append new K/V values (writes to pre-allocated buffer)
    /// new_k, new_v: [batch, heads, new_tokens, head_dim]
    pub fn append(&mut self, new_k: &Tensor, new_v: &Tensor) -> Result<()> {
        let new_tokens = new_k.dim(2)?;
        let end_pos = self.seq_len + new_tokens;

        if end_pos > self.max_seq_len {
            return Err(candle_core::Error::Msg(format!(
                "KV cache overflow: {} + {} > {}",
                self.seq_len, new_tokens, self.max_seq_len
            )));
        }

        // Write new values to the buffer using slice assignment
        // For CUDA, this should be efficient (no reallocation)
        let _k_slice = self.k.narrow(2, self.seq_len, new_tokens)?;
        let _v_slice = self.v.narrow(2, self.seq_len, new_tokens)?;

        // Copy data (this is still a copy, but into pre-allocated memory)
        // Note: Candle doesn't have in-place slice assignment, so we rebuild
        // the tensor. However, the memory is already allocated.
        let k_before = if self.seq_len > 0 {
            Some(self.k.narrow(2, 0, self.seq_len)?)
        } else {
            None
        };
        let k_after = if end_pos < self.max_seq_len {
            Some(self.k.narrow(2, end_pos, self.max_seq_len - end_pos)?)
        } else {
            None
        };

        // Reconstruct (this is still expensive, but shows the pattern)
        // TODO: Use CUDA kernel for in-place write
        match (k_before, k_after) {
            (Some(before), Some(after)) => {
                self.k = Tensor::cat(&[&before, new_k, &after], 2)?;
                let v_before = self.v.narrow(2, 0, self.seq_len)?;
                let v_after = self.v.narrow(2, end_pos, self.max_seq_len - end_pos)?;
                self.v = Tensor::cat(&[&v_before, new_v, &v_after], 2)?;
            }
            (Some(before), None) => {
                self.k = Tensor::cat(&[&before, new_k], 2)?;
                let v_before = self.v.narrow(2, 0, self.seq_len)?;
                self.v = Tensor::cat(&[&v_before, new_v], 2)?;
            }
            (None, Some(after)) => {
                self.k = Tensor::cat(&[new_k, &after], 2)?;
                let v_after = self.v.narrow(2, end_pos, self.max_seq_len - end_pos)?;
                self.v = Tensor::cat(&[new_v, &v_after], 2)?;
            }
            (None, None) => {
                self.k = new_k.clone();
                self.v = new_v.clone();
            }
        }

        self.seq_len = end_pos;
        Ok(())
    }

    /// Get current K/V (only the filled portion)
    pub fn get_kv(&self) -> Result<(Tensor, Tensor)> {
        let k = self.k.narrow(2, 0, self.seq_len)?;
        let v = self.v.narrow(2, 0, self.seq_len)?;
        Ok((k, v))
    }

    /// Reset cache for new sequence
    pub fn reset(&mut self) {
        self.seq_len = 0;
    }
}

/// Self-Attention with 4-bit projections
pub struct Attention4Bit {
    q_proj: Linear4Bit,
    k_proj: Linear4Bit,
    v_proj: Linear4Bit,
    o_proj: Linear4Bit,
    n_heads: usize,
    n_kv_heads: usize,
    head_dim: usize,
    scale: f64,
}

impl Attention4Bit {
    pub fn load(
        tensors: &HashMap<String, Tensor>,
        prefix: &str,
        n_heads: usize,
        n_kv_heads: usize,
        hidden_dim: usize,
        group_size: usize,
        device: &Device,
    ) -> Result<Self> {
        let head_dim = hidden_dim / n_heads;

        let q_proj = Linear4Bit::load(tensors, &format!("{}.q_proj", prefix), group_size, device)?;
        let k_proj = Linear4Bit::load(tensors, &format!("{}.k_proj", prefix), group_size, device)?;
        let v_proj = Linear4Bit::load(tensors, &format!("{}.v_proj", prefix), group_size, device)?;
        let o_proj = Linear4Bit::load(tensors, &format!("{}.o_proj", prefix), group_size, device)?;

        Ok(Self {
            q_proj,
            k_proj,
            v_proj,
            o_proj,
            n_heads,
            n_kv_heads,
            head_dim,
            scale: 1.0 / (head_dim as f64).sqrt(),
        })
    }

    pub fn forward(
        &self,
        x: &Tensor,
        cos: &Tensor,
        sin: &Tensor,
        kv_cache: Option<&KVCache>,
    ) -> Result<(Tensor, KVCache)> {
        self.forward_internal(x, cos, sin, kv_cache, false)
    }

    pub fn forward_profiled(
        &self,
        x: &Tensor,
        cos: &Tensor,
        sin: &Tensor,
        kv_cache: Option<&KVCache>,
    ) -> Result<(Tensor, KVCache)> {
        self.forward_internal(x, cos, sin, kv_cache, true)
    }

    fn forward_internal(
        &self,
        x: &Tensor,
        cos: &Tensor,
        sin: &Tensor,
        kv_cache: Option<&KVCache>,
        profile: bool,
    ) -> Result<(Tensor, KVCache)> {
        use std::time::Instant;

        // Helper to sync and get time
        fn sync_time(t: &Tensor, start: Instant, name: &str, profile: bool) {
            if profile {
                let _ = t.flatten_all().and_then(|f| f.to_vec1::<f32>());
                info!("        [Attn] {}: {:?}", name, start.elapsed());
            }
        }

        let (batch, seq_len, _) = x.dims3()?;

        // Project Q, K, V
        let proj_start = Instant::now();
        let x_2d = x.reshape((batch * seq_len, ()))?;
        let q = self.q_proj.forward(&x_2d)?;
        let k = self.k_proj.forward(&x_2d)?;
        let v = self.v_proj.forward(&x_2d)?;
        sync_time(&v, proj_start, "Q/K/V proj", profile);

        // Reshape to [batch, seq, heads, head_dim]
        let reshape_start = Instant::now();
        let q = q.reshape((batch, seq_len, self.n_heads, self.head_dim))?;
        let k = k.reshape((batch, seq_len, self.n_kv_heads, self.head_dim))?;
        let v = v.reshape((batch, seq_len, self.n_kv_heads, self.head_dim))?;

        // Transpose to [batch, heads, seq, head_dim]
        let q = q.transpose(1, 2)?;
        let k = k.transpose(1, 2)?;
        let v = v.transpose(1, 2)?;
        sync_time(&v, reshape_start, "reshape+transpose", profile);

        // Apply rotary embeddings
        let rope_start = Instant::now();
        let debug_4bit = std::env::var("DEBUG_4BIT").is_ok();
        if debug_4bit {
            let q_before: Vec<f32> = q.flatten_all()?.to_vec1()?;
            println!(
                "[DEBUG] q before RoPE: {:?}",
                &q_before[..8.min(q_before.len())]
            );
        }
        let (q, k) = apply_rotary_emb(&q, &k, cos, sin)?;
        if debug_4bit {
            let q_after: Vec<f32> = q.flatten_all()?.to_vec1()?;
            println!(
                "[DEBUG] q after RoPE: {:?}",
                &q_after[..8.min(q_after.len())]
            );
        }
        sync_time(&k, rope_start, "RoPE", profile);

        // Handle KV cache
        let cache_start = Instant::now();
        let (k, v, kv_cache_new) = match kv_cache {
            Some(cache) => {
                let new_cache = cache.append(&k, &v)?;
                (new_cache.k.clone(), new_cache.v.clone(), new_cache)
            }
            None => (k.clone(), v.clone(), KVCache::new(k.clone(), v.clone())),
        };
        sync_time(&v, cache_start, "KV cache", profile);

        // Repeat KV heads if GQA
        let repeat_start = Instant::now();
        let k = repeat_kv(&k, self.n_heads / self.n_kv_heads)?;
        let v = repeat_kv(&v, self.n_heads / self.n_kv_heads)?;
        sync_time(&v, repeat_start, "repeat_kv", profile);

        // Ensure contiguous for matmul
        let contig_start = Instant::now();
        let q = q.contiguous()?;
        let k = k.contiguous()?;
        let v = v.contiguous()?;
        sync_time(&v, contig_start, "contiguous", profile);

        // Scaled dot-product attention
        let qk_start = Instant::now();
        let attn_weights = (q.matmul(&k.transpose(2, 3)?.contiguous()?)? * self.scale)?;
        sync_time(&attn_weights, qk_start, "Q@K^T", profile);

        // Causal mask
        let mask_start = Instant::now();
        let total_seq = k.dim(2)?;
        let mask = create_causal_mask(seq_len, total_seq, x.device())?;
        let attn_weights = attn_weights.broadcast_add(&mask)?;
        sync_time(&attn_weights, mask_start, "causal mask", profile);

        let softmax_start = Instant::now();
        let attn_weights = softmax_last_dim(&attn_weights)?;
        sync_time(&attn_weights, softmax_start, "softmax", profile);

        // Debug: print attention weights after softmax
        if std::env::var("DEBUG_4BIT").is_ok() || std::env::var("DEBUG_ATTN").is_ok() {
            let attn_shape = attn_weights.shape();
            println!("[DEBUG] attn_weights after softmax shape: {:?}", attn_shape);
            if let Ok(attn_vec) = attn_weights.flatten_all()?.to_vec1::<f32>() {
                let len = attn_vec.len();
                let sum: f32 = attn_vec.iter().sum();
                let min = attn_vec.iter().cloned().fold(f32::INFINITY, f32::min);
                let max = attn_vec.iter().cloned().fold(f32::NEG_INFINITY, f32::max);
                println!(
                    "[DEBUG] attn_weights stats: len={}, sum={:.4}, min={:.6}, max={:.6}",
                    len, sum, min, max
                );
                // Print first few values
                let preview: Vec<_> = attn_vec.iter().take(16).collect();
                println!("[DEBUG] attn_weights first 16 values: {:?}", preview);
            }
        }

        let av_start = Instant::now();
        let attn_output = attn_weights.matmul(&v)?;
        sync_time(&attn_output, av_start, "Attn@V", profile);

        // Reshape back
        let final_start = Instant::now();
        let attn_output =
            attn_output
                .transpose(1, 2)?
                .reshape((batch, seq_len, self.n_heads * self.head_dim))?;

        // Output projection
        let attn_output_2d = attn_output.reshape((batch * seq_len, ()))?;
        let output = self.o_proj.forward(&attn_output_2d)?;
        let output = output.reshape((batch, seq_len, ()))?;
        sync_time(&output, final_start, "O proj + reshape", profile);

        Ok((output, kv_cache_new))
    }

    /// Forward pass with PagedAttention (efficient KV cache)
    ///
    /// # Arguments
    /// * `x` - Input tensor [batch, seq_len, hidden_dim]
    /// * `cos`, `sin` - RoPE embeddings
    /// * `key_cache`, `value_cache` - Paged KV cache tensors
    /// * `slot_mapping` - Maps tokens to cache slots
    /// * `block_tables` - Block indices per sequence
    /// * `context_lens` - Number of cached tokens per sequence
    #[cfg(feature = "cuda")]
    pub fn forward_paged(
        &self,
        x: &Tensor,
        cos: &Tensor,
        sin: &Tensor,
        key_cache: &Tensor,
        value_cache: &Tensor,
        slot_mapping: &Tensor,
        block_tables: &Tensor,
        context_lens: &Tensor,
    ) -> Result<Tensor> {
        use crate::kernels::paged_attention::{paged_attention_v1, reshape_and_cache};

        let (batch, seq_len, _) = x.dims3()?;

        // Project Q, K, V
        let x_2d = x.reshape((batch * seq_len, ()))?;
        let q = self.q_proj.forward(&x_2d)?;
        let k = self.k_proj.forward(&x_2d)?;
        let v = self.v_proj.forward(&x_2d)?;

        // Reshape to [batch * seq_len, num_heads, head_dim]
        let q = q.reshape((batch * seq_len, self.n_heads, self.head_dim))?;
        let k = k.reshape((batch * seq_len, self.n_kv_heads, self.head_dim))?;
        let v = v.reshape((batch * seq_len, self.n_kv_heads, self.head_dim))?;

        // Apply rotary embeddings
        let q_4d = q
            .reshape((batch, seq_len, self.n_heads, self.head_dim))?
            .transpose(1, 2)?;
        let k_4d = k
            .reshape((batch, seq_len, self.n_kv_heads, self.head_dim))?
            .transpose(1, 2)?;
        let (q_rope, k_rope) = apply_rotary_emb(&q_4d, &k_4d, cos, sin)?;

        // Reshape back for paged attention
        let k_flat =
            k_rope
                .transpose(1, 2)?
                .reshape((batch * seq_len, self.n_kv_heads, self.head_dim))?;
        let v_flat = v; // V doesn't need RoPE

        // Write K/V to paged cache
        reshape_and_cache(&k_flat, &v_flat, key_cache, value_cache, slot_mapping)?;

        // Compute attention using paged cache
        let q_flat = q_rope
            .transpose(1, 2)?
            .reshape((batch, self.n_heads, self.head_dim))?;

        let attn_output = paged_attention_v1(
            &q_flat,
            key_cache,
            value_cache,
            block_tables,
            context_lens,
            self.scale as f32,
        )?;

        // Reshape and project output
        let attn_output = attn_output.reshape((batch, self.n_heads * self.head_dim))?;
        let output = self.o_proj.forward(&attn_output)?;
        let output = output.reshape((batch, 1, ()))?;

        Ok(output)
    }
}

fn repeat_kv(x: &Tensor, n_rep: usize) -> Result<Tensor> {
    if n_rep == 1 {
        return Ok(x.clone());
    }
    let (batch, n_kv_heads, seq_len, head_dim) = x.dims4()?;
    x.unsqueeze(2)?
        .expand((batch, n_kv_heads, n_rep, seq_len, head_dim))?
        .reshape((batch, n_kv_heads * n_rep, seq_len, head_dim))
}

fn create_causal_mask(q_len: usize, kv_len: usize, device: &Device) -> Result<Tensor> {
    // Create causal mask: lower triangular with offset
    // For autoregressive attention: position i can attend to positions 0..=i
    let offset = kv_len as i64 - q_len as i64;
    let mut mask_data = vec![0.0f32; q_len * kv_len];
    for i in 0..q_len {
        for j in 0..kv_len {
            // Allow attention if j <= i + offset
            if j as i64 <= i as i64 + offset {
                mask_data[i * kv_len + j] = 0.0; // No mask
            } else {
                mask_data[i * kv_len + j] = f32::NEG_INFINITY; // Mask out
            }
        }
    }
    Tensor::from_vec(mask_data, (q_len, kv_len), device)
}

/// MLP with 4-bit projections (SwiGLU)
pub struct MLP4Bit {
    gate_proj: Linear4Bit,
    up_proj: Linear4Bit,
    down_proj: Linear4Bit,
}

impl MLP4Bit {
    pub fn load(
        tensors: &HashMap<String, Tensor>,
        prefix: &str,
        group_size: usize,
        device: &Device,
    ) -> Result<Self> {
        let gate_proj = Linear4Bit::load(
            tensors,
            &format!("{}.gate_proj", prefix),
            group_size,
            device,
        )?;
        let up_proj =
            Linear4Bit::load(tensors, &format!("{}.up_proj", prefix), group_size, device)?;
        let down_proj = Linear4Bit::load(
            tensors,
            &format!("{}.down_proj", prefix),
            group_size,
            device,
        )?;

        Ok(Self {
            gate_proj,
            up_proj,
            down_proj,
        })
    }

    pub fn forward(&self, x: &Tensor) -> Result<Tensor> {
        let (batch, seq_len, hidden) = x.dims3()?;
        let x_2d = x.reshape((batch * seq_len, hidden))?;

        // Use fused CUDA kernel for SiLU(gate) * up
        let gate = self.gate_proj.forward(&x_2d)?;
        let up = self.up_proj.forward(&x_2d)?;
        let hidden_states = fused_silu_mul_cuda(&gate, &up)?;
        let output = self.down_proj.forward(&hidden_states)?;

        output.reshape((batch, seq_len, ()))
    }
}

/// Transformer Block with 4-bit layers
pub struct Block4Bit {
    self_attn: Attention4Bit,
    mlp: MLP4Bit,
    input_layernorm: RMSNorm,
    post_attention_layernorm: RMSNorm,
}

impl Block4Bit {
    pub fn load(
        tensors: &HashMap<String, Tensor>,
        prefix: &str,
        n_heads: usize,
        n_kv_heads: usize,
        hidden_dim: usize,
        group_size: usize,
        device: &Device,
    ) -> Result<Self> {
        let self_attn = Attention4Bit::load(
            tensors,
            &format!("{}.self_attn", prefix),
            n_heads,
            n_kv_heads,
            hidden_dim,
            group_size,
            device,
        )?;

        let mlp = MLP4Bit::load(tensors, &format!("{}.mlp", prefix), group_size, device)?;

        let input_layernorm = RMSNorm::load_direct(
            tensors,
            &format!("{}.input_layernorm.weight", prefix),
            hidden_dim,
            RMS_NORM_EPS,
            device,
        )?;

        let post_attention_layernorm = RMSNorm::load_direct(
            tensors,
            &format!("{}.post_attention_layernorm.weight", prefix),
            hidden_dim,
            RMS_NORM_EPS,
            device,
        )?;

        Ok(Self {
            self_attn,
            mlp,
            input_layernorm,
            post_attention_layernorm,
        })
    }

    pub fn forward(
        &self,
        x: &Tensor,
        cos: &Tensor,
        sin: &Tensor,
        kv_cache: Option<&KVCache>,
    ) -> Result<(Tensor, KVCache)> {
        // Self-attention with residual
        let residual = x.clone();
        let x = self.input_layernorm.forward(x)?;
        let (attn_output, kv_cache_new) = self.self_attn.forward(&x, cos, sin, kv_cache)?;
        let x = (residual + attn_output)?;

        // MLP with residual
        let residual = x.clone();
        let x = self.post_attention_layernorm.forward(&x)?;
        let mlp_output = self.mlp.forward(&x)?;
        let x = (residual + mlp_output)?;

        Ok((x, kv_cache_new))
    }

    pub fn forward_profiled(
        &self,
        x: &Tensor,
        cos: &Tensor,
        sin: &Tensor,
        kv_cache: Option<&KVCache>,
    ) -> Result<(Tensor, KVCache)> {
        use std::time::Instant;

        info!("      [Block] Starting profiled forward");

        // Self-attention with residual
        let residual = x.clone();
        let norm_start = Instant::now();
        let x = self.input_layernorm.forward(x)?;
        let _ = x.flatten_all()?.to_vec1::<f32>();
        info!("      [Block] input_layernorm: {:?}", norm_start.elapsed());

        let attn_start = Instant::now();
        let (attn_output, kv_cache_new) =
            self.self_attn.forward_profiled(&x, cos, sin, kv_cache)?;
        info!("      [Block] self_attn TOTAL: {:?}", attn_start.elapsed());

        let add_start = Instant::now();
        let x = (residual + attn_output)?;
        let _ = x.flatten_all()?.to_vec1::<f32>();
        info!("      [Block] residual add: {:?}", add_start.elapsed());

        // MLP with residual
        let residual = x.clone();
        let norm_start = Instant::now();
        let x = self.post_attention_layernorm.forward(&x)?;
        let _ = x.flatten_all()?.to_vec1::<f32>();
        info!(
            "      [Block] post_attn_layernorm: {:?}",
            norm_start.elapsed()
        );

        let mlp_start = Instant::now();
        let mlp_output = self.mlp.forward(&x)?;
        let _ = mlp_output.flatten_all()?.to_vec1::<f32>();
        info!("      [Block] MLP: {:?}", mlp_start.elapsed());

        let add_start = Instant::now();
        let x = (residual + mlp_output)?;
        let _ = x.flatten_all()?.to_vec1::<f32>();
        info!(
            "      [Block] final residual add: {:?}",
            add_start.elapsed()
        );

        Ok((x, kv_cache_new))
    }

    /// Forward pass with PagedAttention
    #[cfg(feature = "cuda")]
    pub fn forward_paged(
        &self,
        x: &Tensor,
        cos: &Tensor,
        sin: &Tensor,
        key_cache: &Tensor,
        value_cache: &Tensor,
        slot_mapping: &Tensor,
        block_tables: &Tensor,
        context_lens: &Tensor,
    ) -> Result<Tensor> {
        // Self-attention with residual
        let residual = x.clone();
        let x = self.input_layernorm.forward(x)?;

        let attn_output = self.self_attn.forward_paged(
            &x,
            cos,
            sin,
            key_cache,
            value_cache,
            slot_mapping,
            block_tables,
            context_lens,
        )?;

        let x = (residual + attn_output)?;

        // MLP with residual
        let residual = x.clone();
        let x = self.post_attention_layernorm.forward(&x)?;
        let mlp_output = self.mlp.forward(&x)?;
        let x = (residual + mlp_output)?;

        Ok(x)
    }
}

/// Full 4-bit Llama Model
pub struct Llama4Bit {
    pub embedding: Tensor,
    pub blocks: Vec<Block4Bit>,
    pub norm: RMSNorm,
    pub lm_head: Linear4Bit,
    pub kv_caches: Vec<Option<KVCache>>,
    pub config: Llama4BitConfig,
    pub device: Device,
    // RoPE
    cos_cache: Tensor,
    sin_cache: Tensor,
    // Hybrid GPU/CPU support
    layer_devices: Vec<Device>,
    n_gpu_layers: usize,
}

#[derive(Clone, Debug, serde::Deserialize, serde::Serialize)]
pub struct Llama4BitConfig {
    pub hidden_size: usize,
    pub num_layers: usize,
    pub n_heads: usize,
    pub n_kv_heads: usize,
    pub vocab_size: usize,
    #[serde(default = "default_group_size")]
    pub group_size: usize,
    #[serde(default = "default_rope_theta")]
    pub rope_theta: f64,
    #[serde(default = "default_max_position_embeddings")]
    pub max_position_embeddings: usize,
}

fn default_group_size() -> usize {
    128
}
fn default_rope_theta() -> f64 {
    10000.0
}
fn default_max_position_embeddings() -> usize {
    2048
}

impl Llama4Bit {
    /// Load with hybrid GPU/CPU support
    /// n_gpu_layers: -1 = all GPU, 0 = all CPU, N = first N layers on GPU
    pub fn load_hybrid(
        tensors: &HashMap<String, Tensor>,
        config: Llama4BitConfig,
        gpu_device: &Device,
        n_gpu_layers: i32,
    ) -> Result<Self> {
        let cpu_device = Device::Cpu;
        let effective_gpu_layers = if n_gpu_layers < 0 {
            config.num_layers
        } else {
            (n_gpu_layers as usize).min(config.num_layers)
        };

        info!(
            "Loading 4-bit Llama model (hybrid: {} GPU layers, {} CPU layers)...",
            effective_gpu_layers,
            config.num_layers - effective_gpu_layers
        );

        // Embedding on GPU if any GPU layers, else CPU
        let embed_device = if effective_gpu_layers > 0 {
            gpu_device
        } else {
            &cpu_device
        };
        let embedding = tensors
            .get("model.embed_tokens.weight")
            .ok_or_else(|| candle_core::Error::Msg("Missing embed_tokens".to_string()))?
            .to_device(embed_device)?
            .to_dtype(DType::F32)?;

        info!("  Embedding: {:?} on {:?}", embedding.dims(), embed_device);

        // Blocks - first n_gpu_layers on GPU, rest on CPU
        let mut blocks = Vec::with_capacity(config.num_layers);
        let mut layer_devices = Vec::with_capacity(config.num_layers);
        for i in 0..config.num_layers {
            let layer_device = if i < effective_gpu_layers {
                gpu_device
            } else {
                &cpu_device
            };
            info!(
                "  Loading layer {}/{} on {:?}",
                i + 1,
                config.num_layers,
                layer_device
            );
            let block = Block4Bit::load(
                tensors,
                &format!("model.layers.{}", i),
                config.n_heads,
                config.n_kv_heads,
                config.hidden_size,
                config.group_size,
                layer_device,
            )?;
            blocks.push(block);
            layer_devices.push(layer_device.clone());
        }

        // Final norm and LM head on same device as last layer
        let final_device = if effective_gpu_layers > 0 {
            gpu_device
        } else {
            &cpu_device
        };

        // Final norm
        let norm = RMSNorm::load_direct(
            tensors,
            "model.norm.weight",
            config.hidden_size,
            RMS_NORM_EPS,
            final_device,
        )?;

        // LM head
        let lm_head = Linear4Bit::load(tensors, "lm_head", config.group_size, final_device)?;
        info!(
            "  LM Head: {:?} on {:?}",
            lm_head.weight_packed.dims(),
            final_device
        );

        // Initialize KV caches
        let kv_caches = vec![None; config.num_layers];

        // Precompute RoPE on GPU if available
        let head_dim = config.hidden_size / config.n_heads;
        let (cos_cache, sin_cache) = precompute_rope(
            head_dim,
            config.max_position_embeddings,
            config.rope_theta,
            gpu_device,
        )?;

        info!("4-bit Llama model loaded successfully!");

        Ok(Self {
            embedding,
            blocks,
            norm,
            lm_head,
            kv_caches,
            config,
            device: gpu_device.clone(),
            cos_cache,
            sin_cache,
            layer_devices,
            n_gpu_layers: effective_gpu_layers,
        })
    }

    /// Load all layers on specified device (backward compatible)
    pub fn load(
        tensors: &HashMap<String, Tensor>,
        config: Llama4BitConfig,
        device: &Device,
    ) -> Result<Self> {
        Self::load_hybrid(tensors, config, device, -1)
    }

    pub fn forward(&mut self, input_ids: &Tensor, start_pos: usize) -> Result<Tensor> {
        self.forward_internal(input_ids, start_pos, false)
    }

    pub fn forward_profiled(&mut self, input_ids: &Tensor, start_pos: usize) -> Result<Tensor> {
        self.forward_internal(input_ids, start_pos, true)
    }

    fn forward_internal(
        &mut self,
        input_ids: &Tensor,
        start_pos: usize,
        profile: bool,
    ) -> Result<Tensor> {
        use std::time::Instant;

        let (batch, seq_len) = input_ids.dims2()?;
        let total_start = Instant::now();

        // Embedding lookup
        let emb_start = Instant::now();
        let input_ids_flat = input_ids.flatten_all()?;
        let hidden_states = self.embedding.index_select(&input_ids_flat, 0)?;
        let hidden_states = hidden_states.reshape((batch, seq_len, self.config.hidden_size))?;
        if profile {
            // Sync CUDA to get accurate timing
            let _ = hidden_states.to_vec1::<f32>();
            info!("  [Profile] Embedding: {:?}", emb_start.elapsed());
        }

        // Get RoPE for this position
        let cos = self.cos_cache.narrow(0, start_pos, seq_len)?;
        let sin = self.sin_cache.narrow(0, start_pos, seq_len)?;

        // Debug: Compare cos values at position 0 vs start_pos
        if std::env::var("DEBUG_4BIT").is_ok() {
            let cos_at_0 = self
                .cos_cache
                .narrow(0, 0, 1)?
                .flatten_all()?
                .to_vec1::<f32>()?;
            let cos_at_start = cos.narrow(0, 0, 1)?.flatten_all()?.to_vec1::<f32>()?;
            println!(
                "[DEBUG RoPE] start_pos={}, cos[0][0..4]={:?}, cos[start_pos][0..4]={:?}",
                start_pos,
                &cos_at_0[..4.min(cos_at_0.len())],
                &cos_at_start[..4.min(cos_at_start.len())]
            );
        }

        // Forward through all blocks
        let mut x = hidden_states;
        let mut block_times = Vec::new();
        for (i, block) in self.blocks.iter().enumerate() {
            let block_start = Instant::now();

            // Move tensor to layer's device if needed (hybrid GPU/CPU)
            let target_device = &self.layer_devices[i];
            let need_move = match (x.device(), target_device) {
                (Device::Cpu, Device::Cpu) => false,
                (Device::Cuda(_), Device::Cuda(_)) => false, // Assume same GPU
                _ => true,
            };
            if need_move {
                x = x.to_device(target_device)?;
                if profile {
                    info!(
                        "    [Profile] Moved to {:?} before layer {}",
                        target_device, i
                    );
                }
            }

            // Move RoPE to same device
            let cos_layer = cos.to_device(target_device)?;
            let sin_layer = sin.to_device(target_device)?;

            let kv_cache = self.kv_caches[i].as_ref();
            // Profile Block 0 in detail
            let (new_x, new_kv_cache) = if profile && i == 0 {
                info!("    [Profile] Block 0 detailed:");
                block.forward_profiled(&x, &cos_layer, &sin_layer, kv_cache)?
            } else {
                block.forward(&x, &cos_layer, &sin_layer, kv_cache)?
            };
            x = new_x;
            self.kv_caches[i] = Some(new_kv_cache);
            if profile {
                // Sync CUDA
                let _ = x.flatten_all()?.to_vec1::<f32>();
                block_times.push(block_start.elapsed());
            }
        }
        if profile && !block_times.is_empty() {
            let total_blocks: std::time::Duration = block_times.iter().sum();
            let avg_block = total_blocks / block_times.len() as u32;
            info!(
                "  [Profile] Blocks total: {:?} (avg per block: {:?})",
                total_blocks, avg_block
            );
            // Show first 3 and last block
            if block_times.len() > 4 {
                info!(
                    "    Block 0: {:?}, Block 1: {:?}, Block 2: {:?}, ... Block {}: {:?}",
                    block_times[0],
                    block_times[1],
                    block_times[2],
                    block_times.len() - 1,
                    block_times[block_times.len() - 1]
                );
            }
        }

        // Final norm - move to GPU if needed (norm/lm_head are on GPU when n_gpu_layers > 0)
        let norm_start = Instant::now();
        let need_move_final = matches!((x.device(), &self.device), (Device::Cpu, Device::Cuda(_)));
        let x = if self.n_gpu_layers > 0 && need_move_final {
            x.to_device(&self.device)?
        } else {
            x
        };
        let x = self.norm.forward(&x)?;
        if profile {
            let _ = x.flatten_all()?.to_vec1::<f32>();
            info!("  [Profile] Final norm: {:?}", norm_start.elapsed());
        }

        // LM head (only last token for generation)
        let lm_start = Instant::now();
        let last_hidden = x.i((.., seq_len - 1, ..))?;
        let last_hidden_2d = last_hidden.reshape((batch, self.config.hidden_size))?;

        // Debug: hidden state before lm_head
        if std::env::var("DEBUG_4BIT").is_ok() || std::env::var("DEBUG_HIDDEN").is_ok() {
            let hidden_vec: Vec<f32> = last_hidden_2d.flatten_all()?.to_vec1()?;
            println!(
                "[DEBUG Hidden] before lm_head first 8: {:?}",
                &hidden_vec[..8]
            );
            println!(
                "[DEBUG Hidden] before lm_head sum: {:.4}",
                hidden_vec.iter().sum::<f32>()
            );
        }

        let logits = self.lm_head.forward(&last_hidden_2d)?;
        if profile {
            let _ = logits.flatten_all()?.to_vec1::<f32>();
            info!("  [Profile] LM head: {:?}", lm_start.elapsed());
            info!("  [Profile] TOTAL forward: {:?}", total_start.elapsed());
        }

        Ok(logits)
    }

    pub fn clear_kv_cache(&mut self) {
        self.kv_caches = vec![None; self.config.num_layers];
    }

    /// Generate tokens
    pub fn generate(
        &mut self,
        input_ids: &[u32],
        max_new_tokens: usize,
        temperature: f64,
    ) -> Result<Vec<u32>> {
        let mut tokens = input_ids.to_vec();
        self.clear_kv_cache();
        let debug = std::env::var("DEBUG_4BIT").is_ok();

        if debug {
            println!(
                "[DEBUG generate] Starting generation, input_ids.len() = {}",
                input_ids.len()
            );
        }

        // Prefill
        let input_tensor = Tensor::new(&tokens[..], &self.device)?;
        let input_tensor = input_tensor.unsqueeze(0)?; // [1, seq_len]
        let prefill_logits = self.forward(&input_tensor, 0)?;

        // Debug: KV cache state after prefill
        if debug {
            if let Some(ref cache) = self.kv_caches[0] {
                let kv_seq_len = cache.k.dim(2).unwrap_or(0);
                println!(
                    "[DEBUG generate] After prefill: KV cache seq_len = {}",
                    kv_seq_len
                );
            }
        }

        // Sample first token from prefill logits
        let logits_vec: Vec<f32> = prefill_logits.flatten_all()?.to_vec1()?;
        let mut indexed: Vec<(usize, f32)> = logits_vec
            .iter()
            .enumerate()
            .map(|(i, &v)| (i, v))
            .collect();
        indexed.sort_by(|a, b| b.1.partial_cmp(&a.1).unwrap());
        if debug {
            println!("  Prefill - Top 5 logits:");
            for (rank, (tok, score)) in indexed.iter().take(5).enumerate() {
                println!("    {}. token {} = {:.4}", rank + 1, tok, score);
            }
        }

        // Sample first token from prefill and add to tokens
        let first_generated = if temperature < 1e-6 {
            indexed[0].0 as u32
        } else {
            let logits = (prefill_logits / temperature)?;
            let probs = softmax_last_dim(&logits)?;
            sample_from_probs(&probs)?
        };
        tokens.push(first_generated);
        if debug {
            println!(
                "[DEBUG generate] First generated token from prefill: {}",
                first_generated
            );
        }

        // Check for EOS
        if first_generated == 2 {
            return Ok(tokens);
        }

        // Generate remaining tokens
        for i in 0..(max_new_tokens - 1) {
            let pos = tokens.len();
            let last_token = Tensor::new(&[tokens[tokens.len() - 1]], &self.device)?;
            let last_token = last_token.unsqueeze(0)?;

            // Debug: pos and KV cache state before forward
            if debug {
                let kv_seq_len = if let Some(ref cache) = self.kv_caches[0] {
                    cache.k.dim(2).unwrap_or(0)
                } else {
                    0
                };
                println!(
                    "[DEBUG generate] Step {}: pos = {}, KV cache seq_len = {}, tokens.len() = {}",
                    i,
                    pos,
                    kv_seq_len,
                    tokens.len()
                );
            }

            // Position for current token being processed
            // pos = tokens.len(), but current token is at position (pos - 1) because 0-indexed
            let logits = self.forward(&last_token, pos - 1)?;

            // Debug: KV cache state after forward
            if debug {
                if let Some(ref cache) = self.kv_caches[0] {
                    let new_kv_seq_len = cache.k.dim(2).unwrap_or(0);
                    println!(
                        "[DEBUG generate] Step {}: After forward, KV cache seq_len = {}",
                        i, new_kv_seq_len
                    );
                }
            }

            // Sample from logits
            let logits_vec: Vec<f32> = logits.flatten_all()?.to_vec1()?;
            let mut indexed: Vec<(usize, f32)> = logits_vec
                .iter()
                .enumerate()
                .map(|(i, &v)| (i, v))
                .collect();
            indexed.sort_by(|a, b| b.1.partial_cmp(&a.1).unwrap());
            if debug && i == 0 {
                println!("  First generation - Top 5 logits:");
                for (rank, (tok, score)) in indexed.iter().take(5).enumerate() {
                    println!("    {}. token {} = {:.4}", rank + 1, tok, score);
                }
            }

            // Sample
            let next_token = if temperature < 1e-6 {
                // Greedy - argmax over vocab dimension
                indexed[0].0 as u32
            } else {
                // Temperature sampling
                let logits = (logits / temperature)?;
                let probs = softmax_last_dim(&logits)?;
                sample_from_probs(&probs)?
            };

            tokens.push(next_token);

            // Stop on EOS (token 2 for Llama)
            if next_token == 2 {
                break;
            }
        }

        Ok(tokens)
    }

    /// Generate tokens with PagedAttention (efficient KV cache)
    ///
    /// Uses paged memory for KV cache to avoid per-token memory allocation.
    /// Set `use_paged_decode = false` to use traditional KV cache for decode (debug mode).
    #[cfg(feature = "cuda")]
    pub fn generate_paged(
        &mut self,
        input_ids: &[u32],
        max_new_tokens: usize,
        temperature: f64,
    ) -> Result<Vec<u32>> {
        // Set to true for PagedAttention, false for traditional (debug)
        let use_paged_decode = true;
        self.generate_paged_internal(input_ids, max_new_tokens, temperature, use_paged_decode)
    }

    /// Internal implementation with configurable decode mode
    #[cfg(feature = "cuda")]
    fn generate_paged_internal(
        &mut self,
        input_ids: &[u32],
        max_new_tokens: usize,
        temperature: f64,
        use_paged_decode: bool,
    ) -> Result<Vec<u32>> {
        use crate::kernels::paged_attention::reshape_and_cache;
        use std::time::Instant;

        let mut tokens = input_ids.to_vec();
        let head_dim = self.config.hidden_size / self.config.n_heads;

        // Initialize paged cache for all layers
        let cache_config = CacheConfig::new(
            self.config.n_kv_heads,
            head_dim,
            self.config.num_layers,
            self.config.max_position_embeddings,
            1, // batch_size = 1
        );

        let cache_engine = CacheEngine::new(cache_config.clone(), DType::F32, &self.device)?;
        let mut block_manager =
            BlockManager::new(cache_engine.num_blocks(), cache_engine.block_size());

        // Allocate sequence
        let seq_id = block_manager.allocate_sequence();

        info!(
            "PagedAttention: {} blocks × {} layers, {} tokens/block, {:.1} MB",
            cache_engine.num_blocks(),
            self.config.num_layers,
            cache_engine.block_size(),
            cache_config.memory_bytes(DType::F32) as f64 / (1024.0 * 1024.0)
        );

        // Get all layer caches
        let layer_caches = cache_engine.get_all_caches();

        // ===== PREFILL =====
        // Use standard forward for prefill (builds KV cache traditionally)
        let prefill_start = Instant::now();
        self.clear_kv_cache();
        let input_tensor = Tensor::new(&tokens[..], &self.device)?;
        let input_tensor = input_tensor.unsqueeze(0)?;
        let prefill_logits = self.forward(&input_tensor, 0)?;

        // Sample first token from prefill logits
        let logits_vec: Vec<f32> = prefill_logits.flatten_all()?.to_vec1()?;
        let mut indexed: Vec<(usize, f32)> = logits_vec
            .iter()
            .enumerate()
            .map(|(i, &v)| (i, v))
            .collect();
        indexed.sort_by(|a, b| b.1.partial_cmp(&a.1).unwrap());

        let first_generated = if temperature < 1e-6 {
            indexed[0].0 as u32
        } else {
            let logits = (prefill_logits / temperature)?;
            let probs = softmax_last_dim(&logits)?;
            sample_from_probs(&probs)?
        };
        tokens.push(first_generated);

        // Check for EOS
        if first_generated == 2 {
            return Ok(tokens);
        }

        // Allocate slots for prefill tokens in paged cache (including new token)
        let prefill_len = tokens.len() - 1; // Original input length (not including generated token)
        let prefill_slots = block_manager.allocate_slots(seq_id, prefill_len)?;
        let slot_tensor = Tensor::from_vec(prefill_slots.clone(), (prefill_len,), &self.device)?;

        // Copy prefill K/V from traditional cache to paged cache
        for (layer_idx, kv_cache) in self.kv_caches.iter().enumerate() {
            if let Some(cache) = kv_cache {
                let layer_paged = &layer_caches[layer_idx];
                // K: [batch, heads, seq, head_dim] -> [batch*seq, heads, head_dim]
                let k = cache.k.transpose(1, 2)?.reshape((
                    prefill_len,
                    self.config.n_kv_heads,
                    head_dim,
                ))?;
                let v = cache.v.transpose(1, 2)?.reshape((
                    prefill_len,
                    self.config.n_kv_heads,
                    head_dim,
                ))?;
                reshape_and_cache(
                    &k,
                    &v,
                    &layer_paged.key_cache,
                    &layer_paged.value_cache,
                    &slot_tensor,
                )?;
            }
        }
        info!(
            "Prefill: {:?} ({} tokens), decode_mode={}",
            prefill_start.elapsed(),
            prefill_len,
            if use_paged_decode {
                "paged"
            } else {
                "traditional"
            }
        );

        // ===== DECODE =====
        let decode_start = Instant::now();
        let max_blocks_per_seq = (self.config.max_position_embeddings + cache_engine.block_size()
            - 1)
            / cache_engine.block_size();

        // Generate remaining tokens (first one already generated from prefill)
        for i in 0..(max_new_tokens - 1) {
            let gen_start = Instant::now();
            let pos = tokens.len();

            let logits = if use_paged_decode {
                // ===== PagedAttention decode =====
                // Allocate slot for new token
                let new_slots = block_manager.allocate_slots(seq_id, 1)?;
                let slot_tensor = Tensor::from_vec(new_slots.clone(), (1,), &self.device)?;

                // Get block table and context length
                // context_len = number of tokens to attend to (including current)
                // pos = tokens.len(), so context_len = pos (positions 0 to pos-1)
                let block_table = block_manager.get_block_table_tensor(
                    seq_id,
                    max_blocks_per_seq,
                    &self.device,
                )?;
                let context_len = pos;
                let context_lens = Tensor::from_vec(vec![context_len as u32], (1,), &self.device)?;

                // Embedding for last token
                let last_token_id = tokens[tokens.len() - 1];
                let last_token = Tensor::new(&[last_token_id], &self.device)?;
                let hidden = self.embedding.index_select(&last_token, 0)?;
                let hidden = hidden.reshape((1, 1, self.config.hidden_size))?;

                // RoPE - position for the current token being processed
                let cos = self.cos_cache.narrow(0, pos - 1, 1)?;
                let sin = self.sin_cache.narrow(0, pos - 1, 1)?;

                // Forward through all blocks with PagedAttention
                let mut x = hidden;
                for (layer_idx, block) in self.blocks.iter().enumerate() {
                    let layer_cache = &layer_caches[layer_idx];
                    x = block.forward_paged(
                        &x,
                        &cos,
                        &sin,
                        &layer_cache.key_cache,
                        &layer_cache.value_cache,
                        &slot_tensor,
                        &block_table,
                        &context_lens,
                    )?;
                }

                // Final norm and LM head
                let x = self.norm.forward(&x)?;
                let x = x.reshape((1, self.config.hidden_size))?;
                self.lm_head.forward(&x)?
            } else {
                // ===== Traditional decode (debug mode) =====
                // Uses self.kv_caches built during prefill
                let last_token = Tensor::new(&[tokens[tokens.len() - 1]], &self.device)?;
                let last_token = last_token.unsqueeze(0)?;
                self.forward(&last_token, pos - 1)? // pos-1 is correct: processing token at position (tokens.len()-1)
            };

            // Sample next token
            let logits_vec: Vec<f32> = logits.flatten_all()?.to_vec1()?;
            let mut indexed: Vec<(usize, f32)> = logits_vec
                .iter()
                .enumerate()
                .map(|(i, &v)| (i, v))
                .collect();
            indexed.sort_by(|a, b| b.1.partial_cmp(&a.1).unwrap());

            let next_token = if temperature < 1e-6 {
                indexed[0].0 as u32
            } else {
                let logits = (logits / temperature)?;
                let probs = softmax_last_dim(&logits)?;
                sample_from_probs(&probs)?
            };

            tokens.push(next_token);

            let elapsed = gen_start.elapsed();
            if i < 3 || (i + 1) % 10 == 0 {
                info!(
                    "Token {}: {} ({:.2} tok/s)",
                    i + 1,
                    next_token,
                    1.0 / elapsed.as_secs_f64()
                );
            }

            if next_token == 2 {
                break;
            }
        }

        let total_decode = decode_start.elapsed();
        let decode_tokens = tokens.len() - input_ids.len();
        info!(
            "Decode: {:?} ({} tokens, {:.2} tok/s)",
            total_decode,
            decode_tokens,
            decode_tokens as f64 / total_decode.as_secs_f64()
        );

        Ok(tokens)
    }
}

fn precompute_rope(
    head_dim: usize,
    max_seq_len: usize,
    theta: f64,
    device: &Device,
) -> Result<(Tensor, Tensor)> {
    let inv_freq: Vec<f32> = (0..head_dim)
        .step_by(2)
        .map(|i| 1.0 / (theta.powf(i as f64 / head_dim as f64)) as f32)
        .collect();

    let inv_freq = Tensor::new(&inv_freq[..], device)?;
    let positions: Vec<f32> = (0..max_seq_len).map(|i| i as f32).collect();
    let positions = Tensor::new(&positions[..], device)?;

    let freqs = positions.unsqueeze(1)?.matmul(&inv_freq.unsqueeze(0)?)?;
    let freqs = Tensor::cat(&[&freqs, &freqs], 1)?;

    let cos = freqs.cos()?;
    let sin = freqs.sin()?;

    Ok((cos, sin))
}

fn sample_from_probs(probs: &Tensor) -> Result<u32> {
    use rand::distributions::Distribution;

    let probs_vec: Vec<f32> = probs.flatten_all()?.to_vec1()?;

    let dist = rand::distributions::WeightedIndex::new(&probs_vec)
        .map_err(|e| candle_core::Error::Msg(format!("Sampling error: {}", e)))?;

    let mut rng = rand::thread_rng();
    Ok(dist.sample(&mut rng) as u32)
}
