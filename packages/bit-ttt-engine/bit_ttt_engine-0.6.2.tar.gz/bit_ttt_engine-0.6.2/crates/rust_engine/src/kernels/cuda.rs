//! CUDA Kernels for BitLinear Operations
//!
//! This module provides GPU-accelerated kernels for 1.58-bit quantized matrix operations.
//!
//! # Kernel Modes / カーネルモード
//!
//! ## Legacy Path (Dequant + MatMul)
//! ```text
//! PackedTensor → unpack() → [full FP32 tensor] → matmul()
//! Memory: O(N*K) intermediate tensor
//! ```
//!
//! ## Fused Path (Adaptive Kernel) - Recommended
//! ```text
//! PackedTensor + adaptive_scales → single CUDA kernel → output
//! Memory: O(1) intermediate (on-the-fly dequantization)
//! ```
//!
//! # Performance Comparison / パフォーマンス比較
//!
//! | Mode | Memory Bandwidth | Latency | Recommended |
//! |------|-----------------|---------|-------------|
//! | Legacy | 2x (read packed + write dequant + read dequant) | Higher | No |
//! | Fused | 1x (read packed directly) | Lower | Yes |
//!
//! # Usage / 使用方法
//!
//! ```ignore
//! // Automatic routing based on PackedTensor configuration
//! let output = BitLinearCuda::forward(&input, &packed_weights)?;
//!
//! // If packed_weights has adaptive_scales → fused kernel (fast)
//! // If packed_weights has only scale → legacy path (fallback)
//! ```

use crate::error::BitTTTError;
use crate::kernels::packing::PackedTensor;
use candle_core::{Device, Result, Tensor};

#[cfg(feature = "cuda")]
use candle_core::cuda_backend::cudarc::driver::DevicePtr;
#[cfg(feature = "cuda")]
// use candle_core::backend::BackendStorage;
#[cfg(feature = "cuda")]
use candle_core::cuda_backend::cudarc::driver::{LaunchAsync, LaunchConfig};

// Compile time PTX embedding
#[cfg(feature = "cuda")]
const _BIT_OP_PTX: &str = include_str!(concat!(env!("OUT_DIR"), "/bit_op.ptx"));
#[cfg(feature = "cuda")]
const ADAPTIVE_PTX: &str = include_str!(concat!(env!("OUT_DIR"), "/adaptive_bit_op.ptx"));

/// CUDA-accelerated BitLinear layer implementation.
///
/// Provides two execution paths:
/// 1. **Fused kernel** (preferred): Single-pass dequant+matmul when adaptive_scales available
/// 2. **Legacy path** (fallback): Separate dequant then matmul
///
/// The `forward()` method automatically selects the optimal path based on
/// the PackedTensor configuration.
pub struct BitLinearCuda;

impl BitLinearCuda {
    /// Forward pass with automatic kernel selection.
    ///
    /// 自動カーネル選択による順伝播。
    ///
    /// # Automatic Routing / 自動ルーティング
    ///
    /// This method checks if the PackedTensor has `adaptive_scales` configured:
    /// - **If present**: Routes to fused kernel (`adaptive_forward`) for optimal performance
    /// - **If absent**: Falls back to legacy dequant+matmul path
    ///
    /// # Arguments / 引数
    /// - `input`: Input activations `[Batch, InDim]` (F32)
    /// - `weights`: Packed 1.58-bit weights with optional adaptive_scales
    ///
    /// # Returns / 戻り値
    /// Output tensor `[Batch, OutDim]` (F32)
    ///
    /// # Performance Tip / パフォーマンスのヒント
    ///
    /// For best performance, ensure weights have adaptive_scales:
    /// ```ignore
    /// let packed = PackedTensor::pack(&weights)?
    ///     .with_adaptive_scales(scales)?;
    /// let output = BitLinearCuda::forward(&input, &packed)?; // Uses fused kernel
    /// ```
    pub fn forward(
        input: &Tensor,         // [M, K]
        weights: &PackedTensor, // [N, K/4]
    ) -> Result<Tensor> {
        let (m, k) = input.dims2()?;
        let (n_out, k_w) = weights.shape.dims2()?;
        if k != k_w {
            return Err(BitTTTError::shape_mismatch(format!(
                "Input [{}, {}] vs Weight [{}, {}]",
                m, k, n_out, k_w
            ))
            .into());
        }

        let device = input.device();
        match device {
            Device::Cuda(dev) => {
                // === Fused kernel for multi-base weights ===
                #[cfg(feature = "cuda")]
                if let Some(ref scales) = weights.adaptive_scales {
                    // DEBUG: Log scales values
                    if let Ok(scales_vec) = scales.to_vec1::<f32>() {
                        tracing::debug!(
                            "🔥 [CUDA] forward: n_out={}, k={}, scales={:?}",
                            n_out,
                            k,
                            scales_vec
                        );
                    }

                    // DEBUG: Compare adaptive vs legacy path
                    static DEBUG_COMPARE: std::sync::atomic::AtomicBool =
                        std::sync::atomic::AtomicBool::new(true);
                    if DEBUG_COMPARE.swap(false, std::sync::atomic::Ordering::SeqCst) {
                        // Only compare once to avoid spam
                        let legacy_result = {
                            let w_dequant = weights.unpack(&Device::Cuda(dev.clone()))?;
                            // Log first 8 weights from unpacked data
                            if let Ok(w_flat) = w_dequant.flatten_all()?.to_vec1::<f32>() {
                                tracing::info!(
                                    "🔬 [DEBUG] Unpacked weights first 16: {:?}",
                                    &w_flat[..16.min(w_flat.len())]
                                );
                                // Check for non-zero values
                                let non_zero = w_flat.iter().filter(|&&x| x.abs() > 1e-6).count();
                                tracing::info!(
                                    "🔬 [DEBUG] Unpacked weights: {} non-zero out of {}",
                                    non_zero,
                                    w_flat.len()
                                );
                            }
                            let w_t = w_dequant.t()?;
                            input.matmul(&w_t)?
                        };
                        let adaptive_result =
                            Self::adaptive_forward(input, &weights.data, scales, n_out)?;

                        // Compare results
                        if let (Ok(leg), Ok(adp)) = (
                            legacy_result.flatten_all()?.to_vec1::<f32>(),
                            adaptive_result.flatten_all()?.to_vec1::<f32>(),
                        ) {
                            let diff: f32 = leg
                                .iter()
                                .zip(adp.iter())
                                .map(|(a, b)| (a - b).abs())
                                .sum::<f32>()
                                / leg.len() as f32;
                            tracing::info!(
                                "🔬 [DEBUG] Legacy first 8: {:?}",
                                &leg[..8.min(leg.len())]
                            );
                            tracing::info!(
                                "🔬 [DEBUG] Adaptive first 8: {:?}",
                                &adp[..8.min(adp.len())]
                            );
                            tracing::info!("🔬 [DEBUG] Mean absolute diff: {}", diff);
                        }
                        return Ok(adaptive_result);
                    }

                    return Self::adaptive_forward(input, &weights.data, scales, n_out);
                }

                // === Legacy fallback: dequant then matmul ===
                let w_dequant = weights.unpack(&Device::Cuda(dev.clone()))?;
                let w_t = w_dequant.t()?;
                let output = input.matmul(&w_t)?;
                Ok(output)
            }
            _ => Err(BitTTTError::device_error("BitLinearCuda called on non-CUDA device").into()),
        }
    }

    /// Legacy forward pass (always uses dequant+matmul).
    ///
    /// レガシー順伝播（常にdequant+matmulを使用）。
    ///
    /// Use this when you explicitly need the legacy behavior,
    /// or for debugging/comparison purposes.
    pub fn forward_legacy(input: &Tensor, weights: &PackedTensor) -> Result<Tensor> {
        let (m, k) = input.dims2()?;
        let (n_out, k_w) = weights.shape.dims2()?;
        if k != k_w {
            return Err(BitTTTError::shape_mismatch(format!(
                "Input [{}, {}] vs Weight [{}, {}]",
                m, k, n_out, k_w
            ))
            .into());
        }

        let device = input.device();
        match device {
            Device::Cuda(dev) => {
                let w_dequant = weights.unpack(&Device::Cuda(dev.clone()))?;
                let w_t = w_dequant.t()?;
                let output = input.matmul(&w_t)?;
                Ok(output)
            }
            _ => Err(BitTTTError::device_error("BitLinearCuda called on non-CUDA device").into()),
        }
    }

    /// Adaptive Fused Kernel - High-performance single-pass computation.
    ///
    /// 適応融合カーネル - 高性能シングルパス計算。
    ///
    /// # Performance Characteristics / パフォーマンス特性
    ///
    /// - **Memory**: No intermediate dequantized tensor allocation
    /// - **Bandwidth**: Reads packed weights directly, ~2x reduction
    /// - **Compute**: On-the-fly dequantization fused with matmul
    ///
    /// # When This Is Called / 呼び出しタイミング
    ///
    /// Automatically called by `forward()` when `PackedTensor.adaptive_scales` is set.
    /// Can also be called directly for explicit control.
    ///
    /// # Arguments / 引数
    /// - `input`: Input activations `[Batch, InDim]` (F32)
    /// - `weights`: Packed weight tensor `[n_bases * out_dim * in_dim/4]` (U8)
    ///              Layout: [base0_bytes][base1_bytes][base2_bytes] contiguous
    ///              Each byte: 4 weights as 2-bit codes (00=0, 01=+1, 10=-1)
    /// - `scales`: Per-base scale factors `[NumBases]` (F32)
    /// - `out_dim`: Output dimension (needed because weights is flattened)
    #[cfg(feature = "cuda")]
    pub fn adaptive_forward(
        input: &Tensor,   // [Batch, In] (F32)
        weights: &Tensor, // [n_bases * out_dim * in_dim/4] (U8, contiguous bases)
        scales: &Tensor,  // [NumBases] (F32)
        out_dim: usize,   // Output dimension
    ) -> Result<Tensor> {
        let (batch, in_dim) = input.dims2()?;

        let dev = match input.device() {
            Device::Cuda(d) => d,
            _ => {
                return Err(
                    BitTTTError::device_error("adaptive_forward called on non-CUDA device").into(),
                )
            }
        };

        // 1. Get raw pointers
        // Use scopes to drop ReadGuards immediately after getting pointers
        let inp_ptr = {
            let inp_storage = input.storage_and_layout().0;
            match &*inp_storage {
                candle_core::Storage::Cuda(s) => *s.as_cuda_slice::<f32>()?.device_ptr(),
                _ => return Err(BitTTTError::storage_error("Input must be CUDA F32").into()),
            }
        };

        let w_ptr = {
            let w_storage = weights.storage_and_layout().0;
            match &*w_storage {
                candle_core::Storage::Cuda(s) => *s.as_cuda_slice::<u8>()?.device_ptr(),
                _ => return Err(BitTTTError::storage_error("Weights must be CUDA U8").into()),
            }
        };
        let w_cu_ptr = w_ptr;

        let s_ptr = {
            let s_storage = scales.storage_and_layout().0;
            match &*s_storage {
                candle_core::Storage::Cuda(s) => *s.as_cuda_slice::<f32>()?.device_ptr(),
                _ => return Err(BitTTTError::storage_error("Scales must be CUDA F32").into()),
            }
        };

        // 2. Allocate Output
        let output = Tensor::zeros(
            (batch, out_dim),
            candle_core::DType::F32,
            &Device::Cuda(dev.clone()),
        )?;
        let out_ptr = {
            let out_storage = output.storage_and_layout().0;
            match &*out_storage {
                candle_core::Storage::Cuda(s) => *s.as_cuda_slice::<f32>()?.device_ptr(),
                _ => return Err(BitTTTError::storage_error("Output allocation failed").into()),
            }
        };

        // 3. Launch Kernel
        // Use Candle's internal CudaDevice to share the same CUDA context
        // (Previously DriverCudaDevice::new() created a separate context, causing CUDA_ERROR_ILLEGAL_ADDRESS)
        let module_name = "adaptive_gemm";
        let func_name = "adaptive_gemm_n3_kernel_f32";

        let core_dev = dev.cuda_device();

        core_dev
            .load_ptx(ADAPTIVE_PTX.into(), module_name, &[func_name])
            .map_err(candle_core::Error::wrap)?;

        let f = core_dev
            .get_func(module_name, func_name)
            .ok_or_else(|| BitTTTError::kernel_error(format!("Kernel '{}' not found", func_name)))
            .map_err(|e| candle_core::Error::Msg(e.to_string()))?;

        let block_dim = 256;
        let grid_x = (out_dim as u32 + block_dim - 1) / block_dim;
        let grid_y = batch as u32;

        let cfg = LaunchConfig {
            grid_dim: (grid_x, grid_y, 1),
            block_dim: (block_dim, 1, 1),
            shared_mem_bytes: 0,
        };

        // DEBUG: Log kernel parameters
        tracing::debug!(
            "🔥 [CUDA] adaptive_forward: batch={}, in_dim={}, out_dim={}, grid=({},{}), block={}",
            batch,
            in_dim,
            out_dim,
            grid_x,
            grid_y,
            block_dim
        );

        let params = (
            inp_ptr,  // X
            w_cu_ptr, // W (Packed)
            s_ptr,    // Scales
            out_ptr,  // Y
            batch as i32,
            in_dim as i32,
            out_dim as i32,
        );

        unsafe { f.launch(cfg, params) }.map_err(candle_core::Error::wrap)?;

        // Note: Removed explicit synchronize() - CUDA synchronizes automatically
        // when tensor data is accessed

        Ok(output)
    }

    #[cfg(not(feature = "cuda"))]
    pub fn adaptive_forward(
        _input: &Tensor,
        _weights: &Tensor,
        _scales: &Tensor,
        _out_dim: usize,
    ) -> Result<Tensor> {
        Err(BitTTTError::feature_not_enabled("CUDA (feature 'cuda' missing)").into())
    }

    pub fn smoke_test_compile() -> bool {
        #[cfg(feature = "cuda")]
        return !ADAPTIVE_PTX.is_empty();
        #[cfg(not(feature = "cuda"))]
        return false;
    }
}
