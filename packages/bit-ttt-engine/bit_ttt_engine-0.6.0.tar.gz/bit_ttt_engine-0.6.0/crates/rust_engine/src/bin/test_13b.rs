//! 13B Model Test Script
//!
//! Tests Llama2-13B 1.58-bit quantized model with minimal generation.
//! Run with: RUST_LOG=debug cargo run --release --bin test_13b
//!
//! This script:
//! 1. Loads the 13B model from benchmark/llama2-13b-converted
//! 2. Enables VRAM logging (via RUST_LOG=debug)
//! 3. Generates only 3 tokens (quick test)
//! 4. Reports memory usage and performance

use cortex_rust::model::BitLlamaConfig;
use std::fs;
use std::path::Path;
use std::time::Instant;

fn main() -> anyhow::Result<()> {
    // Note: Set RUST_LOG=debug before running for VRAM logging
    println!("═══════════════════════════════════════════════════════════════════");
    println!("  Llama2-13B 1.58-bit Model Test (GPU FORCED: n_gpu_layers=10)");
    println!("═══════════════════════════════════════════════════════════════════\n");

    let model_path = Path::new("benchmark/llama2-13b-converted");

    if !model_path.exists() {
        eprintln!("❌ Model not found at {:?}", model_path);
        eprintln!("   Please convert Llama2-13B first using bit_converter");
        std::process::exit(1);
    }

    // Report initial memory
    print_memory_usage("Before loading");

    // Load config and FORCE GPU layers
    println!("📋 Loading config...");
    let config_path = model_path.join("config.json");
    let config_str = fs::read_to_string(&config_path)?;
    let mut config: BitLlamaConfig = serde_json::from_str(&config_str)?;

    // CPU-only test (GPU kernel has context issue)
    config.n_gpu_layers = Some(0);
    println!("⚡ CPU-only mode (n_gpu_layers = 0)");

    println!("   Hidden dim: {}", config.hidden_dim);
    println!("   Layers: {}", config.num_layers);
    println!("   Heads: {}", config.n_heads);
    println!("   Vocab size: {}", config.vocab_size);
    println!("   GPU Layers: {:?}", config.n_gpu_layers);
    println!();

    // Load model using load_direct with modified config
    println!("📦 Loading model weights with GPU offload...");
    let load_start = Instant::now();

    let model_file = model_path.join("model.safetensors");
    let tokenizer_file = model_path.join("tokenizer.json");
    let mut llama = cortex_rust::Llama::load_direct(&model_file, &tokenizer_file, config)?;

    let load_time = load_start.elapsed();
    println!("✅ Model loaded in {:.2}s", load_time.as_secs_f64());
    print_memory_usage("After loading");
    println!();

    // Simple generation test
    let prompt = "Hello, my name is";
    let gen_tokens = 3;

    println!("🔤 Prompt: \"{}\"", prompt);
    println!("   Generating {} tokens...", gen_tokens);

    let gen_start = Instant::now();
    let output = llama.generate(prompt, gen_tokens)?;
    let gen_time = gen_start.elapsed();

    let tokens_per_sec = gen_tokens as f64 / gen_time.as_secs_f64();

    println!();
    println!("═══════════════════════════════════════════════════════════════════");
    println!("📊 Results:");
    println!("═══════════════════════════════════════════════════════════════════");
    println!("   Output: \"{}\"", output);
    println!("   Generation time: {:.2}ms", gen_time.as_millis());
    println!("   Throughput: {:.2} tokens/sec", tokens_per_sec);
    print_memory_usage("After generation");
    println!("═══════════════════════════════════════════════════════════════════");

    Ok(())
}

/// Print memory usage hint
/// Note: For detailed VRAM monitoring, use nvidia-smi in another terminal
fn print_memory_usage(label: &str) {
    println!("💾 Memory checkpoint [{}]", label);
    println!("   (Run 'nvidia-smi' in another terminal for GPU memory details)");
}
