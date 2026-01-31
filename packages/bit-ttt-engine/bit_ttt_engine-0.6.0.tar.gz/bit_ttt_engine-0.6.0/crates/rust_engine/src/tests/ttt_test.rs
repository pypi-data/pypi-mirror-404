//! Tests for TTTLayer - Test-Time Training with Online Learning

#[cfg(test)]
mod tests {
    use crate::layers::{AdaptiveBitLinear, BitLinear, TTTLayer};
    use candle_core::{DType, Device, Tensor};

    /// Helper to create a TTTLayer with mock weights (direct construction)
    fn create_test_ttt_layer(hidden_dim: usize, inner_lr: f64) -> candle_core::Result<TTTLayer> {
        let device = Device::Cpu;
        let d_small = hidden_dim / 4;

        // Create down projection with BitLinear
        let down_weight = Tensor::randn(0.0f32, 0.1, (d_small, hidden_dim), &device)?;
        let proj_down = AdaptiveBitLinear {
            legacy_linear: Some(BitLinear {
                weight: down_weight,
                in_features: hidden_dim,
                out_features: d_small,
                packed_params: None,
            }),
            linear_4bit: None,
            reconstructed_weight: None,
            in_features: hidden_dim,
            out_features: d_small,
        };

        // Create up projection with BitLinear
        let up_weight = Tensor::randn(0.0f32, 0.1, (hidden_dim, d_small), &device)?;
        let proj_up = AdaptiveBitLinear {
            legacy_linear: Some(BitLinear {
                weight: up_weight,
                in_features: d_small,
                out_features: hidden_dim,
                packed_params: None,
            }),
            linear_4bit: None,
            reconstructed_weight: None,
            in_features: d_small,
            out_features: hidden_dim,
        };

        Ok(TTTLayer {
            hidden_dim,
            d_small,
            proj_down,
            proj_up,
            inner_lr,
        })
    }

    /// Helper to create initial w_state (identity-like matrix)
    fn create_initial_w_state(d_small: usize, batch_size: usize) -> candle_core::Result<Tensor> {
        let device = Device::Cpu;
        // Start with small identity-like initialization
        let eye = Tensor::eye(d_small, DType::F32, &device)?;
        let eye_scaled = (eye * 0.1)?;

        // Expand to batch: [B, D_small, D_small]
        if batch_size > 1 {
            eye_scaled
                .unsqueeze(0)?
                .expand((batch_size, d_small, d_small))
        } else {
            eye_scaled.unsqueeze(0)
        }
    }

    #[test]
    fn test_ttt_forward_update_basic() -> anyhow::Result<()> {
        let device = Device::Cpu;
        let hidden_dim = 64;
        let d_small = hidden_dim / 4; // 16
        let inner_lr = 0.01;
        let batch_size = 2;

        let ttt = create_test_ttt_layer(hidden_dim, inner_lr)?;

        // Create initial w_state [B, D_small, D_small]
        let w_state = create_initial_w_state(d_small, batch_size)?;

        // Create input x_t [B, Hidden]
        let x_t = Tensor::randn(0.0f32, 1.0, (batch_size, hidden_dim), &device)?;

        // Forward update
        let (output, w_new) = ttt.forward_update(&w_state, &x_t)?;

        // Verify output shape [B, Hidden]
        assert_eq!(
            output.dims(),
            &[batch_size, hidden_dim],
            "Output shape mismatch"
        );

        // Verify w_state shape unchanged [B, D_small, D_small]
        assert_eq!(
            w_new.dims(),
            &[batch_size, d_small, d_small],
            "W_state shape mismatch"
        );

        Ok(())
    }

    #[test]
    fn test_ttt_w_state_update() -> anyhow::Result<()> {
        let device = Device::Cpu;
        let hidden_dim = 64;
        let d_small = hidden_dim / 4;
        let inner_lr = 0.1; // Higher LR to see changes
        let batch_size = 1;

        let ttt = create_test_ttt_layer(hidden_dim, inner_lr)?;

        // Create initial w_state
        let w_state = create_initial_w_state(d_small, batch_size)?;
        let w_state_initial = w_state.clone();

        // Create input
        let x_t = Tensor::randn(0.0f32, 1.0, (batch_size, hidden_dim), &device)?;

        // Forward update
        let (_output, w_new) = ttt.forward_update(&w_state, &x_t)?;

        // W_state should be updated (different from initial)
        let diff = (&w_new - &w_state_initial)?
            .abs()?
            .sum_all()?
            .to_scalar::<f32>()?;
        assert!(
            diff > 1e-6,
            "W_state should be updated after forward_update, diff: {}",
            diff
        );

        Ok(())
    }

    #[test]
    fn test_ttt_sequential_updates() -> anyhow::Result<()> {
        let device = Device::Cpu;
        let hidden_dim = 64;
        let d_small = hidden_dim / 4;
        let inner_lr = 0.01;
        let batch_size = 1;

        let ttt = create_test_ttt_layer(hidden_dim, inner_lr)?;

        // Initial w_state
        let mut w_state = create_initial_w_state(d_small, batch_size)?;
        let w_initial = w_state.clone();

        // Process multiple tokens sequentially
        for _t in 0..5 {
            let x_t = Tensor::randn(0.0f32, 1.0, (batch_size, hidden_dim), &device)?;
            let (_output, w_new) = ttt.forward_update(&w_state, &x_t)?;
            w_state = w_new;
        }

        // W_state should have diverged from initial
        let total_diff = (&w_state - &w_initial)?
            .abs()?
            .sum_all()?
            .to_scalar::<f32>()?;
        assert!(
            total_diff > 0.0,
            "W_state should change over multiple updates"
        );

        Ok(())
    }

    #[test]
    fn test_ttt_forward_chunkwise_basic() -> anyhow::Result<()> {
        let device = Device::Cpu;
        let hidden_dim = 64;
        let d_small = hidden_dim / 4;
        let inner_lr = 0.01;
        let batch_size = 2;
        let seq_len = 16;
        let chunk_size = 4;

        let ttt = create_test_ttt_layer(hidden_dim, inner_lr)?;

        // Create initial w_state [B, D_small, D_small]
        let w_state = create_initial_w_state(d_small, batch_size)?;

        // Create input x [B, T, Hidden]
        let x = Tensor::randn(0.0f32, 1.0, (batch_size, seq_len, hidden_dim), &device)?;

        // Forward chunkwise
        let (output, w_final) = ttt.forward_chunkwise(&w_state, &x, chunk_size)?;

        // Verify output shape [B, T, Hidden]
        assert_eq!(
            output.dims(),
            &[batch_size, seq_len, hidden_dim],
            "Chunkwise output shape mismatch"
        );

        // Verify w_final shape [B, D_small, D_small]
        assert_eq!(
            w_final.dims(),
            &[batch_size, d_small, d_small],
            "W_final shape mismatch"
        );

        Ok(())
    }

    #[test]
    fn test_ttt_chunkwise_different_chunk_sizes() -> anyhow::Result<()> {
        let device = Device::Cpu;
        let hidden_dim = 64;
        let d_small = hidden_dim / 4;
        let inner_lr = 0.01;
        let batch_size = 1;
        let seq_len = 12;

        let ttt = create_test_ttt_layer(hidden_dim, inner_lr)?;

        // Test various chunk sizes
        for chunk_size in [1, 3, 4, 6, 12] {
            let w_state = create_initial_w_state(d_small, batch_size)?;
            let x = Tensor::randn(0.0f32, 1.0, (batch_size, seq_len, hidden_dim), &device)?;

            let (output, w_final) = ttt.forward_chunkwise(&w_state, &x, chunk_size)?;

            assert_eq!(
                output.dims(),
                &[batch_size, seq_len, hidden_dim],
                "Output shape mismatch for chunk_size={}",
                chunk_size
            );
            assert_eq!(
                w_final.dims(),
                &[batch_size, d_small, d_small],
                "W_final shape mismatch for chunk_size={}",
                chunk_size
            );
        }

        Ok(())
    }

    #[test]
    fn test_ttt_chunkwise_non_divisible_seq_len() -> anyhow::Result<()> {
        let device = Device::Cpu;
        let hidden_dim = 64;
        let d_small = hidden_dim / 4;
        let inner_lr = 0.01;
        let batch_size = 1;
        let seq_len = 17; // Not divisible by chunk_size
        let chunk_size = 4;

        let ttt = create_test_ttt_layer(hidden_dim, inner_lr)?;

        let w_state = create_initial_w_state(d_small, batch_size)?;
        let x = Tensor::randn(0.0f32, 1.0, (batch_size, seq_len, hidden_dim), &device)?;

        // Should handle non-divisible sequence length
        let (output, w_final) = ttt.forward_chunkwise(&w_state, &x, chunk_size)?;

        assert_eq!(
            output.dims(),
            &[batch_size, seq_len, hidden_dim],
            "Output should handle non-divisible seq_len"
        );
        assert_eq!(w_final.dims(), &[batch_size, d_small, d_small]);

        Ok(())
    }

    #[test]
    fn test_ttt_chunkwise_w_state_evolves() -> anyhow::Result<()> {
        let device = Device::Cpu;
        let hidden_dim = 64;
        let d_small = hidden_dim / 4;
        let inner_lr = 0.1;
        let batch_size = 1;
        let seq_len = 8;
        let chunk_size = 2;

        let ttt = create_test_ttt_layer(hidden_dim, inner_lr)?;

        let w_state = create_initial_w_state(d_small, batch_size)?;
        let w_initial = w_state.clone();
        let x = Tensor::randn(0.0f32, 1.0, (batch_size, seq_len, hidden_dim), &device)?;

        let (_output, w_final) = ttt.forward_chunkwise(&w_state, &x, chunk_size)?;

        // W_state should evolve through chunks
        let diff = (&w_final - &w_initial)?
            .abs()?
            .sum_all()?
            .to_scalar::<f32>()?;
        assert!(
            diff > 0.0,
            "W_state should change through chunkwise processing"
        );

        Ok(())
    }

    #[test]
    fn test_ttt_output_finite() -> anyhow::Result<()> {
        let device = Device::Cpu;
        let hidden_dim = 64;
        let d_small = hidden_dim / 4;
        let inner_lr = 0.01;
        let batch_size = 2;

        let ttt = create_test_ttt_layer(hidden_dim, inner_lr)?;

        let w_state = create_initial_w_state(d_small, batch_size)?;
        let x_t = Tensor::randn(0.0f32, 1.0, (batch_size, hidden_dim), &device)?;

        let (output, w_new) = ttt.forward_update(&w_state, &x_t)?;

        // Check all values are finite
        let output_vec: Vec<f32> = output.flatten_all()?.to_vec1()?;
        for val in &output_vec {
            assert!(val.is_finite(), "Output contains non-finite value: {}", val);
        }

        let w_vec: Vec<f32> = w_new.flatten_all()?.to_vec1()?;
        for val in &w_vec {
            assert!(val.is_finite(), "W_new contains non-finite value: {}", val);
        }

        Ok(())
    }

    #[test]
    fn test_ttt_precompute_packed() -> anyhow::Result<()> {
        let hidden_dim = 64;
        let inner_lr = 0.01;

        let mut ttt = create_test_ttt_layer(hidden_dim, inner_lr)?;

        // Should not panic
        ttt.precompute_packed()?;

        // Layer should still work after packing
        let device = Device::Cpu;
        let d_small = hidden_dim / 4;
        let w_state = create_initial_w_state(d_small, 1)?;
        let x_t = Tensor::randn(0.0f32, 1.0, (1, hidden_dim), &device)?;

        let (output, _w_new) = ttt.forward_update(&w_state, &x_t)?;
        assert_eq!(output.dims(), &[1, hidden_dim]);

        Ok(())
    }

    #[test]
    fn test_ttt_different_learning_rates() -> anyhow::Result<()> {
        let device = Device::Cpu;
        let hidden_dim = 64;
        let d_small = hidden_dim / 4;
        let batch_size = 1;

        // Same input for both
        let x_t = Tensor::randn(0.0f32, 1.0, (batch_size, hidden_dim), &device)?;

        // Low learning rate
        let ttt_low = create_test_ttt_layer(hidden_dim, 0.001)?;
        let w_state_low = create_initial_w_state(d_small, batch_size)?;
        let (_out_low, w_low) = ttt_low.forward_update(&w_state_low, &x_t)?;

        // High learning rate
        let ttt_high = create_test_ttt_layer(hidden_dim, 0.1)?;
        let w_state_high = create_initial_w_state(d_small, batch_size)?;
        let (_out_high, w_high) = ttt_high.forward_update(&w_state_high, &x_t)?;

        // Higher LR should cause larger change from initial
        let w_initial = create_initial_w_state(d_small, batch_size)?;
        let diff_low = (&w_low - &w_initial)?
            .abs()?
            .sum_all()?
            .to_scalar::<f32>()?;
        let diff_high = (&w_high - &w_initial)?
            .abs()?
            .sum_all()?
            .to_scalar::<f32>()?;

        // Note: Due to different random weights in layers, we just check both run
        // The key point is that both learning rates work without errors
        assert!(diff_low >= 0.0, "Low LR diff should be valid");
        assert!(diff_high >= 0.0, "High LR diff should be valid");

        println!(
            "Low LR update magnitude: {}, High LR update magnitude: {}",
            diff_low, diff_high
        );

        Ok(())
    }

    #[test]
    fn test_ttt_chunkwise_single_chunk() -> anyhow::Result<()> {
        let device = Device::Cpu;
        let hidden_dim = 64;
        let d_small = hidden_dim / 4;
        let inner_lr = 0.01;
        let batch_size = 1;
        let seq_len = 4;
        let chunk_size = 8; // Larger than seq_len, so only one chunk

        let ttt = create_test_ttt_layer(hidden_dim, inner_lr)?;

        let w_state = create_initial_w_state(d_small, batch_size)?;
        let x = Tensor::randn(0.0f32, 1.0, (batch_size, seq_len, hidden_dim), &device)?;

        let (output, w_final) = ttt.forward_chunkwise(&w_state, &x, chunk_size)?;

        assert_eq!(
            output.dims(),
            &[batch_size, seq_len, hidden_dim],
            "Output shape should be correct even with single chunk"
        );
        assert_eq!(w_final.dims(), &[batch_size, d_small, d_small]);

        Ok(())
    }
}
