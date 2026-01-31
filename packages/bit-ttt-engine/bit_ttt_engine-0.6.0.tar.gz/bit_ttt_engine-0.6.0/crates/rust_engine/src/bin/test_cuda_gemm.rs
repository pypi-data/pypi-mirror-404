//! Test CUDA vs CPU 4-bit GEMM

use anyhow::Result;
use candle_core::{Device, Tensor};
use cortex_rust::kernels::matmul_4bit::gemm_4bit;

fn main() -> Result<()> {
    println!("=== 4-bit GEMM CUDA vs CPU Test ===\n");

    // Small test case
    let in_dim = 8;
    let out_dim = 4;
    let group_size = 4;
    let batch_size = 1;

    // Create test input (all ones)
    let x_data: Vec<f32> = vec![1.0; batch_size * in_dim];

    // Create packed weights (simple pattern)
    // Each byte has 2 4-bit values: low nibble + high nibble
    // Value 8 in packed = 0 after -8 offset
    // Value 15 in packed = 7 after -8 offset
    // Value 0 in packed = -8 after -8 offset
    let packed_per_row = in_dim / 2;
    let mut w_data: Vec<u8> = vec![0; out_dim * packed_per_row];

    // Set weights to value 8 (0 after -8 offset) for all
    w_data.fill(0x88); // Both nibbles = 8, so weight = 0

    // Create scales (all 1.0)
    let n_groups = in_dim.div_ceil(group_size);
    let s_data: Vec<f32> = vec![1.0; out_dim * n_groups];

    // CPU test
    let device_cpu = Device::Cpu;
    let x_cpu = Tensor::from_vec(x_data.clone(), (batch_size, in_dim), &device_cpu)?;
    let w_cpu = Tensor::from_vec(w_data.clone(), (out_dim, packed_per_row), &device_cpu)?;
    let s_cpu = Tensor::from_vec(s_data.clone(), (out_dim, n_groups), &device_cpu)?;

    let y_cpu = gemm_4bit(&x_cpu, &w_cpu, &s_cpu, group_size)?;
    let y_cpu_data: Vec<f32> = y_cpu.flatten_all()?.to_vec1()?;

    println!("CPU output: {:?}", y_cpu_data);
    println!("Expected (weights=0): [0, 0, 0, 0]");

    // CUDA test (if available)
    match Device::cuda_if_available(0) {
        Ok(device_cuda) => {
            println!("\nCUDA available, testing...");

            let x_cuda = Tensor::from_vec(x_data.clone(), (batch_size, in_dim), &device_cuda)?;
            let w_cuda = Tensor::from_vec(w_data.clone(), (out_dim, packed_per_row), &device_cuda)?;
            let s_cuda = Tensor::from_vec(s_data.clone(), (out_dim, n_groups), &device_cuda)?;

            let y_cuda = gemm_4bit(&x_cuda, &w_cuda, &s_cuda, group_size)?;
            let y_cuda_data: Vec<f32> = y_cuda.to_device(&device_cpu)?.flatten_all()?.to_vec1()?;

            println!("CUDA output: {:?}", y_cuda_data);

            // Compare
            let diff: f32 = y_cpu_data
                .iter()
                .zip(y_cuda_data.iter())
                .map(|(a, b)| (a - b).abs())
                .sum();
            println!("\nTotal diff: {}", diff);

            if diff < 0.01 {
                println!("✅ CUDA and CPU match!");
            } else {
                println!("❌ CUDA and CPU differ!");
            }
        }
        Err(e) => {
            println!("\nCUDA not available: {}", e);
        }
    }

    Ok(())
}
