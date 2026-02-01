//! Perplexity calculation for language model evaluation.
//!
//! Perplexity measures how well a language model predicts a sample.
//! Lower perplexity = better model. PPL = exp(average cross-entropy loss).

use candle_core::{Result, Tensor, D};

/// Result of perplexity evaluation.
#[derive(Debug, Clone)]
pub struct PerplexityResult {
    /// Perplexity value (exp of average loss).
    pub perplexity: f64,
    /// Average cross-entropy loss.
    pub avg_loss: f64,
    /// Total number of tokens evaluated.
    pub num_tokens: usize,
    /// Total loss (sum of all token losses).
    pub total_loss: f64,
}

impl std::fmt::Display for PerplexityResult {
    fn fmt(&self, f: &mut std::fmt::Formatter<'_>) -> std::fmt::Result {
        write!(
            f,
            "PPL: {:.2} | Loss: {:.4} | Tokens: {}",
            self.perplexity, self.avg_loss, self.num_tokens
        )
    }
}

/// Compute perplexity from logits and target token IDs.
///
/// # Arguments
/// * `logits` - Model output logits, shape: [batch, seq_len, vocab_size]
/// * `targets` - Target token IDs, shape: [batch, seq_len]
/// * `ignore_index` - Token ID to ignore in loss calculation (e.g., padding)
///
/// # Returns
/// * `PerplexityResult` containing perplexity and related metrics
///
/// # Example
/// ```ignore
/// let logits = model.forward(&input_ids)?;
/// let result = compute_perplexity(&logits, &target_ids, Some(-100))?;
/// println!("Perplexity: {:.2}", result.perplexity);
/// ```
pub fn compute_perplexity(
    logits: &Tensor,
    targets: &Tensor,
    ignore_index: Option<i64>,
) -> Result<PerplexityResult> {
    let ignore_idx = ignore_index.unwrap_or(-100);
    
    // Get dimensions
    let (batch_size, seq_len, vocab_size) = logits.dims3()?;
    
    // Reshape logits to [batch * seq_len, vocab_size]
    let logits_flat = logits.reshape((batch_size * seq_len, vocab_size))?;
    
    // Reshape targets to [batch * seq_len]
    let targets_flat = targets.reshape(batch_size * seq_len)?;
    
    // Compute log softmax
    let log_probs = candle_nn::ops::log_softmax(&logits_flat, D::Minus1)?;
    
    // Get target log probabilities
    let targets_i64 = targets_flat.to_vec1::<i64>()?;
    
    let mut total_loss = 0.0f64;
    let mut num_tokens = 0usize;
    
    // Manual cross-entropy calculation to handle ignore_index
    for (i, &target) in targets_i64.iter().enumerate() {
        if target == ignore_idx || target < 0 || target >= vocab_size as i64 {
            continue;
        }
        
        // Get log probability for the target token
        let log_prob = log_probs
            .get(i)?
            .get(target as usize)?
            .to_scalar::<f32>()?;
        
        total_loss += -log_prob as f64;
        num_tokens += 1;
    }
    
    if num_tokens == 0 {
        return Ok(PerplexityResult {
            perplexity: f64::INFINITY,
            avg_loss: f64::INFINITY,
            num_tokens: 0,
            total_loss: 0.0,
        });
    }
    
    let avg_loss = total_loss / num_tokens as f64;
    let perplexity = avg_loss.exp();
    
    Ok(PerplexityResult {
        perplexity,
        avg_loss,
        num_tokens,
        total_loss,
    })
}

/// Compute perplexity over a dataset in chunks.
///
/// This is memory-efficient for large datasets, processing one chunk at a time.
///
/// # Arguments
/// * `model` - Any model implementing the `forward` function
/// * `token_ids` - Full dataset token IDs
/// * `chunk_size` - Number of tokens per chunk (e.g., 512)
/// * `forward_fn` - Function that takes token IDs and returns logits
///
/// # Returns
/// * `PerplexityResult` for the entire dataset
pub fn compute_perplexity_chunked<F>(
    token_ids: &[u32],
    chunk_size: usize,
    forward_fn: F,
) -> Result<PerplexityResult>
where
    F: Fn(&[u32]) -> Result<Tensor>,
{
    let mut total_loss = 0.0f64;
    let mut total_tokens = 0usize;
    
    // Process in overlapping chunks
    let stride = chunk_size / 2; // 50% overlap for context
    let mut pos = 0;
    
    while pos + chunk_size <= token_ids.len() {
        let chunk = &token_ids[pos..pos + chunk_size];
        
        // Input: all but last token
        let input = &chunk[..chunk_size - 1];
        // Target: all but first token (shifted by 1)
        let targets: Vec<i64> = chunk[1..].iter().map(|&x| x as i64).collect();
        
        // Get logits from model
        let logits = forward_fn(input)?;
        
        // Compute loss for this chunk
        let targets_tensor = Tensor::from_vec(
            targets.clone(),
            (1, targets.len()),
            logits.device(),
        )?;
        
        let result = compute_perplexity(&logits, &targets_tensor, Some(-100))?;
        
        total_loss += result.total_loss;
        total_tokens += result.num_tokens;
        
        pos += stride;
    }
    
    if total_tokens == 0 {
        return Ok(PerplexityResult {
            perplexity: f64::INFINITY,
            avg_loss: f64::INFINITY,
            num_tokens: 0,
            total_loss: 0.0,
        });
    }
    
    let avg_loss = total_loss / total_tokens as f64;
    let perplexity = avg_loss.exp();
    
    Ok(PerplexityResult {
        perplexity,
        avg_loss,
        num_tokens: total_tokens,
        total_loss,
    })
}

#[cfg(test)]
mod tests {
    use super::*;
    use candle_core::Device;

    #[test]
    fn test_perplexity_calculation() -> Result<()> {
        let device = Device::Cpu;
        
        // Create dummy logits: [batch=1, seq=3, vocab=5]
        // Perfect prediction: high probability for correct token
        let logits_data: Vec<f32> = vec![
            // Token 0: predict token 1
            -10.0, 10.0, -10.0, -10.0, -10.0,
            // Token 1: predict token 2
            -10.0, -10.0, 10.0, -10.0, -10.0,
            // Token 2: predict token 3
            -10.0, -10.0, -10.0, 10.0, -10.0,
        ];
        let logits = Tensor::from_vec(logits_data, (1, 3, 5), &device)?;
        
        // Targets: [1, 2, 3] (matching the high-probability predictions)
        let targets = Tensor::from_vec(vec![1i64, 2, 3], (1, 3), &device)?;
        
        let result = compute_perplexity(&logits, &targets, None)?;
        
        // With near-perfect predictions, perplexity should be close to 1
        assert!(result.perplexity < 2.0, "PPL should be low: {}", result.perplexity);
        assert_eq!(result.num_tokens, 3);
        
        Ok(())
    }

    #[test]
    fn test_perplexity_with_ignore_index() -> Result<()> {
        let device = Device::Cpu;
        
        let logits = Tensor::from_vec(
            vec![
                -10.0f32, 10.0, -10.0, -10.0, -10.0,
                -10.0, -10.0, 10.0, -10.0, -10.0,
                -10.0, -10.0, -10.0, 10.0, -10.0,
            ],
            (1, 3, 5),
            &device,
        )?;
        
        // Targets with ignore index (-100)
        let targets = Tensor::from_vec(vec![1i64, -100, 3], (1, 3), &device)?;
        
        let result = compute_perplexity(&logits, &targets, Some(-100))?;
        
        // Should only count 2 tokens (ignoring the -100)
        assert_eq!(result.num_tokens, 2);
        
        Ok(())
    }

    #[test]
    fn test_perplexity_uniform_distribution() -> Result<()> {
        let device = Device::Cpu;
        let vocab_size = 100;
        
        // Uniform distribution: all logits equal
        let logits_data: Vec<f32> = vec![0.0; vocab_size];
        let logits = Tensor::from_vec(logits_data, (1, 1, vocab_size), &device)?;
        
        let targets = Tensor::from_vec(vec![50i64], (1, 1), &device)?;
        
        let result = compute_perplexity(&logits, &targets, None)?;
        
        // With uniform distribution, PPL should be close to vocab_size
        assert!(
            (result.perplexity - vocab_size as f64).abs() < 1.0,
            "PPL should be ~{}: {}",
            vocab_size,
            result.perplexity
        );
        
        Ok(())
    }
}
