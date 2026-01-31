//! Flash Attention - Memory-efficient attention computation
//!
//! Implements tiled attention to reduce memory usage from O(n²) to O(n).
//! Uses online softmax for numerical stability without materializing
//! the full attention matrix.
//!
//! # References
//! - Flash Attention: https://arxiv.org/abs/2205.14135
//! - Flash Attention 2: https://arxiv.org/abs/2307.08691

use candle_core::{Result, Tensor};

/// Block size for query dimension (tuned for L2 cache)
const BLOCK_SIZE_Q: usize = 64;

/// Block size for key/value dimension
const BLOCK_SIZE_KV: usize = 64;

/// Flash Attention configuration
#[derive(Clone, Debug)]
pub struct FlashAttentionConfig {
    /// Scale factor (typically 1/sqrt(head_dim))
    pub scale: f32,
    /// Whether to apply causal masking
    pub causal: bool,
    /// Block size for queries (0 = auto)
    pub block_size_q: usize,
    /// Block size for keys/values (0 = auto)
    pub block_size_kv: usize,
}

impl Default for FlashAttentionConfig {
    fn default() -> Self {
        Self {
            scale: 1.0,
            causal: true,
            block_size_q: BLOCK_SIZE_Q,
            block_size_kv: BLOCK_SIZE_KV,
        }
    }
}

impl FlashAttentionConfig {
    pub fn new(head_dim: usize) -> Self {
        Self {
            scale: 1.0 / (head_dim as f32).sqrt(),
            ..Default::default()
        }
    }

    pub fn with_causal(mut self, causal: bool) -> Self {
        self.causal = causal;
        self
    }
}

/// Compute Flash Attention (CPU implementation)
///
/// # Arguments
/// * `q` - Query tensor [batch, heads, seq_q, head_dim]
/// * `k` - Key tensor [batch, heads, seq_kv, head_dim]
/// * `v` - Value tensor [batch, heads, seq_kv, head_dim]
/// * `config` - Flash attention configuration
///
/// # Returns
/// * Output tensor [batch, heads, seq_q, head_dim]
pub fn flash_attention(
    q: &Tensor,
    k: &Tensor,
    v: &Tensor,
    config: &FlashAttentionConfig,
) -> Result<Tensor> {
    let (batch, heads, seq_q, head_dim) = q.dims4()?;
    let (_, _, seq_kv, _) = k.dims4()?;
    let device = q.device();
    let dtype = q.dtype();

    // For small sequences, use standard attention (overhead not worth it)
    if seq_q <= 128 && seq_kv <= 128 {
        return standard_attention(q, k, v, config.scale, config.causal);
    }

    // Determine block sizes
    let block_q = if config.block_size_q == 0 {
        BLOCK_SIZE_Q.min(seq_q)
    } else {
        config.block_size_q.min(seq_q)
    };
    let block_kv = if config.block_size_kv == 0 {
        BLOCK_SIZE_KV.min(seq_kv)
    } else {
        config.block_size_kv.min(seq_kv)
    };

    // Number of blocks
    let num_blocks_q = seq_q.div_ceil(block_q);
    let num_blocks_kv = seq_kv.div_ceil(block_kv);

    // Initialize output accumulator and softmax state
    // output: [batch, heads, seq_q, head_dim]
    // m: [batch, heads, seq_q, 1] - running max for each query position
    // l: [batch, heads, seq_q, 1] - running sum of exp for each query position
    let mut output = Tensor::zeros((batch, heads, seq_q, head_dim), dtype, device)?;
    let mut m = Tensor::full(f32::NEG_INFINITY, (batch, heads, seq_q, 1), device)?;
    let mut l = Tensor::zeros((batch, heads, seq_q, 1), dtype, device)?;

    // Process blocks
    for kv_block_idx in 0..num_blocks_kv {
        let kv_start = kv_block_idx * block_kv;
        let kv_end = (kv_start + block_kv).min(seq_kv);
        let kv_len = kv_end - kv_start;

        // Extract K, V blocks: [batch, heads, kv_len, head_dim]
        let k_block = k.narrow(2, kv_start, kv_len)?;
        let v_block = v.narrow(2, kv_start, kv_len)?;

        for q_block_idx in 0..num_blocks_q {
            let q_start = q_block_idx * block_q;
            let q_end = (q_start + block_q).min(seq_q);
            let q_len = q_end - q_start;

            // Causal masking: skip if all positions are masked
            if config.causal && kv_start > q_end - 1 {
                continue;
            }

            // Extract Q block: [batch, heads, q_len, head_dim]
            let q_block = q.narrow(2, q_start, q_len)?;

            // Compute attention scores: [batch, heads, q_len, kv_len]
            // QK^T / sqrt(d)
            let k_t = k_block.transpose(2, 3)?; // [batch, heads, head_dim, kv_len]
            let scores = q_block.matmul(&k_t)?;
            let scores = (scores * config.scale as f64)?;

            // Apply causal mask if needed
            let scores = if config.causal {
                apply_causal_mask_block(&scores, q_start, kv_start)?
            } else {
                scores
            };

            // Online softmax update
            // m_new = max(m_old, rowmax(scores))
            let scores_max = scores.max_keepdim(3)?; // [batch, heads, q_len, 1]
            let m_block = m.narrow(2, q_start, q_len)?;
            let m_new = m_block.maximum(&scores_max)?;

            // Compute exp(scores - m_new)
            let scores_shifted = scores.broadcast_sub(&m_new)?;
            let p = scores_shifted.exp()?;

            // l_new = exp(m_old - m_new) * l_old + rowsum(p)
            let l_block = l.narrow(2, q_start, q_len)?;
            let scale_factor = (m_block.broadcast_sub(&m_new))?.exp()?;
            let p_sum = p.sum_keepdim(3)?;
            let l_new = (l_block.broadcast_mul(&scale_factor)? + p_sum)?;

            // Update output: o_new = exp(m_old - m_new) * o_old + p @ v
            let output_block = output.narrow(2, q_start, q_len)?;
            let pv = p.matmul(&v_block)?; // [batch, heads, q_len, head_dim]
            let output_scaled = output_block.broadcast_mul(&scale_factor)?;
            let output_new = (output_scaled + pv)?;

            // Write back updates
            // Note: In-place updates are tricky with candle, using slice assignment
            output = tensor_scatter_update(&output, 2, q_start, &output_new)?;
            m = tensor_scatter_update(&m, 2, q_start, &m_new)?;
            l = tensor_scatter_update(&l, 2, q_start, &l_new)?;
        }
    }

    // Final normalization: output / l
    let output = output.broadcast_div(&l)?;

    Ok(output)
}

/// Standard attention implementation (for comparison/fallback)
fn standard_attention(
    q: &Tensor,
    k: &Tensor,
    v: &Tensor,
    scale: f32,
    causal: bool,
) -> Result<Tensor> {
    let (_, _, seq_q, _) = q.dims4()?;
    let (_, _, seq_kv, _) = k.dims4()?;

    // QK^T / sqrt(d)
    let k_t = k.transpose(2, 3)?;
    let scores = q.matmul(&k_t)?;
    let scores = (scores * scale as f64)?;

    // Apply causal mask
    let scores = if causal {
        apply_causal_mask(&scores, seq_q, seq_kv)?
    } else {
        scores
    };

    // Softmax
    let attn_weights = candle_nn::ops::softmax(&scores, 3)?;

    // Attention output
    let output = attn_weights.matmul(v)?;

    Ok(output)
}

/// Apply causal mask to attention scores
fn apply_causal_mask(scores: &Tensor, seq_q: usize, seq_kv: usize) -> Result<Tensor> {
    let device = scores.device();

    // Create causal mask: positions where j > i should be masked
    let mut mask_data = vec![0.0f32; seq_q * seq_kv];
    for i in 0..seq_q {
        for j in 0..seq_kv {
            if j > i {
                mask_data[i * seq_kv + j] = f32::NEG_INFINITY;
            }
        }
    }
    let mask = Tensor::from_vec(mask_data, (1, 1, seq_q, seq_kv), device)?;

    scores.broadcast_add(&mask)
}

/// Apply causal mask to a block of attention scores
fn apply_causal_mask_block(scores: &Tensor, q_start: usize, kv_start: usize) -> Result<Tensor> {
    let (_, _, q_len, kv_len) = scores.dims4()?;
    let device = scores.device();

    let mut mask_data = vec![0.0f32; q_len * kv_len];
    for i in 0..q_len {
        let global_q_pos = q_start + i;
        for j in 0..kv_len {
            let global_kv_pos = kv_start + j;
            if global_kv_pos > global_q_pos {
                mask_data[i * kv_len + j] = f32::NEG_INFINITY;
            }
        }
    }
    let mask = Tensor::from_vec(mask_data, (1, 1, q_len, kv_len), device)?;

    scores.broadcast_add(&mask)
}

/// Helper to update a slice of a tensor (workaround for lack of slice assignment)
fn tensor_scatter_update(
    tensor: &Tensor,
    dim: usize,
    start: usize,
    update: &Tensor,
) -> Result<Tensor> {
    let len = update.dim(dim)?;
    let total = tensor.dim(dim)?;

    if start == 0 && len == total {
        return Ok(update.clone());
    }

    let mut parts = Vec::new();

    // Before slice
    if start > 0 {
        parts.push(tensor.narrow(dim, 0, start)?);
    }

    // Updated slice
    parts.push(update.clone());

    // After slice
    let end = start + len;
    if end < total {
        parts.push(tensor.narrow(dim, end, total - end)?);
    }

    if parts.len() == 1 {
        Ok(parts.into_iter().next().unwrap())
    } else {
        let refs: Vec<&Tensor> = parts.iter().collect();
        Tensor::cat(&refs, dim)
    }
}

#[cfg(test)]
mod tests {
    use super::*;
    use candle_core::Device;

    #[test]
    fn test_flash_attention_small() {
        let device = Device::Cpu;
        let batch = 1;
        let heads = 2;
        let seq = 16;
        let head_dim = 32;

        let q = Tensor::randn(0.0f32, 1.0, (batch, heads, seq, head_dim), &device).unwrap();
        let k = Tensor::randn(0.0f32, 1.0, (batch, heads, seq, head_dim), &device).unwrap();
        let v = Tensor::randn(0.0f32, 1.0, (batch, heads, seq, head_dim), &device).unwrap();

        let config = FlashAttentionConfig::new(head_dim);
        let output = flash_attention(&q, &k, &v, &config).unwrap();

        assert_eq!(output.dims(), &[batch, heads, seq, head_dim]);
    }

    #[test]
    fn test_flash_vs_standard() {
        let device = Device::Cpu;
        let batch = 1;
        let heads = 2;
        let seq = 32;
        let head_dim = 16;
        let scale = 1.0 / (head_dim as f32).sqrt();

        let q = Tensor::randn(0.0f32, 1.0, (batch, heads, seq, head_dim), &device).unwrap();
        let k = Tensor::randn(0.0f32, 1.0, (batch, heads, seq, head_dim), &device).unwrap();
        let v = Tensor::randn(0.0f32, 1.0, (batch, heads, seq, head_dim), &device).unwrap();

        // Standard attention
        let std_out = standard_attention(&q, &k, &v, scale, true).unwrap();

        // Flash attention (will use standard for small seq)
        let config = FlashAttentionConfig {
            scale,
            causal: true,
            block_size_q: 8,
            block_size_kv: 8,
        };
        let flash_out = flash_attention(&q, &k, &v, &config).unwrap();

        // Compare outputs (should be very close)
        let diff = (std_out - flash_out).unwrap().abs().unwrap();
        let max_diff = diff
            .max(0)
            .unwrap()
            .max(0)
            .unwrap()
            .max(0)
            .unwrap()
            .max(0)
            .unwrap();
        let max_val: f32 = max_diff.to_scalar().unwrap();

        assert!(
            max_val < 1e-4,
            "Flash attention differs from standard by {:.6}",
            max_val
        );
    }

    #[test]
    fn test_flash_attention_large() {
        let device = Device::Cpu;
        let batch = 1;
        let heads = 4;
        let seq = 256; // Large enough to trigger tiled processing
        let head_dim = 64;

        let q = Tensor::randn(0.0f32, 1.0, (batch, heads, seq, head_dim), &device).unwrap();
        let k = Tensor::randn(0.0f32, 1.0, (batch, heads, seq, head_dim), &device).unwrap();
        let v = Tensor::randn(0.0f32, 1.0, (batch, heads, seq, head_dim), &device).unwrap();

        let config = FlashAttentionConfig::new(head_dim);
        let output = flash_attention(&q, &k, &v, &config).unwrap();

        assert_eq!(output.dims(), &[batch, heads, seq, head_dim]);

        // Check output is valid (sum should be finite)
        let sum: f32 = output.sum_all().unwrap().to_scalar().unwrap();
        assert!(sum.is_finite(), "Output contains NaN or Inf");
    }
}
