//! Cache Engine - GPU Memory Management for Paged KV Cache
//!
//! Pre-allocates fixed-size blocks on GPU to avoid per-token memory allocation.

use candle_core::{DType, Device, Result, Tensor};
use std::sync::{Arc, Mutex};

/// Configuration for paged attention cache
#[derive(Clone, Debug)]
pub struct CacheConfig {
    /// Number of tokens per block (typically 16 or 32)
    pub block_size: usize,
    /// Number of blocks to allocate on GPU
    pub num_gpu_blocks: usize,
    /// Number of attention heads for KV
    pub num_kv_heads: usize,
    /// Dimension per head
    pub head_dim: usize,
    /// Number of layers
    pub num_layers: usize,
}

impl CacheConfig {
    pub fn new(
        num_kv_heads: usize,
        head_dim: usize,
        num_layers: usize,
        max_seq_len: usize,
        max_batch_size: usize,
    ) -> Self {
        let block_size = 16; // Standard block size

        // Calculate number of blocks needed
        // Each sequence needs ceil(max_seq_len / block_size) blocks
        let blocks_per_seq = max_seq_len.div_ceil(block_size);
        let num_gpu_blocks = blocks_per_seq * max_batch_size;

        Self {
            block_size,
            num_gpu_blocks,
            num_kv_heads,
            head_dim,
            num_layers,
        }
    }

    /// Calculate memory needed for KV cache in bytes
    pub fn memory_bytes(&self, dtype: DType) -> usize {
        let bytes_per_elem = match dtype {
            DType::F32 => 4,
            DType::F16 | DType::BF16 => 2,
            _ => 4,
        };

        // Key cache: [num_blocks, num_heads, head_dim/x, block_size, x]
        // Value cache: [num_blocks, num_heads, head_dim, block_size]
        let key_size = self.num_gpu_blocks * self.num_kv_heads * self.head_dim * self.block_size;
        let value_size = self.num_gpu_blocks * self.num_kv_heads * self.head_dim * self.block_size;

        // Per layer, K + V
        (key_size + value_size) * bytes_per_elem * self.num_layers
    }
}

/// Paged KV Cache for a single layer
#[derive(Clone)]
pub struct PagedKVCache {
    /// Key cache: [num_blocks, num_heads, head_dim, block_size]
    pub key_cache: Tensor,
    /// Value cache: [num_blocks, num_heads, head_dim, block_size]
    pub value_cache: Tensor,
    /// Block size (tokens per block)
    pub block_size: usize,
}

impl PagedKVCache {
    /// Create a new paged KV cache
    pub fn new(
        num_blocks: usize,
        num_heads: usize,
        head_dim: usize,
        block_size: usize,
        dtype: DType,
        device: &Device,
    ) -> Result<Self> {
        // Allocate key cache: [num_blocks, num_heads, head_dim, block_size]
        let key_cache =
            Tensor::zeros((num_blocks, num_heads, head_dim, block_size), dtype, device)?;

        // Allocate value cache: [num_blocks, num_heads, head_dim, block_size]
        let value_cache =
            Tensor::zeros((num_blocks, num_heads, head_dim, block_size), dtype, device)?;

        Ok(Self {
            key_cache,
            value_cache,
            block_size,
        })
    }
}

/// Cache Engine manages all layer caches
pub struct CacheEngine {
    /// KV caches for all layers
    caches: Arc<Mutex<Vec<PagedKVCache>>>,
    /// Configuration
    config: CacheConfig,
}

impl CacheEngine {
    /// Create a new cache engine with pre-allocated GPU memory
    pub fn new(config: CacheConfig, dtype: DType, device: &Device) -> Result<Self> {
        let mut caches = Vec::with_capacity(config.num_layers);

        for _ in 0..config.num_layers {
            let cache = PagedKVCache::new(
                config.num_gpu_blocks,
                config.num_kv_heads,
                config.head_dim,
                config.block_size,
                dtype,
                device,
            )?;
            caches.push(cache);
        }

        tracing::info!(
            "CacheEngine: Allocated {} blocks × {} layers = {:.2} MB",
            config.num_gpu_blocks,
            config.num_layers,
            config.memory_bytes(dtype) as f64 / (1024.0 * 1024.0)
        );

        Ok(Self {
            caches: Arc::new(Mutex::new(caches)),
            config,
        })
    }

    /// Get cache for a specific layer
    pub fn get_cache(&self, layer_idx: usize) -> Option<PagedKVCache> {
        let caches = self.caches.lock().ok()?;
        caches.get(layer_idx).cloned()
    }

    /// Get all caches
    pub fn get_all_caches(&self) -> Vec<PagedKVCache> {
        self.caches.lock().unwrap().clone()
    }

    /// Configuration
    pub fn config(&self) -> &CacheConfig {
        &self.config
    }

    /// Block size
    pub fn block_size(&self) -> usize {
        self.config.block_size
    }

    /// Number of blocks
    pub fn num_blocks(&self) -> usize {
        self.config.num_gpu_blocks
    }
}
