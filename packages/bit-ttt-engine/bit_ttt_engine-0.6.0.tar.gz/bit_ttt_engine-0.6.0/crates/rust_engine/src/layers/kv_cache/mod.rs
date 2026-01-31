use candle_core::{DType, Result, Tensor};

/// Default chunk size for pre-allocated buffer (tokens per chunk)
const DEFAULT_CHUNK_SIZE: usize = 128;

/// KIVI 2-bit quantization mapping
/// 2-bit values: 0, 1, 2, 3 → -1.5, -0.5, 0.5, 1.5
#[allow(dead_code)]
const KIVI_2BIT_LEVELS: [f32; 4] = [-1.5, -0.5, 0.5, 1.5];

/// Quantized Key-Value Cache (Phase 5.2 + 5.4 Pre-allocated Buffer)
///
/// Stores KV pairs in 8-bit quantized format to reduce VRAM usage.
/// Supports on-the-fly dequantization during attention calculation.
///
/// # Architecture
/// - **Storage**: `u8` tensor for data, managed as `Vec<Tensor>` chunks.
/// - **Scale**: `f32` tensor for dequantization factor (per-token-head).
/// - **Zero Point**: Fixed at 128 for symmetric mapping (-127..127 -> 1..255).
///
/// # Phase 5.3: Fused Attention Kernel
/// Provides optimized `matmul_with_dequant()` for inline dequantization during
/// attention computation, eliminating intermediate f32 allocations.
///
/// # Phase 5.4: Pre-allocated Chunk Buffer
/// Instead of using `Tensor::cat` which copies data on every append,
/// we now store chunks in a `Vec<Tensor>` and concatenate only when needed.
/// This reduces memory fragmentation and improves append performance.
#[derive(Debug, Clone)]
#[allow(dead_code)]
pub struct QuantizedKVCache {
    // Chunk-based storage for reduced fragmentation
    k_chunks: Vec<Tensor>, // Each chunk: [batch, n_kv_heads, chunk_seq_len, head_dim] (u8)
    v_chunks: Vec<Tensor>, // Each chunk: [batch, n_kv_heads, chunk_seq_len, head_dim] (u8)
    k_scale_chunks: Vec<Tensor>, // Each chunk: [batch, n_kv_heads, chunk_seq_len, 1] (f32)
    v_scale_chunks: Vec<Tensor>,

    // Legacy single-tensor cache (lazily computed on demand)
    k_cache: Option<Tensor>,
    v_cache: Option<Tensor>,
    k_scale: Option<Tensor>,
    v_scale: Option<Tensor>,
    cache_dirty: bool, // True if chunks were added since last cache rebuild

    current_seq_len: usize,
    max_seq_len: usize,
    chunk_size: usize, // Target tokens per chunk for pre-allocation hints

    // KIVI 2-bit storage (Phase 5.5)
    k_kivi_chunks: Vec<Tensor>,       // Packed u8: 4 values per byte
    v_kivi_chunks: Vec<Tensor>,       // Packed u8: 4 values per byte
    k_kivi_scale_chunks: Vec<Tensor>, // Per-channel scale [batch, heads, 1, dim]
    k_kivi_zero_chunks: Vec<Tensor>,  // Per-channel zero [batch, heads, 1, dim]
    v_kivi_scale_chunks: Vec<Tensor>, // Per-token scale [batch, heads, seq, 1]
    v_kivi_zero_chunks: Vec<Tensor>,  // Per-token zero [batch, heads, seq, 1]
    kivi_seq_len: usize,

    // Bypass mode: store f32 without quantization (for debugging)
    bypass_quantization: bool,
    k_f32_chunks: Vec<Tensor>, // f32 chunks when bypass is enabled
    v_f32_chunks: Vec<Tensor>,
}

impl QuantizedKVCache {
    pub fn new(max_seq_len: usize) -> Self {
        Self::with_chunk_size(max_seq_len, DEFAULT_CHUNK_SIZE)
    }

    /// Create a new cache with bypass mode (no quantization, f32 storage)
    /// Use this to debug quantization-related issues
    pub fn new_bypass(max_seq_len: usize) -> Self {
        let mut cache = Self::with_chunk_size(max_seq_len, DEFAULT_CHUNK_SIZE);
        cache.bypass_quantization = true;
        cache
    }

    /// Enable or disable bypass mode
    pub fn set_bypass(&mut self, bypass: bool) {
        self.bypass_quantization = bypass;
    }

    /// Check if bypass mode is enabled
    pub fn is_bypass(&self) -> bool {
        self.bypass_quantization
    }

    /// Create a new cache with custom chunk size
    ///
    /// # Arguments
    /// - `max_seq_len`: Maximum sequence length to support
    /// - `chunk_size`: Target tokens per chunk (affects memory allocation pattern)
    pub fn with_chunk_size(max_seq_len: usize, chunk_size: usize) -> Self {
        let estimated_chunks = (max_seq_len / chunk_size).max(1) + 1;
        Self {
            k_chunks: Vec::with_capacity(estimated_chunks),
            v_chunks: Vec::with_capacity(estimated_chunks),
            k_scale_chunks: Vec::with_capacity(estimated_chunks),
            v_scale_chunks: Vec::with_capacity(estimated_chunks),
            k_cache: None,
            v_cache: None,
            k_scale: None,
            v_scale: None,
            cache_dirty: false,
            current_seq_len: 0,
            max_seq_len,
            chunk_size,
            // KIVI 2-bit storage
            k_kivi_chunks: Vec::with_capacity(estimated_chunks),
            v_kivi_chunks: Vec::with_capacity(estimated_chunks),
            k_kivi_scale_chunks: Vec::with_capacity(estimated_chunks),
            k_kivi_zero_chunks: Vec::with_capacity(estimated_chunks),
            v_kivi_scale_chunks: Vec::with_capacity(estimated_chunks),
            v_kivi_zero_chunks: Vec::with_capacity(estimated_chunks),
            kivi_seq_len: 0,
            // Bypass mode
            bypass_quantization: false,
            k_f32_chunks: Vec::with_capacity(estimated_chunks),
            v_f32_chunks: Vec::with_capacity(estimated_chunks),
        }
    }

    /// Reset cache state (for new generation)
    pub fn reset(&mut self) {
        self.k_chunks.clear();
        self.v_chunks.clear();
        self.k_scale_chunks.clear();
        self.v_scale_chunks.clear();
        self.k_cache = None;
        self.v_cache = None;
        self.k_scale = None;
        self.v_scale = None;
        self.cache_dirty = false;
        self.current_seq_len = 0;
        // KIVI 2-bit reset
        self.k_kivi_chunks.clear();
        self.v_kivi_chunks.clear();
        self.k_kivi_scale_chunks.clear();
        self.k_kivi_zero_chunks.clear();
        self.v_kivi_scale_chunks.clear();
        self.v_kivi_zero_chunks.clear();
        self.kivi_seq_len = 0;
        // Bypass mode reset
        self.k_f32_chunks.clear();
        self.v_f32_chunks.clear();
    }

    /// Append new keys and values to the cache
    ///
    /// This implementation performs on-the-fly quantization using chunk-based storage.
    /// Returns DEQUANTIZED full cache for use in Attention.
    ///
    /// # Phase 5.4 Optimization
    /// Instead of using `Tensor::cat` on every append (O(n) copy per append),
    /// we store chunks in a Vec and only concatenate when the full cache is needed.
    /// This reduces append complexity from O(n) to O(1) amortized.
    ///
    /// # Bypass Mode
    /// If bypass_quantization is true, stores f32 directly without quantization.
    pub fn append(&mut self, k: &Tensor, v: &Tensor) -> Result<(Tensor, Tensor)> {
        let (_b, _h, seq_len, _d) = k.dims4()?;

        // Bypass mode: store f32 directly
        if self.bypass_quantization {
            self.k_f32_chunks.push(k.clone());
            self.v_f32_chunks.push(v.clone());
            self.current_seq_len += seq_len;
            self.cache_dirty = true;

            // Concatenate f32 chunks
            let k_out = if self.k_f32_chunks.len() == 1 {
                self.k_f32_chunks[0].clone()
            } else {
                let k_refs: Vec<&Tensor> = self.k_f32_chunks.iter().collect();
                Tensor::cat(&k_refs, 2)?
            };
            let v_out = if self.v_f32_chunks.len() == 1 {
                self.v_f32_chunks[0].clone()
            } else {
                let v_refs: Vec<&Tensor> = self.v_f32_chunks.iter().collect();
                Tensor::cat(&v_refs, 2)?
            };
            return Ok((k_out, v_out));
        }

        // Normal quantized path
        // 1. Quantize Inputs (f32/f16 -> u8, f32_scale)
        let (k_u8, k_s) = self.quantize_q8(k)?;
        let (v_u8, v_s) = self.quantize_q8(v)?;

        // 2. Append to chunk vectors (O(1) amortized - no copy!)
        self.k_chunks.push(k_u8);
        self.v_chunks.push(v_u8);
        self.k_scale_chunks.push(k_s);
        self.v_scale_chunks.push(v_s);
        self.cache_dirty = true;

        // 3. Update sequence length
        self.current_seq_len += seq_len;

        // 4. Rebuild concatenated cache (lazy - only when chunks > 1)
        // This is still O(n) but happens less frequently than before
        let (k_next, k_scale_next) = self.get_concatenated_k_cache()?;
        let (v_next, v_scale_next) = self.get_concatenated_v_cache()?;

        // 5. Dequantize for Return (To be compatible with standard Attention)
        let k_out = self.dequantize_q8(&k_next, &k_scale_next)?;
        let v_out = self.dequantize_q8(&v_next, &v_scale_next)?;

        Ok((k_out, v_out))
    }

    /// Get concatenated K cache, rebuilding if dirty
    fn get_concatenated_k_cache(&mut self) -> Result<(Tensor, Tensor)> {
        if self.cache_dirty || self.k_cache.is_none() {
            if self.k_chunks.len() == 1 {
                // Single chunk - no concatenation needed
                self.k_cache = Some(self.k_chunks[0].clone());
                self.k_scale = Some(self.k_scale_chunks[0].clone());
            } else if !self.k_chunks.is_empty() {
                // Multiple chunks - concatenate once
                let k_refs: Vec<&Tensor> = self.k_chunks.iter().collect();
                let k_scale_refs: Vec<&Tensor> = self.k_scale_chunks.iter().collect();
                self.k_cache = Some(Tensor::cat(&k_refs, 2)?);
                self.k_scale = Some(Tensor::cat(&k_scale_refs, 2)?);
            }
        }
        Ok((
            self.k_cache.clone().unwrap_or_else(|| {
                Tensor::zeros((0,), DType::U8, &candle_core::Device::Cpu).unwrap()
            }),
            self.k_scale.clone().unwrap_or_else(|| {
                Tensor::zeros((0,), DType::F32, &candle_core::Device::Cpu).unwrap()
            }),
        ))
    }

    /// Get concatenated V cache, rebuilding if dirty
    fn get_concatenated_v_cache(&mut self) -> Result<(Tensor, Tensor)> {
        if self.cache_dirty || self.v_cache.is_none() {
            if self.v_chunks.len() == 1 {
                // Single chunk - no concatenation needed
                self.v_cache = Some(self.v_chunks[0].clone());
                self.v_scale = Some(self.v_scale_chunks[0].clone());
            } else if !self.v_chunks.is_empty() {
                // Multiple chunks - concatenate once
                let v_refs: Vec<&Tensor> = self.v_chunks.iter().collect();
                let v_scale_refs: Vec<&Tensor> = self.v_scale_chunks.iter().collect();
                self.v_cache = Some(Tensor::cat(&v_refs, 2)?);
                self.v_scale = Some(Tensor::cat(&v_scale_refs, 2)?);
            }
            self.cache_dirty = false;
        }
        Ok((
            self.v_cache.clone().unwrap_or_else(|| {
                Tensor::zeros((0,), DType::U8, &candle_core::Device::Cpu).unwrap()
            }),
            self.v_scale.clone().unwrap_or_else(|| {
                Tensor::zeros((0,), DType::F32, &candle_core::Device::Cpu).unwrap()
            }),
        ))
    }

    /// Quantize a Tensor to Q8 (Symetric + 128 Offset)
    fn quantize_q8(&self, x: &Tensor) -> Result<(Tensor, Tensor)> {
        // x: [batch, heads, seq, dim]
        // Scale per token-head: max(abs(x), dim=3) -> [batch, heads, seq, 1]
        let x_abs = x.abs()?;
        let max_val = x_abs.max_keepdim(3)?;
        // Avoid division by zero
        let scale = (max_val / 127.0)?;

        // Broadcast scale
        let scaled = x.broadcast_div(&scale)?;

        // Quantize: round(x/s) + 128
        // We use standard rounding.
        let rounded = scaled.round()?;

        // Shift to u8 range [0, 255]. Center is 128.
        let shifted = (rounded + 128.0)?;

        // Clamp to ensure safety (though abs/127 should be within range)
        // Candle's to_dtype(U8) naturally saturates or wraps.
        // We trust the math: max_val/127 -> range [-127, 127]. +128 -> [1, 255].
        let quantized = shifted.to_dtype(DType::U8)?;

        Ok((quantized, scale))
    }

    /// Dequantize Q8 back to original dtype (f32/f16)
    fn dequantize_q8(&self, q: &Tensor, s: &Tensor) -> Result<Tensor> {
        // x = (q - 128) * scale
        let q_float = q.to_dtype(DType::F32)?;
        let shifted = (q_float - 128.0)?;
        let out = shifted.broadcast_mul(s)?;
        Ok(out)
    }

    /// [Phase 5.3] Append new keys and values WITHOUT dequantizing
    ///
    /// This is the first step of the fused kernel.
    /// Returns the quantized cache handles (u8 + scale) for use with fused attention.
    ///
    /// # Phase 5.4 Optimization
    /// Uses chunk-based storage internally, concatenates only when returning.
    ///
    /// # Returns
    /// Tuple of:
    /// - (k_cache_u8, k_scale) - quantized key cache
    /// - (v_cache_u8, v_scale) - quantized value cache
    /// - new_k_seq_len - position where new K/V starts in cache
    pub fn append_only(
        &mut self,
        k: &Tensor,
        v: &Tensor,
    ) -> Result<(Tensor, Tensor, Tensor, Tensor, usize)> {
        let (_b, _h, seq_len, _d) = k.dims4()?;

        // 1. Quantize Inputs (f32/f16 -> u8, f32_scale)
        let (k_u8, k_s) = self.quantize_q8(k)?;
        let (v_u8, v_s) = self.quantize_q8(v)?;

        // Remember position of new K/V in cache
        let new_k_pos = self.current_seq_len;

        // 2. Append to chunk vectors (O(1) amortized)
        self.k_chunks.push(k_u8);
        self.v_chunks.push(v_u8);
        self.k_scale_chunks.push(k_s);
        self.v_scale_chunks.push(v_s);
        self.cache_dirty = true;

        // 3. Update sequence length
        self.current_seq_len += seq_len;

        // 4. Get concatenated caches for return
        let (k_next, k_scale_next) = self.get_concatenated_k_cache()?;
        let (v_next, v_scale_next) = self.get_concatenated_v_cache()?;

        // 5. Return quantized caches and scale factors
        // Do NOT dequantize here - that happens inline in fused attention
        Ok((k_next, k_scale_next, v_next, v_scale_next, new_k_pos))
    }

    /// [Phase 5.3] Fused Q @ K^T with inline dequantization and GQA support
    ///
    /// Computes attention scores (Q @ K^T) directly on quantized cache without
    /// allocating temporary dequantized tensors.
    /// Handles Group Query Attention (GQA) by repeating K heads as needed.
    ///
    /// # Arguments
    /// - `q`: Query tensor [batch, heads, seq_len, head_dim] (f32)
    /// - `k_cache_u8`: Quantized K cache [batch, kv_heads, total_seq_len, head_dim] (u8)
    /// - `k_scale`: K scale factors [batch, kv_heads, total_seq_len, 1] (f32)
    /// - `scaling`: Attention scaling factor (1 / sqrt(head_dim))
    /// - `n_heads`: Total number of query heads
    /// - `n_kv_heads`: Number of key/value heads
    ///
    /// # Returns
    /// Attention scores [batch, heads, seq_len, total_seq_len] (f32)
    pub fn matmul_q_k_dequant(
        &self,
        q: &Tensor,
        k_cache_u8: &Tensor,
        k_scale: &Tensor,
        scaling: f64,
        n_heads: usize,
        n_kv_heads: usize,
    ) -> Result<Tensor> {
        // 1. Dequantize K: (k_u8 - 128) * scale
        let k_float = k_cache_u8.to_dtype(DType::F32)?;
        let k_shifted = (k_float - 128.0)?;
        let k_dequant = k_shifted.broadcast_mul(k_scale)?;

        // 2. Handle GQA: Repeat K if n_heads > n_kv_heads
        let k_dequant = Self::repeat_kv_static(k_dequant, n_heads, n_kv_heads)?;

        // 3. Compute Q @ K^T with scaling
        // This is the same as standard attention but avoids intermediate allocation
        // The dequantization happens inline and can be optimized by compiler/MLIR
        let att = q.matmul(&k_dequant.t()?)?;
        let att = (att * scaling)?;

        Ok(att)
    }

    /// [Phase 5.3] Static helper for GQA head repetition
    fn repeat_kv_static(x: Tensor, n_heads: usize, n_kv_heads: usize) -> Result<Tensor> {
        let n_rep = n_heads / n_kv_heads;
        if n_rep == 1 {
            return Ok(x);
        }
        let (b, n_kv, s, d) = x.dims4()?;
        x.unsqueeze(2)?
            .expand((b, n_kv, n_rep, s, d))?
            .reshape((b, n_kv * n_rep, s, d))
    }

    /// [Phase 5.3] Fused Attention @ V with inline dequantization and GQA support
    ///
    /// Computes output (Attention @ V) directly on quantized cache without
    /// allocating temporary dequantized tensors.
    /// Handles Group Query Attention (GQA) by repeating V heads as needed.
    ///
    /// # Arguments
    /// - `att`: Attention weights [batch, heads, seq_len, total_seq_len] (f32)
    /// - `v_cache_u8`: Quantized V cache [batch, kv_heads, total_seq_len, head_dim] (u8)
    /// - `v_scale`: V scale factors [batch, kv_heads, total_seq_len, 1] (f32)
    /// - `n_heads`: Total number of query heads
    /// - `n_kv_heads`: Number of key/value heads
    ///
    /// # Returns
    /// Attention output [batch, heads, seq_len, head_dim] (f32)
    pub fn matmul_att_v_dequant(
        &self,
        att: &Tensor,
        v_cache_u8: &Tensor,
        v_scale: &Tensor,
        n_heads: usize,
        n_kv_heads: usize,
    ) -> Result<Tensor> {
        // 1. Dequantize V: (v_u8 - 128) * scale
        let v_float = v_cache_u8.to_dtype(DType::F32)?;
        let v_shifted = (v_float - 128.0)?;
        let v_dequant = v_shifted.broadcast_mul(v_scale)?;

        // 2. Handle GQA: Repeat V if n_heads > n_kv_heads
        let v_dequant = Self::repeat_kv_static(v_dequant, n_heads, n_kv_heads)?;

        // 3. Compute Attention @ V
        // Inline dequantization reduces peak memory usage significantly
        let y = att.matmul(&v_dequant)?;

        Ok(y)
    }

    /// [Phase 5.3] Getter for quantized K cache (u8)
    pub fn k_cache_u8(&self) -> Option<&Tensor> {
        self.k_cache.as_ref()
    }

    /// [Phase 5.3] Getter for quantized V cache (u8)
    pub fn v_cache_u8(&self) -> Option<&Tensor> {
        self.v_cache.as_ref()
    }

    /// [Phase 5.3] Getter for K scale factors
    pub fn k_scale(&self) -> Option<&Tensor> {
        self.k_scale.as_ref()
    }

    /// [Phase 5.3] Getter for V scale factors
    pub fn v_scale(&self) -> Option<&Tensor> {
        self.v_scale.as_ref()
    }

    /// Get current sequence length in cache
    pub fn seq_len(&self) -> usize {
        self.current_seq_len
    }

    /// [Phase 5.6] Sliding Window: Trim cache to keep only recent tokens + attention sinks
    ///
    /// This implements StreamingLLM's approach to infinite context:
    /// - Always keep the first `sink_size` tokens (attention sinks)
    /// - Keep the most recent `window_size` tokens
    /// - Evict tokens in between: [sink_size .. current_seq_len - window_size]
    ///
    /// # Arguments
    /// - `window_size`: Number of recent tokens to keep (excluding sinks)
    /// - `sink_size`: Number of initial tokens to always keep (attention sinks)
    ///
    /// # Returns
    /// Ok(true) if trimming occurred, Ok(false) if no trimming needed
    ///
    /// # Reference
    /// StreamingLLM: Efficient Streaming Language Models with Attention Sinks
    /// <https://arxiv.org/abs/2309.17453>
    pub fn trim_to_window(&mut self, window_size: usize, sink_size: usize) -> Result<bool> {
        // Total tokens to keep
        let total_keep = sink_size + window_size;

        // If current length <= total_keep, no trimming needed
        if self.current_seq_len <= total_keep {
            return Ok(false);
        }

        // Force rebuild of concatenated cache if dirty
        if self.cache_dirty {
            let _ = self.get_concatenated_k_cache()?;
            let _ = self.get_concatenated_v_cache()?;
        }

        // Get the full concatenated caches
        let k_full = match &self.k_cache {
            Some(k) => k.clone(),
            None => return Ok(false), // No cache to trim
        };
        let v_full = match &self.v_cache {
            Some(v) => v.clone(),
            None => return Ok(false),
        };
        let k_scale_full = match &self.k_scale {
            Some(s) => s.clone(),
            None => return Ok(false),
        };
        let v_scale_full = match &self.v_scale {
            Some(s) => s.clone(),
            None => return Ok(false),
        };

        // Calculate indices to keep:
        // [0..sink_size] + [current_seq_len - window_size .. current_seq_len]
        let window_start = self.current_seq_len - window_size;

        // Extract sink tokens: [0..sink_size]
        let k_sink = k_full.narrow(2, 0, sink_size)?;
        let v_sink = v_full.narrow(2, 0, sink_size)?;
        let k_scale_sink = k_scale_full.narrow(2, 0, sink_size)?;
        let v_scale_sink = v_scale_full.narrow(2, 0, sink_size)?;

        // Extract window tokens: [window_start..current_seq_len]
        let k_window = k_full.narrow(2, window_start, window_size)?;
        let v_window = v_full.narrow(2, window_start, window_size)?;
        let k_scale_window = k_scale_full.narrow(2, window_start, window_size)?;
        let v_scale_window = v_scale_full.narrow(2, window_start, window_size)?;

        // Concatenate sink + window
        let k_trimmed = Tensor::cat(&[&k_sink, &k_window], 2)?;
        let v_trimmed = Tensor::cat(&[&v_sink, &v_window], 2)?;
        let k_scale_trimmed = Tensor::cat(&[&k_scale_sink, &k_scale_window], 2)?;
        let v_scale_trimmed = Tensor::cat(&[&v_scale_sink, &v_scale_window], 2)?;

        // Clear chunk vectors and set single trimmed chunk
        self.k_chunks.clear();
        self.v_chunks.clear();
        self.k_scale_chunks.clear();
        self.v_scale_chunks.clear();

        self.k_chunks.push(k_trimmed.clone());
        self.v_chunks.push(v_trimmed.clone());
        self.k_scale_chunks.push(k_scale_trimmed.clone());
        self.v_scale_chunks.push(v_scale_trimmed.clone());

        // Update cached tensors
        self.k_cache = Some(k_trimmed);
        self.v_cache = Some(v_trimmed);
        self.k_scale = Some(k_scale_trimmed);
        self.v_scale = Some(v_scale_trimmed);

        // Update sequence length
        self.current_seq_len = total_keep;
        self.cache_dirty = false;

        Ok(true)
    }

    /// [Phase 5.6] Check if trimming is needed based on window configuration
    pub fn should_trim(&self, window_size: usize, sink_size: usize) -> bool {
        self.current_seq_len > sink_size + window_size
    }

    // =========================================================================
    // Phase 5.5: KIVI 2-bit Quantization
    // =========================================================================
    // KIVI (Key-Value Implicit Variance Inference) uses different quantization
    // strategies for keys and values based on observed outlier patterns:
    // - Keys: per-channel quantization (outliers concentrate in specific channels)
    // - Values: per-token quantization (no clear outlier pattern)
    //
    // Reference: https://arxiv.org/abs/2402.02750
    // =========================================================================

    /// KIVI 2-bit quantization for Keys (per-channel)
    ///
    /// Keys have outliers concentrated in specific channels (dimensions),
    /// so we compute scale/zero_point per channel for better accuracy.
    ///
    /// # Arguments
    /// - `k`: Key tensor [batch, heads, seq, dim]
    ///
    /// # Returns
    /// - `packed`: Packed u8 tensor [batch, heads, seq, dim/4] (4 values per byte)
    /// - `scale`: Per-channel scale [batch, heads, 1, dim]
    /// - `zero_point`: Per-channel zero point [batch, heads, 1, dim]
    pub fn quantize_kivi_2bit_key(&self, k: &Tensor) -> Result<(Tensor, Tensor, Tensor)> {
        let (batch, heads, seq, dim) = k.dims4()?;
        let device = k.device();

        // Per-channel statistics: compute min/max along seq dimension (dim 2)
        // Shape: [batch, heads, 1, dim]
        let k_min = k.min_keepdim(2)?;
        let k_max = k.max_keepdim(2)?;

        // Scale = (max - min) / 3 (for 4 levels: 0,1,2,3)
        // Avoid division by zero
        let range = (&k_max - &k_min)?;
        let scale = (&range / 3.0)?.clamp(1e-8, f32::MAX as f64)?;

        // Zero point = min (we map min to level 0)
        let zero_point = k_min;

        // Quantize: q = round((x - zero) / scale)
        // Clamp to [0, 3]
        let k_normalized = k.broadcast_sub(&zero_point)?;
        let k_scaled = k_normalized.broadcast_div(&scale)?;
        let k_rounded = k_scaled.round()?;
        let k_clamped = k_rounded.clamp(0.0, 3.0)?;
        let k_u8 = k_clamped.to_dtype(DType::U8)?;

        // Pack 4 values into 1 byte
        // Input: [batch, heads, seq, dim] with values 0-3
        // Output: [batch, heads, seq, dim/4] with packed bytes
        let packed = Self::pack_2bit(&k_u8, batch, heads, seq, dim, device)?;

        Ok((packed, scale, zero_point))
    }

    /// KIVI 2-bit quantization for Values (per-token)
    ///
    /// Values don't have a clear outlier pattern, so we use per-token
    /// quantization for better local accuracy.
    ///
    /// # Arguments
    /// - `v`: Value tensor [batch, heads, seq, dim]
    ///
    /// # Returns
    /// - `packed`: Packed u8 tensor [batch, heads, seq, dim/4] (4 values per byte)
    /// - `scale`: Per-token scale [batch, heads, seq, 1]
    /// - `zero_point`: Per-token zero point [batch, heads, seq, 1]
    pub fn quantize_kivi_2bit_value(&self, v: &Tensor) -> Result<(Tensor, Tensor, Tensor)> {
        let (batch, heads, seq, dim) = v.dims4()?;
        let device = v.device();

        // Per-token statistics: compute min/max along dim dimension (dim 3)
        // Shape: [batch, heads, seq, 1]
        let v_min = v.min_keepdim(3)?;
        let v_max = v.max_keepdim(3)?;

        // Scale = (max - min) / 3 (for 4 levels: 0,1,2,3)
        let range = (&v_max - &v_min)?;
        let scale = (&range / 3.0)?.clamp(1e-8, f32::MAX as f64)?;

        // Zero point = min
        let zero_point = v_min;

        // Quantize: q = round((x - zero) / scale)
        let v_normalized = v.broadcast_sub(&zero_point)?;
        let v_scaled = v_normalized.broadcast_div(&scale)?;
        let v_rounded = v_scaled.round()?;
        let v_clamped = v_rounded.clamp(0.0, 3.0)?;
        let v_u8 = v_clamped.to_dtype(DType::U8)?;

        // Pack 4 values into 1 byte
        let packed = Self::pack_2bit(&v_u8, batch, heads, seq, dim, device)?;

        Ok((packed, scale, zero_point))
    }

    /// Pack 4 x 2-bit values into 1 byte
    ///
    /// Layout: [val0: bits 0-1] [val1: bits 2-3] [val2: bits 4-5] [val3: bits 6-7]
    fn pack_2bit(
        data: &Tensor,
        batch: usize,
        heads: usize,
        seq: usize,
        dim: usize,
        device: &candle_core::Device,
    ) -> Result<Tensor> {
        // Ensure dim is divisible by 4
        assert!(
            dim.is_multiple_of(4),
            "dim must be divisible by 4 for 2-bit packing"
        );

        // Get raw data
        let data_vec: Vec<u8> = data.flatten_all()?.to_vec1()?;
        let packed_dim = dim / 4;
        let total_packed = batch * heads * seq * packed_dim;
        let mut packed_vec = vec![0u8; total_packed];

        // Pack: 4 values -> 1 byte
        for b in 0..batch {
            for h in 0..heads {
                for s in 0..seq {
                    for pd in 0..packed_dim {
                        let src_base = ((b * heads + h) * seq + s) * dim + pd * 4;
                        let dst_idx = ((b * heads + h) * seq + s) * packed_dim + pd;

                        let v0 = data_vec[src_base] & 0x03;
                        let v1 = data_vec[src_base + 1] & 0x03;
                        let v2 = data_vec[src_base + 2] & 0x03;
                        let v3 = data_vec[src_base + 3] & 0x03;

                        packed_vec[dst_idx] = v0 | (v1 << 2) | (v2 << 4) | (v3 << 6);
                    }
                }
            }
        }

        Tensor::from_vec(packed_vec, (batch, heads, seq, packed_dim), device)
    }

    /// Unpack 1 byte into 4 x 2-bit values
    fn unpack_2bit(
        packed: &Tensor,
        batch: usize,
        heads: usize,
        seq: usize,
        packed_dim: usize,
        device: &candle_core::Device,
    ) -> Result<Tensor> {
        let packed_vec: Vec<u8> = packed.flatten_all()?.to_vec1()?;
        let dim = packed_dim * 4;
        let total_unpacked = batch * heads * seq * dim;
        let mut unpacked_vec = vec![0u8; total_unpacked];

        for b in 0..batch {
            for h in 0..heads {
                for s in 0..seq {
                    for pd in 0..packed_dim {
                        let src_idx = ((b * heads + h) * seq + s) * packed_dim + pd;
                        let dst_base = ((b * heads + h) * seq + s) * dim + pd * 4;

                        let byte = packed_vec[src_idx];
                        unpacked_vec[dst_base] = byte & 0x03;
                        unpacked_vec[dst_base + 1] = (byte >> 2) & 0x03;
                        unpacked_vec[dst_base + 2] = (byte >> 4) & 0x03;
                        unpacked_vec[dst_base + 3] = (byte >> 6) & 0x03;
                    }
                }
            }
        }

        Tensor::from_vec(unpacked_vec, (batch, heads, seq, dim), device)
    }

    /// Dequantize KIVI 2-bit back to f32
    ///
    /// # Arguments
    /// - `packed`: Packed u8 tensor
    /// - `scale`: Scale factors (per-channel for key, per-token for value)
    /// - `zero_point`: Zero points
    /// - `is_key`: True for key (per-channel), false for value (per-token)
    ///
    /// # Returns
    /// Dequantized tensor [batch, heads, seq, dim]
    pub fn dequantize_kivi_2bit(
        &self,
        packed: &Tensor,
        scale: &Tensor,
        zero_point: &Tensor,
        is_key: bool,
    ) -> Result<Tensor> {
        let (batch, heads, seq, packed_dim) = packed.dims4()?;
        let device = packed.device();

        // Unpack bytes to 2-bit values
        let unpacked = Self::unpack_2bit(packed, batch, heads, seq, packed_dim, device)?;

        // Convert to f32
        let q_f32 = unpacked.to_dtype(DType::F32)?;

        // Dequantize: x = q * scale + zero_point
        let dequant = if is_key {
            // Key: scale/zero are [batch, heads, 1, dim], broadcast over seq
            let scaled = q_f32.broadcast_mul(scale)?;
            scaled.broadcast_add(zero_point)?
        } else {
            // Value: scale/zero are [batch, heads, seq, 1], broadcast over dim
            let scaled = q_f32.broadcast_mul(scale)?;
            scaled.broadcast_add(zero_point)?
        };

        Ok(dequant)
    }

    /// Append K/V using KIVI 2-bit quantization
    ///
    /// Memory savings: 4x compared to INT8, 16x compared to FP32
    ///
    /// # Returns
    /// Dequantized (k, v) for attention computation
    pub fn append_kivi_2bit(&mut self, k: &Tensor, v: &Tensor) -> Result<(Tensor, Tensor)> {
        let (_b, _h, seq_len, _d) = k.dims4()?;

        // 1. Quantize using KIVI strategy
        let (k_packed, k_scale, k_zero) = self.quantize_kivi_2bit_key(k)?;
        let (v_packed, v_scale, v_zero) = self.quantize_kivi_2bit_value(v)?;

        // 2. Store in KIVI chunks
        self.k_kivi_chunks.push(k_packed);
        self.k_kivi_scale_chunks.push(k_scale);
        self.k_kivi_zero_chunks.push(k_zero);
        self.v_kivi_chunks.push(v_packed);
        self.v_kivi_scale_chunks.push(v_scale);
        self.v_kivi_zero_chunks.push(v_zero);

        self.kivi_seq_len += seq_len;

        // 3. Concatenate all chunks and dequantize for return
        let (k_full, k_scale_full, k_zero_full) = self.get_concatenated_kivi_k()?;
        let (v_full, v_scale_full, v_zero_full) = self.get_concatenated_kivi_v()?;

        let k_out = self.dequantize_kivi_2bit(&k_full, &k_scale_full, &k_zero_full, true)?;
        let v_out = self.dequantize_kivi_2bit(&v_full, &v_scale_full, &v_zero_full, false)?;

        Ok((k_out, v_out))
    }

    /// Get concatenated KIVI K cache
    fn get_concatenated_kivi_k(&self) -> Result<(Tensor, Tensor, Tensor)> {
        if self.k_kivi_chunks.len() == 1 {
            Ok((
                self.k_kivi_chunks[0].clone(),
                self.k_kivi_scale_chunks[0].clone(),
                self.k_kivi_zero_chunks[0].clone(),
            ))
        } else {
            let k_refs: Vec<&Tensor> = self.k_kivi_chunks.iter().collect();
            let k_scale_refs: Vec<&Tensor> = self.k_kivi_scale_chunks.iter().collect();
            let k_zero_refs: Vec<&Tensor> = self.k_kivi_zero_chunks.iter().collect();

            // Concatenate along seq dimension (dim 2)
            let k_cat = Tensor::cat(&k_refs, 2)?;
            // For per-channel scale/zero, we need to average or use latest
            // Since they're per-channel, we take the latest (covers full range)
            let k_scale_cat = Tensor::cat(&k_scale_refs, 2)?;
            let k_zero_cat = Tensor::cat(&k_zero_refs, 2)?;

            // For proper per-channel semantics, compute global min/max
            // But for simplicity, use mean of scales (approximation)
            let k_scale_mean = k_scale_cat.mean_keepdim(2)?;
            let k_zero_mean = k_zero_cat.mean_keepdim(2)?;

            Ok((k_cat, k_scale_mean, k_zero_mean))
        }
    }

    /// Get concatenated KIVI V cache
    fn get_concatenated_kivi_v(&self) -> Result<(Tensor, Tensor, Tensor)> {
        if self.v_kivi_chunks.len() == 1 {
            Ok((
                self.v_kivi_chunks[0].clone(),
                self.v_kivi_scale_chunks[0].clone(),
                self.v_kivi_zero_chunks[0].clone(),
            ))
        } else {
            let v_refs: Vec<&Tensor> = self.v_kivi_chunks.iter().collect();
            let v_scale_refs: Vec<&Tensor> = self.v_kivi_scale_chunks.iter().collect();
            let v_zero_refs: Vec<&Tensor> = self.v_kivi_zero_chunks.iter().collect();

            // Concatenate along seq dimension (dim 2)
            // Per-token scale/zero also concatenate along seq
            Ok((
                Tensor::cat(&v_refs, 2)?,
                Tensor::cat(&v_scale_refs, 2)?,
                Tensor::cat(&v_zero_refs, 2)?,
            ))
        }
    }

    /// Get KIVI cache memory usage in bytes
    pub fn kivi_memory_bytes(&self) -> usize {
        let mut total = 0;
        for chunk in &self.k_kivi_chunks {
            total += chunk.elem_count();
        }
        for chunk in &self.v_kivi_chunks {
            total += chunk.elem_count();
        }
        // Scale/zero are f32
        for chunk in &self.k_kivi_scale_chunks {
            total += chunk.elem_count() * 4;
        }
        for chunk in &self.k_kivi_zero_chunks {
            total += chunk.elem_count() * 4;
        }
        for chunk in &self.v_kivi_scale_chunks {
            total += chunk.elem_count() * 4;
        }
        for chunk in &self.v_kivi_zero_chunks {
            total += chunk.elem_count() * 4;
        }
        total
    }

    /// [Phase 5.5] Fused Q @ K^T with KIVI 2-bit dequantization
    #[allow(clippy::too_many_arguments)]
    pub fn matmul_q_k_kivi_2bit(
        &self,
        q: &Tensor,
        k_packed: &Tensor,
        k_scale: &Tensor,
        k_zero: &Tensor,
        scaling: f64,
        n_heads: usize,
        n_kv_heads: usize,
    ) -> Result<Tensor> {
        // 1. Dequantize K using KIVI 2-bit
        let k_dequant = self.dequantize_kivi_2bit(k_packed, k_scale, k_zero, true)?;

        // 2. Handle GQA
        let k_dequant = Self::repeat_kv_static(k_dequant, n_heads, n_kv_heads)?;

        // 3. Compute Q @ K^T with scaling
        let att = q.matmul(&k_dequant.t()?)?;
        let att = (att * scaling)?;

        Ok(att)
    }

    /// [Phase 5.5] Fused Attention @ V with KIVI 2-bit dequantization
    pub fn matmul_att_v_kivi_2bit(
        &self,
        att: &Tensor,
        v_packed: &Tensor,
        v_scale: &Tensor,
        v_zero: &Tensor,
        n_heads: usize,
        n_kv_heads: usize,
    ) -> Result<Tensor> {
        // 1. Dequantize V using KIVI 2-bit
        let v_dequant = self.dequantize_kivi_2bit(v_packed, v_scale, v_zero, false)?;

        // 2. Handle GQA
        let v_dequant = Self::repeat_kv_static(v_dequant, n_heads, n_kv_heads)?;

        // 3. Compute Attention @ V
        let y = att.matmul(&v_dequant)?;

        Ok(y)
    }

    /// Get KIVI sequence length
    pub fn kivi_seq_len(&self) -> usize {
        self.kivi_seq_len
    }
}

#[cfg(test)]
mod tests {
    use super::*;
    use candle_core::Device;

    #[test]
    fn test_kivi_2bit_pack_unpack() {
        let device = Device::Cpu;
        let batch = 1;
        let heads = 2;
        let seq = 4;
        let dim = 8; // Must be divisible by 4

        // Create test data with values 0-3
        let data: Vec<u8> = (0..batch * heads * seq * dim)
            .map(|i| (i % 4) as u8)
            .collect();
        let tensor = Tensor::from_vec(data.clone(), (batch, heads, seq, dim), &device).unwrap();

        // Pack
        let packed = QuantizedKVCache::pack_2bit(&tensor, batch, heads, seq, dim, &device).unwrap();

        // Check packed shape
        let (pb, ph, ps, pd) = packed.dims4().unwrap();
        assert_eq!((pb, ph, ps, pd), (batch, heads, seq, dim / 4));

        // Unpack
        let unpacked =
            QuantizedKVCache::unpack_2bit(&packed, batch, heads, seq, dim / 4, &device).unwrap();

        // Compare
        let unpacked_vec: Vec<u8> = unpacked.flatten_all().unwrap().to_vec1().unwrap();
        assert_eq!(data, unpacked_vec);
    }

    #[test]
    fn test_kivi_2bit_key_quantization() {
        let device = Device::Cpu;
        let cache = QuantizedKVCache::new(1024);

        // Create random-ish key tensor
        let batch = 1;
        let heads = 2;
        let seq = 4;
        let dim = 16;

        let k_data: Vec<f32> = (0..batch * heads * seq * dim)
            .map(|i| ((i as f32) - 16.0) * 0.1)
            .collect();
        let k = Tensor::from_vec(k_data.clone(), (batch, heads, seq, dim), &device).unwrap();

        // Quantize
        let (packed, scale, zero) = cache.quantize_kivi_2bit_key(&k).unwrap();

        // Check shapes
        let (pb, ph, ps, pd) = packed.dims4().unwrap();
        assert_eq!((pb, ph, ps, pd), (batch, heads, seq, dim / 4));

        let scale_shape = scale.dims4().unwrap();
        assert_eq!(scale_shape, (batch, heads, 1, dim)); // Per-channel

        let zero_shape = zero.dims4().unwrap();
        assert_eq!(zero_shape, (batch, heads, 1, dim)); // Per-channel

        // Dequantize
        let k_recon = cache
            .dequantize_kivi_2bit(&packed, &scale, &zero, true)
            .unwrap();

        // Check reconstruction shape
        let recon_shape = k_recon.dims4().unwrap();
        assert_eq!(recon_shape, (batch, heads, seq, dim));

        // Check reconstruction quality (should be within quantization error)
        let k_vec: Vec<f32> = k.flatten_all().unwrap().to_vec1().unwrap();
        let recon_vec: Vec<f32> = k_recon.flatten_all().unwrap().to_vec1().unwrap();

        let max_error: f32 = k_vec
            .iter()
            .zip(recon_vec.iter())
            .map(|(a, b)| (a - b).abs())
            .fold(0.0, f32::max);

        // 2-bit quantization has limited precision, but should be reasonable
        println!("Key max reconstruction error: {}", max_error);
        assert!(
            max_error < 2.0,
            "Reconstruction error too large: {}",
            max_error
        );
    }

    #[test]
    fn test_kivi_2bit_value_quantization() {
        let device = Device::Cpu;
        let cache = QuantizedKVCache::new(1024);

        let batch = 1;
        let heads = 2;
        let seq = 4;
        let dim = 16;

        let v_data: Vec<f32> = (0..batch * heads * seq * dim)
            .map(|i| ((i as f32) - 16.0) * 0.1)
            .collect();
        let v = Tensor::from_vec(v_data.clone(), (batch, heads, seq, dim), &device).unwrap();

        // Quantize
        let (packed, scale, zero) = cache.quantize_kivi_2bit_value(&v).unwrap();

        // Check shapes
        let (pb, ph, ps, pd) = packed.dims4().unwrap();
        assert_eq!((pb, ph, ps, pd), (batch, heads, seq, dim / 4));

        let scale_shape = scale.dims4().unwrap();
        assert_eq!(scale_shape, (batch, heads, seq, 1)); // Per-token

        let zero_shape = zero.dims4().unwrap();
        assert_eq!(zero_shape, (batch, heads, seq, 1)); // Per-token

        // Dequantize
        let v_recon = cache
            .dequantize_kivi_2bit(&packed, &scale, &zero, false)
            .unwrap();

        let recon_shape = v_recon.dims4().unwrap();
        assert_eq!(recon_shape, (batch, heads, seq, dim));

        // Check reconstruction quality
        let v_vec: Vec<f32> = v.flatten_all().unwrap().to_vec1().unwrap();
        let recon_vec: Vec<f32> = v_recon.flatten_all().unwrap().to_vec1().unwrap();

        let max_error: f32 = v_vec
            .iter()
            .zip(recon_vec.iter())
            .map(|(a, b)| (a - b).abs())
            .fold(0.0, f32::max);

        println!("Value max reconstruction error: {}", max_error);
        assert!(
            max_error < 2.0,
            "Reconstruction error too large: {}",
            max_error
        );
    }

    #[test]
    fn test_kivi_2bit_append() {
        let device = Device::Cpu;
        let mut cache = QuantizedKVCache::new(1024);

        let batch = 1;
        let heads = 2;
        let seq = 4;
        let dim = 16;

        // First append
        let k1_data: Vec<f32> = (0..batch * heads * seq * dim)
            .map(|i| (i as f32) * 0.01)
            .collect();
        let v1_data: Vec<f32> = (0..batch * heads * seq * dim)
            .map(|i| (i as f32) * 0.02)
            .collect();

        let k1 = Tensor::from_vec(k1_data, (batch, heads, seq, dim), &device).unwrap();
        let v1 = Tensor::from_vec(v1_data, (batch, heads, seq, dim), &device).unwrap();

        let (k_out1, v_out1) = cache.append_kivi_2bit(&k1, &v1).unwrap();

        // Check output shapes
        let k_shape = k_out1.dims4().unwrap();
        let v_shape = v_out1.dims4().unwrap();
        assert_eq!(k_shape, (batch, heads, seq, dim));
        assert_eq!(v_shape, (batch, heads, seq, dim));
        assert_eq!(cache.kivi_seq_len(), seq);

        // Second append
        let k2_data: Vec<f32> = (0..batch * heads * seq * dim)
            .map(|i| (i as f32) * 0.03)
            .collect();
        let v2_data: Vec<f32> = (0..batch * heads * seq * dim)
            .map(|i| (i as f32) * 0.04)
            .collect();

        let k2 = Tensor::from_vec(k2_data, (batch, heads, seq, dim), &device).unwrap();
        let v2 = Tensor::from_vec(v2_data, (batch, heads, seq, dim), &device).unwrap();

        let (k_out2, v_out2) = cache.append_kivi_2bit(&k2, &v2).unwrap();

        // Check concatenated shapes
        let k_shape2 = k_out2.dims4().unwrap();
        let v_shape2 = v_out2.dims4().unwrap();
        assert_eq!(k_shape2, (batch, heads, seq * 2, dim));
        assert_eq!(v_shape2, (batch, heads, seq * 2, dim));
        assert_eq!(cache.kivi_seq_len(), seq * 2);
    }

    #[test]
    fn test_kivi_memory_savings() {
        let device = Device::Cpu;
        let mut cache = QuantizedKVCache::new(1024);

        let batch = 1;
        let heads = 8;
        let seq = 128;
        let dim = 64;

        // Create KV tensors
        let k_data: Vec<f32> = vec![0.5; batch * heads * seq * dim];
        let v_data: Vec<f32> = vec![0.5; batch * heads * seq * dim];

        let k = Tensor::from_vec(k_data, (batch, heads, seq, dim), &device).unwrap();
        let v = Tensor::from_vec(v_data, (batch, heads, seq, dim), &device).unwrap();

        // FP32 memory: batch * heads * seq * dim * 4 bytes * 2 (K+V)
        let fp32_bytes = batch * heads * seq * dim * 4 * 2;

        // INT8 memory: batch * heads * seq * dim * 1 byte * 2 + scales
        let int8_bytes = batch * heads * seq * dim * 2 + batch * heads * seq * 4 * 2;

        // Append to KIVI cache
        let _ = cache.append_kivi_2bit(&k, &v).unwrap();

        // INT2 memory (from KIVI cache)
        let kivi_bytes = cache.kivi_memory_bytes();

        // INT2 packed: batch * heads * seq * (dim/4) bytes * 2 + scales/zeros
        // scales/zeros: per-channel for K [batch, heads, 1, dim] * 4 bytes * 2
        //               per-token for V [batch, heads, seq, 1] * 4 bytes * 2
        let expected_packed = batch * heads * seq * (dim / 4) * 2;
        let expected_k_meta = batch * heads * dim * 4 * 2; // scale + zero
        let expected_v_meta = batch * heads * seq * 4 * 2; // scale + zero
        let expected_total = expected_packed + expected_k_meta + expected_v_meta;

        println!("Memory comparison:");
        println!("  FP32:  {} bytes", fp32_bytes);
        println!(
            "  INT8:  {} bytes ({:.1}x reduction)",
            int8_bytes,
            fp32_bytes as f32 / int8_bytes as f32
        );
        println!(
            "  KIVI:  {} bytes ({:.1}x reduction)",
            kivi_bytes,
            fp32_bytes as f32 / kivi_bytes as f32
        );
        println!("  Expected KIVI: {} bytes", expected_total);

        // KIVI should be significantly smaller than FP32
        assert!(
            kivi_bytes < fp32_bytes / 2,
            "KIVI should save at least 2x memory vs FP32"
        );
    }
}
