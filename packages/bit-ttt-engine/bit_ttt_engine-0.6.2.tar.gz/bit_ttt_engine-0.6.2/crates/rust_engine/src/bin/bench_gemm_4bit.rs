//! Benchmark for gemm_4bit kernel
//!
//! Usage: cargo run --release --bin bench_gemm_4bit

use candle_core::{DType, Device, Tensor};
use cortex_rust::kernels::matmul_4bit::gemm_4bit;
use std::time::Instant;

fn main() -> anyhow::Result<()> {
    println!("=== gemm_4bit Benchmark ===\n");

    // Get CUDA device
    let device = Device::cuda_if_available(0)?;
    println!("Device: {:?}\n", device);

    // Test configurations (simulating Llama2-13B layers)
    let configs = [
        ("Embedding lookup equiv", 1, 5120, 32000), // lm_head
        ("Q/K/V proj", 1, 5120, 5120),              // Self-attention projections
        ("O proj", 1, 5120, 5120),                  // Output projection
        ("Gate proj", 1, 5120, 13824),              // MLP gate
        ("Up proj", 1, 5120, 13824),                // MLP up
        ("Down proj", 1, 13824, 5120),              // MLP down
    ];

    let group_size = 128usize;

    for (name, batch, in_dim, out_dim) in configs {
        println!("--- {} ---", name);
        println!(
            "Shape: [{}, {}] x [{}, {}]",
            batch,
            in_dim,
            out_dim,
            in_dim / 2
        );

        // Create random input
        let x = Tensor::randn(0.0f32, 1.0, (batch, in_dim), &device)?;

        // Create packed weights (4-bit, 2 values per byte)
        let packed_dim = in_dim / 2;
        let w_packed_data: Vec<u8> = (0..(out_dim * packed_dim))
            .map(|i| ((i % 16) as u8) | (((i / 16) % 16) as u8) << 4)
            .collect();
        let w_packed = Tensor::from_vec(w_packed_data, (out_dim, packed_dim), &device)?;

        // Create scales
        let n_groups = in_dim.div_ceil(group_size);
        let scales = Tensor::ones((out_dim, n_groups), DType::F32, &device)?;

        // Warmup
        for _ in 0..3 {
            let _ = gemm_4bit(&x, &w_packed, &scales, group_size)?;
        }

        // Benchmark
        let iterations = 10;
        let start = Instant::now();
        for _ in 0..iterations {
            let output = gemm_4bit(&x, &w_packed, &scales, group_size)?;
            // Force sync
            let _ = output.flatten_all()?.to_vec1::<f32>();
        }
        let elapsed = start.elapsed();

        let avg_ms = elapsed.as_secs_f64() * 1000.0 / iterations as f64;

        // Compute theoretical FLOPS
        let flops = 2.0 * batch as f64 * in_dim as f64 * out_dim as f64;
        let gflops = flops / (avg_ms / 1000.0) / 1e9;

        // Memory bandwidth (read input + read weights + write output)
        let bytes = (batch * in_dim * 4) as f64  // input (f32)
                  + (out_dim * packed_dim) as f64  // weights (u8)
                  + (out_dim * n_groups * 4) as f64  // scales (f32)
                  + (batch * out_dim * 4) as f64; // output (f32)
        let gbps = bytes / (avg_ms / 1000.0) / 1e9;

        println!("  Time: {:.3} ms", avg_ms);
        println!("  GFLOPS: {:.2}", gflops);
        println!("  Memory BW: {:.2} GB/s", gbps);
        println!();
    }

    // Measure overhead of to_vec1 (CPU sync)
    println!("--- Sync Overhead Test ---");
    let x = Tensor::randn(0.0f32, 1.0, (1, 5120), &device)?;
    let packed_dim = 5120 / 2;
    let w_packed_data: Vec<u8> = (0..(5120 * packed_dim)).map(|i| (i % 16) as u8).collect();
    let w_packed = Tensor::from_vec(w_packed_data, (5120, packed_dim), &device)?;
    let n_groups = 5120_usize.div_ceil(group_size);
    let scales = Tensor::ones((5120, n_groups), DType::F32, &device)?;

    // Without sync
    let iterations = 100;
    let start = Instant::now();
    for _ in 0..iterations {
        let _ = gemm_4bit(&x, &w_packed, &scales, group_size)?;
    }
    let no_sync_ms = start.elapsed().as_secs_f64() * 1000.0 / iterations as f64;

    // With sync (to_vec1)
    let start = Instant::now();
    for _ in 0..iterations {
        let output = gemm_4bit(&x, &w_packed, &scales, group_size)?;
        let _ = output.flatten_all()?.to_vec1::<f32>();
    }
    let with_sync_ms = start.elapsed().as_secs_f64() * 1000.0 / iterations as f64;

    println!("  Without sync: {:.3} ms/call", no_sync_ms);
    println!("  With sync (to_vec1): {:.3} ms/call", with_sync_ms);
    println!(
        "  Sync overhead: {:.3} ms ({:.1}%)",
        with_sync_ms - no_sync_ms,
        (with_sync_ms - no_sync_ms) / with_sync_ms * 100.0
    );

    Ok(())
}
