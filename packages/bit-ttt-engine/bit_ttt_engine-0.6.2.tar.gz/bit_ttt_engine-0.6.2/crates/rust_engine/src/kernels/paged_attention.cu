/**
 * Paged Attention CUDA Kernels
 * 
 * Based on vLLM's PagedAttention implementation.
 * Reference: https://github.com/vllm-project/vllm
 */

#include <cuda_runtime.h>
#include <stdint.h>
#include <float.h>

#define WARP_SIZE 32
#define MAX_THREADS_PER_BLOCK 1024

// ============================================================================
// Reshape and Cache Kernel
// ============================================================================

/**
 * Write K/V tensors into paged cache blocks.
 * 
 * @param key           [num_tokens, num_heads, head_dim]
 * @param value         [num_tokens, num_heads, head_dim]
 * @param key_cache     [num_blocks, num_heads, head_dim, block_size]
 * @param value_cache   [num_blocks, num_heads, head_dim, block_size]
 * @param slot_mapping  [num_tokens] - maps token to cache slot
 * @param num_heads     Number of attention heads
 * @param head_dim      Dimension per head
 * @param block_size    Tokens per block
 */
extern "C" __global__ void reshape_and_cache_kernel_f32(
    const float* __restrict__ key,
    const float* __restrict__ value,
    float* __restrict__ key_cache,
    float* __restrict__ value_cache,
    const int64_t* __restrict__ slot_mapping,
    int num_tokens,
    int num_heads,
    int head_dim,
    int block_size
) {
    const int token_idx = blockIdx.x;
    if (token_idx >= num_tokens) return;
    
    const int64_t slot_idx = slot_mapping[token_idx];
    if (slot_idx < 0) return;  // Skip padding tokens
    
    const int block_idx = slot_idx / block_size;
    const int block_offset = slot_idx % block_size;
    
    // Copy key and value for this token
    const int n = num_heads * head_dim;
    for (int i = threadIdx.x; i < n; i += blockDim.x) {
        const int src_idx = token_idx * n + i;
        
        const int head_idx = i / head_dim;
        const int head_offset = i % head_dim;
        
        // Cache layout: [num_blocks, num_heads, head_dim, block_size]
        const int tgt_idx = block_idx * num_heads * head_dim * block_size
                         + head_idx * head_dim * block_size
                         + head_offset * block_size
                         + block_offset;
        
        key_cache[tgt_idx] = key[src_idx];
        value_cache[tgt_idx] = value[src_idx];
    }
}

// ============================================================================
// Paged Attention V1 Kernel (Simple Version)
// ============================================================================

/**
 * Compute attention with paged KV cache.
 * 
 * For each query token, compute attention over all cached K/V tokens.
 * 
 * @param out           [num_seqs, num_heads, head_dim]
 * @param query         [num_seqs, num_heads, head_dim]
 * @param key_cache     [num_blocks, num_heads, head_dim, block_size]
 * @param value_cache   [num_blocks, num_heads, head_dim, block_size]
 * @param block_tables  [num_seqs, max_num_blocks_per_seq]
 * @param context_lens  [num_seqs]
 * @param scale         Softmax scale (1/sqrt(head_dim))
 * @param num_seqs      Number of sequences in batch
 * @param num_heads     Number of query heads
 * @param head_dim      Dimension per head
 * @param block_size    Tokens per block
 * @param max_num_blocks_per_seq  Max blocks per sequence
 */
extern "C" __global__ void paged_attention_v1_kernel_f32(
    float* __restrict__ out,
    const float* __restrict__ query,
    const float* __restrict__ key_cache,
    const float* __restrict__ value_cache,
    const int* __restrict__ block_tables,
    const int* __restrict__ context_lens,
    float scale,
    int num_seqs,
    int num_heads,
    int num_kv_heads,   // NEW: for GQA support
    int head_dim,
    int block_size,
    int max_num_blocks_per_seq
) {
    const int seq_idx = blockIdx.x;
    const int head_idx = blockIdx.y;
    
    if (seq_idx >= num_seqs || head_idx >= num_heads) return;
    
    const int context_len = context_lens[seq_idx];
    if (context_len == 0) return;
    
    // GQA: map query head to KV head
    const int kv_head_idx = head_idx * num_kv_heads / num_heads;
    
    // Shared memory layout: [query (head_dim)] [qk_scores (context_len)]
    extern __shared__ float shared_mem[];
    float* q_shared = shared_mem;                    // Query in shared memory
    float* qk_scores = shared_mem + head_dim;       // Scores after query
    
    // Load query into shared memory (all threads cooperate)
    const int q_offset = seq_idx * num_heads * head_dim + head_idx * head_dim;
    for (int i = threadIdx.x; i < head_dim; i += blockDim.x) {
        q_shared[i] = query[q_offset + i];
    }
    __syncthreads();
    
    // Compute Q @ K^T
    float max_score = -FLT_MAX;
    for (int token_idx = threadIdx.x; token_idx < context_len; token_idx += blockDim.x) {
        const int block_idx_in_seq = token_idx / block_size;
        const int block_offset = token_idx % block_size;
        const int physical_block_idx = block_tables[seq_idx * max_num_blocks_per_seq + block_idx_in_seq];
        
        float score = 0.0f;
        for (int d = 0; d < head_dim; d++) {
            // Key cache: [num_blocks, num_kv_heads, head_dim, block_size]
            const int k_idx = physical_block_idx * num_kv_heads * head_dim * block_size
                            + kv_head_idx * head_dim * block_size
                            + d * block_size
                            + block_offset;
            score += q_shared[d] * key_cache[k_idx];  // Use shared memory
        }
        score *= scale;
        qk_scores[token_idx] = score;
        max_score = fmaxf(max_score, score);
    }
    __syncthreads();
    
    // Warp reduction for max (blockDim.x = 32)
    for (int offset = 16; offset > 0; offset >>= 1) {
        max_score = fmaxf(max_score, __shfl_down_sync(0xffffffff, max_score, offset));
    }
    max_score = __shfl_sync(0xffffffff, max_score, 0);
    
    // Softmax
    float sum_exp = 0.0f;
    for (int token_idx = threadIdx.x; token_idx < context_len; token_idx += blockDim.x) {
        float exp_score = expf(qk_scores[token_idx] - max_score);
        qk_scores[token_idx] = exp_score;
        sum_exp += exp_score;
    }
    __syncthreads();
    
    // Warp reduction for sum
    for (int offset = 16; offset > 0; offset >>= 1) {
        sum_exp += __shfl_down_sync(0xffffffff, sum_exp, offset);
    }
    sum_exp = __shfl_sync(0xffffffff, sum_exp, 0);
    
    // Normalize
    for (int token_idx = threadIdx.x; token_idx < context_len; token_idx += blockDim.x) {
        qk_scores[token_idx] /= sum_exp;
    }
    __syncthreads();
    
    // Compute Attn @ V
    const int out_offset = seq_idx * num_heads * head_dim + head_idx * head_dim;
    for (int d = threadIdx.x; d < head_dim; d += blockDim.x) {
        float acc = 0.0f;
        for (int token_idx = 0; token_idx < context_len; token_idx++) {
            const int block_idx_in_seq = token_idx / block_size;
            const int block_offset = token_idx % block_size;
            const int physical_block_idx = block_tables[seq_idx * max_num_blocks_per_seq + block_idx_in_seq];
            
            // Value cache: [num_blocks, num_kv_heads, head_dim, block_size]
            const int v_idx = physical_block_idx * num_kv_heads * head_dim * block_size
                            + kv_head_idx * head_dim * block_size
                            + d * block_size
                            + block_offset;
            acc += qk_scores[token_idx] * value_cache[v_idx];
        }
        out[out_offset + d] = acc;
    }
}

// ============================================================================
// Simple attention for prefill (no paged cache)
// ============================================================================

/**
 * Standard attention for prefill phase.
 * Q @ K^T -> softmax -> @ V
 * 
 * @param out       [batch, seq_len, num_heads, head_dim]
 * @param query     [batch, seq_len, num_heads, head_dim]
 * @param key       [batch, seq_len, num_heads, head_dim]
 * @param value     [batch, seq_len, num_heads, head_dim]
 * @param scale     1/sqrt(head_dim)
 * @param batch_size
 * @param seq_len
 * @param num_heads
 * @param head_dim
 */
extern "C" __global__ void attention_kernel_f32(
    float* __restrict__ out,
    const float* __restrict__ query,
    const float* __restrict__ key,
    const float* __restrict__ value,
    float scale,
    int batch_size,
    int seq_len,
    int num_heads,
    int head_dim
) {
    const int batch_idx = blockIdx.z;
    const int head_idx = blockIdx.y;
    const int q_idx = blockIdx.x;  // Query token index
    
    if (batch_idx >= batch_size || head_idx >= num_heads || q_idx >= seq_len) return;
    
    extern __shared__ float shared[];
    float* scores = shared;
    
    // Base offsets
    const int batch_head_offset = batch_idx * seq_len * num_heads * head_dim 
                                + head_idx * head_dim;
    const int q_offset = batch_head_offset + q_idx * num_heads * head_dim;
    
    // Compute Q @ K^T for this query position
    float max_score = -FLT_MAX;
    for (int k_idx = threadIdx.x; k_idx <= q_idx; k_idx += blockDim.x) {  // Causal mask
        const int k_offset = batch_head_offset + k_idx * num_heads * head_dim;
        
        float score = 0.0f;
        for (int d = 0; d < head_dim; d++) {
            score += query[q_offset + d] * key[k_offset + d];
        }
        score *= scale;
        scores[k_idx] = score;
        max_score = fmaxf(max_score, score);
    }
    // Set masked positions to -inf
    for (int k_idx = q_idx + 1 + threadIdx.x; k_idx < seq_len; k_idx += blockDim.x) {
        scores[k_idx] = -FLT_MAX;
    }
    __syncthreads();
    
    // Softmax
    float sum_exp = 0.0f;
    for (int k_idx = threadIdx.x; k_idx <= q_idx; k_idx += blockDim.x) {
        float exp_score = expf(scores[k_idx] - max_score);
        scores[k_idx] = exp_score;
        sum_exp += exp_score;
    }
    __syncthreads();
    
    // Reduce sum
    for (int stride = blockDim.x / 2; stride > 0; stride >>= 1) {
        if (threadIdx.x < stride && threadIdx.x + stride < seq_len) {
            sum_exp += scores[threadIdx.x + stride];
        }
        __syncthreads();
    }
    
    // Normalize
    for (int k_idx = threadIdx.x; k_idx <= q_idx; k_idx += blockDim.x) {
        scores[k_idx] /= sum_exp;
    }
    __syncthreads();
    
    // Compute weighted sum
    const int out_offset = q_offset;
    for (int d = threadIdx.x; d < head_dim; d += blockDim.x) {
        float acc = 0.0f;
        for (int k_idx = 0; k_idx <= q_idx; k_idx++) {
            const int v_offset = batch_head_offset + k_idx * num_heads * head_dim;
            acc += scores[k_idx] * value[v_offset + d];
        }
        out[out_offset + d] = acc;
    }
}
