//! Paged Attention CUDA Kernels - Rust Bindings
//!
//! Provides efficient KV cache operations using paged memory.

#[cfg(feature = "cuda")]
use candle_core::cuda_backend::cudarc::driver::{DevicePtr, LaunchAsync, LaunchConfig};
#[cfg(feature = "cuda")]
use candle_core::cuda_backend::WrapErr;
#[cfg(feature = "cuda")]
use candle_core::DType;
#[cfg(feature = "cuda")]
use candle_core::Device;
use candle_core::{Result, Tensor};
#[cfg(feature = "cuda")]
use std::sync::OnceLock;

#[cfg(feature = "cuda")]
const PAGED_ATTENTION_PTX: &str = include_str!(concat!(env!("OUT_DIR"), "/paged_attention.ptx"));

#[cfg(feature = "cuda")]
static PAGED_ATTN_LOADED: OnceLock<std::sync::Mutex<std::collections::HashSet<usize>>> =
    OnceLock::new();

#[cfg(feature = "cuda")]
fn ensure_paged_attn_loaded(
    cuda_dev: &std::sync::Arc<candle_core::cuda_backend::cudarc::driver::CudaDevice>,
    device_id: usize,
) -> Result<()> {
    let loaded =
        PAGED_ATTN_LOADED.get_or_init(|| std::sync::Mutex::new(std::collections::HashSet::new()));
    let mut guard = loaded.lock().unwrap();

    if !guard.contains(&device_id) {
        cuda_dev
            .load_ptx(
                PAGED_ATTENTION_PTX.into(),
                "paged_attention",
                &[
                    "reshape_and_cache_kernel_f32",
                    "paged_attention_v1_kernel_f32",
                    "attention_kernel_f32",
                ],
            )
            .w()?;
        guard.insert(device_id);
        tracing::info!("Loaded paged_attention PTX for device {}", device_id);
    }

    Ok(())
}

/// Write K/V tensors into paged cache blocks
///
/// # Arguments
/// * `key` - Key tensor [num_tokens, num_heads, head_dim]
/// * `value` - Value tensor [num_tokens, num_heads, head_dim]
/// * `key_cache` - Key cache [num_blocks, num_heads, head_dim, block_size]
/// * `value_cache` - Value cache [num_blocks, num_heads, head_dim, block_size]
/// * `slot_mapping` - Slot indices for each token [num_tokens]
#[cfg(feature = "cuda")]
pub fn reshape_and_cache(
    key: &Tensor,
    value: &Tensor,
    key_cache: &Tensor,
    value_cache: &Tensor,
    slot_mapping: &Tensor,
) -> Result<()> {
    let dev = match key.device() {
        Device::Cuda(dev) => dev.clone(),
        _ => {
            return Err(candle_core::Error::Msg(
                "Key must be on CUDA device".to_string(),
            ))
        }
    };

    let cuda_dev = dev.cuda_device();
    ensure_paged_attn_loaded(&cuda_dev, dev.ordinal())?;

    let key = key.to_dtype(DType::F32)?.contiguous()?;
    let value = value.to_dtype(DType::F32)?.contiguous()?;
    let slot_mapping = slot_mapping.to_dtype(DType::I64)?.contiguous()?;

    let dims = key.dims();
    let num_tokens = dims[0];
    let num_heads = dims[1];
    let head_dim = dims[2];

    let cache_dims = key_cache.dims();
    let block_size = cache_dims[3];

    // Get device pointers
    let key_ptr = {
        let storage = key.storage_and_layout().0;
        match &*storage {
            candle_core::Storage::Cuda(s) => *s.as_cuda_slice::<f32>()?.device_ptr(),
            _ => {
                return Err(candle_core::Error::Msg(
                    "Key must be CUDA tensor".to_string(),
                ))
            }
        }
    };

    let value_ptr = {
        let storage = value.storage_and_layout().0;
        match &*storage {
            candle_core::Storage::Cuda(s) => *s.as_cuda_slice::<f32>()?.device_ptr(),
            _ => {
                return Err(candle_core::Error::Msg(
                    "Value must be CUDA tensor".to_string(),
                ))
            }
        }
    };

    let key_cache_ptr = {
        let storage = key_cache.storage_and_layout().0;
        match &*storage {
            candle_core::Storage::Cuda(s) => *s.as_cuda_slice::<f32>()?.device_ptr(),
            _ => {
                return Err(candle_core::Error::Msg(
                    "Key cache must be CUDA tensor".to_string(),
                ))
            }
        }
    };

    let value_cache_ptr = {
        let storage = value_cache.storage_and_layout().0;
        match &*storage {
            candle_core::Storage::Cuda(s) => *s.as_cuda_slice::<f32>()?.device_ptr(),
            _ => {
                return Err(candle_core::Error::Msg(
                    "Value cache must be CUDA tensor".to_string(),
                ))
            }
        }
    };

    let slot_mapping_ptr = {
        let storage = slot_mapping.storage_and_layout().0;
        match &*storage {
            candle_core::Storage::Cuda(s) => *s.as_cuda_slice::<i64>()?.device_ptr(),
            _ => {
                return Err(candle_core::Error::Msg(
                    "Slot mapping must be CUDA tensor".to_string(),
                ))
            }
        }
    };

    let func = cuda_dev
        .get_func("paged_attention", "reshape_and_cache_kernel_f32")
        .ok_or_else(|| {
            candle_core::Error::Msg("Failed to get reshape_and_cache kernel".to_string())
        })?;

    let block_dim = 256u32.min((num_heads * head_dim) as u32);
    let cfg = LaunchConfig {
        grid_dim: (num_tokens as u32, 1, 1),
        block_dim: (block_dim, 1, 1),
        shared_mem_bytes: 0,
    };

    let params = (
        key_ptr,
        value_ptr,
        key_cache_ptr,
        value_cache_ptr,
        slot_mapping_ptr,
        num_tokens as i32,
        num_heads as i32,
        head_dim as i32,
        block_size as i32,
    );

    unsafe { func.launch(cfg, params) }.w()?;

    Ok(())
}

#[cfg(not(feature = "cuda"))]
pub fn reshape_and_cache(
    _key: &Tensor,
    _value: &Tensor,
    _key_cache: &Tensor,
    _value_cache: &Tensor,
    _slot_mapping: &Tensor,
) -> Result<()> {
    Err(candle_core::Error::Msg("CUDA not available".to_string()))
}

/// Compute paged attention
///
/// # Arguments
/// * `query` - Query tensor [num_seqs, num_heads, head_dim]
/// * `key_cache` - Key cache [num_blocks, num_heads, head_dim, block_size]
/// * `value_cache` - Value cache [num_blocks, num_heads, head_dim, block_size]
/// * `block_tables` - Block indices per sequence [num_seqs, max_blocks_per_seq]
/// * `context_lens` - Number of cached tokens per sequence [num_seqs]
/// * `scale` - Softmax scale (1/sqrt(head_dim))
#[cfg(feature = "cuda")]
pub fn paged_attention_v1(
    query: &Tensor,
    key_cache: &Tensor,
    value_cache: &Tensor,
    block_tables: &Tensor,
    context_lens: &Tensor,
    scale: f32,
) -> Result<Tensor> {
    let dev = match query.device() {
        Device::Cuda(dev) => dev.clone(),
        _ => {
            return Err(candle_core::Error::Msg(
                "Query must be on CUDA device".to_string(),
            ))
        }
    };

    let cuda_dev = dev.cuda_device();
    ensure_paged_attn_loaded(&cuda_dev, dev.ordinal())?;

    let query = query.to_dtype(DType::F32)?.contiguous()?;
    let key_cache = key_cache.to_dtype(DType::F32)?.contiguous()?;
    let value_cache = value_cache.to_dtype(DType::F32)?.contiguous()?;
    let block_tables = block_tables.to_dtype(DType::U32)?.contiguous()?;
    let context_lens = context_lens.to_dtype(DType::U32)?.contiguous()?;

    let q_dims = query.dims();
    let num_seqs = q_dims[0];
    let num_heads = q_dims[1];
    let head_dim = q_dims[2];

    let cache_dims = key_cache.dims();
    let num_kv_heads = cache_dims[1]; // [num_blocks, num_kv_heads, head_dim, block_size]
    let block_size = cache_dims[3];

    let bt_dims = block_tables.dims();
    let max_num_blocks_per_seq = bt_dims[1];

    // Allocate output
    let output = Tensor::zeros(
        (num_seqs, num_heads, head_dim),
        DType::F32,
        &Device::Cuda(dev.clone()),
    )?;

    // Get device pointers
    let query_ptr = {
        let storage = query.storage_and_layout().0;
        match &*storage {
            candle_core::Storage::Cuda(s) => *s.as_cuda_slice::<f32>()?.device_ptr(),
            _ => {
                return Err(candle_core::Error::Msg(
                    "Query must be CUDA tensor".to_string(),
                ))
            }
        }
    };

    let key_cache_ptr = {
        let storage = key_cache.storage_and_layout().0;
        match &*storage {
            candle_core::Storage::Cuda(s) => *s.as_cuda_slice::<f32>()?.device_ptr(),
            _ => {
                return Err(candle_core::Error::Msg(
                    "Key cache must be CUDA tensor".to_string(),
                ))
            }
        }
    };

    let value_cache_ptr = {
        let storage = value_cache.storage_and_layout().0;
        match &*storage {
            candle_core::Storage::Cuda(s) => *s.as_cuda_slice::<f32>()?.device_ptr(),
            _ => {
                return Err(candle_core::Error::Msg(
                    "Value cache must be CUDA tensor".to_string(),
                ))
            }
        }
    };

    let block_tables_ptr = {
        let storage = block_tables.storage_and_layout().0;
        match &*storage {
            candle_core::Storage::Cuda(s) => *s.as_cuda_slice::<u32>()?.device_ptr(),
            _ => {
                return Err(candle_core::Error::Msg(
                    "Block tables must be CUDA tensor".to_string(),
                ))
            }
        }
    };

    let context_lens_ptr = {
        let storage = context_lens.storage_and_layout().0;
        match &*storage {
            candle_core::Storage::Cuda(s) => *s.as_cuda_slice::<u32>()?.device_ptr(),
            _ => {
                return Err(candle_core::Error::Msg(
                    "Context lens must be CUDA tensor".to_string(),
                ))
            }
        }
    };

    let output_ptr = {
        let storage = output.storage_and_layout().0;
        match &*storage {
            candle_core::Storage::Cuda(s) => *s.as_cuda_slice::<f32>()?.device_ptr(),
            _ => {
                return Err(candle_core::Error::Msg(
                    "Output allocation failed".to_string(),
                ))
            }
        }
    };

    let func = cuda_dev
        .get_func("paged_attention", "paged_attention_v1_kernel_f32")
        .ok_or_else(|| {
            candle_core::Error::Msg("Failed to get paged_attention_v1 kernel".to_string())
        })?;

    // Calculate shared memory: query (head_dim) + attention scores (context_len)
    // Get actual max context length from tensor
    let context_lens_vec: Vec<u32> = context_lens.flatten_all()?.to_vec1()?;
    let actual_max_context = context_lens_vec.iter().max().copied().unwrap_or(0) as usize;
    // Add buffer for safety, minimum 256
    let max_context_len = actual_max_context.max(256);
    let shared_mem_bytes = ((head_dim + max_context_len) * std::mem::size_of::<f32>()) as u32;

    let cfg = LaunchConfig {
        grid_dim: (num_seqs as u32, num_heads as u32, 1),
        block_dim: (32, 1, 1), // 32 threads = 1 warp (warp shuffle works correctly)
        shared_mem_bytes,
    };

    let params = (
        output_ptr,
        query_ptr,
        key_cache_ptr,
        value_cache_ptr,
        block_tables_ptr,
        context_lens_ptr,
        scale,
        num_seqs as i32,
        num_heads as i32,
        num_kv_heads as i32, // NEW: for GQA
        head_dim as i32,
        block_size as i32,
        max_num_blocks_per_seq as i32,
    );

    unsafe { func.launch(cfg, params) }.w()?;

    Ok(output)
}

#[cfg(not(feature = "cuda"))]
pub fn paged_attention_v1(
    _query: &Tensor,
    _key_cache: &Tensor,
    _value_cache: &Tensor,
    _block_tables: &Tensor,
    _context_lens: &Tensor,
    _scale: f32,
) -> Result<Tensor> {
    Err(candle_core::Error::Msg("CUDA not available".to_string()))
}
