//! GGUF End-to-End Tests
//!
//! Tests GGUF model loading and inference.
//! Skipped if no GGUF model is available.

use candle_core::Device;
use cortex_rust::model::gguf_model::GgufModel;

mod common;

/// Test GGUF model loading
#[test]
fn test_gguf_model_load() {
    let model_path = common::get_gguf_model_path();

    if !model_path.exists() {
        eprintln!("⏭️ Skipping GGUF test: model not found at {:?}", model_path);
        eprintln!("   Set BIT_TEST_GGUF_PATH or place a .gguf file at the default location");
        return;
    }

    println!("🧪 Loading GGUF model from: {:?}", model_path);

    let device = Device::Cpu;
    let model = GgufModel::load(&model_path, &device);

    match model {
        Ok(m) => {
            println!("✅ Model loaded successfully!");
            println!(
                "   Config: {} layers, {} hidden",
                m.config.num_layers, m.config.hidden_dim
            );
            println!("   RMS norm eps: {:.0e}", m.config.rms_norm_eps);
        }
        Err(e) => {
            panic!("❌ Failed to load GGUF model: {}", e);
        }
    }
}

/// Test GGUF model inference (single token)
#[test]
fn test_gguf_model_inference() {
    let model_path = common::get_gguf_model_path();

    if !model_path.exists() {
        eprintln!("⏭️ Skipping GGUF inference test: model not found");
        return;
    }

    let device = Device::Cpu;
    let mut model = GgufModel::load(&model_path, &device).expect("Failed to load model");

    // Create input: single token (BOS token = 1 for most LLaMA models)
    let input_ids = candle_core::Tensor::new(&[[1u32]], &device).expect("Failed to create tensor");

    println!(
        "🧪 Running inference with input_ids: {:?}",
        input_ids.dims()
    );

    let logits = model.forward(&input_ids, 0);

    match logits {
        Ok(l) => {
            let dims = l.dims();
            println!("✅ Inference successful!");
            println!("   Logits shape: {:?}", dims);
            assert_eq!(dims.len(), 3, "Logits should be 3D [batch, seq, vocab]");
            assert_eq!(dims[0], 1, "Batch size should be 1");
            assert_eq!(dims[1], 1, "Seq len should be 1");
        }
        Err(e) => {
            panic!("❌ Inference failed: {}", e);
        }
    }
}

/// Test GGUF config reading
#[test]
fn test_gguf_config_rms_norm_eps() {
    let model_path = common::get_gguf_model_path();

    if !model_path.exists() {
        eprintln!("⏭️ Skipping GGUF config test: model not found");
        return;
    }

    let device = Device::Cpu;
    let model = GgufModel::load(&model_path, &device).expect("Failed to load model");

    // rms_norm_eps should be read from model or use default
    let eps = model.config.rms_norm_eps;
    println!("🧪 RMS norm epsilon: {:.2e}", eps);

    // Common values are 1e-5 or 1e-6
    assert!(
        (1e-7..1e-4).contains(&eps),
        "rms_norm_eps should be between 1e-7 and 1e-4, got {}",
        eps
    );
}
