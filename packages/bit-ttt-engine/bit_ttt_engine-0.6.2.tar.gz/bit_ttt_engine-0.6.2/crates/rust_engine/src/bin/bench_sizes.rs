//! Multi-size benchmark for BitLinearCpu
//! Tests various model dimensions

use candle_core::{Device, Tensor};
use cortex_rust::kernels::cpu::BitLinearCpu;
use cortex_rust::kernels::packing::PackedTensor;
use std::time::Instant;

fn bench_size(name: &str, m: usize, k: usize, n: usize, iterations: usize) -> anyhow::Result<()> {
    let device = Device::Cpu;

    // Prepare input
    let x_data = vec![0.5f32; m * k];
    let x = Tensor::from_vec(x_data, (m, k), &device)?;

    // Prepare packed weights
    let packed_len = n * k / 4;
    let w_data: Vec<u8> = (0..packed_len).map(|i| (i % 255) as u8).collect();
    let w_shape = candle_core::Shape::from((n, k));
    let packed_weights = PackedTensor::new(w_data, w_shape, 1.0, &device)?;

    // Warmup
    for _ in 0..5 {
        let _ = BitLinearCpu::forward(&x, &packed_weights)?;
    }

    // Benchmark
    let start = Instant::now();
    for _ in 0..iterations {
        let out = BitLinearCpu::forward(&x, &packed_weights)?;
        let _vec = out.flatten_all()?.to_vec1::<f32>()?;
    }
    let duration = start.elapsed();

    let avg_ms = duration.as_secs_f64() * 1000.0 / iterations as f64;
    let macs = (m as f64) * (n as f64) * (k as f64);
    let gops = macs / (avg_ms / 1000.0) / 1e9;
    let weight_mb = packed_len as f64 / 1024.0 / 1024.0;

    println!(
        "| {:12} | {:>5} | {:>5} | {:>5} | {:>7.2} | {:>8.2} | {:>6.2} |",
        name, m, k, n, avg_ms, gops, weight_mb
    );

    Ok(())
}

fn main() -> anyhow::Result<()> {
    println!("=== BitLinearCpu Multi-Size Benchmark ===\n");
    println!("| Model        |     M |     K |     N |  ms/op  |  GOps/s  | W(MB)  |");
    println!("|--------------|-------|-------|-------|---------|----------|--------|");

    // TinyLlama (1.1B) - hidden=2048
    bench_size("TinyLlama", 1, 2048, 2048, 100)?;
    bench_size("TinyLlama-4", 4, 2048, 2048, 100)?;

    // Llama-7B - hidden=4096
    bench_size("Llama-7B", 1, 4096, 4096, 100)?;
    bench_size("Llama-7B-4", 4, 4096, 4096, 50)?;

    // Llama-13B - hidden=5120
    bench_size("Llama-13B", 1, 5120, 5120, 50)?;

    // Llama-70B - hidden=8192
    bench_size("Llama-70B", 1, 8192, 8192, 50)?;
    bench_size("Llama-70B-4", 4, 8192, 8192, 20)?;

    println!("\n✅ Benchmark complete!");

    Ok(())
}
