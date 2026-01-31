# Changelog

All notable changes to `cortex_rust` will be documented in this file.

The format is based on [Keep a Changelog](https://keepachangelog.com/en/1.1.0/),
and this project adheres to [Semantic Versioning](https://semver.org/spec/v2.0.0.html).

## [Unreleased]

## [0.5.0] - 2026-01-28

### 🚨 Breaking Changes
- `paged_attention_v1()` signature changed: `num_kv_heads` now required for GQA support
- `CacheConfig::new()` parameter order reorganized for clarity

### Added
- **GQA (Grouped Query Attention) support** in PagedAttention kernel
- `num_kv_heads` parameter for proper KV head mapping
- Detailed profiling methods: `forward_profiled()`, `forward_timed()`
- `PreallocKVCache` - pre-allocated KV cache to reduce allocation overhead

### Fixed
- **[CRITICAL] Long sequence quality degradation** - see "Known Issues Resolved" below
- Shared memory overflow for sequences > 2048 tokens
- Warp reduction bug in softmax max computation
- Context length calculation in block manager (off-by-one)

### Changed
- Increased default `max_context_len` to 4096 for shared memory allocation
- Improved error messages with actual tensor dimensions
- Block size default changed from 16 to 32 for better memory efficiency

### Known Issues Resolved
#### Long Sequence Quality Degradation Root Causes

1. **Query Loading Bug in PagedAttention** (`paged_attention.cu`)
   - Query was loaded into per-thread local array `float q[128]`
   - Each thread only loaded some elements, but inner loop accessed all
   - **Result**: Reading uninitialized memory → garbage attention scores
   - **Fix**: Load query into shared memory (`q_shared`)
   - **Commit**: a6f14c8

2. **Block Manager Token Count** (`block_manager.rs`)
   - `allocate_slots()` used `blocks.len() * block_size` for current position
   - With block_size=16, after 5 tokens: calculated 16 instead of 5
   - **Result**: New tokens written to wrong slots (e.g., slot 16 instead of 5)
   - **Fix**: Added `seq_to_num_tokens` HashMap to track actual token count
   - **Commit**: f556c15

#### Additional Fixes in 0.5.0
3. **unpack_4bit offset bug** (`linear_4bit.rs`)
   - Old: `if w > 7 { w - 16 } else { w }` (wrong)
   - New: `w - 8` (Python compatible)
   - **Commit**: 7ffcdc2

4. **Dynamic shared memory** (`paged_attention.rs`)
   - Old: Hardcoded `max_context_len = 2048`
   - New: Calculated from actual `context_lens` tensor
   - **Commit**: 9a748ec

#### Verified (No Bug)
- Warp reduction: Works correctly with `blockDim.x = 32`

## [0.4.0] - 2025-01-XX

### Added
- PagedAttention CUDA kernels (`paged_attention.cu`)
- `BlockManager` for cache block allocation
- `CacheEngine` for GPU memory management
- `generate_paged()` for memory-efficient inference
- 4-bit quantized model support (`Llama4Bit`)
- Fused CUDA kernels: `fused_silu_mul_cuda`, `softmax_cuda`

### Changed
- RoPE implementation moved to precomputed caches
- KV cache supports both traditional (`Tensor::cat`) and paged modes

### Fixed
- Causal mask offset calculation for decode phase

## [0.3.0] - 2025-01-XX

### Added
- Initial CUDA kernel infrastructure
- 4-bit GEMM implementation (`gemm_4bit`)
- RMSNorm layer

## [0.2.0] - 2025-01-XX

### Added
- Basic transformer block implementation
- Embedding and LM head layers

## [0.1.0] - 2025-01-XX

### Added
- Initial project structure
- Candle-core integration
- Basic tensor operations
