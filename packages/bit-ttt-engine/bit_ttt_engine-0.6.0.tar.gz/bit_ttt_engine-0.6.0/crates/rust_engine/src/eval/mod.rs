//! Evaluation utilities for language models.
//!
//! This module provides functions for evaluating language model quality,
//! including perplexity calculation and other metrics.

mod perplexity;

pub use perplexity::{compute_perplexity, PerplexityResult};
