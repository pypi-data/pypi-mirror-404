//! 4-bit GPU Benchmark
//!
//! Benchmarks 4-bit quantized Llama inference on GPU vs CPU.
//! Run: cargo run --release --features cuda --bin bench_4bit_gpu

use anyhow::Result;
use candle_core::Device;
use cortex_rust::model::{Llama4Bit, Llama4BitConfig};
use std::path::Path;
use std::time::Instant;
use tokenizers::Tokenizer;

fn main() -> Result<()> {
    let args: Vec<String> = std::env::args().collect();

    let model_path = args
        .iter()
        .position(|x| x == "--model-path")
        .and_then(|i| args.get(i + 1))
        .map(|s| s.as_str())
        .unwrap_or("benchmark/tinyllama-4bit");

    let gen_tokens: usize = args
        .iter()
        .position(|x| x == "--tokens")
        .and_then(|i| args.get(i + 1))
        .and_then(|s| s.parse().ok())
        .unwrap_or(50);

    let bench_runs: usize = args
        .iter()
        .position(|x| x == "--runs")
        .and_then(|i| args.get(i + 1))
        .and_then(|s| s.parse().ok())
        .unwrap_or(3);

    println!("═══════════════════════════════════════════════");
    println!("  4-bit Quantized Llama GPU Benchmark");
    println!("═══════════════════════════════════════════════");
    println!("Model: {}", model_path);
    println!("Tokens per run: {}", gen_tokens);
    println!("Benchmark runs: {}", bench_runs);
    println!();

    // Check GPU availability
    let gpu_available = Device::cuda_if_available(0).is_ok();
    println!(
        "GPU Available: {}",
        if gpu_available { "✅ Yes" } else { "❌ No" }
    );

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

    // Load tokenizer
    let tokenizer_path = Path::new(model_path).join("tokenizer.json");
    let tokenizer = Tokenizer::from_file(&tokenizer_path)
        .map_err(|e| anyhow::anyhow!("Tokenizer error: {}", e))?;

    let prompt = "The meaning of life is";
    let encoding = tokenizer
        .encode(prompt, false)
        .map_err(|e| anyhow::anyhow!("Encoding error: {}", e))?;
    let input_ids: Vec<u32> = encoding.get_ids().to_vec();

    let model_file = Path::new(model_path).join("model.safetensors");

    // Benchmark function
    let run_benchmark = |device: Device, device_name: &str| -> Result<f64> {
        println!("\n───────────────────────────────────────────────");
        println!("  {} Benchmark", device_name);
        println!("───────────────────────────────────────────────");

        let load_start = Instant::now();
        let tensors = candle_core::safetensors::load(&model_file, &device)?;
        let mut model = Llama4Bit::load(&tensors, config.clone(), &device)?;
        let load_time = load_start.elapsed();
        println!("Model loaded in {:.2}s", load_time.as_secs_f64());

        let mut times = Vec::with_capacity(bench_runs);

        for run in 0..bench_runs {
            model.clear_kv_cache();

            let start = Instant::now();
            let _ = model.generate(&input_ids, gen_tokens, 0.0)?;
            let elapsed = start.elapsed();
            times.push(elapsed);

            if run == 0 {
                println!(
                    "Run {}: {:.2}s ({:.2} tok/s)",
                    run + 1,
                    elapsed.as_secs_f64(),
                    gen_tokens as f64 / elapsed.as_secs_f64()
                );
            }
        }

        let total: std::time::Duration = times.iter().sum();
        let avg = total.as_secs_f64() / bench_runs as f64;
        let tps = gen_tokens as f64 / avg;

        println!("\nAverage: {:.2}s per run", avg);
        println!("Throughput: {:.2} tokens/sec", tps);

        Ok(tps)
    };

    // Run CPU benchmark
    let cpu_tps = run_benchmark(Device::Cpu, "CPU")?;

    // Run GPU benchmark if available
    let gpu_tps = if gpu_available {
        let device = Device::cuda_if_available(0)?;
        Some(run_benchmark(device, "GPU (CUDA)")?)
    } else {
        None
    };

    // Summary
    println!("\n═══════════════════════════════════════════════");
    println!("  Summary");
    println!("═══════════════════════════════════════════════");
    println!("CPU: {:.2} tokens/sec", cpu_tps);

    if let Some(gpu) = gpu_tps {
        println!("GPU: {:.2} tokens/sec", gpu);
        println!("Speedup: {:.1}x", gpu / cpu_tps);
    }
    println!("═══════════════════════════════════════════════");

    Ok(())
}
