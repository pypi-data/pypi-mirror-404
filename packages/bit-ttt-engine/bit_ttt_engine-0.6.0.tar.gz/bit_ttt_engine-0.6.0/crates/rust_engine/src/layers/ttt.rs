//! TTTLayer - Test-Time Training with Online Learning
//!
//! TTTLayerは、Test-Time Training（推論時学習）を実装したアテンション代替層です。
//! 従来のTransformerのSelf-Attentionを、オンライン勾配降下法による
//! 動的な重み更新メカニズムに置き換えます。
//!
//! This module implements Test-Time Training (TTT), an attention alternative layer.
//! It replaces traditional Transformer Self-Attention with a dynamic weight update
//! mechanism using online gradient descent.
//!
//! # Key Concepts / 主要概念
//!
//! - **Inner Loop (内部ループ)**: 各トークンで重み行列Wを勾配降下で更新
//! - **Self-Supervised (自己教師あり)**: 入力特徴量を再構成する損失で学習
//! - **Linear Complexity (線形計算量)**: Attention O(n²) → TTT O(n)
//!
//! # Algorithm / アルゴリズム
//!
//! ```text
//! for each token x_t:
//!     feat = proj_down(x_t)           # 次元削減
//!     feat_norm = L2_normalize(feat)  # 正規化
//!     pred = W @ feat_norm            # 予測
//!     loss = ||pred - feat_norm||²    # 再構成損失
//!     W = W - lr * grad(loss)         # オンライン更新
//!     out = proj_up(pred)             # 次元復元
//! ```
//!
//! # References / 参考文献
//!
//! - "Learning to (Learn at Test Time): RNNs with Expressive Hidden States" (Sun et al., 2024)

use candle_core::{Result, Tensor};
use candle_nn::VarBuilder;
use std::collections::HashMap;

use super::AdaptiveBitLinear;

/// Epsilon for TTT layer normalization to prevent division by zero.
///
/// L2正規化時のゼロ除算を防ぐための微小値。
const TTT_NORM_EPS: f32 = 1e-6;

/// Test-Time Training layer with online gradient descent.
///
/// オンライン勾配降下法によるTest-Time Training層。
/// 隠れ状態として学習可能な重み行列を持ち、推論時に動的に更新します。
///
/// # Fields / フィールド
///
/// - `hidden_dim`: Model hidden dimension / モデル隠れ次元
/// - `d_small`: Compressed dimension (hidden_dim / 4) / 圧縮次元
/// - `proj_down`: Projection to lower dimension / 低次元への射影
/// - `proj_up`: Projection back to hidden dimension / 隠れ次元への復元
/// - `inner_lr`: Learning rate for online updates / オンライン更新の学習率
pub struct TTTLayer {
    /// Hidden dimension size (retained for introspection/debugging)
    #[allow(dead_code)]
    pub hidden_dim: usize,
    /// Compressed dimension size (retained for introspection/debugging)
    #[allow(dead_code)]
    pub d_small: usize,
    pub proj_down: AdaptiveBitLinear,
    pub proj_up: AdaptiveBitLinear,
    pub inner_lr: f64,
}

impl TTTLayer {
    /// Load directly from pre-loaded tensor HashMap (bypasses VarBuilder).
    pub fn load_direct(
        tensors: &HashMap<String, Tensor>,
        prefix: &str,
        hidden_dim: usize,
        inner_lr: f64,
        device: &candle_core::Device,
        quantization: &Option<crate::model::config::QuantizationConfig>,
    ) -> Result<Self> {
        let d_small = hidden_dim / 4;
        Ok(Self {
            hidden_dim,
            d_small,
            proj_down: AdaptiveBitLinear::load_direct(
                tensors,
                &format!("{}.down", prefix),
                hidden_dim,
                d_small,
                device,
                quantization,
            )?,
            proj_up: AdaptiveBitLinear::load_direct(
                tensors,
                &format!("{}.up", prefix),
                d_small,
                hidden_dim,
                device,
                quantization,
            )?,
            inner_lr,
        })
    }

    /// Load TTTLayer from checkpoint.
    ///
    /// チェックポイントからTTTLayerをロードします。
    ///
    /// # Arguments / 引数
    /// - `hidden_dim`: Hidden dimension of the model / モデルの隠れ次元
    /// - `inner_lr`: Learning rate for online weight updates / オンライン重み更新の学習率
    /// - `vb`: VarBuilder for loading projection weights / 射影重みロード用VarBuilder
    /// - `device`: Target device (CPU/CUDA) / ターゲットデバイス
    ///
    /// # Notes / 備考
    /// `d_small` is automatically set to `hidden_dim / 4` for memory efficiency.
    /// `d_small`はメモリ効率のため自動的に`hidden_dim / 4`に設定されます。
    pub fn load(
        hidden_dim: usize,
        inner_lr: f64,
        vb: VarBuilder,
        device: &candle_core::Device,
    ) -> Result<Self> {
        let d_small = hidden_dim / 4;
        Ok(Self {
            hidden_dim,
            d_small,
            proj_down: AdaptiveBitLinear::load(hidden_dim, d_small, vb.pp("down"), device)?,
            proj_up: AdaptiveBitLinear::load(d_small, hidden_dim, vb.pp("up"), device)?,
            inner_lr,
        })
    }

    /// Pre-pack projection weights for optimized inference.
    ///
    /// 射影重みを最適化推論用にpre-packします。
    /// `proj_down`と`proj_up`の両方のBitLinear層をパッキングします。
    pub fn precompute_packed(&mut self) -> Result<()> {
        self.proj_down.precompute_packed()?;
        self.proj_up.precompute_packed()?;
        Ok(())
    }

    /// Sequential forward with weight update (token-by-token processing).
    ///
    /// 逐次的な順伝播と重み更新（トークン単位処理）。
    ///
    /// This is the core TTT algorithm: for each token, predict using current weights,
    /// compute reconstruction loss, and update weights via gradient descent.
    ///
    /// TTTの中核アルゴリズム: 各トークンについて、現在の重みで予測し、
    /// 再構成損失を計算し、勾配降下で重みを更新します。
    ///
    /// # Arguments / 引数
    /// - `w_state`: Current weight state `(B, D_small, D_small)` or `(D_small, D_small)`
    /// - `x_t`: Input token `(B, Hidden)` or `(Hidden)`
    ///
    /// # Returns / 戻り値
    /// - `(output, w_new)`: Output features and updated weight state
    ///   - `output`: `(B, Hidden)` - Transformed features / 変換された特徴量
    ///   - `w_new`: Updated weight matrix / 更新された重み行列
    ///
    /// # Performance Notes / パフォーマンス備考
    /// - `unsqueeze`/`squeeze` are view operations (no memory copy) / ビュー操作（メモリコピーなし）
    /// - Gradient computation uses outer product: grad = diff @ feat^T
    pub fn forward_update(&self, w_state: &Tensor, x_t: &Tensor) -> Result<(Tensor, Tensor)> {
        let feat = self.proj_down.forward(x_t)?;

        // Normalize (L2 per vector)
        // Note: unsqueeze/squeeze are lightweight view operations in Candle
        let last_dim = feat.rank() - 1;
        let norm = feat.sqr()?.sum_keepdim(last_dim)?.sqrt()?;
        // Add epsilon for numerical stability (broadcast_add handles scalar efficiently)
        let norm = (norm + TTT_NORM_EPS as f64)?;
        let feat_norm = feat.broadcast_div(&norm)?;

        // Predict: W @ feat_norm (requires column vector shape)
        let feat_expanded = feat_norm.unsqueeze(last_dim + 1)?;
        let pred_inner = w_state.matmul(&feat_expanded)?.squeeze(last_dim + 1)?;

        // Loss & Grad: outer product diff @ feat_norm^T
        let diff = (&pred_inner - &feat_norm)?;
        let diff_ed = diff.unsqueeze(last_dim + 1)?;
        let feat_ed_t = feat_norm.unsqueeze(last_dim)?;
        let grad = diff_ed.matmul(&feat_ed_t)?;

        // Update W via gradient descent
        let w_new = (w_state - grad * self.inner_lr)?.detach();

        // Project Up
        let out_feat = self.proj_up.forward(&pred_inner)?;

        Ok((out_feat, w_new))
    }

    /// Parallel chunkwise implementation for efficient batched processing.
    ///
    /// 効率的なバッチ処理のための並列チャンクワイズ実装。
    ///
    /// Processes multiple tokens in parallel within chunks, while maintaining
    /// sequential dependency between chunks. This provides a balance between
    /// parallelism and the causal nature of TTT updates.
    ///
    /// チャンク内では複数トークンを並列処理し、チャンク間では
    /// 逐次的な依存関係を維持します。これにより並列性とTTT更新の
    /// 因果関係のバランスを取ります。
    ///
    /// # Arguments / 引数
    /// - `w_state`: Initial weight state `(B, D_small, D_small)`
    /// - `x`: Input sequence `(B, T, Hidden)`
    /// - `chunk_size`: Number of tokens per chunk / チャンクあたりのトークン数
    ///
    /// # Returns / 戻り値
    /// - `(output, w_final)`:
    ///   - `output`: `(B, T, Hidden)` - Transformed sequence / 変換されたシーケンス
    ///   - `w_final`: Final weight state after processing all chunks / 全チャンク処理後の最終重み状態
    pub fn forward_chunkwise(
        &self,
        w_state: &Tensor,
        x: &Tensor,
        chunk_size: usize,
    ) -> Result<(Tensor, Tensor)> {
        let feat = self.proj_down.forward(x)?;

        // Normalize (L2 per vector along dim 2)
        let norm = feat.sqr()?.sum_keepdim(2)?.sqrt()?;
        // Add epsilon directly (avoids creating a new tensor per call)
        let norm = (norm + TTT_NORM_EPS as f64)?;
        let feat_norm = feat.broadcast_div(&norm)?;

        let (_b_sz, t_len, _d_small) = feat_norm.dims3()?;
        let mut current_w = w_state.clone();
        let mut outputs = Vec::new();

        let num_chunks = t_len.div_ceil(chunk_size);

        for i in 0..num_chunks {
            let start = i * chunk_size;
            let len = std::cmp::min(chunk_size, t_len - start);

            let x_chunk = feat_norm.narrow(1, start, len)?;
            let x_chunk_t = x_chunk.transpose(1, 2)?;
            let z_chunk_t = current_w.matmul(&x_chunk_t)?;
            let z_chunk = z_chunk_t.transpose(1, 2)?;
            let diff = (&z_chunk - &x_chunk)?;
            let diff_t = diff.transpose(1, 2)?;
            let grad = diff_t.matmul(&x_chunk)?;

            current_w = (current_w - grad * self.inner_lr)?;
            outputs.push(z_chunk);
        }

        let pred_all = Tensor::cat(&outputs, 1)?;
        let out_feat = self.proj_up.forward(&pred_all)?;

        Ok((out_feat, current_w))
    }
}
