//! WASM Bindings for Bit-TTT-Engine
//!
//! ブラウザやNode.jsからの推論を可能にするWebAssemblyバインディング。
//! 完全な推論機能は複雑なため、まずは構造体とスタブメソッドを提供します。
//!
//! This module provides WebAssembly bindings for browser/Node.js inference.
//! Since full inference is complex, we start with struct definitions and stub methods.

#[cfg(feature = "wasm")]
use wasm_bindgen::prelude::*;

/// Initialize panic hook for better error messages in WASM environment.
///
/// WASM環境でのパニック時に、より詳細なエラーメッセージを表示するためのフックを初期化します。
/// アプリケーション起動時に一度だけ呼び出してください。
#[cfg(feature = "wasm")]
#[wasm_bindgen]
pub fn init_panic_hook() {
    console_error_panic_hook::set_once();
}

/// Simple logging for WASM environment.
///
/// WASM環境用のシンプルなログ出力関数。
/// `console.log`に出力します。
#[cfg(feature = "wasm")]
#[wasm_bindgen]
pub fn wasm_log(message: &str) {
    web_sys::console::log_1(&JsValue::from_str(message));
}

/// Log an error message to the browser console.
///
/// ブラウザコンソールにエラーメッセージを出力します。
#[cfg(feature = "wasm")]
#[wasm_bindgen]
pub fn wasm_error(message: &str) {
    web_sys::console::error_1(&JsValue::from_str(message));
}

/// Lightweight configuration for WASM inference.
///
/// WASM推論用の軽量設定構造体。
/// ブラウザでの使用を想定し、最小限のパラメータのみ保持します。
#[cfg(feature = "wasm")]
#[wasm_bindgen]
pub struct WasmConfig {
    /// Model hidden dimension
    hidden_dim: usize,
    /// Number of transformer layers
    num_layers: usize,
    /// Vocabulary size
    vocab_size: usize,
    /// Maximum sequence length
    max_seq_len: usize,
}

#[cfg(feature = "wasm")]
#[wasm_bindgen]
impl WasmConfig {
    /// Create a new configuration with default values.
    ///
    /// デフォルト値で新しい設定を作成します。
    /// 小規模モデル（256次元、4層）を想定しています。
    #[wasm_bindgen(constructor)]
    pub fn new() -> Self {
        Self {
            hidden_dim: 256,
            num_layers: 4,
            vocab_size: 32000,
            max_seq_len: 512,
        }
    }

    /// Set hidden dimension.
    pub fn with_hidden_dim(mut self, dim: usize) -> Self {
        self.hidden_dim = dim;
        self
    }

    /// Set number of layers.
    pub fn with_num_layers(mut self, layers: usize) -> Self {
        self.num_layers = layers;
        self
    }

    /// Set vocabulary size.
    pub fn with_vocab_size(mut self, vocab: usize) -> Self {
        self.vocab_size = vocab;
        self
    }

    /// Set maximum sequence length.
    pub fn with_max_seq_len(mut self, len: usize) -> Self {
        self.max_seq_len = len;
        self
    }

    /// Get hidden dimension.
    #[wasm_bindgen(getter)]
    pub fn hidden_dim(&self) -> usize {
        self.hidden_dim
    }

    /// Get number of layers.
    #[wasm_bindgen(getter)]
    pub fn num_layers(&self) -> usize {
        self.num_layers
    }
}

/// WASM-compatible BitLlama model wrapper.
///
/// WASM互換のBitLlamaモデルラッパー。
/// ブラウザでの軽量推論を目的としています。
///
/// # Current Status / 現状
///
/// This is a stub implementation. Full functionality requires:
/// - Weight loading from ArrayBuffer (fetch from URL or IndexedDB)
/// - Tokenizer integration (possibly via tokenizers-wasm)
/// - Tensor operations adapted for CPU-only execution
///
/// これはスタブ実装です。完全な機能には以下が必要です：
/// - ArrayBufferからの重みロード（URLフェッチまたはIndexedDB）
/// - トークナイザー統合（tokenizers-wasmの利用を検討）
/// - CPU専用実行に適応したテンソル演算
#[cfg(feature = "wasm")]
#[wasm_bindgen]
pub struct WasmBitLlama {
    config: WasmConfig,
    /// Whether the model is initialized with weights
    initialized: bool,
    /// Current position in the sequence (for KV cache)
    current_pos: usize,
}

#[cfg(feature = "wasm")]
#[wasm_bindgen]
impl WasmBitLlama {
    /// Create a new WasmBitLlama instance with default configuration.
    ///
    /// デフォルト設定で新しいWasmBitLlamaインスタンスを作成します。
    ///
    /// # Returns / 戻り値
    /// - `Ok(WasmBitLlama)`: Successfully created instance
    /// - `Err(JsValue)`: Error during creation (unlikely with defaults)
    #[wasm_bindgen(constructor)]
    pub fn new() -> Result<WasmBitLlama, JsValue> {
        // Initialize panic hook for better error messages
        console_error_panic_hook::set_once();

        Ok(Self {
            config: WasmConfig::new(),
            initialized: false,
            current_pos: 0,
        })
    }

    /// Create a new WasmBitLlama instance with custom configuration.
    ///
    /// カスタム設定で新しいWasmBitLlamaインスタンスを作成します。
    pub fn with_config(config: WasmConfig) -> Result<WasmBitLlama, JsValue> {
        console_error_panic_hook::set_once();

        Ok(Self {
            config,
            initialized: false,
            current_pos: 0,
        })
    }

    /// Load model weights from a Uint8Array (safetensors format).
    ///
    /// Uint8Array（safetensors形式）からモデル重みをロードします。
    ///
    /// # Arguments / 引数
    /// - `weights_data`: Safetensors file content as Uint8Array
    ///
    /// # Status / 状態
    /// Currently a stub - full implementation requires adapting safetensors parsing for WASM.
    /// 現在はスタブ - 完全な実装にはsafetensorsパースのWASM適応が必要。
    pub fn load_weights(&mut self, _weights_data: &[u8]) -> Result<(), JsValue> {
        // TODO: Implement safetensors parsing for WASM
        // 1. Parse safetensors header to get tensor metadata
        // 2. Extract tensor data and convert to appropriate format
        // 3. Initialize model layers with loaded weights
        //
        // For now, mark as initialized for testing purposes
        wasm_log("WasmBitLlama: load_weights called (stub implementation)");
        self.initialized = true;
        Ok(())
    }

    /// Generate text from a prompt.
    ///
    /// プロンプトからテキストを生成します。
    ///
    /// # Arguments / 引数
    /// - `prompt`: Input text prompt / 入力テキストプロンプト
    /// - `max_tokens`: Maximum number of tokens to generate / 生成する最大トークン数
    ///
    /// # Returns / 戻り値
    /// - `Ok(String)`: Generated text / 生成されたテキスト
    /// - `Err(JsValue)`: Error during generation / 生成中のエラー
    ///
    /// # Status / 状態
    /// Currently a stub - returns a placeholder message.
    /// 現在はスタブ - プレースホルダーメッセージを返します。
    pub fn generate(&mut self, prompt: &str, max_tokens: u32) -> Result<String, JsValue> {
        if !self.initialized {
            return Err(JsValue::from_str(
                "Model not initialized. Call load_weights first.",
            ));
        }

        // TODO: Implement actual generation
        // 1. Tokenize input prompt
        // 2. Run forward pass through layers
        // 3. Sample next token
        // 4. Decode and return
        //
        // Stub implementation returns placeholder
        wasm_log(&format!(
            "WasmBitLlama: generate called with prompt='{}', max_tokens={}",
            prompt, max_tokens
        ));

        Ok(format!(
            "[STUB] Generated response for: '{}' (max_tokens: {}). \
             Full implementation pending.",
            prompt, max_tokens
        ))
    }

    /// Generate text with streaming callback.
    ///
    /// ストリーミングコールバック付きでテキストを生成します。
    ///
    /// # Arguments / 引数
    /// - `prompt`: Input text prompt
    /// - `max_tokens`: Maximum tokens to generate
    /// - `callback`: JavaScript function called for each generated token
    ///
    /// # Status / 状態
    /// Stub implementation - demonstrates the API pattern.
    pub fn generate_stream(
        &mut self,
        prompt: &str,
        max_tokens: u32,
        callback: &js_sys::Function,
    ) -> Result<String, JsValue> {
        if !self.initialized {
            return Err(JsValue::from_str(
                "Model not initialized. Call load_weights first.",
            ));
        }

        wasm_log(&format!(
            "WasmBitLlama: generate_stream called with prompt='{}'",
            prompt
        ));

        // Simulate streaming by calling callback for each "token"
        let stub_tokens = ["[STUB]", " response", " for:", " '", prompt, "'"];
        let mut result = String::new();

        for (i, token) in stub_tokens.iter().enumerate() {
            if i as u32 >= max_tokens {
                break;
            }
            result.push_str(token);

            // Call the JavaScript callback with the token
            let this = JsValue::NULL;
            let token_js = JsValue::from_str(token);
            if let Err(e) = callback.call1(&this, &token_js) {
                wasm_error(&format!("Callback error: {:?}", e));
            }
        }

        Ok(result)
    }

    /// Reset the model state (KV cache, position).
    ///
    /// モデル状態（KVキャッシュ、位置）をリセットします。
    /// 新しい会話を開始する前に呼び出してください。
    pub fn reset(&mut self) {
        self.current_pos = 0;
        wasm_log("WasmBitLlama: state reset");
    }

    /// Check if the model is initialized.
    ///
    /// モデルが初期化済みかどうかを確認します。
    #[wasm_bindgen(getter)]
    pub fn is_initialized(&self) -> bool {
        self.initialized
    }

    /// Get current sequence position.
    ///
    /// 現在のシーケンス位置を取得します。
    #[wasm_bindgen(getter)]
    pub fn position(&self) -> usize {
        self.current_pos
    }

    /// Get model information as JSON string.
    ///
    /// モデル情報をJSON文字列として取得します。
    pub fn get_info(&self) -> String {
        serde_json::json!({
            "hidden_dim": self.config.hidden_dim,
            "num_layers": self.config.num_layers,
            "vocab_size": self.config.vocab_size,
            "max_seq_len": self.config.max_seq_len,
            "initialized": self.initialized,
            "current_pos": self.current_pos
        })
        .to_string()
    }
}

// Re-export js_sys for the streaming callback
#[cfg(feature = "wasm")]
use js_sys;

/// Basic WASM-friendly inference function (legacy API).
///
/// 基本的なWASM対応推論関数（レガシーAPI）。
/// 新しいコードでは`WasmBitLlama`構造体を使用してください。
#[cfg(feature = "wasm")]
#[wasm_bindgen]
pub fn wasm_infer(input: &str) -> Result<String, JsValue> {
    // This function is kept for backward compatibility
    // For new code, use WasmBitLlama instead
    wasm_log(&format!("wasm_infer called with: {}", input));

    Ok(format!(
        "[Legacy API] Input received: '{}'. Use WasmBitLlama for full functionality.",
        input
    ))
}

/// Get version information.
///
/// バージョン情報を取得します。
#[cfg(feature = "wasm")]
#[wasm_bindgen]
pub fn wasm_version() -> String {
    env!("CARGO_PKG_VERSION").to_string()
}

#[cfg(all(test, feature = "wasm"))]
mod tests {
    use super::*;

    #[test]
    fn test_wasm_config_creation() {
        let config = WasmConfig::new();
        assert_eq!(config.hidden_dim, 256);
        assert_eq!(config.num_layers, 4);
    }
}
