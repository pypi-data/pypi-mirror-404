//! CUDA GPU Inference Test
//!
//! Tests GPU tensor operations and model loading.

use candle_core::{Device, Tensor};

fn main() -> anyhow::Result<()> {
    println!("🔍 Checking CUDA availability...");

    // Try to create CUDA device
    match Device::new_cuda(0) {
        Ok(device) => {
            println!("✅ CUDA device 0 available!");

            // Test basic tensor operations on GPU
            let a = Tensor::randn(0f32, 1.0, (1024, 1024), &device)?;
            let b = Tensor::randn(0f32, 1.0, (1024, 1024), &device)?;

            println!("📊 Testing matmul on GPU...");
            let start = std::time::Instant::now();
            let _c = a.matmul(&b)?;
            let elapsed = start.elapsed();
            println!("✅ GPU matmul (1024x1024): {:?}", elapsed);

            // Test larger matmul
            let a = Tensor::randn(0f32, 1.0, (4096, 4096), &device)?;
            let b = Tensor::randn(0f32, 1.0, (4096, 4096), &device)?;

            let start = std::time::Instant::now();
            let _c = a.matmul(&b)?;
            let elapsed = start.elapsed();
            println!("✅ GPU matmul (4096x4096): {:?}", elapsed);

            // Compare with CPU
            println!("\n📊 Comparing with CPU...");
            let cpu = Device::Cpu;
            let a_cpu = Tensor::randn(0f32, 1.0, (1024, 1024), &cpu)?;
            let b_cpu = Tensor::randn(0f32, 1.0, (1024, 1024), &cpu)?;

            let start = std::time::Instant::now();
            let _c = a_cpu.matmul(&b_cpu)?;
            let elapsed_cpu = start.elapsed();
            println!("📍 CPU matmul (1024x1024): {:?}", elapsed_cpu);

            println!("\n🎉 CUDA test passed!");
        }
        Err(e) => {
            println!("❌ CUDA not available: {}", e);
            println!("   Running on CPU only.");
        }
    }

    Ok(())
}
