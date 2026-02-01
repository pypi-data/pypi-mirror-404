//! Python Bindings for BitLlama and GgufModel (PyO3)

#[cfg(feature = "python")]
use candle_core::{DType, Device, IndexOp, Tensor, Var};

#[cfg(feature = "python")]
use pyo3::prelude::*;

#[cfg(feature = "python")]
use crate::model::{BitLlama, BitLlamaConfig, GgufModel};
#[cfg(feature = "python")]
use crate::optim::schedule_free::{ParamsScheduleFree, ScheduleFreeOptimizer};
#[cfg(feature = "python")]
use candle_nn::VarMap;

#[cfg(feature = "python")]
use tokenizers::Tokenizer;

// ============================================================================
// PyGgufModel - Python wrapper for GgufModel (GGUF format inference)
// ============================================================================

/// Python wrapper for GgufModel (GGUF format inference)
/// 
/// Example:
/// ```python
/// from cortex_rust import GgufModel
/// 
/// # With tokenizer (recommended)
/// model = GgufModel("model.gguf", tokenizer="tokenizer.json")
/// output = model.generate("Hello, world!", max_tokens=50)
/// 
/// # Without tokenizer (byte-level fallback)
/// model = GgufModel("model.gguf")
/// ```
#[cfg(feature = "python")]
#[pyclass(name = "GgufModel")]
pub struct PyGgufModel {
    inner: GgufModel,
    device: Device,
    tokenizer: Option<Tokenizer>,
}

#[cfg(feature = "python")]
#[pymethods]
impl PyGgufModel {
    /// Load a GGUF model
    /// 
    /// Args:
    ///     path: Path to the GGUF model file
    ///     tokenizer: Path to tokenizer.json (optional but recommended)
    ///     device: Device to use ("cpu" or "cuda"). Default: "cpu"
    #[new]
    #[pyo3(signature = (path, tokenizer=None, device=None))]
    pub fn new(path: &str, tokenizer: Option<&str>, device: Option<&str>) -> PyResult<Self> {
        let device = match device {
            Some("cuda") | Some("gpu") => {
                Device::new_cuda(0).map_err(|e| {
                    pyo3::exceptions::PyRuntimeError::new_err(format!(
                        "Failed to initialize CUDA: {}. Try device='cpu'", e
                    ))
                })?
            }
            Some("cpu") | None => Device::Cpu,
            Some(unknown) => {
                return Err(pyo3::exceptions::PyValueError::new_err(format!(
                    "Unknown device: '{}'. Use 'cpu' or 'cuda'", unknown
                )))
            }
        };

        let model = GgufModel::load(path, &device).map_err(|e| {
            pyo3::exceptions::PyRuntimeError::new_err(format!(
                "Failed to load model '{}': {}", path, e
            ))
        })?;

        // Load tokenizer if provided
        let tokenizer = if let Some(tok_path) = tokenizer {
            Some(Tokenizer::from_file(tok_path).map_err(|e| {
                pyo3::exceptions::PyRuntimeError::new_err(format!(
                    "Failed to load tokenizer '{}': {}", tok_path, e
                ))
            })?)
        } else {
            None
        };

        Ok(Self { inner: model, device, tokenizer })
    }

    /// Get model configuration info
    #[getter]
    pub fn config(&self) -> PyResult<PyGgufConfig> {
        let cfg = self.inner.config();
        Ok(PyGgufConfig {
            vocab_size: cfg.vocab_size,
            hidden_dim: cfg.hidden_dim,
            num_layers: cfg.num_layers,
            n_heads: cfg.n_heads,
            n_kv_heads: cfg.n_kv_heads,
        })
    }

    /// Forward pass through the model
    /// 
    /// Args:
    ///     tokens: List of token IDs
    ///     start_pos: Starting position for KV cache
    /// 
    /// Returns:
    ///     Logits as a list of floats (flattened)
    #[pyo3(signature = (tokens, start_pos=0))]
    pub fn forward(&mut self, tokens: Vec<i64>, start_pos: usize) -> PyResult<Vec<f32>> {
        if tokens.is_empty() {
            return Err(pyo3::exceptions::PyValueError::new_err("tokens cannot be empty"));
        }
        let seq_len = tokens.len();
        let input = Tensor::from_vec(tokens, (1, seq_len), &self.device)
            .map_err(|e| pyo3::exceptions::PyRuntimeError::new_err(e.to_string()))?;

        let logits = self.inner.forward(&input, start_pos)
            .map_err(|e| pyo3::exceptions::PyRuntimeError::new_err(e.to_string()))?;

        // Return last token's logits
        let (_, seq_len, _vocab_size) = logits.dims3()
            .map_err(|e| pyo3::exceptions::PyRuntimeError::new_err(e.to_string()))?;
        
        let last_logits = logits.narrow(1, seq_len - 1, 1)
            .map_err(|e| pyo3::exceptions::PyRuntimeError::new_err(e.to_string()))?
            .squeeze(1)
            .map_err(|e| pyo3::exceptions::PyRuntimeError::new_err(e.to_string()))?
            .squeeze(0)
            .map_err(|e| pyo3::exceptions::PyRuntimeError::new_err(e.to_string()))?;

        let result = last_logits.to_vec1::<f32>()
            .map_err(|e| pyo3::exceptions::PyRuntimeError::new_err(e.to_string()))?;

        Ok(result)
    }

    /// Generate text from a prompt
    /// 
    /// Args:
    ///     prompt: Text prompt to continue
    ///     max_tokens: Maximum number of tokens to generate
    ///     temperature: Sampling temperature (0.0 = greedy, 1.0 = full distribution)
    ///     top_k: Top-k sampling (0 = disabled)
    ///     top_p: Top-p (nucleus) sampling (1.0 = disabled)
    /// 
    /// Returns:
    ///     Generated text (excluding the prompt)
    #[pyo3(signature = (prompt, max_tokens=50, temperature=0.7, top_k=40, top_p=0.9))]
    pub fn generate(&mut self, py: Python, prompt: &str, max_tokens: usize, temperature: f32, top_k: usize, top_p: f32) -> PyResult<String> {
        py.allow_threads(|| {
            self.generate_inner(prompt, max_tokens, temperature, top_k, top_p)
        })
    }

    /// Reset the KV cache (call between conversations)
    pub fn reset_cache(&mut self) {
        self.inner.reset_cache();
    }

    // =========================================================================
    // TTT (Test-Time Training) API
    // =========================================================================

    /// Enable TTT (Test-Time Training) mode
    /// 
    /// TTT allows the model to learn and adapt during inference.
    /// The model will update internal weights based on input patterns.
    /// 
    /// Args:
    ///     layers: Number of layers to enable TTT for (from the end).
    ///             None = all layers, 4 = last 4 layers (recommended)
    ///     learning_rate: TTT learning rate (default: 0.01)
    /// 
    /// Example:
    ///     model.enable_ttt(layers=4, learning_rate=0.01)
    ///     output1 = model.generate("My name is Alice")
    ///     output2 = model.generate("What is my name?")  # Should remember!
    #[pyo3(signature = (layers=None, learning_rate=0.01))]
    pub fn enable_ttt(&mut self, layers: Option<usize>, learning_rate: f64) {
        let num_layers = self.inner.config().num_layers;
        let range = if let Some(n) = layers {
            let start = num_layers.saturating_sub(n);
            Some(start..num_layers)
        } else {
            None
        };
        self.inner.enable_ttt(range, learning_rate);
    }

    /// Disable TTT mode
    pub fn disable_ttt(&mut self) {
        self.inner.disable_ttt();
    }

    /// Reset TTT state (forget learned patterns)
    pub fn reset_ttt_state(&mut self) {
        self.inner.reset_ttt_state();
    }

    /// Check if TTT is enabled
    #[getter]
    pub fn ttt_enabled(&self) -> bool {
        self.inner.is_ttt_enabled()
    }

    /// Generate tokens and return as list (for streaming in Python)
    /// 
    /// Use with a Python wrapper for streaming:
    /// ```python
    /// def stream(model, prompt, **kwargs):
    ///     tokens = model.generate_tokens_list(prompt, **kwargs)
    ///     for token in tokens:
    ///         yield token
    /// ```
    #[pyo3(signature = (prompt, max_tokens=50, temperature=0.7, top_k=40, top_p=0.9))]
    pub fn generate_tokens_list(&mut self, prompt: &str, max_tokens: usize, temperature: f32, top_k: usize, top_p: f32) -> PyResult<Vec<String>> {
        // Tokenize prompt
        let prompt_tokens = if let Some(ref tokenizer) = self.tokenizer {
            let encoding = tokenizer.encode(prompt, false).map_err(|e| {
                pyo3::exceptions::PyRuntimeError::new_err(format!("Tokenization failed: {}", e))
            })?;
            let ids: Vec<i64> = encoding.get_ids().iter().map(|&x| x as i64).collect();
            if ids.is_empty() { vec![1_i64] } else { ids }
        } else {
            let bytes: Vec<i64> = prompt.bytes().map(|b| b as i64).collect();
            if bytes.is_empty() { vec![1_i64] } else { bytes }
        };
        
        let mut tokens = prompt_tokens.clone();
        let mut result = Vec::new();
        
        // Prefill
        let input = Tensor::from_vec(prompt_tokens.clone(), (1, prompt_tokens.len()), &self.device)
            .map_err(|e| pyo3::exceptions::PyRuntimeError::new_err(e.to_string()))?;
        
        let logits = self.inner.forward(&input, 0)
            .map_err(|e| pyo3::exceptions::PyRuntimeError::new_err(e.to_string()))?;
        
        let first_token = self.sample_token(&logits, temperature, top_k, top_p)?;
        
        if first_token <= 2 {
            return Ok(result);
        }
        
        tokens.push(first_token);
        result.push(self.decode_single_token(first_token)?);
        
        // Decode loop
        for _ in 1..max_tokens {
            let pos = tokens.len() - 1;
            let last_token = *tokens.last().unwrap();
            
            let input = Tensor::from_vec(vec![last_token], (1, 1), &self.device)
                .map_err(|e| pyo3::exceptions::PyRuntimeError::new_err(e.to_string()))?;
            
            let logits = self.inner.forward(&input, pos)
                .map_err(|e| pyo3::exceptions::PyRuntimeError::new_err(e.to_string()))?;
            
            let next_token = self.sample_token(&logits, temperature, top_k, top_p)?;
            
            if next_token <= 2 {
                break;
            }
            
            tokens.push(next_token);
            result.push(self.decode_single_token(next_token)?);
        }
        
        Ok(result)
    }

    /// Generate with callback for each token (true streaming)
    /// 
    /// Args:
    ///     prompt: Text prompt
    ///     callback: Python function called with each token string
    ///     max_tokens, temperature, top_k, top_p: Generation params
    /// 
    /// Example:
    ///     model.generate_with_callback("Hello", lambda t: print(t, end="", flush=True))
    #[pyo3(signature = (prompt, callback, max_tokens=50, temperature=0.7, top_k=40, top_p=0.9))]
    pub fn generate_with_callback(
        &mut self,
        py: Python,
        prompt: &str,
        callback: PyObject,
        max_tokens: usize,
        temperature: f32,
        top_k: usize,
        top_p: f32,
    ) -> PyResult<String> {
        // Tokenize prompt
        let prompt_tokens = if let Some(ref tokenizer) = self.tokenizer {
            let encoding = tokenizer.encode(prompt, false).map_err(|e| {
                pyo3::exceptions::PyRuntimeError::new_err(format!("Tokenization failed: {}", e))
            })?;
            let ids: Vec<i64> = encoding.get_ids().iter().map(|&x| x as i64).collect();
            if ids.is_empty() { vec![1_i64] } else { ids }
        } else {
            let bytes: Vec<i64> = prompt.bytes().map(|b| b as i64).collect();
            if bytes.is_empty() { vec![1_i64] } else { bytes }
        };
        
        let mut tokens = prompt_tokens.clone();
        let mut full_output = String::new();
        
        // Prefill
        let input = Tensor::from_vec(prompt_tokens.clone(), (1, prompt_tokens.len()), &self.device)
            .map_err(|e| pyo3::exceptions::PyRuntimeError::new_err(e.to_string()))?;
        
        let logits = self.inner.forward(&input, 0)
            .map_err(|e| pyo3::exceptions::PyRuntimeError::new_err(e.to_string()))?;
        
        let first_token = self.sample_token(&logits, temperature, top_k, top_p)?;
        
        if first_token <= 2 {
            return Ok(full_output);
        }
        
        tokens.push(first_token);
        let token_str = self.decode_single_token(first_token)?;
        full_output.push_str(&token_str);
        callback.call1(py, (token_str,))?;
        
        // Decode loop
        for _ in 1..max_tokens {
            let pos = tokens.len() - 1;
            let last_token = *tokens.last().unwrap();
            
            let input = Tensor::from_vec(vec![last_token], (1, 1), &self.device)
                .map_err(|e| pyo3::exceptions::PyRuntimeError::new_err(e.to_string()))?;
            
            let logits = self.inner.forward(&input, pos)
                .map_err(|e| pyo3::exceptions::PyRuntimeError::new_err(e.to_string()))?;
            
            let next_token = self.sample_token(&logits, temperature, top_k, top_p)?;
            
            if next_token <= 2 {
                break;
            }
            
            tokens.push(next_token);
            let token_str = self.decode_single_token(next_token)?;
            full_output.push_str(&token_str);
            callback.call1(py, (token_str,))?;
        }
        
        Ok(full_output)
    }
}

#[cfg(feature = "python")]
impl PyGgufModel {
    fn decode_single_token(&self, token: i64) -> PyResult<String> {
        if let Some(ref tokenizer) = self.tokenizer {
            tokenizer.decode(&[token as u32], false)
                .map_err(|e| pyo3::exceptions::PyRuntimeError::new_err(e.to_string()))
        } else {
            Ok(if token >= 32 && token < 127 {
                (token as u8 as char).to_string()
            } else if token == 10 {
                "\n".to_string()
            } else {
                String::new()
            })
        }
    }
}

#[cfg(feature = "python")]
impl PyGgufModel {
    fn generate_inner(&mut self, prompt: &str, max_tokens: usize, temperature: f32, top_k: usize, top_p: f32) -> PyResult<String> {
        // Tokenize prompt
        let (prompt_tokens, use_tokenizer) = if let Some(ref tokenizer) = self.tokenizer {
            let encoding = tokenizer.encode(prompt, false).map_err(|e| {
                pyo3::exceptions::PyRuntimeError::new_err(format!("Tokenization failed: {}", e))
            })?;
            let ids: Vec<i64> = encoding.get_ids().iter().map(|&x| x as i64).collect();
            // Handle empty prompt: use BOS token (1) as default
            if ids.is_empty() {
                (vec![1_i64], true)  // BOS token
            } else {
                (ids, true)
            }
        } else {
            // Fallback to byte-level tokenization
            let bytes: Vec<i64> = prompt.bytes().map(|b| b as i64).collect();
            if bytes.is_empty() {
                (vec![1_i64], false)  // BOS token
            } else {
                (bytes, false)
            }
        };
        
        let mut tokens = prompt_tokens.clone();
        let prompt_len = tokens.len();
        
        // Prefill
        let input = Tensor::from_vec(tokens.clone(), (1, tokens.len()), &self.device)
            .map_err(|e| pyo3::exceptions::PyRuntimeError::new_err(e.to_string()))?;
        
        let logits = self.inner.forward(&input, 0)
            .map_err(|e| pyo3::exceptions::PyRuntimeError::new_err(e.to_string()))?;
        
        let first_token = self.sample_token(&logits, temperature, top_k, top_p)?;
        tokens.push(first_token);
        
        // Decode loop
        for _ in 0..max_tokens {
            let pos = tokens.len() - 1;
            let input = Tensor::from_vec(vec![tokens[pos]], (1, 1), &self.device)
                .map_err(|e| pyo3::exceptions::PyRuntimeError::new_err(e.to_string()))?;
            
            let logits = self.inner.forward(&input, pos)
                .map_err(|e| pyo3::exceptions::PyRuntimeError::new_err(e.to_string()))?;
            
            let next_token = self.sample_token(&logits, temperature, top_k, top_p)?;
            
            // Stop on EOS tokens (common values: 0, 1, 2)
            if next_token <= 2 {
                break;
            }
            
            tokens.push(next_token);
        }
        
        // Decode output
        let generated_tokens: Vec<u32> = tokens.iter()
            .skip(prompt_len)
            .map(|&t| t as u32)
            .collect();
        
        if use_tokenizer {
            let tokenizer = self.tokenizer.as_ref().unwrap();
            let output = tokenizer.decode(&generated_tokens, true).map_err(|e| {
                pyo3::exceptions::PyRuntimeError::new_err(format!("Decoding failed: {}", e))
            })?;
            Ok(output)
        } else {
            // Fallback byte-level decoding
            let output: String = generated_tokens.iter()
                .filter_map(|&t| {
                    if t >= 32 && t < 127 {
                        Some(t as u8 as char)
                    } else if t == 10 {
                        Some('\n')
                    } else {
                        None
                    }
                })
                .collect();
            Ok(output)
        }
    }

    fn sample_token(&self, logits: &Tensor, temperature: f32, top_k: usize, top_p: f32) -> PyResult<i64> {
        use rand::Rng;
        
        let (_, seq_len, _) = logits.dims3()
            .map_err(|e| pyo3::exceptions::PyRuntimeError::new_err(e.to_string()))?;
        
        let last_logits = logits.narrow(1, seq_len - 1, 1)
            .map_err(|e| pyo3::exceptions::PyRuntimeError::new_err(e.to_string()))?
            .squeeze(1)
            .map_err(|e| pyo3::exceptions::PyRuntimeError::new_err(e.to_string()))?
            .squeeze(0)
            .map_err(|e| pyo3::exceptions::PyRuntimeError::new_err(e.to_string()))?;
        
        // Greedy sampling if temperature is very low
        if temperature < 0.01 {
            let token_id = last_logits.argmax(0)
                .map_err(|e| pyo3::exceptions::PyRuntimeError::new_err(e.to_string()))?
                .to_scalar::<u32>()
                .map_err(|e| pyo3::exceptions::PyRuntimeError::new_err(e.to_string()))?;
            return Ok(token_id as i64);
        }
        
        // Get logits as vec
        let mut logits_vec = last_logits.to_vec1::<f32>()
            .map_err(|e| pyo3::exceptions::PyRuntimeError::new_err(e.to_string()))?;
        
        // Apply temperature
        for logit in &mut logits_vec {
            *logit /= temperature;
        }
        
        // Top-k filtering
        if top_k > 0 && top_k < logits_vec.len() {
            let mut indexed: Vec<(usize, f32)> = logits_vec.iter().cloned().enumerate().collect();
            indexed.sort_by(|a, b| b.1.partial_cmp(&a.1).unwrap_or(std::cmp::Ordering::Equal));
            let threshold = indexed[top_k - 1].1;
            for logit in &mut logits_vec {
                if *logit < threshold {
                    *logit = f32::NEG_INFINITY;
                }
            }
        }
        
        // Softmax
        let max_logit = logits_vec.iter().cloned().fold(f32::NEG_INFINITY, f32::max);
        let exp_sum: f32 = logits_vec.iter().map(|&x| (x - max_logit).exp()).sum();
        let probs: Vec<f32> = logits_vec.iter().map(|&x| (x - max_logit).exp() / exp_sum).collect();
        
        // Top-p (nucleus) filtering
        let probs = if top_p < 1.0 {
            let mut indexed: Vec<(usize, f32)> = probs.iter().cloned().enumerate().collect();
            indexed.sort_by(|a, b| b.1.partial_cmp(&a.1).unwrap_or(std::cmp::Ordering::Equal));
            
            let mut cumsum = 0.0;
            let mut cutoff_idx = indexed.len();
            for (i, (_, p)) in indexed.iter().enumerate() {
                cumsum += p;
                if cumsum > top_p {
                    cutoff_idx = i + 1;
                    break;
                }
            }
            
            let mut filtered = vec![0.0; probs.len()];
            for (idx, p) in indexed.iter().take(cutoff_idx) {
                filtered[*idx] = *p;
            }
            
            // Renormalize
            let sum: f32 = filtered.iter().sum();
            if sum > 0.0 {
                filtered.iter().map(|&x| x / sum).collect()
            } else {
                probs
            }
        } else {
            probs
        };
        
        // Sample from distribution
        let r: f32 = rand::random();
        let mut cumsum = 0.0;
        for (i, &p) in probs.iter().enumerate() {
            cumsum += p;
            if r < cumsum {
                return Ok(i as i64);
            }
        }
        
        // Fallback to last token
        Ok((probs.len() - 1) as i64)
    }
}

/// Model configuration (read-only)
#[cfg(feature = "python")]
#[pyclass(name = "GgufConfig")]
pub struct PyGgufConfig {
    #[pyo3(get)]
    pub vocab_size: usize,
    #[pyo3(get)]
    pub hidden_dim: usize,
    #[pyo3(get)]
    pub num_layers: usize,
    #[pyo3(get)]
    pub n_heads: usize,
    #[pyo3(get)]
    pub n_kv_heads: usize,
}

// ============================================================================
// PyBitLlama - Original BitLlama wrapper (safetensors format)
// ============================================================================

/// Python wrapper for BitLlama model (Inference)
#[cfg(feature = "python")]
#[pyclass(name = "BitLlama")]
pub struct PyBitLlama {
    inner: BitLlama,
    w_states: Vec<Tensor>,
    tokenizer: Option<Tokenizer>,
}

#[cfg(feature = "python")]
#[pymethods]
impl PyBitLlama {
    #[new]
    #[pyo3(signature = (config, checkpoint_path, device=None, tokenizer_path=None))]
    pub fn new(
        config: BitLlamaConfig,
        checkpoint_path: &str,
        device: Option<&str>,
        tokenizer_path: Option<&str>,
    ) -> PyResult<Self> {
        let _device = match device {
            Some("cuda") => candle_core::Device::new_cuda(0).map_err(|e| {
                pyo3::exceptions::PyValueError::new_err(format!("CUDA error: {}", e))
            })?,
            Some("cpu") | None => candle_core::Device::Cpu,
            Some(unknown) => {
                return Err(pyo3::exceptions::PyValueError::new_err(format!(
                    "Unsupported device: {}. Use 'cpu' or 'cuda'",
                    unknown
                )))
            }
        };

        // Always load to CPU first, then selectively move to GPU in llama.rs
        // This enables hybrid offloading (n_gpu_layers)
        let vb = unsafe {
            candle_nn::VarBuilder::from_mmaped_safetensors(
                &[checkpoint_path],
                DType::F32,
                &candle_core::Device::Cpu,
            )
            .map_err(|e| pyo3::exceptions::PyValueError::new_err(e.to_string()))?
        };

        let mut model = BitLlama::load(config.clone(), vb)
            .map_err(|e| pyo3::exceptions::PyRuntimeError::new_err(e.to_string()))?;

        model
            .precompute_packed()
            .map_err(|e| pyo3::exceptions::PyRuntimeError::new_err(e.to_string()))?;

        // w_states should match each layer's device for Hybrid Offloading
        let d_small = config.hidden_dim / 4;
        let mut w_states = Vec::new();
        for layer in &model.layers {
            let layer_device = layer.device();
            let w = Tensor::zeros((d_small, d_small), DType::F32, layer_device)
                .map_err(|e| pyo3::exceptions::PyRuntimeError::new_err(e.to_string()))?;
            w_states.push(w);
        }

        // Load tokenizer if path provided
        let tokenizer = if let Some(tok_path) = tokenizer_path {
            match Tokenizer::from_file(tok_path) {
                Ok(tok) => Some(tok),
                Err(e) => {
                    return Err(pyo3::exceptions::PyValueError::new_err(format!(
                        "Failed to load tokenizer: {}",
                        e
                    )))
                }
            }
        } else {
            None
        };

        Ok(Self {
            inner: model,
            w_states,
            tokenizer,
        })
    }

    pub fn forward(&mut self, token_id: u32) -> PyResult<Vec<f32>> {
        let device = self.inner.embedding.embeddings().device();
        let input = Tensor::new(&[token_id], device)
            .map_err(|e| pyo3::exceptions::PyRuntimeError::new_err(e.to_string()))?;

        let logits = self
            .inner
            .forward_one(&input, &mut self.w_states)
            .map_err(|e| pyo3::exceptions::PyRuntimeError::new_err(e.to_string()))?;

        let logits_vec = logits
            .flatten_all()
            .map_err(|e| pyo3::exceptions::PyRuntimeError::new_err(e.to_string()))?
            .to_vec1::<f32>()
            .map_err(|e| pyo3::exceptions::PyRuntimeError::new_err(e.to_string()))?;

        Ok(logits_vec)
    }

    #[pyo3(signature = (prompt, max_tokens))]
    pub fn generate(&mut self, py: Python, prompt: &str, max_tokens: usize) -> PyResult<String> {
        // Check if tokenizer is available and encode prompt
        let prompt_tokens = {
            let tokenizer = self.tokenizer.as_ref().ok_or_else(|| {
                pyo3::exceptions::PyValueError::new_err(
                    "Tokenizer not available. Please provide tokenizer_path during initialization.",
                )
            })?;

            // 1. Encode prompt to token IDs
            let encoding = tokenizer.encode(prompt, true).map_err(|e| {
                pyo3::exceptions::PyRuntimeError::new_err(format!("Failed to encode prompt: {}", e))
            })?;

            let tokens: Vec<u32> = encoding.get_ids().to_vec();

            if tokens.is_empty() {
                return Err(pyo3::exceptions::PyValueError::new_err(
                    "Prompt encoded to empty token list",
                ));
            }

            tokens
        };

        // 2. Generate tokens using the parent generate_tokens implementation
        let generated_tokens = self.generate_tokens(py, prompt_tokens.clone(), max_tokens)?;

        // 3. Decode output tokens to string
        let tokenizer = self.tokenizer.as_ref().ok_or_else(|| {
            pyo3::exceptions::PyValueError::new_err(
                "Tokenizer not available. Please provide tokenizer_path during initialization.",
            )
        })?;

        // Remove the prompt tokens from the result, keeping only the newly generated ones
        let new_tokens: Vec<u32> = generated_tokens
            .iter()
            .skip(prompt_tokens.len())
            .copied()
            .collect();

        let decoded = tokenizer.decode(&new_tokens, true).map_err(|e| {
            pyo3::exceptions::PyRuntimeError::new_err(format!("Failed to decode tokens: {}", e))
        })?;

        Ok(decoded)
    }

    pub fn generate_tokens(
        &mut self,
        py: Python,
        start_tokens: Vec<u32>,
        max_new_tokens: usize,
    ) -> PyResult<Vec<u32>> {
        py.allow_threads(move || {
            let device = self.inner.embedding.embeddings().device().clone();
            let mut current_tokens = start_tokens.clone();

            // 1. Prefill
            let input = Tensor::new(start_tokens.as_slice(), &device)
                .map_err(|e| pyo3::exceptions::PyRuntimeError::new_err(e.to_string()))?
                .unsqueeze(0) // Batch size 1
                .map_err(|e| pyo3::exceptions::PyRuntimeError::new_err(e.to_string()))?;

            let logits = self
                .inner
                .forward(&input, &mut self.w_states)
                .map_err(|e| pyo3::exceptions::PyRuntimeError::new_err(e.to_string()))?;

            // Sample first token from last position
            let (_b, seq_len, _v) = logits
                .dims3()
                .map_err(|e| pyo3::exceptions::PyRuntimeError::new_err(e.to_string()))?;
            let last_logits = logits
                .i((0, seq_len - 1))
                .map_err(|e| pyo3::exceptions::PyRuntimeError::new_err(e.to_string()))?;

            let next_token = last_logits
                .argmax(0)
                .map_err(|e| pyo3::exceptions::PyRuntimeError::new_err(e.to_string()))?
                .to_scalar::<u32>()
                .map_err(|e| pyo3::exceptions::PyRuntimeError::new_err(e.to_string()))?;

            current_tokens.push(next_token);

            // 2. Decode Loop
            for _ in 1..max_new_tokens {
                let last_token = *current_tokens.last().unwrap();
                let input = Tensor::new(&[last_token], &device)
                    .map_err(|e| pyo3::exceptions::PyRuntimeError::new_err(e.to_string()))?;

                let logits = self
                    .inner
                    .forward_one(&input, &mut self.w_states)
                    .map_err(|e| pyo3::exceptions::PyRuntimeError::new_err(e.to_string()))?;

                let logits_v = logits
                    .flatten_all()
                    .map_err(|e| pyo3::exceptions::PyRuntimeError::new_err(e.to_string()))?;

                let next_token = logits_v
                    .argmax(0)
                    .map_err(|e| pyo3::exceptions::PyRuntimeError::new_err(e.to_string()))?
                    .to_scalar::<u32>()
                    .map_err(|e| pyo3::exceptions::PyRuntimeError::new_err(e.to_string()))?;

                current_tokens.push(next_token);
            }

            Ok(current_tokens)
        })
    }
}

/// Python wrapper for BitLlama model (Training)
#[cfg(feature = "python")]
#[pyclass(name = "PyTrainer")]
pub struct PyTrainer {
    model: BitLlama,
    varmap: VarMap,
    optimizer: ScheduleFreeOptimizer,
    sorted_vars: Vec<Var>, // For deterministic gradient ordering
}

#[cfg(feature = "python")]
#[pymethods]
impl PyTrainer {
    #[new]
    #[pyo3(signature = (config, checkpoint_path=None, device=None))]
    pub fn new(
        config: BitLlamaConfig,
        checkpoint_path: Option<&str>,
        device: Option<&str>,
    ) -> PyResult<Self> {
        let device = match device {
            Some("cuda") => candle_core::Device::new_cuda(0).map_err(|e| {
                pyo3::exceptions::PyValueError::new_err(format!("CUDA error: {}", e))
            })?,
            Some("cpu") | None => candle_core::Device::Cpu,
            Some(unknown) => {
                return Err(pyo3::exceptions::PyValueError::new_err(format!(
                    "Unsupported device: {}. Use 'cpu' or 'cuda'",
                    unknown
                )))
            }
        };

        let mut varmap = VarMap::new();
        let vb = candle_nn::VarBuilder::from_varmap(&varmap, DType::F32, &device);
        // Note: We use clone() heavily for config here.
        let model = BitLlama::load(config, vb)
            .map_err(|e| pyo3::exceptions::PyRuntimeError::new_err(e.to_string()))?;

        // Load Weights if provided
        if let Some(path) = checkpoint_path {
            varmap.load(path).map_err(|e| {
                pyo3::exceptions::PyRuntimeError::new_err(format!("Failed to load params: {}", e))
            })?;
        }

        // Initialize Optimizer
        // CRITICAL: Sort variables by name to ensure stable order for optimizer mapping
        let data = varmap.data().lock().unwrap();
        let mut named_vars: Vec<_> = data.iter().map(|(n, v)| (n.clone(), v.clone())).collect();
        // Drop lock before sorting/processing to minimize hold time
        drop(data);

        named_vars.sort_by(|a, b| a.0.cmp(&b.0));

        let vars: Vec<Var> = named_vars.iter().map(|(_, v)| v.clone()).collect();
        let sorted_vars = vars.clone();

        let params = ParamsScheduleFree {
            lr: 0.002,
            ..Default::default()
        };
        let optimizer = ScheduleFreeOptimizer::new(vars, params)
            .map_err(|e| pyo3::exceptions::PyRuntimeError::new_err(e.to_string()))?;

        Ok(Self {
            model,
            varmap,
            optimizer,
            sorted_vars,
        })
    }

    pub fn set_learning_rate(&mut self, lr: f64) {
        self.optimizer.set_learning_rate(lr);
    }

    #[pyo3(signature = (py_input_ids, py_targets))]
    pub fn train_step(
        &mut self,
        py: Python,
        py_input_ids: Vec<u32>,
        py_targets: Vec<u32>,
    ) -> PyResult<f64> {
        py.allow_threads(move || {
            let device = self.model.embedding.embeddings().device();
            let input_tensor = Tensor::new(py_input_ids.as_slice(), device)
                .map_err(|e| pyo3::exceptions::PyRuntimeError::new_err(e.to_string()))?
                .unsqueeze(0) // Batch dim 1
                .map_err(|e| pyo3::exceptions::PyRuntimeError::new_err(e.to_string()))?;
            let target_tensor = Tensor::new(py_targets.as_slice(), device)
                .map_err(|e| pyo3::exceptions::PyRuntimeError::new_err(e.to_string()))?
                .unsqueeze(0)
                .map_err(|e| pyo3::exceptions::PyRuntimeError::new_err(e.to_string()))?;

            // 1. Pre-step
            self.optimizer
                .pre_step()
                .map_err(|e| pyo3::exceptions::PyRuntimeError::new_err(e.to_string()))?;

            // 2. Forward
            // Create ephemeral w_states (zeroed) for this chunk
            let d_small = self.model.config.hidden_dim / 4;
            let mut w_states = Vec::new();
            for _ in 0..self.model.config.num_layers {
                let w = Tensor::zeros((d_small, d_small), DType::F32, device)
                    .map_err(|e| pyo3::exceptions::PyRuntimeError::new_err(e.to_string()))?;
                w_states.push(w);
            }

            let seq_len = py_input_ids.len();

            let logits = self
                .model
                .forward_chunkwise(&input_tensor, &mut w_states, seq_len)
                .map_err(|e| pyo3::exceptions::PyRuntimeError::new_err(e.to_string()))?;

            // 3. Loss
            let b_sz = 1;
            let logits = logits
                .reshape((b_sz * seq_len, logits.dim(2).unwrap()))
                .map_err(|e| pyo3::exceptions::PyRuntimeError::new_err(e.to_string()))?;
            let targets = target_tensor
                .reshape((b_sz * seq_len,))
                .map_err(|e| pyo3::exceptions::PyRuntimeError::new_err(e.to_string()))?;

            let loss = candle_nn::loss::cross_entropy(&logits, &targets)
                .map_err(|e| pyo3::exceptions::PyRuntimeError::new_err(e.to_string()))?;

            // 4. Backward
            let grads_store = loss
                .backward()
                .map_err(|e| pyo3::exceptions::PyRuntimeError::new_err(e.to_string()))?;

            // 5. Collect Gradients in determinstic order
            let mut grad_tensors = Vec::new();
            for var in &self.sorted_vars {
                if let Some(g) = grads_store.get(var) {
                    grad_tensors.push(g.clone());
                } else {
                    return Err(pyo3::exceptions::PyRuntimeError::new_err(
                        "Missing gradient for a variable. Graph disconnected?",
                    ));
                }
            }

            // 6. Optimizer Step
            self.optimizer
                .step(&grad_tensors)
                .map_err(|e| pyo3::exceptions::PyRuntimeError::new_err(e.to_string()))?;

            // 7. Return Loss
            let loss_val = loss
                .to_scalar::<f32>()
                .map_err(|e| pyo3::exceptions::PyRuntimeError::new_err(e.to_string()))?
                as f64;
            Ok(loss_val)
        })
    }

    #[pyo3(signature = (path))]
    pub fn save_checkpoint(&self, path: &str) -> PyResult<()> {
        self.varmap
            .save(path)
            .map_err(|e| pyo3::exceptions::PyRuntimeError::new_err(e.to_string()))?;

        // Save Optimizer State (Z)
        // Use sorted_vars to ensure same order as self.optimizer.z
        let mut z_map = std::collections::HashMap::new();

        let data = self.varmap.data().lock().unwrap();
        // We need to map var -> name to key the map.
        // Wait, saving requires "name" -> "tensor".
        // self.sorted_vars is just tensors.
        // But `data` (HashMap) has names.
        // Efficient way:
        // Iterate `data` and find index in `sorted_vars`? No, slow.
        // Better:
        // Re-construct the sorted list of (name, var) pairs similarly to `new`.
        // Since `Var` is RefCell/Arc id based, if we sort by name again, we get same order.
        let mut named_vars: Vec<_> = data.iter().collect();
        named_vars.sort_by(|a, b| a.0.cmp(b.0));

        for (i, (name, _var)) in named_vars.iter().enumerate() {
            if i < self.optimizer.z.len() {
                z_map.insert(format!("{}.z", name), self.optimizer.z[i].clone());
            }
        }

        let optim_path = format!("{}.optim", path);
        candle_core::safetensors::save(&z_map, &optim_path)
            .map_err(|e| pyo3::exceptions::PyRuntimeError::new_err(e.to_string()))?;

        Ok(())
    }
}
