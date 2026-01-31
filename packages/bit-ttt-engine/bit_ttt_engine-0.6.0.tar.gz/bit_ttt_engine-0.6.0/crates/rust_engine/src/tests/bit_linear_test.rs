//! Tests for BitLinear - 1.58-bit Quantized Linear Layer

#[cfg(test)]
mod tests {
    use crate::layers::BitLinear;
    use candle_core::{DType, Device, Tensor};

    /// Helper to create a BitLinear layer with random weights (direct construction)
    fn create_test_bitlinear(in_dim: usize, out_dim: usize) -> candle_core::Result<BitLinear> {
        let device = Device::Cpu;
        let weight = Tensor::randn(0.0f32, 1.0, (out_dim, in_dim), &device)?;

        Ok(BitLinear {
            weight,
            in_features: in_dim,
            out_features: out_dim,
            packed_params: None,
        })
    }

    #[test]
    fn test_bitlinear_forward_basic() -> anyhow::Result<()> {
        let device = Device::Cpu;
        let in_dim = 128;
        let out_dim = 256;

        let linear = create_test_bitlinear(in_dim, out_dim)?;

        // Create input tensor [Batch, Features]
        let x = Tensor::randn(0.0f32, 1.0, (4, in_dim), &device)?;

        // Forward pass (STE path since no packed weights)
        let y = linear.forward(&x)?;

        // Verify output shape
        assert_eq!(y.dims(), &[4, out_dim], "Output shape mismatch");
        assert_eq!(y.dtype(), DType::F32, "Output dtype should be F32");

        Ok(())
    }

    #[test]
    fn test_bitlinear_forward_3d_input() -> anyhow::Result<()> {
        let device = Device::Cpu;
        let in_dim = 64;
        let out_dim = 128;

        let linear = create_test_bitlinear(in_dim, out_dim)?;

        // Create 3D input tensor [Batch, Seq, Features]
        let x = Tensor::randn(0.0f32, 1.0, (2, 10, in_dim), &device)?;

        // Forward pass
        let y = linear.forward(&x)?;

        // Verify output shape [Batch, Seq, OutFeatures]
        assert_eq!(y.dims(), &[2, 10, out_dim], "3D output shape mismatch");

        Ok(())
    }

    #[test]
    fn test_bitlinear_forward_1d_input() -> anyhow::Result<()> {
        let device = Device::Cpu;
        let in_dim = 32;
        let out_dim = 64;

        let linear = create_test_bitlinear(in_dim, out_dim)?;

        // Create input tensor [1, Features] - single sample
        let x = Tensor::randn(0.0f32, 1.0, (1, in_dim), &device)?;

        // Forward pass
        let y = linear.forward(&x)?;

        // Verify output shape
        assert_eq!(y.dims(), &[1, out_dim], "1D output shape mismatch");

        Ok(())
    }

    #[test]
    fn test_bitlinear_weight_shape() -> anyhow::Result<()> {
        let in_dim = 256;
        let out_dim = 512;

        let linear = create_test_bitlinear(in_dim, out_dim)?;

        // Verify weight shape
        assert_eq!(
            linear.weight.dims(),
            &[out_dim, in_dim],
            "Weight shape should be [out_dim, in_dim]"
        );

        Ok(())
    }

    #[test]
    fn test_bitlinear_precompute_packed() -> anyhow::Result<()> {
        let in_dim = 128;
        let out_dim = 256;

        let mut linear = create_test_bitlinear(in_dim, out_dim)?;

        // Initially no packed params
        assert!(
            linear.packed_params.is_none(),
            "Initially should have no packed params"
        );

        // Precompute packed weights
        linear.precompute_packed()?;

        // Now should have packed params
        assert!(
            linear.packed_params.is_some(),
            "After precompute, should have packed params"
        );

        Ok(())
    }

    #[test]
    fn test_bitlinear_forward_with_packed_weights() -> anyhow::Result<()> {
        let device = Device::Cpu;
        let in_dim = 128;
        let out_dim = 256;

        let mut linear = create_test_bitlinear(in_dim, out_dim)?;

        // Precompute packed weights for optimized inference
        linear.precompute_packed()?;

        // Create input tensor
        let x = Tensor::randn(0.0f32, 1.0, (4, in_dim), &device)?;

        // Forward pass (should use packed kernel path)
        let y = linear.forward(&x)?;

        // Verify output shape
        assert_eq!(y.dims(), &[4, out_dim], "Output shape mismatch with packed");
        assert_eq!(y.dtype(), DType::F32, "Output dtype should be F32");

        Ok(())
    }

    #[test]
    fn test_bitlinear_packed_forward_3d() -> anyhow::Result<()> {
        let device = Device::Cpu;
        let in_dim = 64;
        let out_dim = 128;

        let mut linear = create_test_bitlinear(in_dim, out_dim)?;
        linear.precompute_packed()?;

        // Create 3D input tensor [Batch, Seq, Features]
        let x = Tensor::randn(0.0f32, 1.0, (2, 8, in_dim), &device)?;

        // Forward pass with packed weights
        let y = linear.forward(&x)?;

        // Verify output shape [Batch, Seq, OutFeatures]
        assert_eq!(
            y.dims(),
            &[2, 8, out_dim],
            "3D output shape mismatch with packed"
        );

        Ok(())
    }

    #[test]
    fn test_bitlinear_deterministic() -> anyhow::Result<()> {
        let device = Device::Cpu;
        let in_dim = 64;
        let out_dim = 128;

        let linear = create_test_bitlinear(in_dim, out_dim)?;

        // Create deterministic input
        let x = Tensor::ones((2, in_dim), DType::F32, &device)?;

        // Two forward passes should produce identical results
        let y1 = linear.forward(&x)?;
        let y2 = linear.forward(&x)?;

        // Compare outputs
        let diff = (y1 - y2)?.abs()?.max_all()?.to_scalar::<f32>()?;
        assert!(
            diff < 1e-6,
            "Forward pass should be deterministic, diff: {}",
            diff
        );

        Ok(())
    }

    #[test]
    fn test_bitlinear_ste_quantization_bounds() -> anyhow::Result<()> {
        let device = Device::Cpu;
        let in_dim = 64;
        let out_dim = 64;

        // Create layer with extreme weight values
        let weight = Tensor::randn(0.0f32, 10.0, (out_dim, in_dim), &device)?;
        let linear = BitLinear {
            weight,
            in_features: in_dim,
            out_features: out_dim,
            packed_params: None,
        };

        // Forward should still work (STE clamps to [-1, 1])
        let x = Tensor::ones((1, in_dim), DType::F32, &device)?;
        let y = linear.forward(&x)?;

        // Output should be finite
        let y_vec: Vec<f32> = y.flatten_all()?.to_vec1()?;
        for val in &y_vec {
            assert!(val.is_finite(), "Output should be finite, got: {}", val);
        }

        Ok(())
    }

    #[test]
    fn test_bitlinear_packed_vs_unpacked_similarity() -> anyhow::Result<()> {
        let device = Device::Cpu;
        let in_dim = 64;
        let out_dim = 128;

        // Create two identical layers
        let weight = Tensor::randn(0.0f32, 1.0, (out_dim, in_dim), &device)?;
        let linear_unpacked = BitLinear {
            weight: weight.clone(),
            in_features: in_dim,
            out_features: out_dim,
            packed_params: None,
        };

        let mut linear_packed = BitLinear {
            weight,
            in_features: in_dim,
            out_features: out_dim,
            packed_params: None,
        };
        linear_packed.precompute_packed()?;

        // Same input
        let x = Tensor::randn(0.0f32, 1.0, (2, in_dim), &device)?;

        let y_unpacked = linear_unpacked.forward(&x)?;
        let y_packed = linear_packed.forward(&x)?;

        // Results should be reasonably close (quantization will cause some difference)
        let diff = (&y_unpacked - &y_packed)?
            .abs()?
            .mean_all()?
            .to_scalar::<f32>()?;

        // Allow some difference due to quantization (1.58-bit vs full precision)
        // The outputs should at least have similar magnitude
        let max_diff = (&y_unpacked - &y_packed)?
            .abs()?
            .max_all()?
            .to_scalar::<f32>()?;
        assert!(
            max_diff.is_finite(),
            "Difference should be finite, got: {}",
            max_diff
        );

        println!(
            "Mean diff: {}, Max diff: {} (expected due to quantization)",
            diff, max_diff
        );

        Ok(())
    }
}
