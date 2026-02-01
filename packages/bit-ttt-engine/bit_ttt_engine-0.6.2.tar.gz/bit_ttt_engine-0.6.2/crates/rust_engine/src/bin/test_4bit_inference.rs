//! 4-bit Quantized Model Inference Test
//!
//! Tests 4-bit quantized Llama model inference (Attention-based).
//! Run with: cargo run --release --no-default-features --bin test_4bit_inference -- --model-path PATH

use anyhow::Result;
use candle_core::{DType, Device, IndexOp, Tensor};
use std::collections::HashMap;
use std::path::Path;
use tokenizers::Tokenizer;

/// Simple 4-bit Linear layer for testing
#[allow(dead_code)]
struct Linear4BitSimple {
    weight_packed: Tensor,
    scales: Tensor,
    bias: Option<Tensor>,
    in_features: usize,
    out_features: usize,
    group_size: usize,
}

impl Linear4BitSimple {
    fn new(
        weight_packed: Tensor,
        scales: Tensor,
        bias: Option<Tensor>,
        in_features: usize,
        out_features: usize,
        group_size: usize,
    ) -> Self {
        Self {
            weight_packed,
            scales,
            bias,
            in_features,
            out_features,
            group_size,
        }
    }

    fn forward(&self, x: &Tensor) -> Result<Tensor> {
        // Use fused GEMM
        let output = cortex_rust::kernels::matmul_4bit::gemm_4bit(
            x,
            &self.weight_packed,
            &self.scales,
            self.group_size,
        )?;

        // Add bias
        let output = match &self.bias {
            Some(bias) => output.broadcast_add(bias)?,
            None => output,
        };

        Ok(output)
    }
}

fn load_4bit_linear(
    tensors: &HashMap<String, Tensor>,
    prefix: &str,
    in_dim: usize,
    out_dim: usize,
    group_size: usize,
    device: &Device,
) -> Result<Linear4BitSimple> {
    let weight_key = format!("{}.weight_4bit", prefix);
    let scales_key = format!("{}.scales_4bit", prefix);
    let bias_key = format!("{}.bias", prefix);

    let weight = tensors
        .get(&weight_key)
        .ok_or_else(|| anyhow::anyhow!("Missing {}", weight_key))?
        .to_device(device)?;

    let scales = tensors
        .get(&scales_key)
        .ok_or_else(|| anyhow::anyhow!("Missing {}", scales_key))?
        .to_device(device)?;

    let bias = tensors
        .get(&bias_key)
        .map(|t| t.to_device(device))
        .transpose()?;

    Ok(Linear4BitSimple::new(
        weight, scales, bias, in_dim, out_dim, group_size,
    ))
}

fn main() -> Result<()> {
    let args: Vec<String> = std::env::args().collect();
    let model_path = args
        .iter()
        .position(|x| x == "--model-path")
        .and_then(|i| args.get(i + 1))
        .map(|s| s.as_str())
        .unwrap_or("benchmark/tinyllama-4bit");

    let prompt = args
        .iter()
        .position(|x| x == "--prompt")
        .and_then(|i| args.get(i + 1))
        .map(|s| s.as_str())
        .unwrap_or("The capital of France is");

    let use_cpu = args.iter().any(|x| x == "--cpu");

    println!("🧪 4-bit Inference Test");
    println!("========================");
    println!("Model: {}", model_path);
    println!("Prompt: {}", prompt);

    let device = if use_cpu {
        println!("Device: CPU (forced)");
        Device::Cpu
    } else {
        match Device::cuda_if_available(0) {
            Ok(dev) => {
                println!("Device: CUDA (GPU)");
                dev
            }
            Err(_) => {
                println!("Device: CPU (CUDA not available)");
                Device::Cpu
            }
        }
    };
    println!();

    // Load config
    let config_path = Path::new(model_path).join("config.json");
    let config_str = std::fs::read_to_string(&config_path)?;
    let config: serde_json::Value = serde_json::from_str(&config_str)?;

    let hidden_size = config["hidden_size"].as_u64().unwrap() as usize;
    let num_layers = config["num_hidden_layers"].as_u64().unwrap() as usize;
    let vocab_size = config["vocab_size"].as_u64().unwrap() as usize;
    let group_size = config["quantization"]["group_size"].as_u64().unwrap_or(128) as usize;

    println!("Config:");
    println!("  hidden_size: {}", hidden_size);
    println!("  num_layers: {}", num_layers);
    println!("  vocab_size: {}", vocab_size);
    println!("  group_size: {}", group_size);
    println!();

    // Load tokenizer
    println!("Loading tokenizer...");
    let tokenizer_path = Path::new(model_path).join("tokenizer.json");
    let tokenizer = Tokenizer::from_file(&tokenizer_path)
        .map_err(|e| anyhow::anyhow!("Tokenizer error: {}", e))?;

    // Encode prompt
    let encoding = tokenizer
        .encode(prompt, false)
        .map_err(|e| anyhow::anyhow!("Encoding error: {}", e))?;
    let input_ids: Vec<u32> = encoding.get_ids().to_vec();
    println!("Input tokens: {:?}", input_ids);

    // Load model weights
    println!("\nLoading model weights...");
    let model_file = Path::new(model_path).join("model.safetensors");
    let tensors = candle_core::safetensors::load(&model_file, &device)?;

    println!("Loaded {} tensors", tensors.len());

    // Test single layer forward pass
    println!("\n=== Testing Layer 0 Q-Proj (4-bit) ===");

    let q_proj = load_4bit_linear(
        &tensors,
        "model.layers.0.self_attn.q_proj",
        hidden_size,
        hidden_size,
        group_size,
        &device,
    )?;

    println!("Q-Proj loaded:");
    println!("  weight_packed: {:?}", q_proj.weight_packed.dims());
    println!("  scales: {:?}", q_proj.scales.dims());

    // Create dummy input
    let seq_len = input_ids.len();
    let dummy_input = Tensor::randn(0.0f32, 1.0, (1, seq_len, hidden_size), &device)?;
    let dummy_input_2d = dummy_input.reshape((seq_len, hidden_size))?;

    println!("\nInput shape: {:?}", dummy_input_2d.dims());

    // Forward pass
    let output = q_proj.forward(&dummy_input_2d)?;
    println!("Output shape: {:?}", output.dims());

    // Stats
    let output_vec: Vec<f32> = output.flatten_all()?.to_vec1()?;
    let mean: f32 = output_vec.iter().sum::<f32>() / output_vec.len() as f32;
    let std: f32 = (output_vec.iter().map(|x| (x - mean).powi(2)).sum::<f32>()
        / output_vec.len() as f32)
        .sqrt();

    println!("\nOutput stats:");
    println!("  mean: {:.6}", mean);
    println!("  std: {:.6}", std);
    println!(
        "  min: {:.6}",
        output_vec.iter().cloned().fold(f32::INFINITY, f32::min)
    );
    println!(
        "  max: {:.6}",
        output_vec.iter().cloned().fold(f32::NEG_INFINITY, f32::max)
    );

    // Test embedding lookup
    println!("\n=== Testing Embedding ===");
    let embed_weight = tensors
        .get("model.embed_tokens.weight")
        .ok_or_else(|| anyhow::anyhow!("Missing embed_tokens"))?
        .to_device(&device)?
        .to_dtype(DType::F32)?;

    println!("Embedding weight: {:?}", embed_weight.dims());

    let input_tensor = Tensor::new(&input_ids[..], &device)?;
    let embeddings = embed_weight.index_select(&input_tensor, 0)?;
    println!("Embeddings shape: {:?}", embeddings.dims());

    let embed_vec: Vec<f32> = embeddings.flatten_all()?.to_vec1()?;
    let e_mean: f32 = embed_vec.iter().sum::<f32>() / embed_vec.len() as f32;
    println!("Embedding mean: {:.6}", e_mean);

    // Test lm_head
    println!("\n=== Testing LM Head (4-bit) ===");
    let lm_head = load_4bit_linear(
        &tensors,
        "lm_head",
        hidden_size,
        vocab_size,
        group_size,
        &device,
    )?;

    println!("LM Head loaded:");
    println!("  weight_packed: {:?}", lm_head.weight_packed.dims());
    println!("  scales: {:?}", lm_head.scales.dims());

    // Forward through lm_head with last embedding
    let last_hidden = embeddings.i((seq_len - 1, ..))?;
    let last_hidden_2d = last_hidden.reshape((1, hidden_size))?;
    let logits = lm_head.forward(&last_hidden_2d)?;

    println!("Logits shape: {:?}", logits.dims());

    // Get top 5 predictions
    let logits_vec: Vec<f32> = logits.flatten_all()?.to_vec1()?;
    let mut indexed: Vec<(usize, f32)> = logits_vec
        .iter()
        .enumerate()
        .map(|(i, &v)| (i, v))
        .collect();
    indexed.sort_by(|a, b| b.1.partial_cmp(&a.1).unwrap());

    println!("\nTop 5 predictions:");
    for (rank, (token_id, score)) in indexed.iter().take(5).enumerate() {
        let token = tokenizer
            .decode(&[*token_id as u32], false)
            .unwrap_or_else(|_| format!("[{}]", token_id));
        println!(
            "  {}. {} (id={}) score={:.4}",
            rank + 1,
            token,
            token_id,
            score
        );
    }

    // Check if "Paris" is in top predictions
    let paris_tokens = tokenizer
        .encode("Paris", false)
        .map_err(|e| anyhow::anyhow!("Encoding error: {}", e))?;
    let paris_id = paris_tokens.get_ids()[0] as usize;
    let paris_rank = indexed.iter().position(|(id, _)| *id == paris_id);

    println!("\n\"Paris\" token id: {}", paris_id);
    if let Some(rank) = paris_rank {
        println!(
            "\"Paris\" rank: {} (score: {:.4})",
            rank + 1,
            indexed[rank].1
        );
    } else {
        println!("\"Paris\" not in top predictions");
    }

    println!("\n✅ 4-bit inference test completed!");

    Ok(())
}
