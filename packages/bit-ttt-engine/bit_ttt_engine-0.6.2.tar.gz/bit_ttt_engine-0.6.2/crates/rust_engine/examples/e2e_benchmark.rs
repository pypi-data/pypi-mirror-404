//! E2E Inference Benchmark
//!
//! Measures actual token generation speed (tok/s) for GGUF models.
//!
//! Usage:
//!   cargo run --release --no-default-features --example e2e_benchmark -- \
//!     --model path/to/model.gguf \
//!     --tokens 50 \
//!     --warmup 5 \
//!     --gpu

use anyhow::{Context, Result};
use candle_core::{Device, Tensor};
use cortex_rust::GgufModel;
use std::path::PathBuf;
use std::time::Instant;

/// Benchmark configuration
struct Config {
    model_path: PathBuf,
    tokens: usize,
    warmup: usize,
    gpu: bool,
    prompt: String,
}

impl Default for Config {
    fn default() -> Self {
        Self {
            model_path: PathBuf::from("model.gguf"),
            tokens: 50,
            warmup: 5,
            gpu: false,
            prompt: "The quick brown fox".to_string(),
        }
    }
}

fn parse_args() -> Config {
    let args: Vec<String> = std::env::args().collect();
    let mut config = Config::default();

    let mut i = 1;
    while i < args.len() {
        match args[i].as_str() {
            "--model" | "-m" => {
                if i + 1 < args.len() {
                    config.model_path = PathBuf::from(&args[i + 1]);
                    i += 1;
                }
            }
            "--tokens" | "-t" => {
                if i + 1 < args.len() {
                    config.tokens = args[i + 1].parse().unwrap_or(50);
                    i += 1;
                }
            }
            "--warmup" | "-w" => {
                if i + 1 < args.len() {
                    config.warmup = args[i + 1].parse().unwrap_or(5);
                    i += 1;
                }
            }
            "--gpu" => {
                config.gpu = true;
            }
            "--prompt" | "-p" => {
                if i + 1 < args.len() {
                    config.prompt = args[i + 1].clone();
                    i += 1;
                }
            }
            "--help" | "-h" => {
                println!("Usage: e2e_benchmark [OPTIONS]");
                println!();
                println!("Options:");
                println!("  -m, --model <PATH>    Path to GGUF model");
                println!("  -t, --tokens <N>      Tokens to generate [default: 50]");
                println!("  -w, --warmup <N>      Warmup tokens [default: 5]");
                println!("  -p, --prompt <TEXT>   Prompt [default: 'The quick brown fox']");
                println!("      --gpu             Use GPU if available");
                println!("  -h, --help            Show this help");
                std::process::exit(0);
            }
            _ => {}
        }
        i += 1;
    }

    config
}

/// Simple greedy sampling from logits
fn sample_greedy(logits: &Tensor) -> Result<u32> {
    let (batch, seq_len, _vocab) = logits.dims3()?;
    // Get last token's logits: [batch, vocab]
    let last_logits = logits.narrow(1, seq_len - 1, 1)?.squeeze(1)?;
    // Argmax over vocab dimension
    let token_ids = last_logits.argmax(1)?;  // [batch]
    // Get first batch element
    let token_id = if batch == 1 {
        token_ids.squeeze(0)?.to_scalar::<u32>()?
    } else {
        token_ids.get(0)?.to_scalar::<u32>()?
    };
    Ok(token_id)
}

/// Simple tokenizer (byte-level, for benchmarking only)
fn simple_tokenize(text: &str) -> Vec<i64> {
    // For benchmarking, just use ASCII values as token IDs
    // Real usage should use proper tokenizer
    text.bytes().map(|b| b as i64).collect()
}

fn main() -> Result<()> {
    let config = parse_args();

    println!("╔════════════════════════════════════════════════════════════════╗");
    println!("║          Bit-TTT-Engine E2E Inference Benchmark                ║");
    println!("╚════════════════════════════════════════════════════════════════╝\n");

    // Select device
    let device = if config.gpu {
        match Device::new_cuda(0) {
            Ok(d) => {
                println!("🎮 Device: CUDA (GPU)");
                d
            }
            Err(e) => {
                println!("⚠️  CUDA not available ({}), falling back to CPU", e);
                Device::Cpu
            }
        }
    } else {
        println!("🖥️  Device: CPU");
        Device::Cpu
    };

    println!("📁 Model: {:?}", config.model_path);
    println!("📝 Prompt: \"{}\"", config.prompt);
    println!("🔢 Tokens to generate: {} (+ {} warmup)", config.tokens, config.warmup);
    println!();

    // Load model
    println!("⏳ Loading model...");
    let load_start = Instant::now();
    let mut model = GgufModel::load(&config.model_path, &device)
        .context("Failed to load model")?;
    let load_time = load_start.elapsed();
    println!("✅ Model loaded in {:.2}s", load_time.as_secs_f64());
    println!("   Layers: {}", model.config().num_layers);
    println!("   Hidden: {}", model.config().hidden_dim);
    println!("   Vocab: {}", model.config().vocab_size);
    println!();

    // Tokenize prompt
    let prompt_tokens = simple_tokenize(&config.prompt);
    println!("📊 Prompt tokens: {}", prompt_tokens.len());

    // Create input tensor
    let mut tokens: Vec<i64> = prompt_tokens.clone();
    let input = Tensor::from_vec(tokens.clone(), (1, tokens.len()), &device)?;

    // === Prefill ===
    println!("\n=== Prefill ===");
    let prefill_start = Instant::now();
    let logits = model.forward(&input, 0)?;
    let prefill_time = prefill_start.elapsed();
    println!(
        "Prefill: {} tokens in {:.2}ms ({:.1} tok/s)",
        tokens.len(),
        prefill_time.as_secs_f64() * 1000.0,
        tokens.len() as f64 / prefill_time.as_secs_f64()
    );

    // Sample first token
    let first_token = sample_greedy(&logits)?;
    tokens.push(first_token as i64);

    // === Warmup ===
    println!("\n=== Warmup ({} tokens) ===", config.warmup);
    let warmup_start = Instant::now();
    for _ in 0..config.warmup {
        let pos = tokens.len() - 1;
        let input = Tensor::from_vec(vec![tokens[pos]], (1, 1), &device)?;
        let logits = model.forward(&input, pos)?;
        let next_token = sample_greedy(&logits)?;
        tokens.push(next_token as i64);
        print!(".");
        std::io::Write::flush(&mut std::io::stdout())?;
    }
    let warmup_time = warmup_start.elapsed();
    println!(
        "\nWarmup: {} tokens in {:.2}ms ({:.1} tok/s)",
        config.warmup,
        warmup_time.as_secs_f64() * 1000.0,
        config.warmup as f64 / warmup_time.as_secs_f64()
    );

    // === Benchmark ===
    println!("\n=== Benchmark ({} tokens) ===", config.tokens);
    let mut decode_times: Vec<f64> = Vec::with_capacity(config.tokens);

    for i in 0..config.tokens {
        let pos = tokens.len() - 1;
        let input = Tensor::from_vec(vec![tokens[pos]], (1, 1), &device)?;

        let step_start = Instant::now();
        let logits = model.forward(&input, pos)?;
        let next_token = sample_greedy(&logits)?;
        let step_time = step_start.elapsed().as_secs_f64() * 1000.0;

        decode_times.push(step_time);
        tokens.push(next_token as i64);

        // Progress indicator
        if (i + 1) % 10 == 0 || i == config.tokens - 1 {
            print!("\r  Progress: {}/{} tokens", i + 1, config.tokens);
            std::io::Write::flush(&mut std::io::stdout())?;
        }
    }
    println!();

    // === Results ===
    let total_time: f64 = decode_times.iter().sum();
    let avg_time = total_time / decode_times.len() as f64;
    let min_time = decode_times.iter().cloned().fold(f64::INFINITY, f64::min);
    let max_time = decode_times.iter().cloned().fold(f64::NEG_INFINITY, f64::max);
    let tok_per_sec = 1000.0 / avg_time;

    // Calculate percentiles
    let mut sorted_times = decode_times.clone();
    sorted_times.sort_by(|a, b| a.partial_cmp(b).unwrap());
    let p50 = sorted_times[sorted_times.len() / 2];
    let p90_idx = ((sorted_times.len() as f64 * 0.9) as usize).min(sorted_times.len() - 1);
    let p90 = sorted_times[p90_idx];
    let p99_idx = ((sorted_times.len() as f64 * 0.99) as usize).min(sorted_times.len() - 1);
    let p99 = sorted_times[p99_idx];

    println!("\n╔════════════════════════════════════════════════════════════════╗");
    println!("║                         RESULTS                                ║");
    println!("╚════════════════════════════════════════════════════════════════╝");
    println!();
    println!("📊 Decode Performance:");
    println!("   Total tokens: {}", config.tokens);
    println!("   Total time:   {:.2}ms", total_time);
    println!();
    println!("   ┌─────────────────────────────────────┐");
    println!("   │  Throughput: {:>6.2} tok/s          │", tok_per_sec);
    println!("   └─────────────────────────────────────┘");
    println!();
    println!("📈 Latency (per token):");
    println!("   Min:  {:>8.2}ms", min_time);
    println!("   Avg:  {:>8.2}ms", avg_time);
    println!("   Max:  {:>8.2}ms", max_time);
    println!();
    println!("📉 Percentiles:");
    println!("   P50:  {:>8.2}ms", p50);
    println!("   P90:  {:>8.2}ms", p90);
    println!("   P99:  {:>8.2}ms", p99);
    println!();

    // Device info
    println!("🔧 Configuration:");
    println!("   Device:     {:?}", device);
    println!("   Model:      {:?}", config.model_path.file_name().unwrap_or_default());
    // Rough parameter estimate: ~4 * hidden^2 * layers (Q,K,V,O + MLP)
    let params_m = (4 * model.config().hidden_dim * model.config().hidden_dim * model.config().num_layers) / 1_000_000;
    println!("   Parameters: ~{}M", params_m);

    Ok(())
}
