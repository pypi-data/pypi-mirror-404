/**
 * 4-bit Quantized Matrix Multiplication CUDA Kernel
 * 
 * Performs fused dequantization and matrix multiplication for 4-bit quantized weights.
 * 
 * Data Layout:
 * - W_packed: [out_dim, in_dim/2] (U8) - 2 weights per byte
 *   - Lower 4 bits: first weight (signed, -8 to +7)
 *   - Upper 4 bits: second weight (signed, -8 to +7)
 * - Scales: [out_dim, n_groups] (F16/F32) - per-group scales
 * 
 * Quantization Formula:
 *   W_dequant[o,k] = W_quant[o,k] * scale[o, k/group_size]
 * 
 * Computation:
 *   Y[b,o] = sum_k( X[b,k] * W_dequant[o,k] )
 */

#include <cuda_runtime.h>
#include <cuda_fp16.h>
#include <stdint.h>

#define BLOCK_SIZE_X 16
#define BLOCK_SIZE_Y 16
#define TILE_SIZE 64

// Unpack 4-bit value from byte with -8 offset (Python compatible)
// Python packs as: (quantized + 8) -> 0~15 (unsigned)
// So we unpack as: value - 8 -> -8~7 (signed)
__device__ __forceinline__ float unpack_4bit_low(uint8_t packed) {
    // Lower 4 bits, apply -8 offset
    int val = (int)(packed & 0x0F) - 8;
    return (float)val;
}

__device__ __forceinline__ float unpack_4bit_high(uint8_t packed) {
    // Upper 4 bits, apply -8 offset
    int val = (int)((packed >> 4) & 0x0F) - 8;
    return (float)val;
}

/**
 * 4-bit GEMM Kernel with group-wise scaling
 * 
 * @param X           Input tensor [batch, in_dim] (F32)
 * @param W_packed    Packed weights [out_dim, in_dim/2] (U8)
 * @param Scales      Per-group scales [out_dim, n_groups] (F32)
 * @param Y           Output tensor [batch, out_dim] (F32)
 * @param batch_size  Batch dimension
 * @param in_dim      Input dimension (must be even)
 * @param out_dim     Output dimension
 * @param group_size  Elements per group for scaling
 */
extern "C" __global__ void gemm_4bit_kernel_f32(
    const float* __restrict__ X,           // [batch, in_dim]
    const uint8_t* __restrict__ W_packed,  // [out_dim, in_dim/2]
    const float* __restrict__ Scales,      // [out_dim, n_groups]
    float* __restrict__ Y,                 // [batch, out_dim]
    int batch_size,
    int in_dim,
    int out_dim,
    int group_size
) {
    // Thread mapping: each thread computes one output element
    int o = blockIdx.x * blockDim.x + threadIdx.x;  // Output index
    int b = blockIdx.y;                              // Batch index

    if (o >= out_dim || b >= batch_size) return;

    const int packed_per_row = in_dim / 2;  // Bytes per output row
    const int n_groups = (in_dim + group_size - 1) / group_size;
    
    // Pointer to weight row and input row
    const uint8_t* w_row = W_packed + o * packed_per_row;
    const float* x_row = X + b * in_dim;
    const float* scale_row = Scales + o * n_groups;

    float acc = 0.0f;
    
    // Process pairs of weights (2 per byte)
    for (int k_pair = 0; k_pair < packed_per_row; k_pair++) {
        uint8_t packed = w_row[k_pair];
        
        int k0 = k_pair * 2;
        int k1 = k_pair * 2 + 1;
        
        // Get scales for each position
        int g0 = k0 / group_size;
        int g1 = k1 / group_size;
        float s0 = scale_row[g0];
        float s1 = scale_row[g1];
        
        // Unpack and dequantize
        float w0 = unpack_4bit_low(packed) * s0;
        float w1 = unpack_4bit_high(packed) * s1;
        
        // Accumulate
        acc += x_row[k0] * w0;
        if (k1 < in_dim) {
            acc += x_row[k1] * w1;
        }
    }
    
    Y[b * out_dim + o] = acc;
}

/**
 * Optimized 4-bit GEMM with shared memory tiling
 */
extern "C" __global__ void gemm_4bit_tiled_kernel_f32(
    const float* __restrict__ X,           // [batch, in_dim]
    const uint8_t* __restrict__ W_packed,  // [out_dim, in_dim/2]
    const float* __restrict__ Scales,      // [out_dim, n_groups]
    float* __restrict__ Y,                 // [batch, out_dim]
    int batch_size,
    int in_dim,
    int out_dim,
    int group_size
) {
    __shared__ float x_tile[TILE_SIZE];
    __shared__ float w_tile[BLOCK_SIZE_X][TILE_SIZE];
    
    int o = blockIdx.x * BLOCK_SIZE_X + threadIdx.x;
    int b = blockIdx.y;
    
    if (b >= batch_size) return;
    
    const int packed_per_row = in_dim / 2;
    const int n_groups = (in_dim + group_size - 1) / group_size;
    
    float acc = 0.0f;
    
    // Process tiles
    for (int tile_start = 0; tile_start < in_dim; tile_start += TILE_SIZE) {
        // Load input tile to shared memory
        int local_k = threadIdx.x;
        while (local_k < TILE_SIZE && tile_start + local_k < in_dim) {
            x_tile[local_k] = X[b * in_dim + tile_start + local_k];
            local_k += BLOCK_SIZE_X;
        }
        
        // Load and dequantize weights to shared memory
        if (o < out_dim) {
            const uint8_t* w_row = W_packed + o * packed_per_row;
            const float* scale_row = Scales + o * n_groups;
            
            for (int k = 0; k < TILE_SIZE && tile_start + k < in_dim; k += 2) {
                int k_pair = (tile_start + k) / 2;
                if (k_pair < packed_per_row) {
                    uint8_t packed = w_row[k_pair];
                    int g = (tile_start + k) / group_size;
                    float scale = scale_row[g];
                    
                    w_tile[threadIdx.x][k] = unpack_4bit_low(packed) * scale;
                    if (k + 1 < TILE_SIZE && tile_start + k + 1 < in_dim) {
                        w_tile[threadIdx.x][k + 1] = unpack_4bit_high(packed) * scale;
                    }
                }
            }
        }
        
        __syncthreads();
        
        // Compute partial dot product
        if (o < out_dim) {
            for (int k = 0; k < TILE_SIZE && tile_start + k < in_dim; k++) {
                acc += x_tile[k] * w_tile[threadIdx.x][k];
            }
        }
        
        __syncthreads();
    }
    
    if (o < out_dim) {
        Y[b * out_dim + o] = acc;
    }
}

// ============================================================================
// Multi-Base Ternary (1.58-bit) Quantization CUDA Kernels
// ============================================================================

/**
 * Unpack 4 ternary values from a single byte (2-bit encoding)
 * 
 * Encoding: byte = (t0 << 0) | (t1 << 2) | (t2 << 4) | (t3 << 6)
 * where ti ∈ {0, 1, 2} stored in 2 bits each
 * Returns: (ti - 1) ∈ {-1, 0, +1}
 */
__device__ __forceinline__ void unpack_ternary_4(
    uint8_t packed,
    float* t0, float* t1, float* t2, float* t3
) {
    // Extract 2 bits for each ternary value, then subtract 1
    *t0 = (float)((int)((packed >> 0) & 0x03) - 1);
    *t1 = (float)((int)((packed >> 2) & 0x03) - 1);
    *t2 = (float)((int)((packed >> 4) & 0x03) - 1);
    *t3 = (float)((int)((packed >> 6) & 0x03) - 1);
}

/**
 * Multi-Base Ternary GEMM Kernel
 * 
 * Computes Y = X @ W^T where W is stored in multi-base ternary format.
 * 
 * Data Layout:
 * - W_packed: [out_dim, in_dim/4, n_bases] (U8)
 *   - Each byte contains 4 ternary values (base-3 encoded)
 *   - Multiple bases are summed with respective scales
 * - Scales: [n_bases] (F32) - one scale per base
 * 
 * Computation:
 *   W_dequant[o,k] = sum_b( ternary[o,k,b] * scale[b] )
 *   Y[batch,o] = sum_k( X[batch,k] * W_dequant[o,k] )
 * 
 * @param X           Input tensor [batch, in_dim] (F32)
 * @param W_packed    Packed weights [out_dim, packed_in, n_bases] (U8)
 * @param Scales      Per-base scales [n_bases] (F32)
 * @param Y           Output tensor [batch, out_dim] (F32)
 * @param batch_size  Batch dimension
 * @param in_dim      Input dimension (= packed_in * 4)
 * @param out_dim     Output dimension
 * @param packed_in   Packed input dimension (= in_dim / 4)
 * @param n_bases     Number of bases (typically 3)
 */
extern "C" __global__ void gemm_ternary_multibase_kernel_f32(
    const float* __restrict__ X,           // [batch, in_dim]
    const uint8_t* __restrict__ W_packed,  // [out_dim, packed_in, n_bases]
    const float* __restrict__ Scales,      // [n_bases]
    float* __restrict__ Y,                 // [batch, out_dim]
    int batch_size,
    int in_dim,
    int out_dim,
    int packed_in,
    int n_bases
) {
    // Thread mapping: each thread computes one output element
    int o = blockIdx.x * blockDim.x + threadIdx.x;  // Output index
    int b = blockIdx.y;                              // Batch index

    if (o >= out_dim || b >= batch_size) return;

    // Load scales into registers (n_bases is typically small, e.g., 3)
    float scale[8];  // Support up to 8 bases
    for (int base = 0; base < n_bases && base < 8; base++) {
        scale[base] = Scales[base];
    }

    // Pointer to input row
    const float* x_row = X + b * in_dim;
    
    // Accumulator
    float acc = 0.0f;
    
    // Process 4 input elements at a time (1 byte per base)
    for (int pk = 0; pk < packed_in; pk++) {
        int k_base = pk * 4;  // Starting input index for this packed position
        
        // Load input values
        float x0 = (k_base + 0 < in_dim) ? x_row[k_base + 0] : 0.0f;
        float x1 = (k_base + 1 < in_dim) ? x_row[k_base + 1] : 0.0f;
        float x2 = (k_base + 2 < in_dim) ? x_row[k_base + 2] : 0.0f;
        float x3 = (k_base + 3 < in_dim) ? x_row[k_base + 3] : 0.0f;
        
        // Accumulate across all bases
        for (int base = 0; base < n_bases; base++) {
            // Weight index: [o, pk, base] -> o * packed_in * n_bases + pk * n_bases + base
            int w_idx = o * packed_in * n_bases + pk * n_bases + base;
            uint8_t packed_byte = W_packed[w_idx];
            
            // Unpack 4 ternary values
            float t0, t1, t2, t3;
            unpack_ternary_4(packed_byte, &t0, &t1, &t2, &t3);
            
            // Dequantize and accumulate: x * ternary * scale
            float s = scale[base];
            acc += x0 * t0 * s;
            acc += x1 * t1 * s;
            acc += x2 * t2 * s;
            acc += x3 * t3 * s;
        }
    }
    
    Y[b * out_dim + o] = acc;
}

// ============================================================================
// Vectorized Load Optimized Kernels (float4 + uchar4)
// ============================================================================

/**
 * Vectorized 4-bit GEMM Kernel
 * 
 * Uses float4 (128-bit) for input X and processes 8 weights per iteration.
 * Requires in_dim to be multiple of 8.
 * 
 * Performance: ~1.5-2x faster than simple kernel due to:
 * - 4x fewer memory transactions for X
 * - Better instruction-level parallelism
 * - FMA instructions
 */
extern "C" __global__ void gemm_4bit_vectorized_kernel_f32(
    const float* __restrict__ X,           // [batch, in_dim] - should be 16-byte aligned
    const uint8_t* __restrict__ W_packed,  // [out_dim, in_dim/2]
    const float* __restrict__ Scales,      // [out_dim, n_groups]
    float* __restrict__ Y,                 // [batch, out_dim]
    int batch_size,
    int in_dim,
    int out_dim,
    int group_size
) {
    int o = blockIdx.x * blockDim.x + threadIdx.x;
    int b = blockIdx.y;
    if (o >= out_dim || b >= batch_size) return;

    const int packed_per_row = in_dim / 2;
    const int n_groups = (in_dim + group_size - 1) / group_size;
    
    // Cast to vectorized types
    const float4* x_vec = reinterpret_cast<const float4*>(X + b * in_dim);
    const uint8_t* w_row = W_packed + o * packed_per_row;
    const float* scale_row = Scales + o * n_groups;

    float acc = 0.0f;
    
    // Process 8 elements per iteration (2 x float4 = 8 floats, 4 bytes = 8 weights)
    const int vec4_pairs = in_dim / 8;
    
    #pragma unroll 4
    for (int vp = 0; vp < vec4_pairs; vp++) {
        // Load 8 floats using two float4 loads (2 x 128-bit = 256-bit total)
        float4 x_v0 = x_vec[vp * 2];
        float4 x_v1 = x_vec[vp * 2 + 1];
        
        // Load 4 packed bytes (8 weights)
        int w_base = vp * 4;
        uint8_t p0 = w_row[w_base + 0];
        uint8_t p1 = w_row[w_base + 1];
        uint8_t p2 = w_row[w_base + 2];
        uint8_t p3 = w_row[w_base + 3];
        
        int k_base = vp * 8;
        int g = k_base / group_size;
        float s = scale_row[g];
        
        // Unpack and compute - first float4 (4 weights from p0, p1)
        float w0 = (float)((int)(p0 & 0x0F) - 8);
        float w1 = (float)((int)((p0 >> 4) & 0x0F) - 8);
        float w2 = (float)((int)(p1 & 0x0F) - 8);
        float w3 = (float)((int)((p1 >> 4) & 0x0F) - 8);
        
        // FMA operations
        acc = fmaf(x_v0.x, w0 * s, acc);
        acc = fmaf(x_v0.y, w1 * s, acc);
        acc = fmaf(x_v0.z, w2 * s, acc);
        acc = fmaf(x_v0.w, w3 * s, acc);
        
        // Second float4 (4 weights from p2, p3)
        // Check if we crossed a group boundary
        int g2 = (k_base + 4) / group_size;
        float s2 = (g2 != g) ? scale_row[g2] : s;
        
        float w4 = (float)((int)(p2 & 0x0F) - 8);
        float w5 = (float)((int)((p2 >> 4) & 0x0F) - 8);
        float w6 = (float)((int)(p3 & 0x0F) - 8);
        float w7 = (float)((int)((p3 >> 4) & 0x0F) - 8);
        
        acc = fmaf(x_v1.x, w4 * s2, acc);
        acc = fmaf(x_v1.y, w5 * s2, acc);
        acc = fmaf(x_v1.z, w6 * s2, acc);
        acc = fmaf(x_v1.w, w7 * s2, acc);
    }
    
    // Handle remaining elements (if in_dim not multiple of 8)
    int remaining_start = vec4_pairs * 8;
    for (int k = remaining_start; k < in_dim; k += 2) {
        int k_pair = k / 2;
        uint8_t packed = w_row[k_pair];
        int g = k / group_size;
        float s = scale_row[g];
        
        float w0 = (float)((int)(packed & 0x0F) - 8) * s;
        float w1 = (float)((int)((packed >> 4) & 0x0F) - 8) * s;
        
        acc = fmaf(X[b * in_dim + k], w0, acc);
        if (k + 1 < in_dim) {
            acc = fmaf(X[b * in_dim + k + 1], w1, acc);
        }
    }
    
    Y[b * out_dim + o] = acc;
}

/**
 * Vectorized Multi-Base Ternary GEMM Kernel
 * 
 * Uses float4 (128-bit) for input X.
 * Optimized for 1.58-bit quantized models.
 */
extern "C" __global__ void gemm_ternary_multibase_vectorized_kernel_f32(
    const float* __restrict__ X,           // [batch, in_dim]
    const uint8_t* __restrict__ W_packed,  // [out_dim, packed_in, n_bases]
    const float* __restrict__ Scales,      // [n_bases]
    float* __restrict__ Y,                 // [batch, out_dim]
    int batch_size,
    int in_dim,
    int out_dim,
    int packed_in,
    int n_bases
) {
    int o = blockIdx.x * blockDim.x + threadIdx.x;
    int b = blockIdx.y;
    if (o >= out_dim || b >= batch_size) return;

    // Load scales into registers
    float scale[8];
    #pragma unroll
    for (int base = 0; base < 8 && base < n_bases; base++) {
        scale[base] = Scales[base];
    }

    // Cast input to float4 for vectorized load
    const float4* x_vec = reinterpret_cast<const float4*>(X + b * in_dim);
    const int w_stride = packed_in * n_bases;
    const uint8_t* w_base = W_packed + o * w_stride;
    
    float acc = 0.0f;
    
    // Process 4 elements per iteration (1 float4 = 4 floats = 1 packed byte per base)
    #pragma unroll 4
    for (int pk = 0; pk < packed_in; pk++) {
        // Load 4 floats at once (128-bit load)
        float4 x_v = x_vec[pk];
        
        // Process all bases
        #pragma unroll
        for (int base = 0; base < n_bases && base < 8; base++) {
            uint8_t packed_byte = w_base[pk * n_bases + base];
            float s = scale[base];
            
            // Unpack 4 ternary values
            float t0 = (float)((int)((packed_byte >> 0) & 0x03) - 1);
            float t1 = (float)((int)((packed_byte >> 2) & 0x03) - 1);
            float t2 = (float)((int)((packed_byte >> 4) & 0x03) - 1);
            float t3 = (float)((int)((packed_byte >> 6) & 0x03) - 1);
            
            // FMA operations
            acc = fmaf(x_v.x * t0, s, acc);
            acc = fmaf(x_v.y * t1, s, acc);
            acc = fmaf(x_v.z * t2, s, acc);
            acc = fmaf(x_v.w * t3, s, acc);
        }
    }
    
    Y[b * out_dim + o] = acc;
}

/**
 * Optimized Multi-Base Ternary GEMM with Tiling
 * 
 * Uses shared memory for better cache efficiency on large matrices.
 * Recommended for hidden_size >= 4096.
 */
extern "C" __global__ void gemm_ternary_multibase_tiled_kernel_f32(
    const float* __restrict__ X,           // [batch, in_dim]
    const uint8_t* __restrict__ W_packed,  // [out_dim, packed_in, n_bases]
    const float* __restrict__ Scales,      // [n_bases]
    float* __restrict__ Y,                 // [batch, out_dim]
    int batch_size,
    int in_dim,
    int out_dim,
    int packed_in,
    int n_bases
) {
    // Shared memory for input tile and scales
    __shared__ float x_tile[TILE_SIZE];
    __shared__ float s_shared[8];  // Up to 8 bases
    
    int o = blockIdx.x * blockDim.x + threadIdx.x;
    int b = blockIdx.y;
    
    if (b >= batch_size) return;
    
    // Load scales into shared memory (once per block)
    if (threadIdx.x < n_bases && threadIdx.x < 8) {
        s_shared[threadIdx.x] = Scales[threadIdx.x];
    }
    __syncthreads();
    
    float acc = 0.0f;
    
    // Process input in tiles
    for (int tile_start = 0; tile_start < in_dim; tile_start += TILE_SIZE) {
        // Load input tile into shared memory (all threads cooperate)
        for (int i = threadIdx.x; i < TILE_SIZE && tile_start + i < in_dim; i += blockDim.x) {
            x_tile[i] = X[b * in_dim + tile_start + i];
        }
        __syncthreads();
        
        if (o < out_dim) {
            // Process this tile
            int pk_start = tile_start / 4;
            int pk_end = (tile_start + TILE_SIZE + 3) / 4;
            if (pk_end > packed_in) pk_end = packed_in;
            
            for (int pk = pk_start; pk < pk_end; pk++) {
                int k_base = pk * 4;
                
                // Get input values from shared memory
                float x0 = (k_base + 0 >= tile_start && k_base + 0 < tile_start + TILE_SIZE && k_base + 0 < in_dim) 
                           ? x_tile[k_base + 0 - tile_start] : 0.0f;
                float x1 = (k_base + 1 >= tile_start && k_base + 1 < tile_start + TILE_SIZE && k_base + 1 < in_dim) 
                           ? x_tile[k_base + 1 - tile_start] : 0.0f;
                float x2 = (k_base + 2 >= tile_start && k_base + 2 < tile_start + TILE_SIZE && k_base + 2 < in_dim) 
                           ? x_tile[k_base + 2 - tile_start] : 0.0f;
                float x3 = (k_base + 3 >= tile_start && k_base + 3 < tile_start + TILE_SIZE && k_base + 3 < in_dim) 
                           ? x_tile[k_base + 3 - tile_start] : 0.0f;
                
                // Skip if no valid inputs in this tile
                if (x0 == 0.0f && x1 == 0.0f && x2 == 0.0f && x3 == 0.0f) continue;
                
                for (int base = 0; base < n_bases && base < 8; base++) {
                    int w_idx = o * packed_in * n_bases + pk * n_bases + base;
                    uint8_t packed_byte = W_packed[w_idx];
                    
                    float t0, t1, t2, t3;
                    unpack_ternary_4(packed_byte, &t0, &t1, &t2, &t3);
                    
                    float s = s_shared[base];
                    acc += x0 * t0 * s + x1 * t1 * s + x2 * t2 * s + x3 * t3 * s;
                }
            }
        }
        
        __syncthreads();
    }
    
    if (o < out_dim) {
        Y[b * out_dim + o] = acc;
    }
}
