//! AdaptiveBitLinear - Optimized Loading with Rayon & LUT

use super::{BitLinear, Linear4Bit};
use crate::error::BitTTTError;
use crate::model::config::QuantizationConfig;
use candle_core::{Device, Result, Tensor};
use candle_nn::VarBuilder;
use rayon::prelude::*; // 並列処理用
use std::collections::HashMap;
use tracing::{info, warn};

// 🔥 高速化の要: 0-255 のバイト値を 4つのf32値に変換する「カンニングペーパー」
// 計算を一切せず、メモリから値を拾うだけにします。
static UNPACK_LUT: [[f32; 4]; 256] = {
    let mut table = [[0.0; 4]; 256];
    let mut i = 0;
    while i < 256 {
        let byte = i as u8;
        let mut j = 0;
        while j < 4 {
            // 2bit: 00=0, 01=1, 10=-1, 11=0
            let val = (byte >> (j * 2)) & 0b11;
            table[i][j] = match val {
                1 => 1.0,
                2 => -1.0,
                _ => 0.0,
            };
            j += 1;
        }
        i += 1;
    }
    table
};

#[derive(Clone)]
pub struct AdaptiveBitLinear {
    pub legacy_linear: Option<BitLinear>,
    pub linear_4bit: Option<Linear4Bit>,
    pub reconstructed_weight: Option<Tensor>,
    pub in_features: usize,
    pub out_features: usize,
}

impl AdaptiveBitLinear {
    /// Load from pre-loaded Bit-TTT tensors (weight_packed + scales).
    ///
    /// 事前ロード済みのBit-TTTテンソル（weight_packed + scales）からロードします。
    ///
    /// This is the recommended way to load quantized models, as it avoids
    /// VarBuilder dtype issues with U8 tensors.
    ///
    /// # Arguments / 引数
    /// - `weight_packed`: Packed weights `[out_dim, in_dim/4]` or `[out_dim, in_dim/4, n_bases]` as U8
    /// - `scales`: Per-base scales `[n_bases]` as F32
    /// - `device`: Target device (CPU/CUDA) / ターゲットデバイス
    pub fn from_packed_tensors(
        weight_packed: &Tensor,
        scales: &Tensor,
        device: &Device,
    ) -> Result<Self> {
        // Delegate to BitLinear::from_packed_tensors
        let bit_linear = BitLinear::from_packed_tensors(weight_packed, scales, device)?;

        let in_features = bit_linear.in_features;
        let out_features = bit_linear.out_features;

        Ok(Self {
            legacy_linear: Some(bit_linear),
            linear_4bit: None,
            reconstructed_weight: None,
            in_features,
            out_features,
        })
    }

    /// Load directly from pre-loaded tensor HashMap (bypasses VarBuilder).
    ///
    /// 事前ロードしたテンソルHashMapから直接ロードします（VarBuilderをバイパス）。
    /// これにより、U8テンソルのF32変換を回避し、ロード時間を短縮します。
    ///
    /// # Arguments / 引数
    /// - `tensors`: Pre-loaded tensors from `candle_core::safetensors::load()`
    /// - `prefix`: Layer prefix (e.g., "model.layers.0.mlp.gate_proj")
    /// - `in_dim`: Input dimension / 入力次元
    /// - `out_dim`: Output dimension / 出力次元
    /// - `device`: Target device / ターゲットデバイス
    /// - `quantization`: Quantization configuration (for 4-bit support) / 量子化設定（4bit対応用）
    pub fn load_direct(
        tensors: &HashMap<String, Tensor>,
        prefix: &str,
        in_dim: usize,
        out_dim: usize,
        device: &Device,
        quantization: &Option<QuantizationConfig>,
    ) -> Result<Self> {
        let packed_key = format!("{}.weight_packed", prefix);
        let scales_key = format!("{}.scales", prefix);
        let weight_key = format!("{}.weight", prefix);
        let weight_4bit_key = format!("{}.weight_4bit", prefix);
        let scales_4bit_key = format!("{}.scales_4bit", prefix);

        // 1. Try 4-bit format first (int4 quantized) if configured
        if let Some(quant_cfg) = quantization {
            if quant_cfg.quant_type == "int4" {
                if let (Some(_weight_4bit), Some(_scales_4bit)) =
                    (tensors.get(&weight_4bit_key), tensors.get(&scales_4bit_key))
                {
                    info!(
                        "🚀 [DIRECT-LOAD] 4-bit quantized: {}x{} (int4 format, group_size={})",
                        in_dim, out_dim, quant_cfg.group_size
                    );
                    let linear_4bit = Linear4Bit::load_direct(
                        tensors,
                        prefix,
                        in_dim,
                        out_dim,
                        quant_cfg.group_size,
                        quant_cfg.symmetric,
                        device,
                    )?;
                    return Ok(Self {
                        legacy_linear: None,
                        linear_4bit: Some(linear_4bit),
                        reconstructed_weight: None,
                        in_features: in_dim,
                        out_features: out_dim,
                    });
                } else {
                    warn!(
                        "⚠️ [DIRECT-LOAD] 4-bit quantization configured but weight files not found for {}",
                        prefix
                    );
                }
            }
        }

        // 2. Try packed format (Bit-TTT quantized)
        if let (Some(packed), Some(scales)) = (tensors.get(&packed_key), tensors.get(&scales_key)) {
            // Verify U8 dtype is preserved (no conversion needed!)
            let dtype = packed.dtype();
            if dtype == candle_core::DType::U8 {
                info!(
                    "🚀 [DIRECT-LOAD] U8 preserved: {}x{} (no F32→U8 conversion!)",
                    in_dim, out_dim
                );
            } else {
                warn!(
                    "⚠️ [DIRECT-LOAD] Unexpected dtype {:?} for weight_packed at {}",
                    dtype, packed_key
                );
            }
            return Self::from_packed_tensors(packed, scales, device);
        }

        // 3. Try legacy format (FP32/FP16 weights)
        if let Some(weight) = tensors.get(&weight_key) {
            info!(
                "📦 [DIRECT-LOAD] Legacy weight: {}x{} (FP format)",
                in_dim, out_dim
            );
            let bit_linear = BitLinear::from_weight_tensor(weight, in_dim, out_dim, device)?;
            return Ok(Self {
                legacy_linear: Some(bit_linear),
                linear_4bit: None,
                reconstructed_weight: None,
                in_features: in_dim,
                out_features: out_dim,
            });
        }

        Err(BitTTTError::storage_error(format!(
            "No supported weight format found for prefix: {}",
            prefix
        ))
        .into())
    }

    pub fn load(in_dim: usize, out_dim: usize, vb: VarBuilder, device: &Device) -> Result<Self> {
        // 1. Try weight_packed format first (Bit-TTT converter output)
        // Check if weight_packed exists using contains_tensor
        if vb.contains_tensor("weight_packed") {
            // weight_packed exists, try to load with various n_bases
            for n_bases in 1..=8usize {
                let packed_shape: Vec<usize> = if n_bases == 1 {
                    vec![out_dim, in_dim / 4]
                } else {
                    vec![out_dim, in_dim / 4, n_bases]
                };

                // Try to load weight_packed + scales
                let packed_result = vb.get(packed_shape.as_slice(), "weight_packed");
                let scales_result = vb.get(&[n_bases], "scales");

                if let (Ok(packed), Ok(scales)) = (packed_result, scales_result) {
                    info!(
                        "🚀 [PACKED-LOAD] Loading layer via PackedTensor: {}x{} (n_bases={})",
                        in_dim, out_dim, n_bases
                    );
                    return Self::from_packed_tensors(&packed, &scales, device);
                }
            }
            // weight_packed exists but couldn't load - log warning
            warn!(
                "⚠️ weight_packed tensor found but failed to load (in={}, out={})",
                in_dim, out_dim
            );
        }

        // 2. レガシー (BitNet FP16/FP32 weight) の確認
        if let Ok(linear) = BitLinear::load(in_dim, out_dim, vb.clone(), device) {
            return Ok(Self {
                legacy_linear: Some(linear),
                linear_4bit: None,
                reconstructed_weight: None,
                in_features: in_dim,
                out_features: out_dim,
            });
        }

        // 3. Adaptive Format (Bit-TTT with Rayon+LUT reconstruction) - Fallback
        for num_bases in 1..=8 {
            if let Ok(scales) = vb.get((num_bases,), "scales") {
                let packed = vb.get((out_dim, in_dim / 4, num_bases), "weight_packed")?;

                // CPUに一度持ってくる
                let packed_cpu = packed.to_device(&Device::Cpu)?;
                let scales_cpu = scales.to_device(&Device::Cpu)?;

                info!(
                    "🚀 [FAST-LOAD] Loading layer: {}x{} (bases={})",
                    in_dim, out_dim, num_bases
                );

                // 生データを取得 (Type agnostic handling)
                let packed_dtype = packed_cpu.dtype();
                let packed_vec = match packed_dtype {
                    candle_core::DType::U8 => packed_cpu.flatten_all()?.to_vec1::<u8>()?,
                    candle_core::DType::F32 => {
                        warn!("⚠️ [FAST-LOAD] Converting F32 packed weights to U8 (Legacy Model Format)");
                        // Use Candle's native cast (optimized)
                        packed_cpu
                            .to_dtype(candle_core::DType::U8)?
                            .flatten_all()?
                            .to_vec1::<u8>()?
                    }
                    _ => {
                        return Err(BitTTTError::device_error(format!(
                            "Unexpected dtype for weight_packed: {:?}",
                            packed_dtype
                        ))
                        .into())
                    }
                };

                let scales_vec = scales_cpu.to_vec1::<f32>()?;

                // 🚀 【ここが高速化の核心】
                // Rayonを使って「行ごと」に並列処理で解凍・再構築する
                let packed_row_stride = (in_dim / 4) * num_bases;

                let rows: Vec<Vec<f32>> = (0..out_dim)
                    .into_par_iter()
                    .map(|row_idx| {
                        let mut row_w = vec![0.0f32; in_dim];
                        let row_start = row_idx * packed_row_stride;

                        for (base, scale) in scales_vec.iter().enumerate().take(num_bases) {
                            let scale = *scale;

                            for col_pack in 0..(in_dim / 4) {
                                // LUTを使って一瞬で値を取得
                                let flat_idx = row_start + (col_pack * num_bases) + base;
                                let byte_val = packed_vec[flat_idx];
                                let vals = UNPACK_LUT[byte_val as usize];

                                // 加算
                                let out_col_base = col_pack * 4;
                                row_w[out_col_base] += vals[0] * scale;
                                row_w[out_col_base + 1] += vals[1] * scale;
                                row_w[out_col_base + 2] += vals[2] * scale;
                                row_w[out_col_base + 3] += vals[3] * scale;
                            }
                        }
                        row_w
                    })
                    .collect();

                // 結合してTensor化
                let final_flat: Vec<f32> = rows.into_iter().flatten().collect();
                let w_recon = Tensor::from_vec(final_flat, (out_dim, in_dim), device)?;

                return Ok(Self {
                    legacy_linear: None,
                    linear_4bit: None,
                    reconstructed_weight: Some(w_recon),
                    in_features: in_dim,
                    out_features: out_dim,
                });
            }
        }

        // Debug: Log what we tried
        eprintln!(
            "❌ [ADAPTIVE-LOAD] Failed for layer {}x{}: \
             weight_packed={}, weight={}, scales_found={}",
            in_dim,
            out_dim,
            vb.contains_tensor("weight_packed"),
            vb.contains_tensor("weight"),
            vb.contains_tensor("scales")
        );

        Err(BitTTTError::storage_error(
            "Failed to load layer: neither legacy nor adaptive weights found",
        )
        .into())
    }

    pub fn forward(&self, x: &Tensor) -> Result<Tensor> {
        if let Some(linear) = &self.legacy_linear {
            return linear.forward(x);
        }
        if let Some(linear_4bit) = &self.linear_4bit {
            return linear_4bit.forward(x);
        }
        if let Some(w_recon) = &self.reconstructed_weight {
            // 入力次元の調整 [Batch, Seq, In] -> [Batch*Seq, In]
            let (x_flat, original_shape) = if x.rank() == 3 {
                let (b, s, _) = x.dims3()?;
                (x.flatten(0, 1)?, Some((b, s)))
            } else {
                (x.clone(), None)
            };

            // デバイス整合性チェックと移動
            let w = if w_recon.device().same_device(x_flat.device()) {
                w_recon.clone()
            } else {
                // ここで転送ログを出すとうるさいので、必要な時だけにする
                w_recon.to_device(x_flat.device())?
            };

            let result = x_flat.matmul(&w.t()?)?;

            if let Some((b, s)) = original_shape {
                let (_, out_d) = result.dims2()?;
                return result.reshape((b, s, out_d));
            }
            return Ok(result);
        }
        Err(
            BitTTTError::device_error("AdaptiveBitLinear: Invalid State - no weights loaded")
                .into(),
        )
    }

    pub fn precompute_packed(&mut self) -> Result<()> {
        if let Some(linear) = &mut self.legacy_linear {
            linear.precompute_packed()?;
        }
        // Note: Linear4Bit doesn't need precompute_packed as it stores weights pre-packed
        Ok(())
    }
}
