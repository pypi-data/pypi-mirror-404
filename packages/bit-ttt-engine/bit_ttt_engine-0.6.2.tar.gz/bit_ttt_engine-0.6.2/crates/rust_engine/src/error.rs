//! Unified Error Types for Bit-TTT-Engine (統一エラー型)
//!
//! このモジュールはプロジェクト全体で使用する統一されたエラー型を定義します。
//! `candle_core::Result`との互換性を維持しつつ、エラーの種類を明確に分類します。
//!
//! This module defines unified error types used throughout the project.
//! It maintains compatibility with `candle_core::Result` while clearly categorizing error types.

use thiserror::Error;

/// Bit-TTT-Engine統一エラー型
///
/// プロジェクト内のすべてのエラーを分類し、適切なエラーメッセージを提供します。
#[derive(Error, Debug)]
pub enum BitTTTError {
    /// Shape mismatch between tensors / テンソル間の形状不一致
    #[error("Shape mismatch: {0}")]
    ShapeMismatch(String),

    /// Device-related errors (CPU/CUDA/WASM) / デバイス関連エラー
    #[error("Device error: {0}")]
    DeviceError(String),

    /// Kernel execution errors / カーネル実行エラー
    #[error("Kernel error: {0}")]
    KernelError(String),

    /// Storage-related errors / ストレージ関連エラー
    #[error("Storage error: {0}")]
    StorageError(String),

    /// Feature not enabled / 機能が有効化されていない
    #[error("Feature not enabled: {0}")]
    FeatureNotEnabled(String),

    /// Candle core errors / Candleコアエラー
    #[error("Candle error: {0}")]
    Candle(#[from] candle_core::Error),
}

/// Result type alias using BitTTTError
///
/// 内部処理用のResult型エイリアス。
/// 最終的に`candle_core::Result`に変換可能。
pub type BitResult<T> = std::result::Result<T, BitTTTError>;

impl BitTTTError {
    /// Create a shape mismatch error / 形状不一致エラーを作成
    pub fn shape_mismatch(msg: impl Into<String>) -> Self {
        Self::ShapeMismatch(msg.into())
    }

    /// Create a device error / デバイスエラーを作成
    pub fn device_error(msg: impl Into<String>) -> Self {
        Self::DeviceError(msg.into())
    }

    /// Create a kernel error / カーネルエラーを作成
    pub fn kernel_error(msg: impl Into<String>) -> Self {
        Self::KernelError(msg.into())
    }

    /// Create a storage error / ストレージエラーを作成
    pub fn storage_error(msg: impl Into<String>) -> Self {
        Self::StorageError(msg.into())
    }

    /// Create a feature not enabled error / 機能未有効化エラーを作成
    pub fn feature_not_enabled(feature: impl Into<String>) -> Self {
        Self::FeatureNotEnabled(feature.into())
    }
}

// Allow conversion to candle_core::Error for API compatibility
// API互換性のため、candle_core::Errorへの変換を許可
impl From<BitTTTError> for candle_core::Error {
    fn from(err: BitTTTError) -> Self {
        candle_core::Error::Msg(err.to_string())
    }
}

#[cfg(test)]
mod tests {
    use super::*;

    #[test]
    fn test_error_messages() {
        let err = BitTTTError::shape_mismatch("Input [4, 8] vs Weight [8, 16]");
        assert!(err.to_string().contains("Shape mismatch"));

        let err = BitTTTError::device_error("Expected CUDA device");
        assert!(err.to_string().contains("Device error"));

        let err = BitTTTError::kernel_error("Kernel not found");
        assert!(err.to_string().contains("Kernel error"));
    }

    #[test]
    fn test_conversion_to_candle_error() {
        let bit_err = BitTTTError::shape_mismatch("test");
        let candle_err: candle_core::Error = bit_err.into();
        assert!(candle_err.to_string().contains("Shape mismatch"));
    }
}
