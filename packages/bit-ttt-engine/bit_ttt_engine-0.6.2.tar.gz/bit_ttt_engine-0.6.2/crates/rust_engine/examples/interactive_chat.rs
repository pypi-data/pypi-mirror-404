//! Interactive Chat Example
//!
//! A simple REPL for chatting with a GGUF model.
//!
//! Usage:
//!   cargo run --release --example interactive_chat -- --model path/to/model.gguf

use anyhow::{Context, Result};
use candle_core::{Device, Tensor};
use cortex_rust::GgufModel;
use std::io::{self, BufRead, Write};
use std::path::PathBuf;

fn parse_args() -> (PathBuf, usize) {
    let args: Vec<String> = std::env::args().collect();
    let mut model_path = PathBuf::from("model.gguf");
    let mut max_tokens = 100usize;

    let mut i = 1;
    while i < args.len() {
        match args[i].as_str() {
            "--model" | "-m" => {
                if i + 1 < args.len() {
                    model_path = PathBuf::from(&args[i + 1]);
                    i += 1;
                }
            }
            "--tokens" | "-t" => {
                if i + 1 < args.len() {
                    max_tokens = args[i + 1].parse().unwrap_or(100);
                    i += 1;
                }
            }
            "--help" | "-h" => {
                println!("Interactive Chat - Bit-TTT-Engine");
                println!();
                println!("Usage: interactive_chat [OPTIONS]");
                println!();
                println!("Options:");
                println!("  -m, --model <PATH>  Path to GGUF model");
                println!("  -t, --tokens <N>    Max tokens per response [default: 100]");
                std::process::exit(0);
            }
            _ => {}
        }
        i += 1;
    }

    (model_path, max_tokens)
}

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

fn tokenize(text: &str) -> Vec<i64> {
    text.bytes().map(|b| b as i64).collect()
}

fn generate(model: &mut GgufModel, prompt: &str, max_tokens: usize, device: &Device) -> Result<String> {
    let mut tokens = tokenize(prompt);
    let input = Tensor::from_vec(tokens.clone(), (1, tokens.len()), device)?;

    // Prefill
    let logits = model.forward(&input, 0)?;
    let first_token = sample_greedy(&logits)?;
    tokens.push(first_token as i64);

    // Generate
    for _ in 0..max_tokens {
        let pos = tokens.len() - 1;
        let input = Tensor::from_vec(vec![tokens[pos]], (1, 1), device)?;
        let logits = model.forward(&input, pos)?;
        let next_token = sample_greedy(&logits)?;
        
        // Stop on newline or special tokens
        if next_token == 10 || next_token == 0 {
            break;
        }
        tokens.push(next_token as i64);
    }

    // Decode
    let output: String = tokens.iter()
        .skip(prompt.len())
        .filter_map(|&t| {
            if t >= 32 && t < 127 {
                Some(t as u8 as char)
            } else {
                None
            }
        })
        .collect();

    Ok(output)
}

fn main() -> Result<()> {
    let (model_path, max_tokens) = parse_args();

    println!("╔════════════════════════════════════════════╗");
    println!("║     🤖 Bit-TTT-Engine Interactive Chat     ║");
    println!("╚════════════════════════════════════════════╝");
    println!();
    println!("Model: {:?}", model_path);
    println!("Type 'quit' or 'exit' to end.");
    println!();

    // Load model
    println!("📦 Loading model...");
    let device = Device::Cpu;
    let mut model = GgufModel::load(&model_path, &device)
        .context("Failed to load model")?;
    println!("✅ Ready!");
    println!();

    let stdin = io::stdin();
    let mut stdout = io::stdout();

    loop {
        print!("You: ");
        stdout.flush()?;

        let mut input = String::new();
        stdin.lock().read_line(&mut input)?;
        let input = input.trim();

        if input.is_empty() {
            continue;
        }

        if input.eq_ignore_ascii_case("quit") || input.eq_ignore_ascii_case("exit") {
            println!("👋 Goodbye!");
            break;
        }

        // Reset cache for new conversation
        model.reset_cache();

        // Generate response
        match generate(&mut model, input, max_tokens, &device) {
            Ok(response) => {
                println!("🤖: {}", response.trim());
            }
            Err(e) => {
                println!("❌ Error: {}", e);
            }
        }
        println!();
    }

    Ok(())
}
