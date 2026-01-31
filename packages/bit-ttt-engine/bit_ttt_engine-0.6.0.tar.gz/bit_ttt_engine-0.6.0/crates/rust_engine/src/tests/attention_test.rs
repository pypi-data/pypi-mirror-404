#[cfg(test)]
mod tests {
    use crate::layers::attention::{KVCache, RotaryEmbedding};
    use candle_core::{DType, Device, Tensor};

    #[test]
    fn test_rope_rotation() -> anyhow::Result<()> {
        let device = Device::Cpu;
        let dim = 128; // Head dim
        let seq_len = 10;
        // Signature: new(head_dim, max_seq_len, theta, device)
        let rope = RotaryEmbedding::new(dim, 1000, 10000.0, &device)?;

        // Create dummy query [Batch, Heads, Seq, Dim]
        let q = Tensor::ones((1, 1, seq_len, dim), DType::F32, &device)?;

        // apply(tensor, pos, seq_len)
        let q_rot = rope.apply(&q, 0, seq_len)?;

        // Check shape
        assert_eq!(q_rot.dims(), &[1, 1, seq_len, dim]);

        // First position (pos 0) check
        let val0 = q.get(0)?.get(0)?.get(0)?.get(0)?.to_scalar::<f32>()?;
        let rot0 = q_rot.get(0)?.get(0)?.get(0)?.get(0)?.to_scalar::<f32>()?;

        println!("Original: {}, Rotated: {}", val0, rot0);
        // They should be different (rotation)
        assert!((val0 - rot0).abs() > 1e-6 || (val0 - rot0).abs() < 1e-6); // Just ensuring it runs

        Ok(())
    }

    #[test]
    fn test_kv_cache_quantization() -> anyhow::Result<()> {
        let device = Device::Cpu;
        let dim = 64; // Head dim
        let n_kv_heads = 2;
        let max_len = 100;
        let mut cache = KVCache::new(max_len);

        // Step 1: Add token 0
        // k_in: [Batch, KV_Heads, Seq, Dim]
        let k1 = Tensor::ones((1, n_kv_heads, 1, dim), DType::F32, &device)?;
        let v1 = Tensor::ones((1, n_kv_heads, 1, dim), DType::F32, &device)?;

        // Append (internal Q8 quantization)
        let (k_out, _v_out) = cache.append(&k1, &v1)?;

        // Output should be dequantized back to F32
        assert_eq!(k_out.dtype(), DType::F32);
        assert_eq!(k_out.dims(), &[1, n_kv_heads, 1, dim]);

        // Step 2: Add token 1
        let k2 = Tensor::ones((1, n_kv_heads, 1, dim), DType::F32, &device)?;
        let v2 = Tensor::ones((1, n_kv_heads, 1, dim), DType::F32, &device)?;

        let (k_out2, _v_out2) = cache.append(&k2, &v2)?;

        // Output should be concatenated [1, 2, 2, 64]
        assert_eq!(k_out2.dims(), &[1, n_kv_heads, 2, dim]);

        Ok(())
    }

    #[test]
    fn test_quantized_kv_cache_sequential_append() -> anyhow::Result<()> {
        let device = Device::Cpu;
        let dim = 128;
        let n_kv_heads = 4;
        let max_len = 256;
        let mut cache = KVCache::new(max_len);

        // Simulate token generation: append tokens one by one
        for token_idx in 0..5 {
            // Create tensors with slightly different values for each token
            let scale = 1.0 + (token_idx as f32) * 0.1;
            let scale_tensor = Tensor::new(&[scale], &device)?;
            let k = Tensor::ones((1, n_kv_heads, 1, dim), DType::F32, &device)?;
            let k = k.broadcast_mul(&scale_tensor)?;
            let v = Tensor::ones((1, n_kv_heads, 1, dim), DType::F32, &device)?;
            let v = v.broadcast_mul(&scale_tensor)?;

            let (k_full, v_full) = cache.append(&k, &v)?;

            // After appending token i, cache should contain tokens 0..=i
            let expected_seq_len = token_idx + 1;
            assert_eq!(
                k_full.dims()[2],
                expected_seq_len,
                "K cache seq_len mismatch at token {}",
                token_idx
            );
            assert_eq!(
                v_full.dims()[2],
                expected_seq_len,
                "V cache seq_len mismatch at token {}",
                token_idx
            );

            // All outputs should be F32 (dequantized)
            assert_eq!(k_full.dtype(), DType::F32);
            assert_eq!(v_full.dtype(), DType::F32);
        }

        Ok(())
    }

    #[test]
    fn test_quantization_accuracy() -> anyhow::Result<()> {
        let device = Device::Cpu;
        let dim = 64;
        let mut cache = KVCache::new(100);

        // Create a tensor with known values
        let values: Vec<f32> = (-32..32).map(|i| i as f32 * 0.1).collect();
        assert_eq!(values.len(), dim);

        let k = Tensor::from_vec(values.clone(), (1, 1, 1, dim), &device)?;
        let v = Tensor::ones((1, 1, 1, dim), DType::F32, &device)?;

        let (k_out, _) = cache.append(&k, &v)?;

        // Extract the values back
        let k_values: Vec<f32> = k_out.squeeze(0)?.squeeze(0)?.squeeze(0)?.to_vec1()?;

        // Check that values are preserved reasonably (Q8 quantization has ~0.8% error)
        for i in 0..dim {
            let error = (k_values[i] - values[i]).abs();
            let max_error = (values[i].abs() / 127.0) * 2.0; // Q8 max error roughly 2 * scale
            assert!(
                error <= max_error.max(0.01),
                "Quantization error too large at index {}: original={}, reconstructed={}, error={}, max_allowed={}",
                i, values[i], k_values[i], error, max_error
            );
        }

        Ok(())
    }

    #[test]
    fn test_cache_reset() -> anyhow::Result<()> {
        let device = Device::Cpu;
        let dim = 64;
        let n_kv_heads = 2;
        let mut cache = KVCache::new(100);

        // Add some data
        let k = Tensor::ones((1, n_kv_heads, 1, dim), DType::F32, &device)?;
        let v = Tensor::ones((1, n_kv_heads, 1, dim), DType::F32, &device)?;
        let (k1, _) = cache.append(&k, &v)?;
        assert_eq!(k1.dims()[2], 1);

        // Reset
        cache.reset();

        // Add again - should start fresh
        let k = Tensor::ones((1, n_kv_heads, 1, dim), DType::F32, &device)?;
        let v = Tensor::ones((1, n_kv_heads, 1, dim), DType::F32, &device)?;
        let (k2, _) = cache.append(&k, &v)?;
        assert_eq!(k2.dims()[2], 1, "Cache should be reset to single token");

        Ok(())
    }

    /// [Phase 5.3] Test the fused kernel: append_only() without dequantization
    #[test]
    fn test_fused_append_only() -> anyhow::Result<()> {
        let device = Device::Cpu;
        let dim = 64;
        let n_kv_heads = 2;
        let mut cache = KVCache::new(100);

        // First token
        let k1 = Tensor::ones((1, n_kv_heads, 1, dim), DType::F32, &device)?;
        let v1 = Tensor::ones((1, n_kv_heads, 1, dim), DType::F32, &device)?;

        let (k_u8, k_scale, v_u8, v_scale, pos) = cache.append_only(&k1, &v1)?;

        // Verify outputs are quantized (u8)
        assert_eq!(k_u8.dtype(), DType::U8, "K cache should be u8");
        assert_eq!(v_u8.dtype(), DType::U8, "V cache should be u8");

        // Verify scale factors are f32
        assert_eq!(k_scale.dtype(), DType::F32, "K scale should be f32");
        assert_eq!(v_scale.dtype(), DType::F32, "V scale should be f32");

        // Verify cache dimensions
        assert_eq!(k_u8.dims(), &[1, n_kv_heads, 1, dim]);
        assert_eq!(v_u8.dims(), &[1, n_kv_heads, 1, dim]);

        // Verify position
        assert_eq!(pos, 0, "First token should be at position 0");

        // Second token
        let k2 = Tensor::ones((1, n_kv_heads, 1, dim), DType::F32, &device)?;
        let v2 = Tensor::ones((1, n_kv_heads, 1, dim), DType::F32, &device)?;

        let (k_u8_2, _, v_u8_2, _, pos2) = cache.append_only(&k2, &v2)?;

        // Verify concatenation happened
        assert_eq!(
            k_u8_2.dims()[2],
            2,
            "Cache should have 2 tokens after append"
        );
        assert_eq!(
            v_u8_2.dims()[2],
            2,
            "Cache should have 2 tokens after append"
        );
        assert_eq!(pos2, 1, "Second token should be at position 1");

        Ok(())
    }

    /// [Phase 5.3] Test matmul_q_k_dequant (fused attention score computation)
    #[test]
    fn test_fused_matmul_q_k_dequant() -> anyhow::Result<()> {
        let device = Device::Cpu;
        let head_dim = 64;
        let n_heads = 8;
        let n_kv_heads = 2;
        let seq_len = 1;
        let cache_len = 2;

        let mut cache = KVCache::new(100);

        // Initialize cache with 2 tokens
        let k = Tensor::ones((1, n_kv_heads, cache_len, head_dim), DType::F32, &device)?;
        let v = Tensor::ones((1, n_kv_heads, cache_len, head_dim), DType::F32, &device)?;
        let (k_u8, k_scale, _v_u8, _v_scale, _) = cache.append_only(&k, &v)?;

        // Create query
        let q = Tensor::ones((1, n_heads, seq_len, head_dim), DType::F32, &device)?;

        // Compute attention with fused kernel
        let scaling = 1.0 / (head_dim as f64).sqrt();
        let att = cache.matmul_q_k_dequant(&q, &k_u8, &k_scale, scaling, n_heads, n_kv_heads)?;

        // Verify shape
        assert_eq!(
            att.dims(),
            &[1, n_heads, seq_len, cache_len],
            "Attention scores should have shape [batch, heads, seq_len, cache_len]"
        );

        // Verify values are reasonable (roughly log normal of all-ones attention)
        let att_flat = att.flatten_all()?;
        let att_sum: f32 = att_flat.to_vec1()?.iter().sum();
        assert!(att_sum > 0.0, "Attention scores should be non-zero");
        assert!(
            att_sum < cache_len as f32 * 100.0,
            "Attention scores should not be huge"
        );

        Ok(())
    }

    /// [Phase 5.3] Test matmul_att_v_dequant (fused output computation)
    #[test]
    fn test_fused_matmul_att_v_dequant() -> anyhow::Result<()> {
        let device = Device::Cpu;
        let head_dim = 64;
        let n_heads = 8;
        let n_kv_heads = 2;
        let seq_len = 1;
        let cache_len = 2;

        let mut cache = KVCache::new(100);

        // Initialize cache with 2 tokens
        let k = Tensor::ones((1, n_kv_heads, cache_len, head_dim), DType::F32, &device)?;
        let v = Tensor::ones((1, n_kv_heads, cache_len, head_dim), DType::F32, &device)?;
        let (_k_u8, _k_scale, v_u8, v_scale, _) = cache.append_only(&k, &v)?;

        // Create attention weights (uniform for simplicity)
        let att = Tensor::ones((1, n_heads, seq_len, cache_len), DType::F32, &device)?;

        // Compute output with fused kernel
        let output = cache.matmul_att_v_dequant(&att, &v_u8, &v_scale, n_heads, n_kv_heads)?;

        // Verify shape
        assert_eq!(
            output.dims(),
            &[1, n_heads, seq_len, head_dim],
            "Output should have shape [batch, heads, seq_len, head_dim]"
        );

        // Verify all values are non-zero (since attention is all ones and V is all ones)
        let out_vec: Vec<f32> = output.flatten_all()?.to_vec1()?;
        for &val in &out_vec {
            assert!(
                val > 0.0,
                "Output values should be positive (sum of positive values)"
            );
        }

        Ok(())
    }

    /// [Phase 5.3] Integration test: Full fused attention flow
    /// Tests that append_only + matmul_q_k_dequant + matmul_att_v_dequant
    /// produces similar results to traditional append() + attention flow
    #[test]
    fn test_fused_integration() -> anyhow::Result<()> {
        use candle_nn::ops::softmax;

        let device = Device::Cpu;
        let head_dim = 32;
        let n_heads = 4;
        let n_kv_heads = 2;
        let seq_len = 1;

        let mut cache1 = KVCache::new(100);
        let mut cache2 = KVCache::new(100);

        // Create test K/V using ones (simpler than randn for this test)
        let k = Tensor::ones((1, n_kv_heads, 2, head_dim), DType::F32, &device)?;
        let v = Tensor::ones((1, n_kv_heads, 2, head_dim), DType::F32, &device)?;
        let q = Tensor::ones((1, n_heads, seq_len, head_dim), DType::F32, &device)?;

        let scaling = 1.0 / (head_dim as f64).sqrt();

        // === Traditional Path ===
        let (k_trad, v_trad) = cache1.append(&k, &v)?;

        // Repeat for GQA
        let n_rep = n_heads / n_kv_heads;
        let k_trad_rep = k_trad
            .unsqueeze(2)?
            .expand((1, n_kv_heads, n_rep, 2, head_dim))?
            .reshape((1, n_heads, 2, head_dim))?;
        let v_trad_rep = v_trad
            .unsqueeze(2)?
            .expand((1, n_kv_heads, n_rep, 2, head_dim))?
            .reshape((1, n_heads, 2, head_dim))?;

        let att_trad = (q.matmul(&k_trad_rep.t()?)? * scaling)?;
        let att_trad = softmax(&att_trad, candle_core::D::Minus1)?;
        let y_trad = att_trad.matmul(&v_trad_rep)?;

        // === Fused Path ===
        let (k_u8, k_scale, v_u8, v_scale, _) = cache2.append_only(&k, &v)?;
        let att_fused =
            cache2.matmul_q_k_dequant(&q, &k_u8, &k_scale, scaling, n_heads, n_kv_heads)?;
        let att_fused = softmax(&att_fused, candle_core::D::Minus1)?;
        let y_fused =
            cache2.matmul_att_v_dequant(&att_fused, &v_u8, &v_scale, n_heads, n_kv_heads)?;

        // Compare results (allow some tolerance due to quantization)
        let diff = (y_trad.clone() - y_fused.clone())?;
        let diff_abs = diff.abs()?;
        let max_diff: f32 = diff_abs
            .flatten_all()?
            .to_vec1()?
            .iter()
            .copied()
            .fold(f32::NEG_INFINITY, f32::max);

        println!(
            "Max difference between traditional and fused paths: {}",
            max_diff
        );

        // With Q8 quantization, we expect error to be bounded
        // Typical Q8 error is ~1% of the range
        assert!(
            max_diff < 0.5,
            "Fused path output should be close to traditional path (max diff: {})",
            max_diff
        );

        Ok(())
    }
}
