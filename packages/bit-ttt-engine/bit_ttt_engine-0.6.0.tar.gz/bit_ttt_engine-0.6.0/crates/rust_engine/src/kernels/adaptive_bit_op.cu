/**
 * Adaptive BitNet CUDA Kernel - Multi-base 2-bit Quantization
 * 
 * This kernel performs fused dequantization and matrix multiplication for
 * BitNet b1.58 weights with multi-base (adaptive) quantization.
 * 
 * Data Layout:
 * - W: [base0_packed][base1_packed][base2_packed] (contiguous bases)
 *   - Each base: [out_dim * in_dim/4] bytes
 *   - Each byte: 4 weights packed as 2-bit codes
 * 
 * 2-bit Encoding:
 *   00 -> 0.0
 *   01 -> +1.0
 *   10 -> -1.0
 *   11 -> 0.0 (padding)
 * 
 * Computation: Y[b,o] = sum_k( X[b,k] * sum_base(decode(W[base,o,k]) * scales[base]) )
 */

#include <cuda_runtime.h>
#include <stdint.h>

#define BLOCK_SIZE 256
#define N_BASES 3

// Decode 2-bit code to float coefficient
__device__ __forceinline__ float decode_2bit(uint8_t code) {
    // 00 -> 0.0, 01 -> 1.0, 10 -> -1.0, 11 -> 0.0
    // Branchless: (code & 1) - (code >> 1)
    // But need to handle 11 -> 0 case
    // code=0: 0-0=0, code=1: 1-0=1, code=2: 0-1=-1, code=3: 1-1=0 ✓
    return (float)((int)(code & 1) - (int)(code >> 1));
}

/**
 * Adaptive GEMM Kernel for N=3 bases with 2-bit packed weights
 * 
 * @param X       Input tensor [batch, in_dim] (F32)
 * @param W       Packed weights [n_bases * out_dim * in_dim/4] (U8)
 *                Layout: base0 bytes, then base1, then base2
 * @param Scales  Per-base scales [N_BASES] (F32)
 * @param Y       Output tensor [batch, out_dim] (F32)
 * @param batch_size  Batch dimension
 * @param in_dim      Input dimension (must be multiple of 4)
 * @param out_dim     Output dimension
 */
extern "C" __global__ void adaptive_gemm_n3_kernel_f32(
    const float* __restrict__ X,       // [batch, in_dim]
    const uint8_t* __restrict__ W,     // [n_bases * out_dim * (in_dim/4)]
    const float* __restrict__ Scales,  // [N_BASES]
    float* __restrict__ Y,             // [batch, out_dim]
    int batch_size,
    int in_dim,
    int out_dim
) {
    // Thread mapping: each thread computes one output element
    int o = blockIdx.x * blockDim.x + threadIdx.x;  // Output index
    int b = blockIdx.y;                              // Batch index

    if (o >= out_dim || b >= batch_size) return;

    // Calculate offsets
    const int packed_per_row = in_dim / 4;  // Bytes per output row per base
    const int base_stride = out_dim * packed_per_row;  // Bytes per base

    // Pointers to weight rows for each base
    const uint8_t* w_base0 = W + 0 * base_stride + o * packed_per_row;
    const uint8_t* w_base1 = W + 1 * base_stride + o * packed_per_row;
    const uint8_t* w_base2 = W + 2 * base_stride + o * packed_per_row;

    // Load scales to registers
    float s0 = Scales[0];
    float s1 = Scales[1];
    float s2 = Scales[2];

    // Pointer to input row
    const float* x_row = X + b * in_dim;

    // Accumulator
    float acc = 0.0f;

    // Process 4 weights at a time (1 byte per base)
    for (int k = 0; k < packed_per_row; ++k) {
        // Load packed bytes for all bases
        uint8_t byte0 = w_base0[k];
        uint8_t byte1 = w_base1[k];
        uint8_t byte2 = w_base2[k];

        // Load 4 input values
        float x0 = x_row[k * 4 + 0];
        float x1 = x_row[k * 4 + 1];
        float x2 = x_row[k * 4 + 2];
        float x3 = x_row[k * 4 + 3];

        // Process param 0 (bits 0-1)
        {
            uint8_t c0 = (byte0 >> 0) & 0x03;
            uint8_t c1 = (byte1 >> 0) & 0x03;
            uint8_t c2 = (byte2 >> 0) & 0x03;
            float w = decode_2bit(c0) * s0 + decode_2bit(c1) * s1 + decode_2bit(c2) * s2;
            acc += x0 * w;
        }

        // Process param 1 (bits 2-3)
        {
            uint8_t c0 = (byte0 >> 2) & 0x03;
            uint8_t c1 = (byte1 >> 2) & 0x03;
            uint8_t c2 = (byte2 >> 2) & 0x03;
            float w = decode_2bit(c0) * s0 + decode_2bit(c1) * s1 + decode_2bit(c2) * s2;
            acc += x1 * w;
        }

        // Process param 2 (bits 4-5)
        {
            uint8_t c0 = (byte0 >> 4) & 0x03;
            uint8_t c1 = (byte1 >> 4) & 0x03;
            uint8_t c2 = (byte2 >> 4) & 0x03;
            float w = decode_2bit(c0) * s0 + decode_2bit(c1) * s1 + decode_2bit(c2) * s2;
            acc += x2 * w;
        }

        // Process param 3 (bits 6-7)
        {
            uint8_t c0 = (byte0 >> 6) & 0x03;
            uint8_t c1 = (byte1 >> 6) & 0x03;
            uint8_t c2 = (byte2 >> 6) & 0x03;
            float w = decode_2bit(c0) * s0 + decode_2bit(c1) * s1 + decode_2bit(c2) * s2;
            acc += x3 * w;
        }
    }

    // Write output
    Y[b * out_dim + o] = acc;
}
