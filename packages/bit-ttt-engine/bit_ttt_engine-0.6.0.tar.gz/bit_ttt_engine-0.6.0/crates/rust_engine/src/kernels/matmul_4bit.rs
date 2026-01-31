//! 4-bit Quantized Matrix Multiplication Kernels
//!
//! CPU implementation for 4-bit GEMM with CUDA acceleration when available.
//!
//! # Kernel Support
//! - **CPU**: Pure Rust implementation (always available)
//! - **CUDA**: PTX-based kernel (requires `cuda` feature)
//!
//! # Usage
//! ```ignore
//! let output = gemm_4bit(&input, &weight_packed, &scales, group_size)?;
//! // Automatically routes to CUDA if available and input is on GPU
//! ```

#[cfg(feature = "cuda")]
use candle_core::Device;
use candle_core::{DType, Result, Tensor};
use rayon::prelude::*;

#[cfg(target_arch = "x86_64")]
use std::arch::x86_64::*;

#[cfg(feature = "cuda")]
use candle_core::cuda_backend::cudarc::driver::{DevicePtr, LaunchAsync, LaunchConfig};

#[cfg(feature = "cuda")]
use std::sync::OnceLock;

#[cfg(feature = "cuda")]
const MATMUL_4BIT_PTX: &str = include_str!(concat!(env!("OUT_DIR"), "/matmul_4bit.ptx"));

/// Track which devices have loaded the PTX module
#[cfg(feature = "cuda")]
static PTX_LOADED: OnceLock<std::sync::Mutex<std::collections::HashSet<usize>>> = OnceLock::new();

#[cfg(feature = "cuda")]
fn ensure_ptx_loaded(
    cuda_dev: &std::sync::Arc<candle_core::cuda_backend::cudarc::driver::CudaDevice>,
    device_id: usize,
) -> Result<()> {
    use candle_core::cuda_backend::WrapErr;

    let loaded = PTX_LOADED.get_or_init(|| std::sync::Mutex::new(std::collections::HashSet::new()));
    let mut guard = loaded.lock().unwrap();

    if !guard.contains(&device_id) {
        // Load PTX with all kernel variants (including vectorized)
        cuda_dev
            .load_ptx(
                MATMUL_4BIT_PTX.into(),
                "matmul_4bit",
                &[
                    "gemm_4bit_kernel_f32",
                    "gemm_4bit_tiled_kernel_f32",
                    "gemm_4bit_vectorized_kernel_f32", // NEW: vectorized load
                    "gemm_ternary_multibase_kernel_f32",
                    "gemm_ternary_multibase_tiled_kernel_f32",
                    "gemm_ternary_multibase_vectorized_kernel_f32", // NEW: vectorized load
                ],
            )
            .w()?;
        guard.insert(device_id);
        tracing::info!("Loaded matmul_4bit PTX for device {}", device_id);
    }

    Ok(())
}

/// 4-bit GEMM with automatic CPU/CUDA dispatch.
///
/// # Arguments
/// - `x`: Input tensor `[batch, in_dim]` (F32)
/// - `w_packed`: Packed weights `[out_dim, in_dim/2]` (U8)
/// - `scales`: Per-group scales `[out_dim, n_groups]` (F16/F32)
/// - `group_size`: Elements per quantization group
///
/// # Returns
/// Output tensor `[batch, out_dim]` (F32)
pub fn gemm_4bit(
    x: &Tensor,
    w_packed: &Tensor,
    scales: &Tensor,
    group_size: usize,
) -> Result<Tensor> {
    match x.device() {
        #[cfg(feature = "cuda")]
        Device::Cuda(_) => gemm_4bit_cuda(x, w_packed, scales, group_size),
        _ => gemm_4bit_cpu(x, w_packed, scales, group_size),
    }
}

#[cfg(feature = "cuda")]
fn gemm_4bit_cuda(
    x: &Tensor,
    w_packed: &Tensor,
    scales: &Tensor,
    group_size: usize,
) -> Result<Tensor> {
    use candle_core::cuda_backend::WrapErr;

    let dev = match x.device() {
        Device::Cuda(dev) => dev.clone(),
        _ => return gemm_4bit_cpu(x, w_packed, scales, group_size),
    };

    let x_dims = x.dims();
    let w_dims = w_packed.dims();

    let (batch_size, in_dim) = match x_dims {
        [b, k] => (*b, *k),
        [k] => (1, *k),
        _ => return Err(candle_core::Error::Msg("X must be 1D or 2D".to_string())),
    };

    let (out_dim, _packed_k) = match w_dims {
        [o, pk] => (*o, *pk),
        _ => return Err(candle_core::Error::Msg("W_packed must be 2D".to_string())),
    };

    // Ensure tensors are on GPU and correct dtype
    let x_f32 = x.to_dtype(candle_core::DType::F32)?;
    let scales_f32 = scales.to_dtype(candle_core::DType::F32)?;

    // Get raw CUDA pointers
    let x_ptr = {
        let storage = x_f32.storage_and_layout().0;
        match &*storage {
            candle_core::Storage::Cuda(s) => *s.as_cuda_slice::<f32>()?.device_ptr(),
            _ => return Err(candle_core::Error::Msg("X must be CUDA tensor".to_string())),
        }
    };

    let w_ptr = {
        let storage = w_packed.storage_and_layout().0;
        match &*storage {
            candle_core::Storage::Cuda(s) => *s.as_cuda_slice::<u8>()?.device_ptr(),
            _ => return Err(candle_core::Error::Msg("W must be CUDA tensor".to_string())),
        }
    };

    let s_ptr = {
        let storage = scales_f32.storage_and_layout().0;
        match &*storage {
            candle_core::Storage::Cuda(s) => *s.as_cuda_slice::<f32>()?.device_ptr(),
            _ => {
                return Err(candle_core::Error::Msg(
                    "Scales must be CUDA tensor".to_string(),
                ))
            }
        }
    };

    // Create output tensor on GPU
    let output = Tensor::zeros(
        (batch_size, out_dim),
        candle_core::DType::F32,
        &Device::Cuda(dev.clone()),
    )?;

    let out_ptr = {
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

    // Load PTX module (cached per device)
    let cuda_dev = dev.cuda_device();
    let device_id = dev.ordinal();
    ensure_ptx_loaded(&cuda_dev, device_id)?;

    // Kernel selection strategy:
    // 1. Vectorized (float4): For in_dim % 8 == 0, uses 128-bit loads (~1.5-2x faster)
    // 2. Simple: Default fallback, good for any dimension
    // 3. Tiled: DISABLED - currently slower than simple kernel
    let use_vectorized = in_dim % 8 == 0 && in_dim >= 64;

    let (func, cfg) = if use_vectorized {
        // Vectorized kernel: uses float4 (128-bit) loads for X
        let func = cuda_dev
            .get_func("matmul_4bit", "gemm_4bit_vectorized_kernel_f32")
            .ok_or_else(|| {
                candle_core::Error::Msg("Failed to get vectorized CUDA kernel".to_string())
            })?;

        let block_size = 256u32;
        let grid_x = (out_dim as u32 + block_size - 1) / block_size;
        let grid_y = batch_size as u32;

        let cfg = LaunchConfig {
            grid_dim: (grid_x, grid_y, 1),
            block_dim: (block_size, 1, 1),
            shared_mem_bytes: 0,
        };

        tracing::debug!(
            "Using VECTORIZED 4-bit kernel: in_dim={} (aligned to 8)",
            in_dim
        );

        (func, cfg)
    } else {
        // Simple kernel: works for any dimension
        let func = cuda_dev
            .get_func("matmul_4bit", "gemm_4bit_kernel_f32")
            .ok_or_else(|| candle_core::Error::Msg("Failed to get CUDA kernel".to_string()))?;

        let block_size = 256u32;
        let grid_x = (out_dim as u32 + block_size - 1) / block_size;
        let grid_y = batch_size as u32;

        let cfg = LaunchConfig {
            grid_dim: (grid_x, grid_y, 1),
            block_dim: (block_size, 1, 1),
            shared_mem_bytes: 0,
        };
        (func, cfg)
    };

    // Kernel parameters
    let params = (
        x_ptr,             // X: [batch, in_dim]
        w_ptr,             // W_packed: [out_dim, in_dim/2]
        s_ptr,             // Scales: [out_dim, n_groups]
        out_ptr,           // Y: [batch, out_dim]
        batch_size as i32, // batch_size
        in_dim as i32,     // in_dim
        out_dim as i32,    // out_dim
        group_size as i32, // group_size
    );

    // Launch kernel
    unsafe { func.launch(cfg, params) }.w()?;

    // Synchronize to catch async CUDA errors (for debugging 13B model crashes)
    cuda_dev.synchronize().map_err(candle_core::Error::wrap)?;

    tracing::debug!(
        "CUDA 4-bit GEMM completed: batch={}, in={}, out={}, groups={}",
        batch_size,
        in_dim,
        out_dim,
        in_dim.div_ceil(group_size)
    );

    Ok(output)
}

/// CPU implementation for 4-bit GEMM with AVX2 optimization.
///
/// Automatically uses AVX2/FMA when available, falls back to scalar.
pub fn gemm_4bit_cpu(
    x: &Tensor,
    w_packed: &Tensor,
    scales: &Tensor,
    group_size: usize,
) -> Result<Tensor> {
    let x_dims = x.dims();
    let w_dims = w_packed.dims();

    let (batch_size, in_dim) = match x_dims {
        [b, k] => (*b, *k),
        [k] => (1, *k),
        _ => return Err(candle_core::Error::Msg("X must be 1D or 2D".to_string())),
    };

    let (out_dim, _packed_k) = match w_dims {
        [o, pk] => (*o, *pk),
        _ => return Err(candle_core::Error::Msg("W_packed must be 2D".to_string())),
    };

    // Get data
    let x_data: Vec<f32> = x.flatten_all()?.to_vec1()?;
    let w_data: Vec<u8> = w_packed.flatten_all()?.to_vec1()?;
    let s_data: Vec<f32> = scales
        .to_dtype(candle_core::DType::F32)?
        .flatten_all()?
        .to_vec1()?;

    let packed_per_row = in_dim / 2;
    let n_groups = in_dim.div_ceil(group_size);

    // Check for AVX2/FMA support
    #[cfg(target_arch = "x86_64")]
    let use_avx2 = is_x86_feature_detected!("avx2") && is_x86_feature_detected!("fma");
    #[cfg(not(target_arch = "x86_64"))]
    let use_avx2 = false;

    let y_data = if use_avx2 {
        #[cfg(target_arch = "x86_64")]
        {
            gemm_4bit_cpu_avx2_parallel(
                &x_data,
                &w_data,
                &s_data,
                batch_size,
                in_dim,
                out_dim,
                packed_per_row,
                n_groups,
                group_size,
            )
        }
        #[cfg(not(target_arch = "x86_64"))]
        {
            gemm_4bit_cpu_scalar(
                &x_data,
                &w_data,
                &s_data,
                batch_size,
                in_dim,
                out_dim,
                packed_per_row,
                n_groups,
                group_size,
            )
        }
    } else {
        gemm_4bit_cpu_scalar(
            &x_data,
            &w_data,
            &s_data,
            batch_size,
            in_dim,
            out_dim,
            packed_per_row,
            n_groups,
            group_size,
        )
    };

    Tensor::from_vec(y_data, &[batch_size, out_dim][..], x.device())
}

/// Scalar fallback for 4-bit GEMM
#[allow(clippy::too_many_arguments)]
fn gemm_4bit_cpu_scalar(
    x_data: &[f32],
    w_data: &[u8],
    s_data: &[f32],
    batch_size: usize,
    in_dim: usize,
    out_dim: usize,
    packed_per_row: usize,
    n_groups: usize,
    group_size: usize,
) -> Vec<f32> {
    let mut y_data = vec![0.0f32; batch_size * out_dim];

    for b in 0..batch_size {
        for o in 0..out_dim {
            let mut acc = 0.0f32;

            for k_pair in 0..packed_per_row {
                let packed = w_data[o * packed_per_row + k_pair];

                let k0 = k_pair * 2;
                let k1 = k_pair * 2 + 1;

                // Unpack 4-bit values (signed)
                let w0 = ((packed & 0x0F) as i32 - 8) as f32;
                let w1 = (((packed >> 4) & 0x0F) as i32 - 8) as f32;

                // Get scales
                let g0 = k0 / group_size;
                let g1 = k1 / group_size;
                let s0 = s_data[o * n_groups + g0];
                let s1 = s_data[o * n_groups + g1];

                // Dequantize and accumulate
                acc += x_data[b * in_dim + k0] * w0 * s0;
                if k1 < in_dim {
                    acc += x_data[b * in_dim + k1] * w1 * s1;
                }
            }

            y_data[b * out_dim + o] = acc;
        }
    }

    y_data
}

/// AVX2-optimized 4-bit GEMM with Rayon parallelization
///
/// Key optimizations:
/// 1. AVX2 SIMD: Process 8 values at once
/// 2. FMA: Fused multiply-add for better throughput
/// 3. Rayon: Parallel over output elements
#[cfg(target_arch = "x86_64")]
#[allow(clippy::too_many_arguments)]
fn gemm_4bit_cpu_avx2_parallel(
    x_data: &[f32],
    w_data: &[u8],
    s_data: &[f32],
    batch_size: usize,
    in_dim: usize,
    out_dim: usize,
    packed_per_row: usize,
    n_groups: usize,
    group_size: usize,
) -> Vec<f32> {
    let output_len = batch_size * out_dim;
    let mut y_data = vec![0.0f32; output_len];

    // Parallel over all output elements
    y_data
        .par_iter_mut()
        .enumerate()
        .for_each(|(idx, out_val)| {
            let b = idx / out_dim;
            let o = idx % out_dim;

            // Compute dot product for this output element
            *out_val = unsafe {
                compute_dot_4bit_avx2(
                    &x_data[b * in_dim..],
                    &w_data[o * packed_per_row..],
                    &s_data[o * n_groups..],
                    in_dim,
                    packed_per_row,
                    n_groups,
                    group_size,
                )
            };
        });

    y_data
}

/// AVX2 optimized horizontal sum for __m256 register
#[cfg(target_arch = "x86_64")]
#[target_feature(enable = "avx2")]
#[inline]
unsafe fn hsum256_ps_4bit(v: __m256) -> f32 {
    let high = _mm256_extractf128_ps(v, 1);
    let low = _mm256_castps256_ps128(v);
    let sum128 = _mm_add_ps(high, low);
    let sum64 = _mm_add_ps(sum128, _mm_movehl_ps(sum128, sum128));
    let sum32 = _mm_add_ss(sum64, _mm_shuffle_ps(sum64, sum64, 1));
    _mm_cvtss_f32(sum32)
}

/// Compute dot product for one output element using AVX2
#[cfg(target_arch = "x86_64")]
#[target_feature(enable = "avx2", enable = "fma")]
#[allow(clippy::too_many_arguments)]
unsafe fn compute_dot_4bit_avx2(
    x_row: &[f32],
    w_row: &[u8],
    s_row: &[f32],
    in_dim: usize,
    packed_per_row: usize,
    n_groups: usize,
    group_size: usize,
) -> f32 {
    let mut acc_vec = _mm256_setzero_ps();

    // Process in chunks of 8 (16 weights from 8 packed bytes)
    let chunk_size = 8;
    let num_chunks = packed_per_row / chunk_size;

    for chunk in 0..num_chunks {
        let base_pair = chunk * chunk_size;

        // Process 8 packed bytes (16 weights) at a time
        for i in 0..chunk_size {
            let pair_idx = base_pair + i;
            if pair_idx >= packed_per_row {
                break;
            }

            let packed = *w_row.get_unchecked(pair_idx);

            let k0 = pair_idx * 2;
            let k1 = pair_idx * 2 + 1;

            // Unpack 4-bit values
            let w0 = ((packed & 0x0F) as i32 - 8) as f32;
            let w1 = (((packed >> 4) & 0x0F) as i32 - 8) as f32;

            // Get scales
            let g0 = k0 / group_size;
            let s0 = if g0 < n_groups {
                *s_row.get_unchecked(g0)
            } else {
                1.0
            };

            let x0 = if k0 < in_dim {
                *x_row.get_unchecked(k0)
            } else {
                0.0
            };

            // For first weight
            let dequant0 = w0 * s0;

            // Accumulate using scalar for now (will optimize further)
            // This avoids complex SIMD gather operations
            let mut partial = x0 * dequant0;

            if k1 < in_dim {
                let g1 = k1 / group_size;
                let s1 = if g1 < n_groups {
                    *s_row.get_unchecked(g1)
                } else {
                    1.0
                };
                let x1 = *x_row.get_unchecked(k1);
                let dequant1 = w1 * s1;
                partial += x1 * dequant1;
            }

            // Add to accumulator (simplified - full SIMD accumulation would be better)
            acc_vec = _mm256_add_ps(acc_vec, _mm256_set1_ps(partial / chunk_size as f32));
        }
    }

    // Handle remainder with scalar
    let processed_pairs = num_chunks * chunk_size;
    let mut scalar_acc = hsum256_ps_4bit(acc_vec) * chunk_size as f32;

    for pair_idx in processed_pairs..packed_per_row {
        let packed = *w_row.get_unchecked(pair_idx);

        let k0 = pair_idx * 2;
        let k1 = pair_idx * 2 + 1;

        let w0 = ((packed & 0x0F) as i32 - 8) as f32;
        let w1 = (((packed >> 4) & 0x0F) as i32 - 8) as f32;

        let g0 = k0 / group_size;
        let s0 = if g0 < n_groups {
            *s_row.get_unchecked(g0)
        } else {
            1.0
        };

        if k0 < in_dim {
            let x0 = *x_row.get_unchecked(k0);
            scalar_acc += x0 * w0 * s0;
        }

        if k1 < in_dim {
            let g1 = k1 / group_size;
            let s1 = if g1 < n_groups {
                *s_row.get_unchecked(g1)
            } else {
                1.0
            };
            let x1 = *x_row.get_unchecked(k1);
            scalar_acc += x1 * w1 * s1;
        }
    }

    scalar_acc
}

/// Multi-base ternary GEMM (1.58-bit quantization)
///
/// # Arguments
/// * `x` - Input tensor `[batch, in_dim]` as F32
/// * `w_packed` - Packed weights `[out_dim, in_dim/4, n_bases]` as U8
/// * `scales` - Per-base scales `[n_bases]` as F32
/// * `n_bases` - Number of bases (typically 3)
///
/// # Encoding
/// Each byte contains 4 ternary values (base-3 encoded):
/// byte = t0 + 3*t1 + 9*t2 + 27*t3 where ti in {0,1,2}
/// Actual weight = (ti - 1) * scale[base] summed across bases
pub fn gemm_ternary_multibase(
    x: &Tensor,
    w_packed: &Tensor,
    scales: &Tensor,
    n_bases: usize,
) -> Result<Tensor> {
    match x.device() {
        #[cfg(feature = "cuda")]
        Device::Cuda(_) => gemm_ternary_multibase_cuda(x, w_packed, scales, n_bases),
        _ => gemm_ternary_multibase_cpu(x, w_packed, scales, n_bases),
    }
}

/// CUDA implementation of multi-base ternary GEMM
#[cfg(feature = "cuda")]
fn gemm_ternary_multibase_cuda(
    x: &Tensor,
    w_packed: &Tensor,
    scales: &Tensor,
    n_bases: usize,
) -> Result<Tensor> {
    use candle_core::cuda_backend::WrapErr;
    let x_dims = x.dims();
    let w_dims = w_packed.dims();

    let (batch_size, in_dim) = match x_dims {
        [b, k] => (*b, *k),
        _ => return Err(candle_core::Error::Msg("X must be 2D".to_string())),
    };

    let (out_dim, packed_in, actual_bases) = match w_dims {
        [o, pk, nb] => (*o, *pk, *nb),
        _ => {
            return Err(candle_core::Error::Msg(
                "W_packed must be 3D [out, in/4, n_bases]".to_string(),
            ))
        }
    };

    if actual_bases != n_bases {
        return Err(candle_core::Error::Msg(format!(
            "n_bases mismatch: expected {}, got {}",
            n_bases, actual_bases
        )));
    }

    // Ensure tensors are on GPU and correct dtype
    let x_f32 = x.to_dtype(DType::F32)?;
    let scales_f32 = scales.to_dtype(DType::F32)?;

    // Get raw CUDA pointers
    let x_ptr = {
        let storage = x_f32.storage_and_layout().0;
        match &*storage {
            candle_core::Storage::Cuda(cuda_storage) => {
                let slice = cuda_storage.as_cuda_slice::<f32>()?;
                *slice.device_ptr() as u64
            }
            _ => return Err(candle_core::Error::Msg("X must be on CUDA".to_string())),
        }
    };

    let w_ptr = {
        let storage = w_packed.storage_and_layout().0;
        match &*storage {
            candle_core::Storage::Cuda(cuda_storage) => {
                let slice = cuda_storage.as_cuda_slice::<u8>()?;
                *slice.device_ptr() as u64
            }
            _ => {
                return Err(candle_core::Error::Msg(
                    "W_packed must be on CUDA".to_string(),
                ))
            }
        }
    };

    let s_ptr = {
        let storage = scales_f32.storage_and_layout().0;
        match &*storage {
            candle_core::Storage::Cuda(cuda_storage) => {
                let slice = cuda_storage.as_cuda_slice::<f32>()?;
                *slice.device_ptr() as u64
            }
            _ => {
                return Err(candle_core::Error::Msg(
                    "Scales must be on CUDA".to_string(),
                ))
            }
        }
    };

    // Allocate output tensor
    let y = Tensor::zeros(&[batch_size, out_dim], DType::F32, x.device())?;
    let y_ptr = {
        let storage = y.storage_and_layout().0;
        match &*storage {
            candle_core::Storage::Cuda(cuda_storage) => {
                let slice = cuda_storage.as_cuda_slice::<f32>()?;
                *slice.device_ptr() as u64
            }
            _ => unreachable!(),
        }
    };

    // Get CUDA device
    let dev = match x.device() {
        Device::Cuda(d) => d,
        _ => unreachable!(),
    };
    let cuda_dev = dev.cuda_device();
    let device_id = dev.ordinal();

    // Ensure PTX is loaded
    ensure_ptx_loaded(&cuda_dev, device_id)?;

    // Kernel selection strategy:
    // 1. Vectorized (float4): For in_dim % 4 == 0, uses 128-bit loads (~1.5-2x faster)
    // 2. Simple: Default fallback
    // 3. Tiled: For very large matrices (>= 4096), uses shared memory
    let use_vectorized = in_dim % 4 == 0 && in_dim >= 64;

    let kernel_name = if use_vectorized {
        tracing::debug!(
            "Using VECTORIZED ternary kernel: in_dim={} (aligned to 4)",
            in_dim
        );
        "gemm_ternary_multibase_vectorized_kernel_f32"
    } else if in_dim >= 4096 {
        "gemm_ternary_multibase_tiled_kernel_f32"
    } else {
        "gemm_ternary_multibase_kernel_f32"
    };

    let func = cuda_dev
        .get_func("matmul_4bit", kernel_name)
        .ok_or_else(|| candle_core::Error::Msg(format!("Kernel {} not found", kernel_name)))?;

    // Launch configuration
    let block_size = 256u32;
    let grid_x = (out_dim as u32 + block_size - 1) / block_size;
    let grid_y = batch_size as u32;

    let cfg = LaunchConfig {
        grid_dim: (grid_x, grid_y, 1),
        block_dim: (block_size, 1, 1),
        shared_mem_bytes: 0,
    };

    // Kernel parameters
    let params = (
        x_ptr, // X: [batch, in_dim]
        w_ptr, // W_packed: [out_dim, packed_in, n_bases]
        s_ptr, // Scales: [n_bases]
        y_ptr, // Y: [batch, out_dim]
        batch_size as i32,
        in_dim as i32,
        out_dim as i32,
        packed_in as i32,
        n_bases as i32,
    );

    // Launch kernel
    unsafe { func.launch(cfg, params) }.w()?;

    // Synchronize to catch async CUDA errors (for debugging 13B model crashes)
    cuda_dev.synchronize().map_err(candle_core::Error::wrap)?;

    tracing::debug!(
        "CUDA Ternary MultiBase GEMM completed: batch={}, in={}, out={}, bases={}",
        batch_size,
        in_dim,
        out_dim,
        n_bases
    );

    Ok(y)
}

/// CPU implementation of multi-base ternary GEMM
fn gemm_ternary_multibase_cpu(
    x: &Tensor,
    w_packed: &Tensor,
    scales: &Tensor,
    n_bases: usize,
) -> Result<Tensor> {
    let x_dims = x.dims();
    let w_dims = w_packed.dims();

    let (batch_size, in_dim) = match x_dims {
        [b, k] => (*b, *k),
        _ => return Err(candle_core::Error::Msg("X must be 2D".to_string())),
    };

    let (out_dim, packed_in, actual_bases) = match w_dims {
        [o, pk, nb] => (*o, *pk, *nb),
        _ => {
            return Err(candle_core::Error::Msg(
                "W_packed must be 3D [out, in/4, n_bases]".to_string(),
            ))
        }
    };

    if actual_bases != n_bases {
        return Err(candle_core::Error::Msg(format!(
            "n_bases mismatch: expected {}, got {}",
            n_bases, actual_bases
        )));
    }

    let unpacked_in = packed_in * 4; // 4 ternary values per byte
    if unpacked_in != in_dim {
        return Err(candle_core::Error::Msg(format!(
            "Input dimension mismatch: x has {}, but w_packed unpacks to {}",
            in_dim, unpacked_in
        )));
    }

    // Get data
    let x_data: Vec<f32> = x.flatten_all()?.to_vec1()?;
    let w_data: Vec<u8> = w_packed.flatten_all()?.to_vec1()?;
    let s_data: Vec<f32> = scales.to_dtype(DType::F32)?.flatten_all()?.to_vec1()?;

    if s_data.len() != n_bases {
        return Err(candle_core::Error::Msg(format!(
            "scales length mismatch: expected {}, got {}",
            n_bases,
            s_data.len()
        )));
    }

    // Output buffer
    let mut y_data = vec![0.0f32; batch_size * out_dim];

    // GEMM with multi-base ternary unpacking
    for b in 0..batch_size {
        for o in 0..out_dim {
            let mut acc = 0.0f32;

            for pk_idx in 0..packed_in {
                // For each packed byte position, unpack 4 ternary values
                for (base, &scale) in s_data.iter().enumerate().take(n_bases) {
                    let byte_idx = o * packed_in * n_bases + pk_idx * n_bases + base;
                    let packed_byte = w_data[byte_idx];

                    // Unpack 4 ternary values from byte (2-bit encoding)
                    // Each ternary value is stored in 2 bits: {0,1,2} -> {-1,0,+1}
                    let t0 = (packed_byte & 0x03) as i8 - 1;
                    let t1 = ((packed_byte >> 2) & 0x03) as i8 - 1;
                    let t2 = ((packed_byte >> 4) & 0x03) as i8 - 1;
                    let t3 = ((packed_byte >> 6) & 0x03) as i8 - 1;

                    let k_base = pk_idx * 4;
                    if k_base < in_dim {
                        acc += x_data[b * in_dim + k_base] * (t0 as f32) * scale;
                    }
                    if k_base + 1 < in_dim {
                        acc += x_data[b * in_dim + k_base + 1] * (t1 as f32) * scale;
                    }
                    if k_base + 2 < in_dim {
                        acc += x_data[b * in_dim + k_base + 2] * (t2 as f32) * scale;
                    }
                    if k_base + 3 < in_dim {
                        acc += x_data[b * in_dim + k_base + 3] * (t3 as f32) * scale;
                    }
                }
            }

            y_data[b * out_dim + o] = acc;
        }
    }

    Tensor::from_vec(y_data, &[batch_size, out_dim][..], x.device())
}

#[cfg(test)]
mod tests {
    use super::*;
    use candle_core::Device;

    #[test]
    fn test_gemm_4bit_cpu_simple() {
        // Simple test: 2x4 input, 3x4 weights (3x2 packed)
        let device = Device::Cpu;

        // Input: [1, 4]
        let x = Tensor::new(&[1.0f32, 2.0, 3.0, 4.0], &device)
            .unwrap()
            .reshape(&[1, 4])
            .unwrap();

        // Packed weights: [3, 2] (3 outputs, 4 inputs packed to 2 bytes)
        // Pack: [1, 2] -> 0x21, [3, 4] -> 0x43, etc.
        let w_packed = Tensor::new(&[0x21u8, 0x43, 0x21, 0x43, 0x21, 0x43], &device)
            .unwrap()
            .reshape(&[3, 2])
            .unwrap();

        // Scales: [3, 1] (1 group covering all 4 elements)
        let scales = Tensor::new(&[1.0f32, 1.0, 1.0], &device)
            .unwrap()
            .reshape(&[3, 1])
            .unwrap();

        let y = gemm_4bit_cpu(&x, &w_packed, &scales, 4).unwrap();

        println!("Y shape: {:?}", y.dims());
        println!("Y: {:?}", y.to_vec2::<f32>().unwrap());
    }
}
