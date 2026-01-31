//! Accuracy test: Verify quantized output is reasonable
//!
//! Since we can't easily get the "reference" FP32 output from the same weights,
//! we verify that:
//! 1. Output is not NaN/Inf
//! 2. Output has reasonable distribution (not all zeros/same value)
//! 3. Multiple forward passes give consistent results

use candle_core::{Device, Tensor};
use cortex_rust::layers::bit_linear::BitLinear;

mod common;

/// Test that quantized forward gives consistent and reasonable output
#[test]
fn test_quantized_consistency() {
    // Get model path from common utilities (supports env var override)
    let model_path = common::get_test_model_safetensors();

    if !model_path.exists() {
        eprintln!("Skipping test: model not found at {:?}", model_path);
        return;
    }

    let device = Device::Cpu;
    let tensors =
        candle_core::safetensors::load(model_path, &device).expect("Failed to load safetensors");

    // Load a layer
    let packed = tensors
        .get("model.layers.0.mlp.gate_proj.weight_packed")
        .expect("Missing weight_packed");
    let scales = tensors
        .get("model.layers.0.mlp.gate_proj.scales")
        .expect("Missing scales");

    let layer = BitLinear::from_packed_tensors(packed, scales, &device)
        .expect("Failed to create BitLinear");

    let in_dim = packed.dims()[1] * 4;

    // Test 1: Multiple runs with same input should give identical output
    let x1 = Tensor::randn(0.0f32, 1.0, (1, in_dim), &device).expect("Failed to create input");

    let y1 = layer.forward(&x1).expect("Forward 1 failed");
    let y2 = layer.forward(&x1).expect("Forward 2 failed");

    let y1_vec = y1.flatten_all().unwrap().to_vec1::<f32>().unwrap();
    let y2_vec = y2.flatten_all().unwrap().to_vec1::<f32>().unwrap();

    // Should be exactly equal (deterministic)
    for (a, b) in y1_vec.iter().zip(y2_vec.iter()) {
        assert!(
            (a - b).abs() < 1e-6,
            "Outputs not consistent: {} vs {}",
            a,
            b
        );
    }
    println!("✅ Test 1: Consistent output across runs");

    // Test 2: Different inputs should give different outputs
    let x2 = Tensor::randn(0.0f32, 1.0, (1, in_dim), &device).expect("Failed to create input 2");

    let y3 = layer.forward(&x2).expect("Forward 3 failed");
    let y3_vec = y3.flatten_all().unwrap().to_vec1::<f32>().unwrap();

    let same_count = y1_vec
        .iter()
        .zip(y3_vec.iter())
        .filter(|(a, b)| (*a - *b).abs() < 1e-6)
        .count();

    // Most values should be different
    assert!(
        same_count < y1_vec.len() / 2,
        "Outputs too similar for different inputs"
    );
    println!("✅ Test 2: Different inputs give different outputs");

    // Test 3: Output distribution is reasonable
    let mean: f32 = y1_vec.iter().sum::<f32>() / y1_vec.len() as f32;
    let variance: f32 =
        y1_vec.iter().map(|v| (v - mean).powi(2)).sum::<f32>() / y1_vec.len() as f32;
    let std_dev = variance.sqrt();

    println!("Output stats: mean={:.4}, std={:.4}", mean, std_dev);

    // Should have some variance (not all same value)
    assert!(std_dev > 1e-4, "Output has no variance (all same value)");

    // Mean shouldn't be extreme
    assert!(mean.abs() < 100.0, "Mean too extreme: {}", mean);

    println!("✅ Test 3: Output distribution reasonable");

    // Test 4: Batch processing
    let x_batch =
        Tensor::randn(0.0f32, 1.0, (4, in_dim), &device).expect("Failed to create batch input");

    let y_batch = layer.forward(&x_batch).expect("Batch forward failed");

    assert_eq!(y_batch.dims()[0], 4, "Batch dim mismatch");
    println!("✅ Test 4: Batch processing works");

    println!("\n🎉 All accuracy tests passed!");
}
