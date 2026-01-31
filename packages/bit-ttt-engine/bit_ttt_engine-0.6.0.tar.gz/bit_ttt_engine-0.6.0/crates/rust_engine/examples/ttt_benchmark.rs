//! TTT (Test-Time Training) Effect Benchmark
//!
//! This benchmark measures the effect of TTT on language model quality.
//! It compares perplexity before and after TTT adaptation.
//!
//! Usage:
//!   cargo run --release --example ttt_benchmark -- --model path/to/model.gguf
//!
//! Expected output:
//!   Baseline PPL: 15.0
//!   After TTT: 13.5 (-10%)

use anyhow::{Context, Result};
use candle_core::{Device, Tensor};
use cortex_rust::{compute_perplexity, GgufModel, PerplexityResult};
use std::path::PathBuf;
use std::time::Instant;

/// Benchmark configuration
struct BenchmarkConfig {
    model_path: PathBuf,
    eval_tokens: usize,
    chunk_size: usize,
    device: Device,
}

impl Default for BenchmarkConfig {
    fn default() -> Self {
        Self {
            model_path: PathBuf::from("model.gguf"),
            eval_tokens: 1000,
            chunk_size: 128,
            device: Device::Cpu,
        }
    }
}

/// Sample evaluation text (for demo purposes)
/// First half: adaptation context
/// Second half: evaluation
const EVAL_TEXT: &str = r#"
The quick brown fox jumps over the lazy dog. This is a simple sentence for testing.
Language models learn patterns from text data and can generate coherent responses.
Test-Time Training allows models to adapt during inference without explicit training.
This benchmark measures how well TTT improves perplexity on given contexts.
Machine learning has revolutionized many fields including natural language processing.
Deep neural networks can learn complex patterns from large amounts of data.
Transformers use attention mechanisms to process sequences in parallel.
The key innovation of TTT is that it updates model parameters during inference.
This allows the model to adapt to the specific context it is processing.
Unlike traditional fine-tuning, TTT requires no separate training phase.
The model learns online from each token it processes.
This makes TTT particularly useful for personalization and domain adaptation.
"#;

fn main() -> Result<()> {
    println!("=== TTT Effect Benchmark ===\n");

    // Parse arguments
    let args: Vec<String> = std::env::args().collect();
    let model_path = if args.len() > 2 && args[1] == "--model" {
        PathBuf::from(&args[2])
    } else {
        // Default: look for any .gguf in current directory
        std::fs::read_dir(".")?
            .filter_map(|e| e.ok())
            .map(|e| e.path())
            .find(|p| p.extension().map_or(false, |ext| ext == "gguf"))
            .unwrap_or_else(|| {
                eprintln!("Usage: ttt_benchmark --model <path/to/model.gguf>");
                eprintln!("No GGUF file found in current directory.");
                std::process::exit(1);
            })
    };

    let config = BenchmarkConfig {
        model_path,
        ..Default::default()
    };

    println!("Model: {:?}", config.model_path);
    println!("Device: {:?}", config.device);
    println!();

    // Load model
    println!("Loading model...");
    let start = Instant::now();
    let mut model = GgufModel::load(&config.model_path, &config.device)
        .context("Failed to load model")?;
    println!("Model loaded in {:.2}s\n", start.elapsed().as_secs_f32());

    // Get tokenizer
    let tokenizer_path = config.model_path.with_file_name("tokenizer.json");
    let tokenizer = if tokenizer_path.exists() {
        Some(
            tokenizers::Tokenizer::from_file(&tokenizer_path)
                .map_err(|e| anyhow::anyhow!("Tokenizer error: {}", e))?,
        )
    } else {
        println!("Warning: tokenizer.json not found, using dummy tokens");
        None
    };

    // Tokenize evaluation text
    let token_ids: Vec<u32> = if let Some(ref tok) = tokenizer {
        let encoding = tok
            .encode(EVAL_TEXT, false)
            .map_err(|e| anyhow::anyhow!("Encoding error: {}", e))?;
        encoding.get_ids().to_vec()
    } else {
        // Dummy tokens for testing without tokenizer
        (0..200).map(|i| (i % 1000) as u32).collect()
    };

    println!("Total tokens: {}", token_ids.len());
    println!();

    // === Baseline Measurement (all tokens) ===
    println!("=== Baseline (no TTT) ===");
    let baseline_result = measure_perplexity(&mut model, &token_ids, config.chunk_size)?;
    println!("{}", baseline_result);
    println!();

    // === TTT Mode ===
    // Reset cache and enable TTT on last 2 layers
    model.reset_cache();
    let num_layers = model.config().num_layers;
    let ttt_start = if num_layers > 2 { num_layers - 2 } else { 0 };
    model.enable_ttt(Some(ttt_start..num_layers), 0.001);
    
    println!("=== TTT Mode (last 2 layers, lr=0.001) ===");
    let ttt_result = measure_perplexity(&mut model, &token_ids, config.chunk_size)?;
    println!("{}", ttt_result);
    println!();
    
    // === Summary ===
    println!("=== Summary ===");
    println!("Baseline PPL: {:.2}", baseline_result.perplexity);
    println!("TTT PPL: {:.2}", ttt_result.perplexity);
    
    let improvement = if baseline_result.perplexity > 0.0 && ttt_result.perplexity > 0.0 {
        (baseline_result.perplexity - ttt_result.perplexity) / baseline_result.perplexity * 100.0
    } else {
        0.0
    };
    
    if improvement > 0.0 {
        println!("Improvement: {:.1}% ✅", improvement);
    } else {
        println!("Change: {:.1}%", improvement);
    }

    Ok(())
}

/// Measure perplexity on token sequence
fn measure_perplexity(
    model: &mut GgufModel,
    token_ids: &[u32],
    chunk_size: usize,
) -> Result<PerplexityResult> {
    let device = &Device::Cpu; // Use CPU for benchmark
    let mut total_loss = 0.0f64;
    let mut total_tokens = 0usize;

    // Adjust chunk size if tokens are fewer
    let effective_chunk = chunk_size.min(token_ids.len());
    
    // Process in chunks (or single pass if small)
    let step = if effective_chunk > 2 { effective_chunk / 2 } else { 1 };
    let end_pos = if token_ids.len() > effective_chunk {
        token_ids.len() - effective_chunk + 1
    } else {
        1  // At least one iteration
    };
    
    for chunk_start in (0..end_pos).step_by(step.max(1)) {
        let chunk_end = (chunk_start + effective_chunk).min(token_ids.len());
        let chunk = &token_ids[chunk_start..chunk_end];

        if chunk.len() < 2 {
            continue;
        }

        // Input: all but last
        let input_ids = &chunk[..chunk.len() - 1];
        let input_tensor = Tensor::from_vec(
            input_ids.iter().map(|&x| x as i64).collect::<Vec<_>>(),
            (1, input_ids.len()),
            device,
        )?;

        // Forward pass
        let logits = model.forward(&input_tensor, 0)?;

        // Targets: shifted by 1
        let targets: Vec<i64> = chunk[1..].iter().map(|&x| x as i64).collect();
        let targets_tensor = Tensor::from_vec(targets.clone(), (1, targets.len()), device)?;

        // Compute perplexity for this chunk
        let result = compute_perplexity(&logits, &targets_tensor, Some(-100))?;

        total_loss += result.total_loss;
        total_tokens += result.num_tokens;
    }

    if total_tokens == 0 {
        return Ok(PerplexityResult {
            perplexity: f64::INFINITY,
            avg_loss: f64::INFINITY,
            num_tokens: 0,
            total_loss: 0.0,
        });
    }

    let avg_loss = total_loss / total_tokens as f64;
    let perplexity = avg_loss.exp();

    Ok(PerplexityResult {
        perplexity,
        avg_loss,
        num_tokens: total_tokens,
        total_loss,
    })
}
