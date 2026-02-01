//! Comprehensive Benchmark Suite
//!
//! Benchmarks CPU vs GPU performance across various operations.

use candle_core::{DType, Device, Tensor};
use std::time::Instant;

fn benchmark_matmul(device: &Device, sizes: &[(usize, usize, usize)], warmup: usize, iterations: usize) {
    println!("\n📊 Matrix Multiplication Benchmark ({:?})", device);
    println!("{:─<60}", "");
    println!("{:<20} {:>12} {:>12} {:>12}", "Size", "Min", "Avg", "Max");
    println!("{:─<60}", "");

    for &(m, k, n) in sizes {
        // Warmup
        for _ in 0..warmup {
            let a = Tensor::randn(0f32, 1.0, (m, k), device).unwrap();
            let b = Tensor::randn(0f32, 1.0, (k, n), device).unwrap();
            let _ = a.matmul(&b).unwrap();
        }

        // Benchmark
        let mut times = Vec::with_capacity(iterations);
        for _ in 0..iterations {
            let a = Tensor::randn(0f32, 1.0, (m, k), device).unwrap();
            let b = Tensor::randn(0f32, 1.0, (k, n), device).unwrap();
            
            let start = Instant::now();
            let _ = a.matmul(&b).unwrap();
            times.push(start.elapsed().as_secs_f64() * 1000.0);
        }

        let min = times.iter().cloned().fold(f64::INFINITY, f64::min);
        let max = times.iter().cloned().fold(f64::NEG_INFINITY, f64::max);
        let avg: f64 = times.iter().sum::<f64>() / times.len() as f64;

        println!("{:<20} {:>10.3}ms {:>10.3}ms {:>10.3}ms", 
            format!("{}x{}x{}", m, k, n), min, avg, max);
    }
}

fn benchmark_softmax(device: &Device, sizes: &[(usize, usize)], warmup: usize, iterations: usize) {
    println!("\n📊 Softmax Benchmark ({:?})", device);
    println!("{:─<60}", "");
    println!("{:<20} {:>12} {:>12} {:>12}", "Size", "Min", "Avg", "Max");
    println!("{:─<60}", "");

    for &(batch, seq) in sizes {
        // Warmup
        for _ in 0..warmup {
            let x = Tensor::randn(0f32, 1.0, (batch, seq), device).unwrap();
            let _ = candle_nn::ops::softmax(&x, 1).unwrap();
        }

        // Benchmark
        let mut times = Vec::with_capacity(iterations);
        for _ in 0..iterations {
            let x = Tensor::randn(0f32, 1.0, (batch, seq), device).unwrap();
            
            let start = Instant::now();
            let _ = candle_nn::ops::softmax(&x, 1).unwrap();
            times.push(start.elapsed().as_secs_f64() * 1000.0);
        }

        let min = times.iter().cloned().fold(f64::INFINITY, f64::min);
        let max = times.iter().cloned().fold(f64::NEG_INFINITY, f64::max);
        let avg: f64 = times.iter().sum::<f64>() / times.len() as f64;

        println!("{:<20} {:>10.3}ms {:>10.3}ms {:>10.3}ms", 
            format!("{}x{}", batch, seq), min, avg, max);
    }
}

fn benchmark_layer_norm(device: &Device, sizes: &[(usize, usize)], warmup: usize, iterations: usize) {
    println!("\n📊 Layer Norm Benchmark ({:?})", device);
    println!("{:─<60}", "");
    println!("{:<20} {:>12} {:>12} {:>12}", "Size", "Min", "Avg", "Max");
    println!("{:─<60}", "");

    for &(batch, hidden) in sizes {
        let weight = Tensor::ones((hidden,), DType::F32, device).unwrap();
        let bias = Tensor::zeros((hidden,), DType::F32, device).unwrap();

        // Warmup
        for _ in 0..warmup {
            let x = Tensor::randn(0f32, 1.0, (batch, hidden), device).unwrap();
            let mean = x.mean_keepdim(1).unwrap();
            let x_centered = x.broadcast_sub(&mean).unwrap();
            let var = x_centered.sqr().unwrap().mean_keepdim(1).unwrap();
            let _ = x_centered.broadcast_div(&(var + 1e-5).unwrap().sqrt().unwrap()).unwrap()
                .broadcast_mul(&weight).unwrap()
                .broadcast_add(&bias).unwrap();
        }

        // Benchmark
        let mut times = Vec::with_capacity(iterations);
        for _ in 0..iterations {
            let x = Tensor::randn(0f32, 1.0, (batch, hidden), device).unwrap();
            
            let start = Instant::now();
            let mean = x.mean_keepdim(1).unwrap();
            let x_centered = x.broadcast_sub(&mean).unwrap();
            let var = x_centered.sqr().unwrap().mean_keepdim(1).unwrap();
            let _ = x_centered.broadcast_div(&(var + 1e-5).unwrap().sqrt().unwrap()).unwrap()
                .broadcast_mul(&weight).unwrap()
                .broadcast_add(&bias).unwrap();
            times.push(start.elapsed().as_secs_f64() * 1000.0);
        }

        let min = times.iter().cloned().fold(f64::INFINITY, f64::min);
        let max = times.iter().cloned().fold(f64::NEG_INFINITY, f64::max);
        let avg: f64 = times.iter().sum::<f64>() / times.len() as f64;

        println!("{:<20} {:>10.3}ms {:>10.3}ms {:>10.3}ms", 
            format!("{}x{}", batch, hidden), min, avg, max);
    }
}

fn benchmark_attention_like(device: &Device, configs: &[(usize, usize, usize, usize)], warmup: usize, iterations: usize) {
    println!("\n📊 Attention-like Benchmark ({:?})", device);
    println!("{:─<70}", "");
    println!("{:<30} {:>12} {:>12} {:>12}", "Config (B,H,S,D)", "Min", "Avg", "Max");
    println!("{:─<70}", "");

    for &(batch, heads, seq, head_dim) in configs {
        // Q, K, V
        let q = Tensor::randn(0f32, 1.0, (batch, heads, seq, head_dim), device).unwrap();
        let k = Tensor::randn(0f32, 1.0, (batch, heads, seq, head_dim), device).unwrap();
        let v = Tensor::randn(0f32, 1.0, (batch, heads, seq, head_dim), device).unwrap();
        let scale = 1.0 / (head_dim as f64).sqrt();

        // Warmup
        for _ in 0..warmup {
            let scores = q.matmul(&k.transpose(2, 3).unwrap()).unwrap();
            let scores = (scores * scale).unwrap();
            let attn = candle_nn::ops::softmax(&scores, 3).unwrap();
            let _ = attn.matmul(&v).unwrap();
        }

        // Benchmark
        let mut times = Vec::with_capacity(iterations);
        for _ in 0..iterations {
            let start = Instant::now();
            let scores = q.matmul(&k.transpose(2, 3).unwrap()).unwrap();
            let scores = (scores * scale).unwrap();
            let attn = candle_nn::ops::softmax(&scores, 3).unwrap();
            let _ = attn.matmul(&v).unwrap();
            times.push(start.elapsed().as_secs_f64() * 1000.0);
        }

        let min = times.iter().cloned().fold(f64::INFINITY, f64::min);
        let max = times.iter().cloned().fold(f64::NEG_INFINITY, f64::max);
        let avg: f64 = times.iter().sum::<f64>() / times.len() as f64;

        println!("{:<30} {:>10.3}ms {:>10.3}ms {:>10.3}ms", 
            format!("B{}H{}S{}D{}", batch, heads, seq, head_dim), min, avg, max);
    }
}

fn main() -> anyhow::Result<()> {
    println!("╔════════════════════════════════════════════════════════════════╗");
    println!("║         Bit-TTT-Engine Comprehensive Benchmark Suite          ║");
    println!("╚════════════════════════════════════════════════════════════════╝\n");

    let warmup = 3;
    let iterations = 10;

    // Matrix sizes
    let matmul_sizes = vec![
        (512, 512, 512),
        (1024, 1024, 1024),
        (2048, 2048, 2048),
        (4096, 4096, 4096),
    ];

    let softmax_sizes = vec![
        (1, 1024),
        (1, 4096),
        (32, 2048),
        (128, 2048),
    ];

    let layernorm_sizes = vec![
        (1, 2048),
        (1, 4096),
        (32, 2048),
        (128, 4096),
    ];

    let attention_configs = vec![
        (1, 8, 128, 64),    // Small
        (1, 8, 512, 64),    // Medium
        (1, 32, 512, 128),  // Large (Llama-like)
        (1, 8, 2048, 256),  // Long context
    ];

    // CPU Benchmarks
    let cpu = Device::Cpu;
    println!("🖥️  CPU Benchmarks");
    println!("{}", "═".repeat(60));
    
    benchmark_matmul(&cpu, &matmul_sizes, warmup, iterations);
    benchmark_softmax(&cpu, &softmax_sizes, warmup, iterations);
    benchmark_layer_norm(&cpu, &layernorm_sizes, warmup, iterations);
    benchmark_attention_like(&cpu, &attention_configs, warmup, iterations);

    // GPU Benchmarks
    match Device::new_cuda(0) {
        Ok(gpu) => {
            println!("\n\n🎮 GPU Benchmarks (CUDA)");
            println!("{}", "═".repeat(60));
            
            benchmark_matmul(&gpu, &matmul_sizes, warmup, iterations);
            benchmark_softmax(&gpu, &softmax_sizes, warmup, iterations);
            benchmark_layer_norm(&gpu, &layernorm_sizes, warmup, iterations);
            benchmark_attention_like(&gpu, &attention_configs, warmup, iterations);

            // Summary comparison
            println!("\n\n📈 GPU vs CPU Speedup Summary");
            println!("{:─<60}", "");
            
            // Quick comparison for 2048x2048 matmul
            let size = (2048, 2048, 2048);
            
            // CPU time
            let a_cpu = Tensor::randn(0f32, 1.0, (size.0, size.1), &cpu)?;
            let b_cpu = Tensor::randn(0f32, 1.0, (size.1, size.2), &cpu)?;
            let _ = a_cpu.matmul(&b_cpu)?; // warmup
            let start = Instant::now();
            let _ = a_cpu.matmul(&b_cpu)?;
            let cpu_time = start.elapsed().as_secs_f64() * 1000.0;

            // GPU time
            let a_gpu = Tensor::randn(0f32, 1.0, (size.0, size.1), &gpu)?;
            let b_gpu = Tensor::randn(0f32, 1.0, (size.1, size.2), &gpu)?;
            let _ = a_gpu.matmul(&b_gpu)?; // warmup
            let start = Instant::now();
            let _ = a_gpu.matmul(&b_gpu)?;
            let gpu_time = start.elapsed().as_secs_f64() * 1000.0;

            println!("matmul 2048x2048: CPU={:.2}ms, GPU={:.2}ms, Speedup={:.1}x",
                cpu_time, gpu_time, cpu_time / gpu_time);
        }
        Err(e) => {
            println!("\n⚠️  GPU not available: {}", e);
        }
    }

    println!("\n✅ Benchmark complete!");
    Ok(())
}
