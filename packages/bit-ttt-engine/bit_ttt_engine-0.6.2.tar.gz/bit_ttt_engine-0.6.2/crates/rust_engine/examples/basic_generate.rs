//! Basic Text Generation Example
//!
//! Simple example showing how to generate text with a GGUF model.
//!
//! Usage:
//!   cargo run --release --example basic_generate -- \
//!     --model path/to/model.gguf --prompt "Hello, world!"

use anyhow::{Context, Result};
use candle_core::{Device, Tensor};
use cortex_rust::GgufModel;
use std::path::PathBuf;

fn parse_args() -> (PathBuf, String, usize) {
    let args: Vec<String> = std::env::args().collect();
    let mut model_path = PathBuf::from("model.gguf");
    let mut prompt = "Hello, how are you?".to_string();
    let mut max_tokens = 50usize;

    let mut i = 1;
    while i < args.len() {
        match args[i].as_str() {
            "--model" | "-m" => {
                if i + 1 < args.len() {
                    model_path = PathBuf::from(&args[i + 1]);
                    i += 1;
                }
            }
            "--prompt" | "-p" => {
                if i + 1 < args.len() {
                    prompt = args[i + 1].clone();
                    i += 1;
                }
            }
            "--tokens" | "-t" => {
                if i + 1 < args.len() {
                    max_tokens = args[i + 1].parse().unwrap_or(50);
                    i += 1;
                }
            }
            "--help" | "-h" => {
                println!("Usage: basic_generate [OPTIONS]");
                println!();
                println!("Options:");
                println!("  -m, --model <PATH>   Path to GGUF model");
                println!("  -p, --prompt <TEXT>  Prompt text");
                println!("  -t, --tokens <N>     Max tokens to generate [default: 50]");
                std::process::exit(0);
            }
            _ => {}
        }
        i += 1;
    }

    (model_path, prompt, max_tokens)
}

/// Simple greedy sampling
fn sample_greedy(logits: &Tensor) -> Result<u32> {
    let (batch, seq_len, _) = logits.dims3()?;
    let last_logits = logits.narrow(1, seq_len - 1, 1)?.squeeze(1)?;
    let token_ids = last_logits.argmax(1)?;
    let token_id = if batch == 1 {
        token_ids.squeeze(0)?.to_scalar::<u32>()?
    } else {
        token_ids.get(0)?.to_scalar::<u32>()?
    };
    Ok(token_id)
}

/// Simple byte-level tokenization (for demo purposes)
fn tokenize(text: &str) -> Vec<i64> {
    text.bytes().map(|b| b as i64).collect()
}

fn main() -> Result<()> {
    let (model_path, prompt, max_tokens) = parse_args();

    println!("🚀 Bit-TTT-Engine Basic Generation Example");
    println!("━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━");
    println!("Model:  {:?}", model_path);
    println!("Prompt: \"{}\"", prompt);
    println!("Tokens: {}", max_tokens);
    println!();

    // Load model
    println!("📦 Loading model...");
    let device = Device::Cpu;
    let mut model = GgufModel::load(&model_path, &device)
        .context("Failed to load model")?;
    println!("✅ Model loaded!");
    println!("   Layers: {}", model.config().num_layers);
    println!("   Hidden: {}", model.config().hidden_dim);
    println!();

    // Tokenize
    let mut tokens = tokenize(&prompt);
    let input = Tensor::from_vec(tokens.clone(), (1, tokens.len()), &device)?;

    // Prefill
    println!("⚡ Generating...");
    let logits = model.forward(&input, 0)?;
    let first_token = sample_greedy(&logits)?;
    tokens.push(first_token as i64);

    // Generate
    for _ in 0..max_tokens {
        let pos = tokens.len() - 1;
        let input = Tensor::from_vec(vec![tokens[pos]], (1, 1), &device)?;
        let logits = model.forward(&input, pos)?;
        let next_token = sample_greedy(&logits)?;
        tokens.push(next_token as i64);
    }

    // Decode (simple byte->char)
    let output: String = tokens.iter()
        .skip(prompt.len())
        .filter_map(|&t| {
            if t >= 0 && t < 256 {
                Some(t as u8 as char)
            } else {
                None
            }
        })
        .collect();

    println!();
    println!("📝 Output:");
    println!("━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━");
    println!("{}", output);
    println!("━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━");

    Ok(())
}
