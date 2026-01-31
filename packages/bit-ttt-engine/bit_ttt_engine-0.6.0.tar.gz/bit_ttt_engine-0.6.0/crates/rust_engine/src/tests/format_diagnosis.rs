//! Format Diagnosis Test
//!
//! Diagnoses the mismatch between Python converter output and Rust loader expectations.
//!
//! This test examines:
//! - Tensor shapes (expected vs actual)
//! - Data types (U8, F32, etc.)
//! - Value ranges (0-255 full range vs 0,1,2 ternary codes)
//! - Scales structure and values

use candle_core::{Device, Tensor};
use std::collections::HashMap;
use std::path::PathBuf;

/// Get the path to the TinyLlama 1.1B converted test model.
///
/// # Environment Variable
/// Set `BIT_TEST_TINYLLAMA_PATH` to override the default path.
fn get_tinyllama_model_safetensors() -> PathBuf {
    std::env::var("BIT_TEST_TINYLLAMA_PATH")
        .map(|p| PathBuf::from(p).join("model.safetensors"))
        .unwrap_or_else(|_| {
            PathBuf::from(env!("CARGO_MANIFEST_DIR"))
                .join("../../benchmark/tinyllama-1.1b-converted/model.safetensors")
        })
}

/// Comprehensive diagnosis of converted model format
#[test]
fn format_diagnosis_full() {
    // Get model path from helper function (supports env var override)
    let model_path = get_tinyllama_model_safetensors();

    if !model_path.exists() {
        eprintln!("⚠️ Model not found: {:?}", model_path);
        eprintln!("  Run the converter first to create the model.");
        eprintln!("  Or set BIT_TEST_TINYLLAMA_PATH to the model directory.");
        return;
    }

    let device = Device::Cpu;

    // Load all tensors
    let tensors =
        candle_core::safetensors::load(&model_path, &device).expect("Failed to load safetensors");

    println!("\n{:=^80}", "");
    println!("{:^80}", " FORMAT DIAGNOSIS REPORT ");
    println!("{:=^80}\n", "");
    println!("Model: {:?}", model_path);
    println!("Total tensors: {}\n", tensors.len());

    // Categorize tensors
    let mut weight_packed: Vec<(&String, &Tensor)> = Vec::new();
    let mut scales: Vec<(&String, &Tensor)> = Vec::new();
    let mut other: Vec<(&String, &Tensor)> = Vec::new();

    for (name, tensor) in &tensors {
        if name.ends_with(".weight_packed") {
            weight_packed.push((name, tensor));
        } else if name.ends_with(".scales") {
            scales.push((name, tensor));
        } else {
            other.push((name, tensor));
        }
    }

    println!("Tensor categories:");
    println!("  - weight_packed: {}", weight_packed.len());
    println!("  - scales: {}", scales.len());
    println!("  - other: {}\n", other.len());

    // === WEIGHT_PACKED ANALYSIS ===
    println!("\n{:-^80}", " WEIGHT_PACKED ANALYSIS ");

    if weight_packed.is_empty() {
        println!("❌ No weight_packed tensors found!");
        println!("   This suggests the model is not in Bit-TTT format.");
        return;
    }

    // Analyze first few weight_packed tensors
    let mut shape_stats: HashMap<String, usize> = HashMap::new();
    let mut dtype_stats: HashMap<String, usize> = HashMap::new();
    let mut value_range_issues = 0;

    for (i, (name, tensor)) in weight_packed.iter().enumerate() {
        let dims = tensor.dims();
        let dtype = format!("{:?}", tensor.dtype());
        let shape_str = format!("{:?}", dims);

        *shape_stats.entry(shape_str.clone()).or_insert(0) += 1;
        *dtype_stats.entry(dtype.clone()).or_insert(0) += 1;

        // Detailed analysis for first 3 tensors
        if i < 3 {
            println!("\n[{}] {}", i + 1, name);
            println!("  Shape: {:?}", dims);
            println!("  Dtype: {:?}", tensor.dtype());

            // Analyze dimensions
            match dims.len() {
                2 => {
                    let (out_dim, packed_in) = (dims[0], dims[1]);
                    let in_dim = packed_in * 4;
                    println!("  → Inferred: out_dim={}, in_dim={}", out_dim, in_dim);
                    println!("  → Format: [Out, In/4] (simple packed)");
                }
                3 => {
                    let (out_dim, packed_in, n_bases) = (dims[0], dims[1], dims[2]);
                    let in_dim = packed_in * 4;
                    println!(
                        "  → Inferred: out_dim={}, in_dim={}, n_bases={}",
                        out_dim, in_dim, n_bases
                    );
                    println!("  → Format: [Out, In/4, NumBases] (multi-base)");
                }
                4 => {
                    println!("  ⚠️ 4D shape detected! This may indicate incorrect format.");
                    println!(
                        "  → Dims: [{}] × [{}] × [{}] × [{}]",
                        dims[0], dims[1], dims[2], dims[3]
                    );
                    if dims[3] == 4 {
                        println!(
                            "  → Possible format: [Out, In/4, NumBases, 4] (unpacked ternary)"
                        );
                        println!("  ❌ ISSUE: 4 ternary values should be packed into 1 byte!");
                    }
                }
                _ => {
                    println!("  ❌ Unexpected rank: {}", dims.len());
                }
            }

            // Value range analysis
            if let Ok(values) = tensor.flatten_all() {
                if let Ok(values) = values.to_vec1::<u8>() {
                    let min = values.iter().cloned().min().unwrap_or(0);
                    let max = values.iter().cloned().max().unwrap_or(0);
                    let unique: std::collections::HashSet<_> = values.iter().cloned().collect();

                    println!("  Value range: {} - {}", min, max);
                    println!("  Unique values: {} (first 20: {:?})", unique.len(), {
                        let mut v: Vec<_> = unique.iter().cloned().collect();
                        v.sort();
                        v.truncate(20);
                        v
                    });

                    // Check if values are properly packed
                    if unique.len() <= 4 && unique.iter().all(|&v| v <= 2) {
                        println!("  ❌ ISSUE: Values are raw ternary codes (0,1,2), NOT packed!");
                        println!("     Expected: 4 ternary values packed into each u8 (0-255)");
                        println!("     Actual: Each u8 contains only one ternary value");
                        value_range_issues += 1;
                    } else if max <= 85 {
                        // 01010101 = 85 (all +1)
                        println!("  ✅ Values appear to be properly packed");
                    } else {
                        println!("  ⚠️ Full u8 range used, need to verify encoding");
                    }
                } else if let Ok(values) = values.to_vec1::<f32>() {
                    // F32 dtype - definitely wrong for packed weights
                    let min = values.iter().cloned().fold(f32::INFINITY, f32::min);
                    let max = values.iter().cloned().fold(f32::NEG_INFINITY, f32::max);
                    println!("  ❌ DTYPE ISSUE: weight_packed is F32, should be U8!");
                    println!("  F32 value range: {} - {}", min, max);
                    value_range_issues += 1;
                }
            }
        }
    }

    // Summary statistics
    println!("\n{:-^80}", " SHAPE STATISTICS ");
    for (shape, count) in &shape_stats {
        println!("  {} : {} tensors", shape, count);
    }

    println!("\n{:-^80}", " DTYPE STATISTICS ");
    for (dtype, count) in &dtype_stats {
        println!("  {} : {} tensors", dtype, count);
    }

    // === SCALES ANALYSIS ===
    println!("\n{:-^80}", " SCALES ANALYSIS ");

    if scales.is_empty() {
        println!("❌ No scales tensors found!");
    } else {
        let mut scales_shape_stats: HashMap<String, usize> = HashMap::new();

        for (i, (name, tensor)) in scales.iter().enumerate() {
            let dims = tensor.dims();
            let shape_str = format!("{:?}", dims);
            *scales_shape_stats.entry(shape_str.clone()).or_insert(0) += 1;

            if i < 3 {
                println!("\n[{}] {}", i + 1, name);
                println!("  Shape: {:?}", dims);
                println!("  Dtype: {:?}", tensor.dtype());

                // Print actual values
                if let Ok(values) = tensor.flatten_all() {
                    if let Ok(values) = values.to_vec1::<f32>() {
                        println!("  Values: {:?}", values);

                        // Analyze scales interpretation
                        if values.len() == 1 {
                            println!("  → Single scale (legacy format)");
                        } else if values.len() == 3 {
                            println!("  → 3 scales (expected for ternary: -1, 0, +1)");
                            if values[1].abs() < 0.01 {
                                println!("  ✅ Middle scale near 0 (correct for zero value)");
                            }
                        } else {
                            println!("  ⚠️ Unusual number of scales: {}", values.len());
                        }
                    }
                }
            }
        }

        println!("\nScales shape statistics:");
        for (shape, count) in &scales_shape_stats {
            println!("  {} : {} tensors", shape, count);
        }
    }

    // === EXPECTED VS ACTUAL FORMAT ===
    println!("\n{:-^80}", " EXPECTED VS ACTUAL FORMAT ");

    println!("\nExpected Rust loader format:");
    println!("  weight_packed: [Out, In/4] as U8");
    println!("    - Each u8 contains 4 packed ternary values");
    println!("    - Encoding: 00=0, 01=+1, 10=-1, 11=padding");
    println!("    - Value range: 0-255 (various bit patterns)");
    println!("  scales: [1] or [NumBases] as F32");
    println!("    - Single value for legacy mode");
    println!("    - Multiple values for multi-base mode");

    println!("\nPotential format issues detected: {}", value_range_issues);

    if value_range_issues > 0 {
        println!("\n{:-^80}", " RECOMMENDATIONS ");
        println!("1. Check Python converter packing logic");
        println!("2. Ensure 4 ternary values are packed into each u8");
        println!("3. Verify bit encoding matches Rust unpacking");
        println!("4. Consider running converter with debug output");
    }

    println!("\n{:=^80}\n", "");
}

/// Test a specific layer's format in detail
#[test]
fn format_diagnosis_single_layer() {
    // Get model path from helper function (supports env var override)
    let model_path = get_tinyllama_model_safetensors();

    if !model_path.exists() {
        eprintln!("⚠️ Model not found at {:?}, skipping test", model_path);
        eprintln!("  Or set BIT_TEST_TINYLLAMA_PATH to the model directory.");
        return;
    }

    let device = Device::Cpu;
    let tensors =
        candle_core::safetensors::load(&model_path, &device).expect("Failed to load safetensors");

    // Test layer 0 gate_proj
    let layer_name = "model.layers.0.mlp.gate_proj";
    let packed_key = format!("{}.weight_packed", layer_name);
    let scales_key = format!("{}.scales", layer_name);

    println!("\n=== Detailed Layer Analysis: {} ===\n", layer_name);

    let packed = match tensors.get(&packed_key) {
        Some(t) => t,
        None => {
            println!("❌ {} not found", packed_key);
            return;
        }
    };

    let scales = match tensors.get(&scales_key) {
        Some(t) => t,
        None => {
            println!("❌ {} not found", scales_key);
            return;
        }
    };

    println!("weight_packed:");
    println!("  Shape: {:?}", packed.dims());
    println!("  Dtype: {:?}", packed.dtype());

    println!("\nscales:");
    println!("  Shape: {:?}", scales.dims());
    println!("  Dtype: {:?}", scales.dtype());

    // Check if values are ternary codes or packed
    if let Ok(flat) = packed.flatten_all() {
        if let Ok(values) = flat.to_vec1::<u8>() {
            let sample: Vec<_> = values.iter().take(100).cloned().collect();
            println!("\nFirst 100 byte values: {:?}", sample);

            // Count value distribution
            let mut dist = [0usize; 256];
            for &v in &values {
                dist[v as usize] += 1;
            }

            // Find non-zero distribution
            let non_zero: Vec<_> = dist
                .iter()
                .enumerate()
                .filter(|(_, &c)| c > 0)
                .map(|(v, c)| (v, *c))
                .collect();

            println!("\nValue distribution (value: count):");
            for (v, c) in &non_zero {
                let pct = (*c as f64 / values.len() as f64) * 100.0;
                println!("  {}: {} ({:.1}%)", v, c, pct);
            }

            // Diagnostic conclusion
            if non_zero.len() <= 4 {
                println!(
                    "\n❌ DIAGNOSIS: Only {} unique values found!",
                    non_zero.len()
                );
                println!("   This indicates unpacked ternary codes, not bit-packed data.");
                println!("   Python converter is saving raw codes instead of packing them.");
            }
        }
    }

    // Print scales values
    if let Ok(scales_vec) = scales.flatten_all() {
        if let Ok(values) = scales_vec.to_vec1::<f32>() {
            println!("\nScales values: {:?}", values);
        }
    }
}

/// Verify the expected bit encoding
#[test]
fn format_diagnosis_encoding_check() {
    println!("\n=== Expected Bit Encoding Reference ===\n");

    // Reference encoding from packing.rs
    println!("Ternary to 2-bit encoding:");
    println!("   0  → 00 (binary)");
    println!("  +1  → 01 (binary)");
    println!("  -1  → 10 (binary)");
    println!("  pad → 11 (binary)");

    println!("\nExample packed byte (4 weights → 1 byte):");
    println!("  Weights: [+1, 0, -1, +1]");
    println!("  Codes:   [01, 00, 10, 01]");
    println!("  Packed:  01_00_10_01 = 0x49 = 73");

    // Create a reference packed byte
    let weights = [1i8, 0, -1, 1]; // +1, 0, -1, +1
    let mut byte: u8 = 0;
    for (i, &w) in weights.iter().enumerate() {
        let code: u8 = match w {
            1 => 1,  // 01
            -1 => 2, // 10
            0 => 0,  // 00
            _ => 3,  // 11 (padding)
        };
        byte |= code << (i * 2);
    }
    println!("\nVerification: packed byte = {} (0x{:02X})", byte, byte);

    // All +1: 01010101 = 85
    let all_plus = 0b01010101u8;
    println!(
        "\nAll +1 weights: {:08b} = {} (0x{:02X})",
        all_plus, all_plus, all_plus
    );

    // All -1: 10101010 = 170
    let all_minus = 0b10101010u8;
    println!(
        "All -1 weights: {:08b} = {} (0x{:02X})",
        all_minus, all_minus, all_minus
    );

    // All 0: 00000000 = 0
    let all_zero = 0b00000000u8;
    println!(
        "All 0 weights:  {:08b} = {} (0x{:02X})",
        all_zero, all_zero, all_zero
    );

    println!("\nIf Python converter outputs only values 0, 1, 2:");
    println!("  → Values are raw ternary CODES, not packed bytes");
    println!("  → Need to pack 4 codes into each byte");
}
