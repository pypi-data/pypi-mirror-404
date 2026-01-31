//! Quick generation test - just 3 tokens

use candle_core::{IndexOp, Tensor};
use cortex_rust::model::{BitLlamaConfig, Llama};
use std::fs;

fn main() -> anyhow::Result<()> {
    // Parse arguments
    let args: Vec<String> = std::env::args().collect();
    let model_path = args
        .iter()
        .position(|s| s == "--model" || s == "--model-path")
        .and_then(|i| args.get(i + 1))
        .map(|s| s.as_str())
        .unwrap_or("benchmark/tinyllama-1.1b-converted");
    let prompt = args
        .iter()
        .position(|s| s == "--prompt")
        .and_then(|i| args.get(i + 1))
        .map(|s| s.as_str())
        .unwrap_or("Hello, my name is");

    let bypass_kv = args.iter().any(|s| s == "--bypass-kv");

    // Load config
    let config_str = fs::read_to_string(format!("{}/config.json", model_path))?;
    let config: BitLlamaConfig = serde_json::from_str(&config_str)?;

    println!("Loading model...");
    let mut llama = Llama::load_direct(
        format!("{}/model.safetensors", model_path),
        format!("{}/tokenizer.json", model_path),
        config,
    )?;
    println!("Model loaded!");

    // Enable bypass mode if requested (debug: f32 KV cache without quantization)
    if bypass_kv {
        println!("⚠️  Bypass mode enabled: KV cache will use f32 (no quantization)");
        llama.model.set_kv_bypass(true);
    }
    let tokens = llama
        .tokenizer
        .encode(prompt, true)
        .map_err(candle_core::Error::wrap)?;
    let mut token_ids: Vec<u32> = tokens.get_ids().to_vec();

    println!("\nPrompt: {:?}", prompt);
    println!("Token IDs: {:?}", token_ids);

    // Reset model state
    llama.model.reset_kv_cache();

    // Prefill
    let device = &llama.device;
    let input = Tensor::new(&token_ids[..], device)?.unsqueeze(0)?;
    println!("\nPrefill input shape: {:?}", input.dims());

    let logits = llama.model.forward(&input, &mut llama.w_states)?;
    println!("Prefill logits shape: {:?}", logits.dims());

    // Get next token from last position
    let last_logits = logits.i((0, logits.dim(1)? - 1))?;

    // Debug: print top 5 logits
    let logits_vec: Vec<f32> = last_logits.to_vec1()?;
    let mut indexed: Vec<(usize, f32)> = logits_vec
        .iter()
        .enumerate()
        .map(|(i, &v)| (i, v))
        .collect();
    indexed.sort_by(|a, b| b.1.partial_cmp(&a.1).unwrap());
    println!("\nTop 5 logits:");
    for (i, (idx, val)) in indexed.iter().take(5).enumerate() {
        println!("  {}. {} = {:.4}", i + 1, idx, val);
    }

    let next_token = argmax(&last_logits)?;
    println!("\nNext token (greedy): {}", next_token);
    let decoded = llama
        .tokenizer
        .decode(&[next_token], true)
        .unwrap_or_else(|_| "<error>".to_string());
    println!("Decoded: {:?}", decoded);
    token_ids.push(next_token);

    // Generate 2 more tokens
    for i in 0..2 {
        println!("\n--- Generate token {} ---", i + 2);
        println!("Current pos before forward: {}", llama.model.current_pos);
        let input = Tensor::new(&[*token_ids.last().unwrap()], device)?.unsqueeze(0)?;
        let logits = llama.model.forward(&input, &mut llama.w_states)?;
        println!("Current pos after forward: {}", llama.model.current_pos);
        let last_logits = logits.i((0, logits.dim(1)? - 1))?;

        // Debug: print top 5 logits for each generation
        let logits_vec: Vec<f32> = last_logits.to_vec1()?;
        let mut indexed: Vec<(usize, f32)> = logits_vec
            .iter()
            .enumerate()
            .map(|(i, &v)| (i, v))
            .collect();
        indexed.sort_by(|a, b| b.1.partial_cmp(&a.1).unwrap());
        println!("Top 5 logits:");
        for (j, (idx, val)) in indexed.iter().take(5).enumerate() {
            println!("  {}. {} = {:.4}", j + 1, idx, val);
        }

        let next_token = argmax(&last_logits)?;
        println!("Next token: {}", next_token);
        let decoded = llama
            .tokenizer
            .decode(&[next_token], true)
            .unwrap_or_else(|_| "<error>".to_string());
        println!("Decoded: {:?}", decoded);
        token_ids.push(next_token);
    }

    // Final output
    let full_output = llama
        .tokenizer
        .decode(&token_ids, true)
        .unwrap_or_else(|_| "<error>".to_string());
    println!("\n=== Full output ===");
    println!("{}", full_output);

    Ok(())
}

fn argmax(logits: &Tensor) -> candle_core::Result<u32> {
    let logits_vec: Vec<f32> = logits.to_vec1()?;
    let (idx, _) = logits_vec
        .iter()
        .enumerate()
        .max_by(|a, b| a.1.partial_cmp(b.1).unwrap())
        .unwrap();
    Ok(idx as u32)
}
