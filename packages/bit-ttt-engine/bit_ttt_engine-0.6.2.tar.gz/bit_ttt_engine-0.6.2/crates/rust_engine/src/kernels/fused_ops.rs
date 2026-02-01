//! Fused CUDA Kernels for LLM Inference
//!
//! Provides optimized CUDA implementations for:
//! - RMSNorm
//! - Softmax
//! - RoPE (Rotary Position Embedding)
//! - SiLU activation
//! - Fused SiLU * multiply

#[cfg(feature = "cuda")]
use candle_core::cuda_backend::cudarc::driver::{DevicePtr, LaunchAsync, LaunchConfig};
#[cfg(feature = "cuda")]
use candle_core::cuda_backend::WrapErr;
#[cfg(feature = "cuda")]
use candle_core::Device;
use candle_core::{DType, Result, Tensor};
#[cfg(feature = "cuda")]
use std::sync::OnceLock;

#[cfg(feature = "cuda")]
const FUSED_OPS_PTX: &str = include_str!(concat!(env!("OUT_DIR"), "/fused_ops.ptx"));

#[cfg(feature = "cuda")]
static FUSED_OPS_LOADED: OnceLock<std::sync::Mutex<std::collections::HashSet<usize>>> =
    OnceLock::new();

#[cfg(feature = "cuda")]
fn ensure_fused_ops_loaded(
    cuda_dev: &std::sync::Arc<candle_core::cuda_backend::cudarc::driver::CudaDevice>,
    device_id: usize,
) -> Result<()> {
    let loaded =
        FUSED_OPS_LOADED.get_or_init(|| std::sync::Mutex::new(std::collections::HashSet::new()));
    let mut guard = loaded.lock().unwrap();

    if !guard.contains(&device_id) {
        cuda_dev
            .load_ptx(
                FUSED_OPS_PTX.into(),
                "fused_ops",
                &[
                    "rms_norm_kernel_f32",
                    "softmax_kernel_f32",
                    "rope_kernel_f32",
                    "silu_kernel_f32",
                    "fused_silu_mul_kernel_f32",
                ],
            )
            .w()?;
        guard.insert(device_id);
        tracing::info!("Loaded fused_ops PTX for device {}", device_id);
    }

    Ok(())
}

/// RMSNorm using CUDA kernel
///
/// y = x * weight / sqrt(mean(x^2) + eps)
#[cfg(feature = "cuda")]
pub fn rms_norm_cuda(x: &Tensor, weight: &Tensor, eps: f64) -> Result<Tensor> {
    let dev = match x.device() {
        Device::Cuda(dev) => dev.clone(),
        _ => return rms_norm_cpu(x, weight, eps),
    };

    let cuda_dev = dev.cuda_device();
    ensure_fused_ops_loaded(&cuda_dev, dev.ordinal())?;

    let dims = x.dims();
    let hidden_dim = dims[dims.len() - 1];
    let n_elements: usize = dims[..dims.len() - 1].iter().product();

    let x_f32 = x.to_dtype(DType::F32)?.contiguous()?;
    let weight_f32 = weight.to_dtype(DType::F32)?.contiguous()?;

    let x_ptr = {
        let storage = x_f32.storage_and_layout().0;
        match &*storage {
            candle_core::Storage::Cuda(s) => *s.as_cuda_slice::<f32>()?.device_ptr(),
            _ => return Err(candle_core::Error::Msg("X must be CUDA tensor".to_string())),
        }
    };

    let weight_ptr = {
        let storage = weight_f32.storage_and_layout().0;
        match &*storage {
            candle_core::Storage::Cuda(s) => *s.as_cuda_slice::<f32>()?.device_ptr(),
            _ => {
                return Err(candle_core::Error::Msg(
                    "Weight must be CUDA tensor".to_string(),
                ))
            }
        }
    };

    let output = Tensor::zeros(x.dims(), DType::F32, &Device::Cuda(dev.clone()))?;
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

    let func = cuda_dev
        .get_func("fused_ops", "rms_norm_kernel_f32")
        .ok_or_else(|| candle_core::Error::Msg("Failed to get rms_norm kernel".to_string()))?;

    let block_size = 256u32;
    let cfg = LaunchConfig {
        grid_dim: (n_elements as u32, 1, 1),
        block_dim: (block_size, 1, 1),
        shared_mem_bytes: 0,
    };

    let params = (
        x_ptr,
        weight_ptr,
        out_ptr,
        hidden_dim as i32,
        eps as f32,
        n_elements as i32,
    );

    unsafe { func.launch(cfg, params) }.w()?;

    output.to_dtype(x.dtype())
}

#[cfg(not(feature = "cuda"))]
pub fn rms_norm_cuda(x: &Tensor, weight: &Tensor, eps: f64) -> Result<Tensor> {
    rms_norm_cpu(x, weight, eps)
}

/// CPU fallback for RMSNorm
pub fn rms_norm_cpu(x: &Tensor, weight: &Tensor, eps: f64) -> Result<Tensor> {
    let x_f32 = x.to_dtype(DType::F32)?;
    let dim = x_f32.rank() - 1;
    let hidden_size = x_f32.dim(dim)?;

    let norm_x = (x_f32.sqr()?.sum_keepdim(dim)? / (hidden_size as f64))?;
    let x_normed = x_f32.broadcast_div(&(norm_x + eps)?.sqrt()?)?;

    let weight_f32 = weight
        .to_dtype(DType::F32)?
        .broadcast_as(x_normed.shape())?;
    let result = (x_normed * weight_f32)?;

    result.to_dtype(x.dtype())
}

/// Softmax on last dimension using CUDA kernel
#[cfg(feature = "cuda")]
pub fn softmax_cuda(x: &Tensor) -> Result<Tensor> {
    let dev = match x.device() {
        Device::Cuda(dev) => dev.clone(),
        _ => return softmax_cpu(x),
    };

    let cuda_dev = dev.cuda_device();
    ensure_fused_ops_loaded(&cuda_dev, dev.ordinal())?;

    let dims = x.dims();
    let last_dim = dims[dims.len() - 1];
    let n_rows: usize = dims[..dims.len() - 1].iter().product();

    let x_f32 = x.to_dtype(DType::F32)?.contiguous()?;

    let x_ptr = {
        let storage = x_f32.storage_and_layout().0;
        match &*storage {
            candle_core::Storage::Cuda(s) => *s.as_cuda_slice::<f32>()?.device_ptr(),
            _ => return Err(candle_core::Error::Msg("X must be CUDA tensor".to_string())),
        }
    };

    let output = Tensor::zeros(x.dims(), DType::F32, &Device::Cuda(dev.clone()))?;
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

    let func = cuda_dev
        .get_func("fused_ops", "softmax_kernel_f32")
        .ok_or_else(|| candle_core::Error::Msg("Failed to get softmax kernel".to_string()))?;

    let block_size = 256u32;
    let cfg = LaunchConfig {
        grid_dim: (n_rows as u32, 1, 1),
        block_dim: (block_size, 1, 1),
        shared_mem_bytes: 0,
    };

    let params = (x_ptr, out_ptr, last_dim as i32, n_rows as i32);

    unsafe { func.launch(cfg, params) }.w()?;

    output.to_dtype(x.dtype())
}

#[cfg(not(feature = "cuda"))]
pub fn softmax_cuda(x: &Tensor) -> Result<Tensor> {
    softmax_cpu(x)
}

/// CPU fallback for softmax
pub fn softmax_cpu(x: &Tensor) -> Result<Tensor> {
    use candle_core::D;
    let max = x.max_keepdim(D::Minus1)?;
    let exp = (x.broadcast_sub(&max))?.exp()?;
    let sum = exp.sum_keepdim(D::Minus1)?;
    exp.broadcast_div(&sum)
}

/// SiLU activation using CUDA kernel
#[cfg(feature = "cuda")]
pub fn silu_cuda(x: &Tensor) -> Result<Tensor> {
    let dev = match x.device() {
        Device::Cuda(dev) => dev.clone(),
        _ => return candle_nn::ops::silu(x),
    };

    let cuda_dev = dev.cuda_device();
    ensure_fused_ops_loaded(&cuda_dev, dev.ordinal())?;

    let n_elements = x.elem_count();
    let x_f32 = x.to_dtype(DType::F32)?.contiguous()?;

    let x_ptr = {
        let storage = x_f32.storage_and_layout().0;
        match &*storage {
            candle_core::Storage::Cuda(s) => *s.as_cuda_slice::<f32>()?.device_ptr(),
            _ => return Err(candle_core::Error::Msg("X must be CUDA tensor".to_string())),
        }
    };

    let output = Tensor::zeros(x.dims(), DType::F32, &Device::Cuda(dev.clone()))?;
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

    let func = cuda_dev
        .get_func("fused_ops", "silu_kernel_f32")
        .ok_or_else(|| candle_core::Error::Msg("Failed to get silu kernel".to_string()))?;

    let block_size = 256u32;
    let grid_size = (n_elements as u32 + block_size - 1) / block_size;
    let cfg = LaunchConfig {
        grid_dim: (grid_size, 1, 1),
        block_dim: (block_size, 1, 1),
        shared_mem_bytes: 0,
    };

    let params = (x_ptr, out_ptr, n_elements as i32);

    unsafe { func.launch(cfg, params) }.w()?;

    output.to_dtype(x.dtype())
}

#[cfg(not(feature = "cuda"))]
pub fn silu_cuda(x: &Tensor) -> Result<Tensor> {
    candle_nn::ops::silu(x)
}

/// Fused SiLU(gate) * up using CUDA kernel
#[cfg(feature = "cuda")]
pub fn fused_silu_mul_cuda(gate: &Tensor, up: &Tensor) -> Result<Tensor> {
    let dev = match gate.device() {
        Device::Cuda(dev) => dev.clone(),
        _ => {
            let silu_gate = candle_nn::ops::silu(gate)?;
            return silu_gate.mul(up);
        }
    };

    let cuda_dev = dev.cuda_device();
    ensure_fused_ops_loaded(&cuda_dev, dev.ordinal())?;

    let n_elements = gate.elem_count();
    let gate_f32 = gate.to_dtype(DType::F32)?.contiguous()?;
    let up_f32 = up.to_dtype(DType::F32)?.contiguous()?;

    let gate_ptr = {
        let storage = gate_f32.storage_and_layout().0;
        match &*storage {
            candle_core::Storage::Cuda(s) => *s.as_cuda_slice::<f32>()?.device_ptr(),
            _ => {
                return Err(candle_core::Error::Msg(
                    "Gate must be CUDA tensor".to_string(),
                ))
            }
        }
    };

    let up_ptr = {
        let storage = up_f32.storage_and_layout().0;
        match &*storage {
            candle_core::Storage::Cuda(s) => *s.as_cuda_slice::<f32>()?.device_ptr(),
            _ => {
                return Err(candle_core::Error::Msg(
                    "Up must be CUDA tensor".to_string(),
                ))
            }
        }
    };

    let output = Tensor::zeros(gate.dims(), DType::F32, &Device::Cuda(dev.clone()))?;
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

    let func = cuda_dev
        .get_func("fused_ops", "fused_silu_mul_kernel_f32")
        .ok_or_else(|| {
            candle_core::Error::Msg("Failed to get fused_silu_mul kernel".to_string())
        })?;

    let block_size = 256u32;
    let grid_size = (n_elements as u32 + block_size - 1) / block_size;
    let cfg = LaunchConfig {
        grid_dim: (grid_size, 1, 1),
        block_dim: (block_size, 1, 1),
        shared_mem_bytes: 0,
    };

    let params = (gate_ptr, up_ptr, out_ptr, n_elements as i32);

    unsafe { func.launch(cfg, params) }.w()?;

    output.to_dtype(gate.dtype())
}

#[cfg(not(feature = "cuda"))]
pub fn fused_silu_mul_cuda(gate: &Tensor, up: &Tensor) -> Result<Tensor> {
    let silu_gate = candle_nn::ops::silu(gate)?;
    silu_gate.mul(up)
}
