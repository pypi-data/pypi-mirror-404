//! GGUF File Loader
//!
//! Loads GGUF format models (llama.cpp compatible) using candle's quantized module.
//! Provides automatic config extraction from GGUF metadata.
//!
//! # Example
//! ```ignore
//! let mut loader = GgufLoader::load("model.gguf")?;
//! let config = loader.to_config()?;
//! let tensor = loader.tensor("blk.0.attn_q.weight", &device)?;
//! ```

use anyhow::{anyhow, Context, Result};
use candle_core::quantized::gguf_file::{Content, Value};
use candle_core::quantized::{GgmlDType, QTensor};
use candle_core::Device;
use std::fs::File;
use std::io::{BufReader, Seek, SeekFrom};
use std::path::{Path, PathBuf};
use tracing::info;

use super::config::BitLlamaConfig;
use super::detector::{ModelArchitecture, QuantizationType};

/// GGUF Model Loader
///
/// Wraps candle's GGUF parser with convenience methods for
/// config extraction and tensor loading.
pub struct GgufLoader {
    /// Parsed GGUF content (metadata + tensor info)
    content: Content,
    /// File reader (kept open for tensor loading)
    reader: BufReader<File>,
    /// Original file path
    path: PathBuf,
    /// Cached architecture string
    architecture: Option<String>,
}

impl GgufLoader {
    /// Load a GGUF file
    ///
    /// # Arguments
    /// * `path` - Path to the .gguf file
    ///
    /// # Returns
    /// * `GgufLoader` instance ready for config extraction and tensor loading
    pub fn load<P: AsRef<Path>>(path: P) -> Result<Self> {
        let path = path.as_ref().to_path_buf();
        info!("📦 Loading GGUF file: {:?}", path);

        let file = File::open(&path).context("Failed to open GGUF file")?;
        let mut reader = BufReader::new(file);

        let content = Content::read(&mut reader).context("Failed to parse GGUF content")?;

        info!(
            "   ✅ GGUF v{} loaded: {} tensors, {} metadata keys",
            match content.magic {
                candle_core::quantized::gguf_file::VersionedMagic::GgufV1 => "1",
                candle_core::quantized::gguf_file::VersionedMagic::GgufV2 => "2",
                candle_core::quantized::gguf_file::VersionedMagic::GgufV3 => "3",
            },
            content.tensor_infos.len(),
            content.metadata.len()
        );

        Ok(Self {
            content,
            reader,
            path,
            architecture: None,
        })
    }

    /// Get the file path
    pub fn path(&self) -> &Path {
        &self.path
    }

    /// Get model architecture from metadata
    ///
    /// Reads `general.architecture` key (e.g., "llama", "mistral", "phi")
    pub fn architecture(&mut self) -> Result<&str> {
        if self.architecture.is_none() {
            let arch = self
                .get_string("general.architecture")
                .context("Missing general.architecture in GGUF metadata")?;
            self.architecture = Some(arch);
        }
        Ok(self.architecture.as_ref().unwrap())
    }

    /// Get model name from metadata
    pub fn model_name(&self) -> Option<String> {
        self.get_string("general.name").ok()
    }

    /// Generate BitLlamaConfig from GGUF metadata
    ///
    /// Maps GGUF metadata keys to BitLlamaConfig fields.
    /// Architecture-specific keys are prefixed (e.g., `llama.context_length`).
    pub fn to_config(&mut self) -> Result<BitLlamaConfig> {
        let arch = self.architecture()?.to_string();
        info!("   🔍 Detected architecture: {}", arch);

        // Architecture-specific prefix for metadata keys
        let prefix = &arch;

        // Required fields
        let vocab_size = self
            .get_u64(&format!("{}.vocab_size", prefix))
            .or_else(|_| self.get_u64("tokenizer.ggml.vocab_size"))
            .unwrap_or(32000) as usize;

        let hidden_dim = self
            .get_u64(&format!("{}.embedding_length", prefix))
            .context("Missing embedding_length")? as usize;

        let num_layers = self
            .get_u64(&format!("{}.block_count", prefix))
            .context("Missing block_count")? as usize;

        let n_heads = self
            .get_u64(&format!("{}.attention.head_count", prefix))
            .context("Missing attention.head_count")? as usize;

        let n_kv_heads = self
            .get_u64(&format!("{}.attention.head_count_kv", prefix))
            .unwrap_or(n_heads as u64) as usize;

        // Optional fields
        let intermediate_dim = self
            .get_u64(&format!("{}.feed_forward_length", prefix))
            .map(|v| v as usize)
            .ok();

        let rope_theta = self
            .get_f32(&format!("{}.rope.freq_base", prefix))
            .unwrap_or(10000.0) as f64;

        let max_position_embeddings = self
            .get_u64(&format!("{}.context_length", prefix))
            .unwrap_or(2048) as usize;

        // RMS norm epsilon
        let rms_norm_eps = self
            .get_f32(&format!("{}.attention.layer_norm_rms_epsilon", prefix))
            .unwrap_or(1e-5) as f64;

        info!(
            "   📊 Config: {}L, {}H, {}KV, {}D, eps={:.0e}",
            num_layers, n_heads, n_kv_heads, hidden_dim, rms_norm_eps
        );

        // Determine architecture and activation from arch string
        let (model_arch, activation) = match arch.to_lowercase().as_str() {
            "gemma" => (
                super::config::ModelArch::Gemma,
                super::config::ActivationType::GELU,
            ),
            "gemma2" => (
                super::config::ModelArch::Gemma2,
                super::config::ActivationType::GELU,
            ),
            _ => (
                super::config::ModelArch::Llama,
                super::config::ActivationType::SiLU,
            ),
        };

        info!(
            "   🔧 Architecture: {:?}, Activation: {:?}",
            model_arch, activation
        );

        Ok(BitLlamaConfig {
            arch: model_arch,
            vocab_size,
            hidden_dim,
            num_layers,
            n_heads,
            n_kv_heads,
            intermediate_dim,
            inner_lr: 0.01, // Default TTT learning rate
            n_gpu_layers: None,
            rope_theta,
            max_position_embeddings,
            lm_head_cpu: false,
            sliding_window: None,
            attention_sink_size: None,
            quantization: None, // GGUF uses its own quantization
            rms_norm_eps,
            activation,
        })
    }

    /// Load a tensor by name
    ///
    /// # Arguments
    /// * `name` - Tensor name (e.g., "blk.0.attn_q.weight")
    /// * `device` - Target device (CPU/CUDA)
    ///
    /// # Returns
    /// * `QTensor` - Quantized tensor ready for computation
    pub fn tensor(&mut self, name: &str, device: &Device) -> Result<QTensor> {
        // Reset reader position
        self.reader.seek(SeekFrom::Start(0))?;

        self.content
            .tensor(&mut self.reader, name, device)
            .map_err(|e| anyhow!("Failed to load tensor '{}': {}", name, e))
    }

    /// Check if a tensor exists
    pub fn has_tensor(&self, name: &str) -> bool {
        self.content.tensor_infos.contains_key(name)
    }

    /// List all tensor names
    pub fn tensor_names(&self) -> Vec<&str> {
        self.content
            .tensor_infos
            .keys()
            .map(|s| s.as_str())
            .collect()
    }

    /// Get tensor info (shape, dtype) without loading data
    pub fn tensor_info(&self, name: &str) -> Option<TensorInfo> {
        self.content.tensor_infos.get(name).map(|info| TensorInfo {
            name: name.to_string(),
            shape: info.shape.dims().to_vec(),
            dtype: info.ggml_dtype,
        })
    }

    /// Get all tensor infos
    pub fn all_tensor_infos(&self) -> Vec<TensorInfo> {
        self.content
            .tensor_infos
            .iter()
            .map(|(name, info)| TensorInfo {
                name: name.clone(),
                shape: info.shape.dims().to_vec(),
                dtype: info.ggml_dtype,
            })
            .collect()
    }

    /// Detect quantization type from tensors
    pub fn detect_quantization(&self) -> QuantizationType {
        // Sample a weight tensor to detect quantization
        for (name, info) in &self.content.tensor_infos {
            if name.contains("weight") && !name.contains("norm") {
                return match info.ggml_dtype {
                    GgmlDType::Q4_0 | GgmlDType::Q4_1 | GgmlDType::Q4K => QuantizationType::Int4,
                    GgmlDType::Q8_0 | GgmlDType::Q8_1 | GgmlDType::Q8K => QuantizationType::Int8,
                    GgmlDType::F16 => QuantizationType::FP16,
                    GgmlDType::F32 => QuantizationType::FP32,
                    _ => QuantizationType::Unknown,
                };
            }
        }
        QuantizationType::Unknown
    }

    /// Detect model architecture
    pub fn detect_architecture(&mut self) -> ModelArchitecture {
        if let Ok(arch) = self.architecture() {
            ModelArchitecture::from_str(arch)
        } else {
            ModelArchitecture::Unknown
        }
    }

    /// Get the number of layers
    pub fn num_layers(&mut self) -> Result<usize> {
        let arch = self.architecture()?.to_string();
        self.get_u64(&format!("{}.block_count", arch))
            .map(|v| v as usize)
    }

    /// Print model summary
    pub fn print_summary(&mut self) {
        println!("╔══════════════════════════════════════════════════════════════╗");
        println!("║                      GGUF MODEL SUMMARY                       ║");
        println!("╠══════════════════════════════════════════════════════════════╣");

        if let Some(name) = self.model_name() {
            println!("║ Name:          {:47} ║", truncate_str(&name, 47));
        }

        if let Ok(arch) = self.architecture() {
            println!("║ Architecture:  {:47} ║", arch);
        }

        println!("║ Quantization:  {:47?} ║", self.detect_quantization());
        println!("║ Tensors:       {:>47} ║", self.content.tensor_infos.len());
        println!("║ Metadata:      {:>47} ║", self.content.metadata.len());

        if let Ok(config) = self.to_config() {
            println!("╠══════════════════════════════════════════════════════════════╣");
            println!("║ Vocab Size:    {:>47} ║", config.vocab_size);
            println!("║ Hidden Dim:    {:>47} ║", config.hidden_dim);
            println!("║ Layers:        {:>47} ║", config.num_layers);
            println!("║ Heads:         {:>47} ║", config.n_heads);
            println!("║ KV Heads:      {:>47} ║", config.n_kv_heads);
            if let Some(ff) = config.intermediate_dim {
                println!("║ FF Dim:        {:>47} ║", ff);
            }
            println!("║ RoPE Theta:    {:>47.1} ║", config.rope_theta);
            println!("║ Max Position:  {:>47} ║", config.max_position_embeddings);
        }

        println!("╚══════════════════════════════════════════════════════════════╝");
    }

    // ========== Helper methods ==========

    /// Get string value from metadata
    fn get_string(&self, key: &str) -> Result<String> {
        self.content
            .metadata
            .get(key)
            .ok_or_else(|| anyhow!("Missing key: {}", key))?
            .to_string()
            .map(|s| s.to_owned())
            .map_err(|e| anyhow!("Invalid string for {}: {}", key, e))
    }

    /// Get u64 value from metadata (with auto-upcast)
    fn get_u64(&self, key: &str) -> Result<u64> {
        self.content
            .metadata
            .get(key)
            .ok_or_else(|| anyhow!("Missing key: {}", key))?
            .to_u64()
            .map_err(|e| anyhow!("Invalid u64 for {}: {}", key, e))
    }

    /// Get f32 value from metadata
    fn get_f32(&self, key: &str) -> Result<f32> {
        self.content
            .metadata
            .get(key)
            .ok_or_else(|| anyhow!("Missing key: {}", key))?
            .to_f32()
            .map_err(|e| anyhow!("Invalid f32 for {}: {}", key, e))
    }

    /// Get raw metadata value
    pub fn get_metadata(&self, key: &str) -> Option<&Value> {
        self.content.metadata.get(key)
    }

    /// Get all metadata keys
    pub fn metadata_keys(&self) -> Vec<&str> {
        self.content.metadata.keys().map(|s| s.as_str()).collect()
    }
}

/// Tensor information (without loading data)
#[derive(Debug, Clone)]
pub struct TensorInfo {
    pub name: String,
    pub shape: Vec<usize>,
    pub dtype: GgmlDType,
}

impl TensorInfo {
    /// Get number of elements
    pub fn numel(&self) -> usize {
        self.shape.iter().product()
    }

    /// Estimate size in bytes
    pub fn size_bytes(&self) -> usize {
        let block_size = self.dtype.block_size();
        let type_size = self.dtype.type_size();
        (self.numel() / block_size) * type_size
    }
}

/// Helper to truncate string for display
fn truncate_str(s: &str, max_len: usize) -> String {
    if s.len() <= max_len {
        s.to_string()
    } else {
        format!("{}...", &s[..max_len - 3])
    }
}

/// GGUF tensor name mappings
///
/// Maps standard GGUF tensor names to Bit-TTT internal names
pub mod tensor_names {
    /// Get embedding tensor name
    pub fn embedding() -> &'static str {
        "token_embd.weight"
    }

    /// Get output norm tensor name
    pub fn output_norm() -> &'static str {
        "output_norm.weight"
    }

    /// Get output (lm_head) tensor name
    pub fn output() -> &'static str {
        "output.weight"
    }

    /// Get layer tensor name
    pub fn layer_tensor(layer_idx: usize, name: &str) -> String {
        format!("blk.{}.{}", layer_idx, name)
    }

    /// Attention Q projection
    pub fn attn_q(layer_idx: usize) -> String {
        layer_tensor(layer_idx, "attn_q.weight")
    }

    /// Attention K projection
    pub fn attn_k(layer_idx: usize) -> String {
        layer_tensor(layer_idx, "attn_k.weight")
    }

    /// Attention V projection
    pub fn attn_v(layer_idx: usize) -> String {
        layer_tensor(layer_idx, "attn_v.weight")
    }

    /// Attention output projection
    pub fn attn_output(layer_idx: usize) -> String {
        layer_tensor(layer_idx, "attn_output.weight")
    }

    /// Attention norm
    pub fn attn_norm(layer_idx: usize) -> String {
        layer_tensor(layer_idx, "attn_norm.weight")
    }

    /// FFN gate projection
    pub fn ffn_gate(layer_idx: usize) -> String {
        layer_tensor(layer_idx, "ffn_gate.weight")
    }

    /// FFN up projection
    pub fn ffn_up(layer_idx: usize) -> String {
        layer_tensor(layer_idx, "ffn_up.weight")
    }

    /// FFN down projection
    pub fn ffn_down(layer_idx: usize) -> String {
        layer_tensor(layer_idx, "ffn_down.weight")
    }

    /// FFN norm
    pub fn ffn_norm(layer_idx: usize) -> String {
        layer_tensor(layer_idx, "ffn_norm.weight")
    }
}

#[cfg(test)]
mod tests {
    use super::*;

    #[test]
    fn test_tensor_names() {
        assert_eq!(tensor_names::embedding(), "token_embd.weight");
        assert_eq!(tensor_names::attn_q(0), "blk.0.attn_q.weight");
        assert_eq!(tensor_names::ffn_gate(5), "blk.5.ffn_gate.weight");
    }
}
