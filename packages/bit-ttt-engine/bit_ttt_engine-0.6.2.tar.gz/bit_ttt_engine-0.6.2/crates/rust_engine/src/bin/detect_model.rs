//! Model Detection CLI Tool
//!
//! Usage: detect_model <model_path> [--vram <mb>] [--json] [--config]
//!
//! Detects model architecture, quantization type, and generates
//! optimal inference configuration.

use anyhow::Result;
use cortex_rust::model::{ModelDetector, OptimalConfig};
use std::env;

fn main() -> Result<()> {
    let args: Vec<String> = env::args().collect();

    if args.len() < 2 {
        eprintln!(
            "Usage: {} <model_path> [--vram <mb>] [--json] [--config]",
            args[0]
        );
        eprintln!();
        eprintln!("Options:");
        eprintln!("  --vram <mb>   Available VRAM in MB (default: 8000)");
        eprintln!("  --json        Output in JSON format");
        eprintln!("  --config      Show optimal configuration");
        std::process::exit(1);
    }

    let model_path = &args[1];
    let mut vram_mb = 8000u64;
    let mut json_format = false;
    let mut show_config = false;

    let mut i = 2;
    while i < args.len() {
        match args[i].as_str() {
            "--vram" => {
                i += 1;
                if i < args.len() {
                    vram_mb = args[i].parse().unwrap_or(8000);
                }
            }
            "--json" => json_format = true,
            "--config" => show_config = true,
            _ => {}
        }
        i += 1;
    }

    println!("🔍 Detecting model at: {}", model_path);
    println!();

    // Detect model
    let info = ModelDetector::detect(model_path)?;

    if json_format {
        let json = serde_json::to_string_pretty(&info)?;
        println!("{}", json);
    } else {
        // Text format
        ModelDetector::print_summary(&info);

        if show_config {
            println!();
            let config = ModelDetector::generate_optimal_config(&info, vram_mb);
            print_optimal_config(&config, vram_mb);
        }
    }

    Ok(())
}

fn print_optimal_config(config: &OptimalConfig, vram_mb: u64) {
    println!("╔══════════════════════════════════════════════════════════════╗");
    println!(
        "║               OPTIMAL CONFIGURATION ({}MB VRAM)           ║",
        vram_mb
    );
    println!("╠══════════════════════════════════════════════════════════════╣");
    println!(
        "║ Flash Attention:   {:>43} ║",
        if config.use_flash_attention {
            "✓"
        } else {
            "✗"
        }
    );
    println!(
        "║ Paged Attention:   {:>43} ║",
        if config.use_paged_attention {
            "✓"
        } else {
            "✗"
        }
    );
    println!(
        "║ KV Cache:          {:>43} ║",
        if config.use_kv_cache { "✓" } else { "✗" }
    );
    println!(
        "║ Sliding Window:    {:>43} ║",
        if config.use_sliding_window {
            "✓"
        } else {
            "✗"
        }
    );
    if let Some(window_size) = config.sliding_window_size {
        println!("║   Window Size:     {:>43} ║", window_size);
    }
    println!("║ Batch Size:        {:>43} ║", config.batch_size);
    println!("║ Max Context:       {:>43} ║", config.max_context_length);
    println!("║ GPU Layers:        {:>43} ║", config.n_gpu_layers);
    println!(
        "║ Temperature:       {:>43.1} ║",
        config.recommended_temperature
    );
    println!("╚══════════════════════════════════════════════════════════════╝");
}
