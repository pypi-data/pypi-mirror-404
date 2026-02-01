pub mod cpu;
pub mod cuda;
pub mod fused_ops; // Fused CUDA kernels (RMSNorm, softmax, RoPE, SiLU)
pub mod matmul_4bit;
pub mod packing;
pub mod packing_4bit; // 4-bit quantization packing/unpacking
pub mod paged_attention; // PagedAttention CUDA kernels
