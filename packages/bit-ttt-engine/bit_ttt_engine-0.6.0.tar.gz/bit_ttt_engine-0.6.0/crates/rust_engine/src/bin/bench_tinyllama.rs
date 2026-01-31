//! TinyLlama-1.1B Benchmark for 1.58-bit quantized model
//!
//! Run: cargo run --release --bin bench_tinyllama

use cortex_rust::Llama;
use std::path::Path;
use std::time::Instant;

fn main() -> anyhow::Result<()> {
    println!("=== TinyLlama-1.1B 1.58-bit Benchmark ===\n");

    // Model path
    let model_path = Path::new("benchmark/tinyllama-1.1b-converted");

    if !model_path.exists() {
        eprintln!("❌ Model not found at {:?}", model_path);
        eprintln!("   Please run bit_converter first to convert TinyLlama-1.1B");
        std::process::exit(1);
    }

    println!("📁 Loading model from: {:?}", model_path);
    let load_start = Instant::now();

    let mut llama = Llama::load_auto(model_path)?;

    let load_time = load_start.elapsed();
    println!("✅ Model loaded in {:.2}s", load_time.as_secs_f64());
    println!("   Layers: {}", llama.model.layers.len());
    println!("   Device: {:?}", llama.device);
    println!();

    // Benchmark prompts
    let prompts = [
        "Hello, my name is",
        "The meaning of life is",
        "Once upon a time",
    ];

    let gen_tokens = 32;
    let warmup_runs = 1;
    let bench_runs = 3;

    println!("🔥 Warming up ({} run)...", warmup_runs);
    for _ in 0..warmup_runs {
        let _ = llama.generate("Test", 8);
    }

    println!(
        "\n📊 Running benchmark ({} runs, {} tokens per run)...\n",
        bench_runs, gen_tokens
    );

    let mut total_tokens = 0usize;
    let mut total_time = std::time::Duration::ZERO;

    for prompt in prompts {
        println!("Prompt: \"{}\"", prompt);

        let mut prompt_times = Vec::new();
        #[allow(unused_assignments)]
        let mut output = String::new();

        for run in 0..bench_runs {
            let start = Instant::now();
            output = llama.generate(prompt, gen_tokens)?;
            let elapsed = start.elapsed();
            prompt_times.push(elapsed);

            if run == 0 {
                println!(
                    "Output: \"{}\"",
                    output.chars().take(80).collect::<String>()
                );
            }
        }

        let avg_time = prompt_times.iter().sum::<std::time::Duration>() / bench_runs as u32;
        let tokens_per_sec = gen_tokens as f64 / avg_time.as_secs_f64();

        println!(
            "  Avg time: {:.2}ms | {:.2} tokens/sec",
            avg_time.as_millis(),
            tokens_per_sec
        );
        println!();

        total_tokens += gen_tokens * bench_runs;
        total_time += prompt_times.iter().sum::<std::time::Duration>();
    }

    let overall_tps = total_tokens as f64 / total_time.as_secs_f64();

    println!("═══════════════════════════════════════════════");
    println!("📈 Overall Results:");
    println!("   Total tokens generated: {}", total_tokens);
    println!("   Total time: {:.2}s", total_time.as_secs_f64());
    println!("   Average throughput: {:.2} tokens/sec", overall_tps);
    println!("═══════════════════════════════════════════════");

    Ok(())
}
