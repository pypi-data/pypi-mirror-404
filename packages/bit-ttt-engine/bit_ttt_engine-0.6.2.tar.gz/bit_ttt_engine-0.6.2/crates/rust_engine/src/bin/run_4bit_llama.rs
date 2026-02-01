//! Run 4-bit Quantized Llama Inference
//!
//! Usage: cargo run --release --no-default-features --bin run_4bit_llama -- \
//!        --model-path benchmark/tinyllama-4bit \
//!        --prompt "The capital of France is" \
//!        --max-tokens 20

use anyhow::Result;
use candle_core::Device;
use std::path::Path;
use tokenizers::Tokenizer;

use cortex_rust::model::{Llama4Bit, Llama4BitConfig};

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

    let max_tokens: usize = args
        .iter()
        .position(|x| x == "--max-tokens")
        .and_then(|i| args.get(i + 1))
        .and_then(|s| s.parse().ok())
        .unwrap_or(20);

    let temperature: f64 = args
        .iter()
        .position(|x| x == "--temperature")
        .and_then(|i| args.get(i + 1))
        .and_then(|s| s.parse().ok())
        .unwrap_or(0.0); // Greedy by default

    let use_cpu = args.iter().any(|x| x == "--cpu");
    let use_paged = args.iter().any(|x| x == "--paged");

    println!("🦙 4-bit Llama Inference");
    println!("========================");
    println!("Model: {}", model_path);
    println!("Prompt: \"{}\"", prompt);
    println!("Max tokens: {}", max_tokens);
    println!("Temperature: {}", temperature);

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
    let config_json: serde_json::Value = serde_json::from_str(&config_str)?;

    let config = Llama4BitConfig {
        hidden_size: config_json["hidden_size"].as_u64().unwrap() as usize,
        num_layers: config_json["num_hidden_layers"].as_u64().unwrap() as usize,
        n_heads: config_json["num_attention_heads"].as_u64().unwrap() as usize,
        n_kv_heads: config_json["num_key_value_heads"].as_u64().unwrap() as usize,
        vocab_size: config_json["vocab_size"].as_u64().unwrap() as usize,
        group_size: config_json["quantization"]["group_size"]
            .as_u64()
            .unwrap_or(128) as usize,
        rope_theta: config_json["rope_theta"].as_f64().unwrap_or(10000.0),
        max_position_embeddings: config_json["max_position_embeddings"]
            .as_u64()
            .unwrap_or(2048) as usize,
    };

    println!("Config:");
    println!("  hidden_size: {}", config.hidden_size);
    println!("  num_layers: {}", config.num_layers);
    println!("  n_heads: {}", config.n_heads);
    println!("  n_kv_heads: {}", config.n_kv_heads);
    println!("  vocab_size: {}", config.vocab_size);
    println!("  group_size: {}", config.group_size);
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
    println!("Input tokens: {:?} (len={})", input_ids, input_ids.len());

    // Load model
    println!("\nLoading model...");
    let model_file = Path::new(model_path).join("model.safetensors");
    let tensors = candle_core::safetensors::load(&model_file, &device)?;
    println!("Loaded {} tensors", tensors.len());

    let mut model = Llama4Bit::load(&tensors, config.clone(), &device)?;

    // Generate
    println!(
        "\nGenerating{}...",
        if use_paged { " (PagedAttention)" } else { "" }
    );
    let start = std::time::Instant::now();
    #[cfg(feature = "cuda")]
    let output_tokens = if use_paged {
        model.generate_paged(&input_ids, max_tokens, temperature)?
    } else {
        model.generate(&input_ids, max_tokens, temperature)?
    };
    #[cfg(not(feature = "cuda"))]
    let output_tokens = model.generate(&input_ids, max_tokens, temperature)?;
    let elapsed = start.elapsed();

    println!("Output tokens: {:?}", output_tokens);

    // Decode
    let output_text = tokenizer
        .decode(&output_tokens, true)
        .map_err(|e| anyhow::anyhow!("Decode error: {}", e))?;

    let new_tokens = output_tokens.len() - input_ids.len();
    let tokens_per_sec = new_tokens as f64 / elapsed.as_secs_f64();

    println!("\n=== Output ===");
    println!("{}", output_text);
    println!();
    println!("=== Stats ===");
    println!("Generated: {} tokens", new_tokens);
    println!("Time: {:.2}s", elapsed.as_secs_f64());
    println!("Speed: {:.2} tokens/s", tokens_per_sec);

    // Check if Paris is mentioned
    if output_text.to_lowercase().contains("paris") {
        println!("\n✅ \"Paris\" found in output!");
    }

    Ok(())
}
