//! CPU Optimized Kernel for BitNet MatMul (CPU最適化BitNet行列積カーネル)
//!
//! このモジュールは、1.58ビット量子化重みを使用した行列積のCPU最適化実装を提供します。
//! AVX2/FMA命令を活用したSIMD最適化により、高速な推論を実現します。
//!
//! This module provides CPU-optimized matrix multiplication for 1.58-bit quantized weights.
//! It achieves fast inference through SIMD optimization using AVX2/FMA instructions.
//!
//! # Optimization Strategy / 最適化戦略
//!
//! 1. **Streaming Dequantization (ストリーミング逆量子化)**:
//!    重みを行単位でL1キャッシュに展開し、メモリ帯域を節約
//!
//! 2. **Branchless LUT (分岐なしルックアップテーブル)**:
//!    2ビットコードから係数へのマッピングを分岐なしで実行
//!    ```text
//!    00 -> 0.0, 01 -> 1.0, 10 -> -1.0, 11 -> 0.0
//!    ```
//!
//! 3. **Parallel Processing (並列処理)**:
//!    Rayonによる出力要素単位の並列化でマルチコア活用
//!
//! 4. **AVX2/FMA SIMD**:
//!    32重みを一度に処理、FMADDで積和演算を融合
//!
//! # Performance Notes / パフォーマンスノート
//!
//! - 入力サイズが小さい場合はスカラーフォールバックを使用
//! - AVX-512対応は将来の拡張として予定
//! - メモリバウンドな処理のため、キャッシュ効率が重要

use crate::error::BitTTTError;
use crate::kernels::packing::PackedTensor;
use candle_core::{Result, Tensor};
use rayon::prelude::*;

#[cfg(target_arch = "x86_64")]
use std::arch::x86_64::*;

/// CPU Optimized Kernel for BitNet MatMul.
///
/// BitNet行列積のためのCPU最適化カーネル。
/// AVX2/AVX-512対応時はSIMD命令を使用し、非対応時は自動ベクトル化ループにフォールバックします。
///
/// Uses explicit SIMD (AVX2/AVX-512) if available, or auto-vectorized loop as fallback.
#[derive(Debug, Clone)]
pub struct BitLinearCpu;

impl BitLinearCpu {
    /// Forward pass: Y = X @ W^T with streaming dequantization.
    ///
    /// 順伝播: ストリーミング逆量子化を用いた Y = X @ W^T。
    ///
    /// # Algorithm / アルゴリズム
    ///
    /// 1. 入力テンソルをフラット化して`Vec<f32>`に変換
    /// 2. パックされた重みをゼロコピーで参照
    /// 3. 出力要素ごとに並列処理（Rayon）
    /// 4. AVX2利用可能時は32要素ずつSIMD処理、残りはスカラー処理
    ///
    /// # Arguments / 引数
    /// - `input`: Input tensor of shape `[M, K]` (Float32) / 入力テンソル
    /// - `weights`: Packed weight tensor `[N, K/4]` (1.58-bit) / パック済み重みテンソル
    ///
    /// # Returns / 戻り値
    /// Output tensor of shape `[M, N]` (Float32) / 出力テンソル
    ///
    /// # Panics / パニック
    /// - Shape mismatch between input K and weight K / 入力と重みのK次元不一致
    /// - Weights not on CPU storage / 重みがCPUストレージ上にない
    pub fn forward(input: &Tensor, weights: &PackedTensor) -> Result<Tensor> {
        // Validation
        let (m, k) = input.dims2()?;
        let (n, k_w) = weights.shape.dims2()?;

        if k != k_w {
            return Err(BitTTTError::shape_mismatch(format!(
                "Input [{}, {}] vs Weight [{}, {}]",
                m, k, n, k_w
            ))
            .into());
        }

        // Multi-base mode: fall back to standard matmul with unpacked weights
        // This is slower but correct for multi-base quantization
        if weights.is_multibase() {
            let w_dequant = weights.unpack(&candle_core::Device::Cpu)?;
            let w_t = w_dequant.t()?;
            return input.matmul(&w_t);
        }

        // Single-base mode: use optimized streaming dequantization
        // This avoids allocating a huge full-float weight matrix.

        // 1. Flatten Input to Vec<f32>
        let x_vec = input.flatten_all()?.to_vec1::<f32>()?;

        // 2. Fetch Packed Weights (Zero-Copy!)
        // Access storage directly to avoid 16MB copy per call.
        let (w_storage, w_layout) = weights.data.storage_and_layout();
        let w_slice = match &*w_storage {
            candle_core::Storage::Cpu(storage) => storage.as_slice::<u8>()?,
            _ => {
                return Err(BitTTTError::storage_error(
                    "BitLinearCpu: Weights must be on CPU storage",
                )
                .into())
            }
        };

        if !w_layout.is_contiguous() {
            return Err(
                BitTTTError::storage_error("BitLinearCpu: Weights must be contiguous").into(),
            );
        }

        let output_len = m * n;
        let mut output = vec![0.0f32; output_len];

        // Branchless Optimization (LUT)
        // 00 -> 0.0
        // 01 -> 1.0
        // 10 -> -1.0
        // 11 -> 0.0
        const LUT: [f32; 4] = [0.0, 1.0, -1.0, 0.0];

        // Runtime check for AVX2
        #[cfg(target_arch = "x86_64")]
        let has_avx2 = is_x86_feature_detected!("avx2") && is_x86_feature_detected!("fma");
        #[cfg(not(target_arch = "x86_64"))]
        let has_avx2 = false;

        // Parallelize over all output elements (M * N)
        // This scales perfectly regardless of M or N sizes.

        // Note: x_vec and w_vec are read-only and shared across threads.
        // Rust's borrow checker allows this with Rayon.

        output
            .par_iter_mut()
            .enumerate()
            .for_each(|(global_idx, out_val)| {
                let i = global_idx / n; // Row Index (Batch)
                let j = global_idx % n; // Col Index (Output Feature)

                let mut sum = 0.0f32;
                let w_row_start = j * k.div_ceil(4);
                let x_row_start = i * k;

                // AVX2 Path
                let mut processed = 0;
                if has_avx2 {
                    // Process in chunks of 32 (128 bytes of X, 8 bytes of W)
                    // 32 weights = 64 bits = 8 bytes.
                    let chunk_size = 32;
                    let num_chunks = k / chunk_size;

                    // Unsafe block for AVX intrinsics
                    #[cfg(target_arch = "x86_64")]
                    unsafe {
                        sum += compute_row_avx2(
                            &x_vec[x_row_start..],
                            &w_slice[w_row_start..],
                            num_chunks,
                        );
                    }
                    processed = num_chunks * chunk_size;
                }

                // Remainder (Scalar Loop)
                for l in processed..k {
                    // Safety: We assume valid shapes from validation check.
                    // Using get_unchecked for max speed in inner loop.
                    let x_val = unsafe { *x_vec.get_unchecked(x_row_start + l) };

                    let byte_idx = l / 4;
                    let bit_idx = l % 4;

                    if w_row_start + byte_idx >= w_slice.len() {
                        break;
                    }
                    let byte = unsafe { *w_slice.get_unchecked(w_row_start + byte_idx) };

                    let code = (byte >> (bit_idx * 2)) & 0b11;

                    let coeff = unsafe { *LUT.get_unchecked(code as usize) };
                    sum += x_val * coeff;
                }
                *out_val = sum * weights.scale;
            });

        Tensor::from_vec(output, (m, n), &candle_core::Device::Cpu)
    }
}

/// Optimized horizontal sum for AVX2 __m256 register
///
/// AVX2レジスタの最適化された水平加算
///
/// # Algorithm / アルゴリズム
///
/// 段階的水平加算で効率的にスカラー値を取得:
/// 1. 256-bit → 128-bit: 上位128bitと下位128bitを加算
/// 2. 128-bit → 64-bit: movehl + add
/// 3. 64-bit → 32-bit: shuffle + add
/// 4. 最終スカラー抽出
///
/// This is more efficient than storing to memory and summing,
/// as it keeps values in registers throughout.
///
/// # Safety / 安全性
/// Requires AVX2 support. / AVX2サポートが必要
#[cfg(target_arch = "x86_64")]
#[target_feature(enable = "avx2")]
#[inline]
unsafe fn hsum256_ps(v: __m256) -> f32 {
    // Step 1: Extract high 128 bits and add to low 128 bits
    // 高位128bitを抽出し、低位128bitに加算
    let high = _mm256_extractf128_ps(v, 1);
    let low = _mm256_castps256_ps128(v);
    let sum128 = _mm_add_ps(high, low);

    // Step 2: Horizontal add within 128-bit register
    // [a, b, c, d] -> movehl gives [c, d, ?, ?]
    // add gives [a+c, b+d, ?, ?]
    // 128bitレジスタ内で水平加算
    let sum64 = _mm_add_ps(sum128, _mm_movehl_ps(sum128, sum128));

    // Step 3: Final horizontal add
    // shuffle gives [b+d, ?, ?, ?]
    // add gives [a+c+b+d, ?, ?, ?]
    // 最終水平加算
    let sum32 = _mm_add_ss(sum64, _mm_shuffle_ps(sum64, sum64, 1));

    // Step 4: Extract scalar result
    // スカラー結果を抽出
    _mm_cvtss_f32(sum32)
}

/// AVX2 Kernel: Processes K dimension in chunks of 32.
///
/// AVX2カーネル: K次元を32要素チャンクで処理。
///
/// # Algorithm / アルゴリズム
///
/// 各チャンク（32要素）について:
/// 1. 8バイト（32重み）をロード
/// 2. 2ビットコードを整数演算で係数に変換: `(code & 1) - (code >> 1)`
///    - 00 → 0, 01 → 1, 10 → -1, 11 → 0
/// 3. 8要素ずつYMMレジスタに展開
/// 4. FMADDで積和演算を実行
/// 5. 最後に最適化された水平加算で部分和を計算
///
/// # Phase 5.4 Optimization
/// Uses optimized `hsum256_ps` for horizontal sum instead of storing
/// to memory array. This keeps values in registers and reduces memory traffic.
///
/// # Arguments / 引数
/// - `x_ptr`: Pointer to input values (32 f32) / 入力値へのポインタ
/// - `w_ptr`: Pointer to packed weights (8 bytes = 32 weights) / パック済み重みへのポインタ
/// - `num_chunks`: Number of 32-element chunks to process / 処理する32要素チャンク数
///
/// # Returns / 戻り値
/// Partial sum from processing all chunks / 全チャンク処理の部分和
///
/// # Safety / 安全性
/// Caller must ensure AVX2/FMA support and valid pointers.
/// 呼び出し側はAVX2/FMAサポートと有効なポインタを保証する必要があります。
#[cfg(target_arch = "x86_64")]
#[target_feature(enable = "avx2", enable = "fma")]
unsafe fn compute_row_avx2(x_ptr: &[f32], w_ptr: &[u8], num_chunks: usize) -> f32 {
    let mut sum_vec = _mm256_setzero_ps();

    // Pointer Iteration
    let mut x_curr = x_ptr.as_ptr();
    let mut w_curr = w_ptr.as_ptr();

    for _ in 0..num_chunks {
        // Process 32 weights (8 bytes) in 4 iterations of 8 weights each
        // 32重み（8バイト）を8重みずつ4回のイテレーションで処理

        for _ in 0..4 {
            // 1. Load 2 bytes (8 weights)
            // 2バイト（8重み）をロード
            let w_val = *(w_curr as *const u16);
            w_curr = w_curr.add(2);

            // 2. Expand 2-bit codes to f32 coefficients
            // 2ビットコードをf32係数に展開
            // Using branchless arithmetic: coeff = (code & 1) - (code >> 1)
            // 分岐なし演算を使用: coeff = (code & 1) - (code >> 1)
            let mut coeffs = [0.0f32; 8];
            for (b, coeff) in coeffs.iter_mut().enumerate() {
                let shift = b * 2;
                let code = (w_val >> shift) & 0x03;
                let val = ((code & 1) as i32) - ((code >> 1) as i32);
                *coeff = val as f32;
            }
            let w_vec = _mm256_loadu_ps(coeffs.as_ptr());

            // 3. Load 8 Inputs
            // 8入力をロード
            let x_vec = _mm256_loadu_ps(x_curr);
            x_curr = x_curr.add(8);

            // 4. FMADD: sum_vec += x_vec * w_vec
            // 積和演算: sum_vec += x_vec * w_vec
            sum_vec = _mm256_fmadd_ps(x_vec, w_vec, sum_vec);
        }
    }

    // Optimized Horizontal Sum (Phase 5.4)
    // Uses register-only operations instead of memory store + scalar sum
    // 最適化水平加算（Phase 5.4）
    // メモリストア+スカラー加算の代わりにレジスタのみの演算を使用
    hsum256_ps(sum_vec)
}
