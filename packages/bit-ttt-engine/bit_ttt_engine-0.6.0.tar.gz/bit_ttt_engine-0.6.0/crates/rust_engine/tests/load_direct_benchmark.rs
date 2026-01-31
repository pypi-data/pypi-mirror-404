//! Benchmark: VarBuilder vs Direct Load
//!
//! Compares loading time and verifies U8 preservation.
//! Run with: cargo test --test load_direct_benchmark --release -- --nocapture

use candle_core::{DType, Device, Tensor};
use cortex_rust::layers::bit_linear::BitLinear;
use std::time::Instant;

mod common;

/// Test that direct safetensors load preserves U8 dtype
#[test]
fn test_u8_preservation() {
    // Get model path from common utilities (supports env var override)
    let model_path = common::get_test_model_safetensors();

    if !model_path.exists() {
        eprintln!("⏭️ Skipping: model not found at {:?}", model_path);
        return;
    }

    println!("\n🧪 U8 Preservation Test");
    println!("━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━");

    let device = Device::Cpu;

    // Load with candle_core::safetensors::load (direct)
    let tensors =
        candle_core::safetensors::load(model_path, &device).expect("Failed to load safetensors");

    let mut u8_count = 0;
    let mut f32_count = 0;
    let mut other_count = 0;

    for (name, tensor) in &tensors {
        match tensor.dtype() {
            DType::U8 => {
                u8_count += 1;
                if name.contains("weight_packed") {
                    println!("  ✅ {} → U8 (preserved!)", name);
                }
            }
            DType::F32 => f32_count += 1,
            _ => other_count += 1,
        }
    }

    println!("\n📊 Tensor Stats:");
    println!("  - U8:    {} tensors", u8_count);
    println!("  - F32:   {} tensors", f32_count);
    println!("  - Other: {} tensors", other_count);

    assert!(u8_count > 0, "Expected at least some U8 tensors!");
    println!("\n✅ U8 tensors preserved correctly!");
}

/// Benchmark: Load single layer via from_packed_tensors (direct) vs VarBuilder
#[test]
fn benchmark_single_layer_load() {
    // Get model path from common utilities (supports env var override)
    let model_path = common::get_test_model_safetensors();

    if !model_path.exists() {
        eprintln!("⏭️ Skipping: model not found at {:?}", model_path);
        return;
    }

    println!("\n⏱️ Single Layer Load Benchmark");
    println!("━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━");

    let device = Device::Cpu;
    let iterations = 5;
    let model_path_ref = model_path.as_path();

    // Method 1: Direct safetensors load (U8 preserved)
    let start = Instant::now();
    for _ in 0..iterations {
        let tensors = candle_core::safetensors::load(model_path_ref, &device).unwrap();

        // Find a weight_packed layer
        let layer_prefix = "model.layers.0.mlp.gate_proj";
        let packed_key = format!("{}.weight_packed", layer_prefix);
        let scales_key = format!("{}.scales", layer_prefix);

        if let (Some(packed), Some(scales)) = (tensors.get(&packed_key), tensors.get(&scales_key)) {
            // Check dtype BEFORE loading
            let dtype = packed.dtype();
            let _ = BitLinear::from_packed_tensors(packed, scales, &device).unwrap();

            // If U8, no conversion needed. If F32, conversion was done.
            if dtype != DType::U8 {
                println!("  ⚠️ Warning: dtype was {:?}, not U8", dtype);
            }
        }
    }
    let direct_time = start.elapsed();

    // Method 2: VarBuilder load (F32 conversion happens)
    let start = Instant::now();
    for _ in 0..iterations {
        let vb = unsafe {
            candle_nn::VarBuilder::from_mmaped_safetensors(&[model_path_ref], DType::F32, &device)
                .unwrap()
        };

        // Try to load packed via VarBuilder
        let layer_vb = vb.pp("model.layers.0.mlp.gate_proj");

        // VarBuilder.get() will convert U8 to F32
        // Note: VarBuilder signature is get(shape, name)
        if let (Ok(packed), Ok(scales)) = (
            layer_vb.get(&[2048usize, 1376 / 4], "weight_packed"),
            layer_vb.get(&[1usize], "scales"),
        ) {
            // packed will be F32 here due to VarBuilder
            let dtype = packed.dtype();
            let _ = BitLinear::from_packed_tensors(&packed, &scales, &device);

            if dtype != DType::F32 {
                println!("  Unexpected: VarBuilder returned {:?}", dtype);
            }
        }
    }
    let varbuilder_time = start.elapsed();

    println!("\n📊 Results ({} iterations):", iterations);
    println!("  - Direct (U8):     {:?}", direct_time);
    println!("  - VarBuilder (F32): {:?}", varbuilder_time);

    let speedup = varbuilder_time.as_secs_f64() / direct_time.as_secs_f64();
    println!("  - Speedup: {:.2}x", speedup);

    if direct_time < varbuilder_time {
        println!("\n✅ Direct load is faster!");
    }
}

/// Test forward pass works correctly with direct-loaded model
#[test]
fn test_direct_load_forward() {
    // Get model path from common utilities (supports env var override)
    let model_path = common::get_test_model_safetensors();

    if !model_path.exists() {
        eprintln!("⏭️ Skipping: model not found at {:?}", model_path);
        return;
    }

    println!("\n🧪 Forward Pass Test (Direct Load)");
    println!("━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━");

    let device = Device::Cpu;

    // Direct load
    let tensors = candle_core::safetensors::load(model_path, &device).unwrap();

    let layer_prefix = "model.layers.0.mlp.gate_proj";
    let packed_key = format!("{}.weight_packed", layer_prefix);
    let scales_key = format!("{}.scales", layer_prefix);

    let packed = tensors.get(&packed_key).unwrap();
    let scales = tensors.get(&scales_key).unwrap();

    println!("  packed dtype: {:?}", packed.dtype());
    println!("  packed shape: {:?}", packed.dims());

    let layer = BitLinear::from_packed_tensors(packed, scales, &device).unwrap();

    // Create test input
    let in_dim = layer.in_features;
    let x = Tensor::randn(0.0f32, 1.0, (1, in_dim), &device).unwrap();

    // Forward pass
    let output = layer.forward(&x).unwrap();

    println!("  output shape: {:?}", output.dims());

    // Verify output
    let output_vec = output.flatten_all().unwrap().to_vec1::<f32>().unwrap();
    let has_nan = output_vec.iter().any(|v| v.is_nan());
    let has_inf = output_vec.iter().any(|v| v.is_infinite());

    assert!(!has_nan, "Output contains NaN!");
    assert!(!has_inf, "Output contains Inf!");

    println!("\n✅ Forward pass successful!");
}
