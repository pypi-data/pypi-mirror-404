//! End-to-End test: load_packed() with real converted model
//!
//! Tests the full pipeline:
//! 1. Load weight_packed + scales from safetensors
//! 2. Create BitLinear via load_packed()
//! 3. Run forward pass
//! 4. Verify output is reasonable (not NaN/Inf)

use candle_core::{Device, Tensor};
use cortex_rust::layers::bit_linear::BitLinear;

mod common;

/// Test loading a real converted model
#[test]
fn test_load_packed_real_model() {
    // Get model path from common utilities (supports env var override)
    let model_path = common::get_test_model_safetensors();

    if !model_path.exists() {
        eprintln!("Skipping test: model not found at {:?}", model_path);
        return;
    }

    println!("Using model at: {:?}", model_path);

    println!("Using model at: {:?}", model_path);

    let device = Device::Cpu;

    // Load safetensors
    let tensors =
        candle_core::safetensors::load(model_path, &device).expect("Failed to load safetensors");

    println!("Loaded {} tensors", tensors.len());

    // Find a layer with weight_packed
    let layer_prefix = "model.layers.0.mlp.gate_proj";
    let packed_key = format!("{}.weight_packed", layer_prefix);
    let scales_key = format!("{}.scales", layer_prefix);

    let packed = tensors
        .get(&packed_key)
        .unwrap_or_else(|| panic!("Missing {}", packed_key));
    let scales = tensors
        .get(&scales_key)
        .unwrap_or_else(|| panic!("Missing {}", scales_key));

    println!(
        "weight_packed shape: {:?}, dtype: {:?}",
        packed.dims(),
        packed.dtype()
    );
    println!(
        "scales shape: {:?}, dtype: {:?}",
        scales.dims(),
        scales.dtype()
    );

    // Extract dimensions from packed tensor
    // weight_packed: [out_dim, in_dim/4, n_bases]
    let dims = packed.dims();
    let (out_dim, in_dim) = match dims.len() {
        2 => (dims[0], dims[1] * 4),
        3 => (dims[0], dims[1] * 4),
        _ => panic!("Unexpected tensor shape: {:?}", dims),
    };

    println!("Layer: out_dim={}, in_dim={}", out_dim, in_dim);

    // Load via from_packed_tensors (new API that handles U8 correctly)
    let layer = BitLinear::from_packed_tensors(packed, scales, &device)
        .expect("Failed to from_packed_tensors");

    println!("BitLinear created successfully!");
    println!("  in_features: {}", in_dim);
    println!("  out_features: {}", out_dim);

    // Create test input
    let x = Tensor::randn(0.0f32, 1.0, (1, in_dim), &device).expect("Failed to create input");

    // Forward pass
    let output = layer.forward(&x).expect("Forward pass failed");

    println!("Output shape: {:?}", output.dims());

    // Verify output is valid
    let output_vec = output
        .flatten_all()
        .expect("Flatten failed")
        .to_vec1::<f32>()
        .expect("to_vec1 failed");

    // Check for NaN/Inf
    let has_nan = output_vec.iter().any(|&v| v.is_nan());
    let has_inf = output_vec.iter().any(|&v| v.is_infinite());

    assert!(!has_nan, "Output contains NaN!");
    assert!(!has_inf, "Output contains Inf!");

    // Check output has reasonable values (not all zeros)
    let sum: f32 = output_vec.iter().map(|v| v.abs()).sum();
    assert!(sum > 1e-6, "Output is all zeros!");

    println!("✅ Output valid: no NaN/Inf, sum={:.4}", sum);
}
