/**
 * Fused CUDA Kernels for LLM Inference
 * 
 * Contains optimized implementations of:
 * - RMSNorm
 * - Softmax
 * - RoPE (Rotary Position Embedding)
 */

#include <cuda_runtime.h>
#include <cuda_fp16.h>
#include <stdint.h>
#include <float.h>

// Warp size
#define WARP_SIZE 32

// Block sizes
#define RMS_BLOCK_SIZE 256
#define SOFTMAX_BLOCK_SIZE 256
#define ROPE_BLOCK_SIZE 256

// ============================================================================
// RMSNorm Kernel
// ============================================================================

/**
 * RMSNorm: y = x * weight / sqrt(mean(x^2) + eps)
 * 
 * @param x       Input tensor [batch, seq_len, hidden_dim]
 * @param weight  Weight tensor [hidden_dim]
 * @param y       Output tensor [batch, seq_len, hidden_dim]
 * @param hidden_dim Hidden dimension
 * @param eps     Epsilon for numerical stability
 * @param n_elements Total number of rows (batch * seq_len)
 */
extern "C" __global__ void rms_norm_kernel_f32(
    const float* __restrict__ x,
    const float* __restrict__ weight,
    float* __restrict__ y,
    int hidden_dim,
    float eps,
    int n_elements
) {
    int row = blockIdx.x;
    if (row >= n_elements) return;
    
    const float* x_row = x + row * hidden_dim;
    float* y_row = y + row * hidden_dim;
    
    // Compute sum of squares using parallel reduction
    __shared__ float shared_sum[RMS_BLOCK_SIZE];
    
    float thread_sum = 0.0f;
    for (int i = threadIdx.x; i < hidden_dim; i += blockDim.x) {
        float val = x_row[i];
        thread_sum += val * val;
    }
    
    shared_sum[threadIdx.x] = thread_sum;
    __syncthreads();
    
    // Reduce within block
    for (int stride = blockDim.x / 2; stride > 0; stride >>= 1) {
        if (threadIdx.x < stride) {
            shared_sum[threadIdx.x] += shared_sum[threadIdx.x + stride];
        }
        __syncthreads();
    }
    
    // Compute RMS
    float rms = rsqrtf(shared_sum[0] / (float)hidden_dim + eps);
    
    // Apply normalization
    for (int i = threadIdx.x; i < hidden_dim; i += blockDim.x) {
        y_row[i] = x_row[i] * rms * weight[i];
    }
}

// ============================================================================
// Softmax Kernel
// ============================================================================

/**
 * Softmax on last dimension: y = exp(x - max(x)) / sum(exp(x - max(x)))
 * 
 * @param x       Input tensor [batch, seq_len, vocab_size] or [batch, heads, seq, seq]
 * @param y       Output tensor (same shape)
 * @param last_dim Size of last dimension
 * @param n_rows  Number of rows (product of all dims except last)
 */
extern "C" __global__ void softmax_kernel_f32(
    const float* __restrict__ x,
    float* __restrict__ y,
    int last_dim,
    int n_rows
) {
    int row = blockIdx.x;
    if (row >= n_rows) return;
    
    const float* x_row = x + row * last_dim;
    float* y_row = y + row * last_dim;
    
    __shared__ float shared_max[SOFTMAX_BLOCK_SIZE];
    __shared__ float shared_sum[SOFTMAX_BLOCK_SIZE];
    
    // Find max
    float thread_max = -FLT_MAX;
    for (int i = threadIdx.x; i < last_dim; i += blockDim.x) {
        thread_max = fmaxf(thread_max, x_row[i]);
    }
    shared_max[threadIdx.x] = thread_max;
    __syncthreads();
    
    // Reduce max
    for (int stride = blockDim.x / 2; stride > 0; stride >>= 1) {
        if (threadIdx.x < stride) {
            shared_max[threadIdx.x] = fmaxf(shared_max[threadIdx.x], shared_max[threadIdx.x + stride]);
        }
        __syncthreads();
    }
    float max_val = shared_max[0];
    
    // Compute exp and sum
    float thread_sum = 0.0f;
    for (int i = threadIdx.x; i < last_dim; i += blockDim.x) {
        float exp_val = expf(x_row[i] - max_val);
        y_row[i] = exp_val;  // Store intermediate
        thread_sum += exp_val;
    }
    shared_sum[threadIdx.x] = thread_sum;
    __syncthreads();
    
    // Reduce sum
    for (int stride = blockDim.x / 2; stride > 0; stride >>= 1) {
        if (threadIdx.x < stride) {
            shared_sum[threadIdx.x] += shared_sum[threadIdx.x + stride];
        }
        __syncthreads();
    }
    float sum_val = shared_sum[0];
    
    // Normalize
    float inv_sum = 1.0f / sum_val;
    for (int i = threadIdx.x; i < last_dim; i += blockDim.x) {
        y_row[i] *= inv_sum;
    }
}

// ============================================================================
// RoPE Kernel
// ============================================================================

/**
 * Apply Rotary Position Embedding in-place
 * 
 * q[..., :half] = q[..., :half] * cos - q[..., half:] * sin
 * q[..., half:] = q[..., :half] * sin + q[..., half:] * cos
 * 
 * @param q       Query tensor [batch, heads, seq_len, head_dim]
 * @param k       Key tensor [batch, heads, seq_len, head_dim]
 * @param cos     Cosine cache [seq_len, head_dim]
 * @param sin     Sine cache [seq_len, head_dim]
 * @param batch   Batch size
 * @param n_heads Number of heads
 * @param seq_len Sequence length
 * @param head_dim Head dimension (must be even)
 * @param start_pos Starting position for cache lookup
 */
extern "C" __global__ void rope_kernel_f32(
    float* __restrict__ q,
    float* __restrict__ k,
    const float* __restrict__ cos,
    const float* __restrict__ sin,
    int batch,
    int n_heads,
    int seq_len,
    int head_dim,
    int start_pos
) {
    int idx = blockIdx.x * blockDim.x + threadIdx.x;
    int total = batch * n_heads * seq_len * (head_dim / 2);
    if (idx >= total) return;
    
    int half_dim = head_dim / 2;
    
    // Decode indices
    int h_idx = idx % half_dim;
    int remaining = idx / half_dim;
    int s = remaining % seq_len;
    remaining /= seq_len;
    int head = remaining % n_heads;
    int b = remaining / n_heads;
    
    // Position in cos/sin cache
    int pos = start_pos + s;
    float cos_val = cos[pos * head_dim + h_idx];
    float sin_val = sin[pos * head_dim + h_idx];
    
    // Compute offset in q/k tensors
    int offset_base = ((b * n_heads + head) * seq_len + s) * head_dim;
    int offset_lo = offset_base + h_idx;
    int offset_hi = offset_base + h_idx + half_dim;
    
    // Apply RoPE to Q
    float q_lo = q[offset_lo];
    float q_hi = q[offset_hi];
    q[offset_lo] = q_lo * cos_val - q_hi * sin_val;
    q[offset_hi] = q_lo * sin_val + q_hi * cos_val;
    
    // Apply RoPE to K
    float k_lo = k[offset_lo];
    float k_hi = k[offset_hi];
    k[offset_lo] = k_lo * cos_val - k_hi * sin_val;
    k[offset_hi] = k_lo * sin_val + k_hi * cos_val;
}

// ============================================================================
// SiLU (Swish) Kernel
// ============================================================================

/**
 * SiLU activation: y = x * sigmoid(x)
 */
extern "C" __global__ void silu_kernel_f32(
    const float* __restrict__ x,
    float* __restrict__ y,
    int n_elements
) {
    int idx = blockIdx.x * blockDim.x + threadIdx.x;
    if (idx >= n_elements) return;
    
    float val = x[idx];
    y[idx] = val / (1.0f + expf(-val));
}

// ============================================================================
// Fused Gate-Up with SiLU
// ============================================================================

/**
 * Fused: y = silu(gate) * up
 * 
 * @param gate   Gate projection output [batch, hidden]
 * @param up     Up projection output [batch, hidden]  
 * @param y      Output [batch, hidden]
 * @param n_elements Total elements
 */
extern "C" __global__ void fused_silu_mul_kernel_f32(
    const float* __restrict__ gate,
    const float* __restrict__ up,
    float* __restrict__ y,
    int n_elements
) {
    int idx = blockIdx.x * blockDim.x + threadIdx.x;
    if (idx >= n_elements) return;
    
    float g = gate[idx];
    float silu_g = g / (1.0f + expf(-g));
    y[idx] = silu_g * up[idx];
}
