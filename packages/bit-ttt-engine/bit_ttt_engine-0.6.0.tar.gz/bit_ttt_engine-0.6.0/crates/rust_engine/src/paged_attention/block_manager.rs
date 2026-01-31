//! Block Manager - Allocates and manages cache blocks
//!
//! Tracks which blocks are free/used and generates block tables for sequences.

use candle_core::{Device, Result, Tensor};
use std::collections::{HashMap, VecDeque};

/// Manages block allocation for paged attention
pub struct BlockManager {
    /// Total number of blocks available
    num_blocks: usize,
    /// Block size (tokens per block)
    block_size: usize,
    /// Queue of free block indices
    free_blocks: VecDeque<usize>,
    /// Mapping: sequence_id -> list of allocated block indices
    seq_to_blocks: HashMap<usize, Vec<usize>>,
    /// Mapping: sequence_id -> actual number of tokens (NOT blocks * block_size!)
    seq_to_num_tokens: HashMap<usize, usize>,
    /// Next sequence ID
    next_seq_id: usize,
}

impl BlockManager {
    /// Create a new block manager
    pub fn new(num_blocks: usize, block_size: usize) -> Self {
        // Initialize all blocks as free
        let free_blocks: VecDeque<usize> = (0..num_blocks).collect();

        Self {
            num_blocks,
            block_size,
            free_blocks,
            seq_to_blocks: HashMap::new(),
            seq_to_num_tokens: HashMap::new(),
            next_seq_id: 0,
        }
    }

    /// Allocate a new sequence and return its ID
    pub fn allocate_sequence(&mut self) -> usize {
        let seq_id = self.next_seq_id;
        self.next_seq_id += 1;
        self.seq_to_blocks.insert(seq_id, Vec::new());
        self.seq_to_num_tokens.insert(seq_id, 0);
        seq_id
    }

    /// Allocate blocks for a sequence to hold `num_tokens` tokens
    /// Returns the slot indices for each token
    pub fn allocate_slots(&mut self, seq_id: usize, num_tokens: usize) -> Result<Vec<i64>> {
        let blocks = self
            .seq_to_blocks
            .get_mut(&seq_id)
            .ok_or_else(|| candle_core::Error::Msg(format!("Sequence {} not found", seq_id)))?;

        // Use actual token count, not blocks.len() * block_size!
        let current_tokens = *self.seq_to_num_tokens.get(&seq_id).unwrap_or(&0);
        let total_tokens_needed = current_tokens + num_tokens;
        let blocks_needed = total_tokens_needed.div_ceil(self.block_size);
        let new_blocks_needed = blocks_needed.saturating_sub(blocks.len());

        // Allocate new blocks if needed
        for _ in 0..new_blocks_needed {
            let block_idx = self
                .free_blocks
                .pop_front()
                .ok_or_else(|| candle_core::Error::Msg("Out of cache blocks".to_string()))?;
            blocks.push(block_idx);
        }

        // Generate slot indices for the new tokens
        let mut slots = Vec::with_capacity(num_tokens);
        for i in 0..num_tokens {
            let token_pos = current_tokens + i;
            let block_idx_in_seq = token_pos / self.block_size;
            let offset_in_block = token_pos % self.block_size;
            let global_block_idx = blocks[block_idx_in_seq];
            let slot = (global_block_idx * self.block_size + offset_in_block) as i64;
            slots.push(slot);
        }

        // Update token count
        self.seq_to_num_tokens.insert(seq_id, total_tokens_needed);

        Ok(slots)
    }

    /// Get the block table for a sequence (for attention computation)
    pub fn get_block_table(&self, seq_id: usize) -> Option<Vec<u32>> {
        self.seq_to_blocks
            .get(&seq_id)
            .map(|blocks| blocks.iter().map(|&b| b as u32).collect())
    }

    /// Get block table as tensor
    pub fn get_block_table_tensor(
        &self,
        seq_id: usize,
        max_blocks: usize,
        device: &Device,
    ) -> Result<Tensor> {
        let blocks = self
            .seq_to_blocks
            .get(&seq_id)
            .ok_or_else(|| candle_core::Error::Msg(format!("Sequence {} not found", seq_id)))?;

        // Pad to max_blocks
        let mut padded: Vec<u32> = blocks.iter().map(|&b| b as u32).collect();
        padded.resize(max_blocks, 0);

        Tensor::from_vec(padded, (1, max_blocks), device)
    }

    /// Get slot mapping as tensor
    pub fn get_slot_mapping_tensor(&self, slots: &[i64], device: &Device) -> Result<Tensor> {
        Tensor::from_vec(slots.to_vec(), (slots.len(),), device)
    }

    /// Get context length for a sequence (actual number of tokens cached)
    pub fn get_context_len(&self, seq_id: usize) -> usize {
        *self.seq_to_num_tokens.get(&seq_id).unwrap_or(&0)
    }

    /// Free all blocks for a sequence
    pub fn free_sequence(&mut self, seq_id: usize) {
        if let Some(blocks) = self.seq_to_blocks.remove(&seq_id) {
            for block_idx in blocks {
                self.free_blocks.push_back(block_idx);
            }
        }
        self.seq_to_num_tokens.remove(&seq_id);
    }

    /// Get number of free blocks
    pub fn num_free_blocks(&self) -> usize {
        self.free_blocks.len()
    }

    /// Get number of used blocks
    pub fn num_used_blocks(&self) -> usize {
        self.num_blocks - self.free_blocks.len()
    }

    /// Reset all allocations
    pub fn reset(&mut self) {
        self.free_blocks = (0..self.num_blocks).collect();
        self.seq_to_blocks.clear();
        self.seq_to_num_tokens.clear();
        self.next_seq_id = 0;
    }
}

#[cfg(test)]
mod tests {
    use super::*;

    #[test]
    fn test_block_allocation() {
        let mut manager = BlockManager::new(10, 16);

        let seq_id = manager.allocate_sequence();
        assert_eq!(seq_id, 0);

        // Allocate 5 tokens (needs 1 block)
        let slots = manager.allocate_slots(seq_id, 5).unwrap();
        assert_eq!(slots.len(), 5);
        assert_eq!(slots, vec![0, 1, 2, 3, 4]);

        // Allocate 20 more tokens (needs 2 more blocks)
        let slots = manager.allocate_slots(seq_id, 20).unwrap();
        assert_eq!(slots.len(), 20);

        assert_eq!(manager.num_used_blocks(), 2); // ceil(25/16) = 2
    }
}
