//! Model Info Example
//!
//! Display information about a GGUF model.
//!
//! Usage:
//!   cargo run --release --example model_info -- --model path/to/model.gguf

use anyhow::{Context, Result};
use candle_core::Device;
use cortex_rust::GgufModel;
use std::path::PathBuf;

fn parse_args() -> PathBuf {
    let args: Vec<String> = std::env::args().collect();
    let mut model_path = PathBuf::from("model.gguf");

    let mut i = 1;
    while i < args.len() {
        match args[i].as_str() {
            "--model" | "-m" => {
                if i + 1 < args.len() {
                    model_path = PathBuf::from(&args[i + 1]);
                    i += 1;
                }
            }
            "--help" | "-h" => {
                println!("Model Info - Bit-TTT-Engine");
                println!();
                println!("Usage: model_info --model <PATH>");
                std::process::exit(0);
            }
            _ => {}
        }
        i += 1;
    }

    model_path
}

fn format_size(bytes: usize) -> String {
    if bytes >= 1_000_000_000 {
        format!("{:.2} GB", bytes as f64 / 1_000_000_000.0)
    } else if bytes >= 1_000_000 {
        format!("{:.2} MB", bytes as f64 / 1_000_000.0)
    } else if bytes >= 1_000 {
        format!("{:.2} KB", bytes as f64 / 1_000.0)
    } else {
        format!("{} B", bytes)
    }
}

fn main() -> Result<()> {
    let model_path = parse_args();

    println!("╔════════════════════════════════════════════╗");
    println!("║       📊 Bit-TTT-Engine Model Info         ║");
    println!("╚════════════════════════════════════════════╝");
    println!();

    // Get file size
    let file_size = std::fs::metadata(&model_path)
        .map(|m| m.len() as usize)
        .unwrap_or(0);

    println!("📁 File: {:?}", model_path);
    println!("📦 Size: {}", format_size(file_size));
    println!();

    // Load model
    println!("⏳ Loading model...");
    let device = Device::Cpu;
    let model = GgufModel::load(&model_path, &device)
        .context("Failed to load model")?;
    println!("✅ Loaded!");
    println!();

    let config = model.config();

    println!("┌─────────────────────────────────────────┐");
    println!("│              Model Config               │");
    println!("├─────────────────────────────────────────┤");
    println!("│  Vocab Size:     {:>20} │", config.vocab_size);
    println!("│  Hidden Dim:     {:>20} │", config.hidden_dim);
    println!("│  Num Layers:     {:>20} │", config.num_layers);
    println!("│  Num Heads:      {:>20} │", config.n_heads);
    println!("│  Num KV Heads:   {:>20} │", config.n_kv_heads);
    println!("│  Intermediate:   {:>20} │", config.intermediate_dim.unwrap_or(0));
    println!("│  Max Positions:  {:>20} │", config.max_position_embeddings);
    println!("│  RoPE Theta:     {:>20.1} │", config.rope_theta);
    println!("│  RMS Norm Eps:   {:>20.2e} │", config.rms_norm_eps);
    println!("│  Activation:     {:>20?} │", config.activation);
    println!("└─────────────────────────────────────────┘");
    println!();

    // Estimate parameters
    let head_dim = config.hidden_dim / config.n_heads;
    let intermediate = config.intermediate_dim.unwrap_or(config.hidden_dim * 4);
    let params_per_layer = 
        4 * config.hidden_dim * config.hidden_dim +  // Q, K, V, O
        3 * config.hidden_dim * intermediate;  // gate, up, down
    let total_params = 
        config.vocab_size * config.hidden_dim +  // embeddings
        config.num_layers * params_per_layer +  // layers
        config.hidden_dim +  // final norm
        config.vocab_size * config.hidden_dim;  // lm_head

    println!("📈 Estimated Parameters:");
    println!("   Per Layer:  ~{:.1}M", params_per_layer as f64 / 1_000_000.0);
    println!("   Total:      ~{:.1}M", total_params as f64 / 1_000_000.0);
    println!("   Head Dim:   {}", head_dim);

    Ok(())
}
