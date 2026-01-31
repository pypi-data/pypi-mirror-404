# PagedAttention 品質劣化調査レポート

## 概要
長いシーケンス（2048+ tokens）での推論品質劣化の原因を調査しました。

## 調査ファイル
- `src/kernels/paged_attention.cu` - CUDA カーネル
- `src/kernels/paged_attention.rs` - Rust バインディング
- `src/model/llama_4bit.rs` - generate_paged() フロー
- `src/paged_attention/block_manager.rs` - ブロック管理
- `src/paged_attention/cache_engine.rs` - キャッシュエンジン

---

## 🔴 Critical Issue 1: Shared Memory Overflow

### 場所
`src/kernels/paged_attention.rs:155-156`

```rust
let max_context_len = 2048; // TODO: Make configurable
let shared_mem_bytes = ((head_dim + max_context_len) * std::mem::size_of::<f32>()) as u32;
```

### 問題
- `max_context_len = 2048` がハードコード
- 2048トークンを超えるシーケンスでは、qk_scores の書き込みが shared memory 境界外にアクセス
- **結果**: 未定義動作、ガベージ値、クラッシュ

### 修正案
```rust
// context_lens から実際の最大値を取得
let context_lens_host: Vec<u32> = context_lens.to_vec1()?;
let max_context = *context_lens_host.iter().max().unwrap_or(&2048) as usize;
let shared_mem_bytes = ((head_dim + max_context) * std::mem::size_of::<f32>()) as u32;
```

---

## 🔴 Critical Issue 2: Warp Reduction Bug

### 場所
`src/kernels/paged_attention.cu:114-118`

```cuda
// Warp reduction for max (blockDim.x = 32)
for (int offset = 16; offset > 0; offset >>= 1) {
    max_score = fmaxf(max_score, __shfl_down_sync(0xffffffff, max_score, offset));
}
max_score = __shfl_sync(0xffffffff, max_score, 0);
```

### 問題
- `__shfl_down_sync` は同一 warp (32 threads) 内でのみ有効
- `context_len > 32` の場合、各スレッドは自分が担当した token の中でのみ max を計算
- 全体の max ではなく、部分的な max で softmax を計算
- **結果**: softmax が不正確 → attention weights が歪む

### 修正案
```cuda
// 1. 各スレッドの local max を shared memory に格納
__shared__ float max_scores_shared[32];
if (threadIdx.x < 32) max_scores_shared[threadIdx.x] = -FLT_MAX;
__syncthreads();

// 2. Atomic max (or reduction via shared memory)
atomicMax(&max_scores_shared[0], max_score); // Note: float atomicMax needs custom impl
__syncthreads();

// 3. Broadcast global max
max_score = max_scores_shared[0];
```

より効率的な実装は shared memory reduction:
```cuda
// Two-step reduction: warp-level -> block-level
float warp_max = warpReduceMax(max_score);
__shared__ float block_max[32]; // one per warp
if (lane_id == 0) block_max[warp_id] = warp_max;
__syncthreads();
if (warp_id == 0) warp_max = warpReduceMax(block_max[lane_id]);
if (threadIdx.x == 0) block_max[0] = warp_max;
__syncthreads();
max_score = block_max[0];
```

---

## 🟡 Issue 3: Context Length Miscalculation

### 場所
`src/paged_attention/block_manager.rs:76-79`

```rust
pub fn get_context_len(&self, seq_id: usize) -> usize {
    self.seq_to_blocks.get(&seq_id)
        .map(|blocks| blocks.len() * self.block_size)
        .unwrap_or(0)
}
```

### 問題
- 実際のトークン数ではなく `blocks * block_size` を返す
- 最後のブロックが満杯でない場合、過大な context_len が CUDA カーネルに渡される
- カーネルは未初期化領域の K/V を読む

### 修正案
```rust
pub struct BlockManager {
    // ...
    /// Actual token count per sequence
    seq_token_counts: HashMap<usize, usize>,
}

pub fn get_context_len(&self, seq_id: usize) -> usize {
    self.seq_token_counts.get(&seq_id).copied().unwrap_or(0)
}

pub fn allocate_slots(&mut self, seq_id: usize, num_tokens: usize) -> Result<Vec<i64>> {
    // ... existing logic ...
    *self.seq_token_counts.entry(seq_id).or_insert(0) += num_tokens;
    // ...
}
```

---

## 🟡 Issue 4: Softmax Sum Reduction Bug

### 場所
`src/kernels/paged_attention.cu:125-128`

```cuda
// Warp reduction for sum
for (int offset = 16; offset > 0; offset >>= 1) {
    sum_exp += __shfl_down_sync(0xffffffff, sum_exp, offset);
}
sum_exp = __shfl_sync(0xffffffff, sum_exp, 0);
```

### 問題
- Issue 2 と同様、warp 内でしか sum が計算されない
- `context_len > 32` では各 warp が部分和しか持たない
- **結果**: 正規化係数が不正確 → attention weights の合計が 1 にならない

---

## 🟢 Minor Issue: RoPE Position Off-by-One

### 場所
`src/model/llama_4bit.rs:564`

```rust
let cos = self.cos_cache.narrow(0, pos - 1, 1)?;
let sin = self.sin_cache.narrow(0, pos - 1, 1)?;
```

### 問題
- decode フェーズで `pos - 1` を使用
- 正しくは `pos` (現在の位置) であるべき可能性
- 長いシーケンスでは累積的なズレが発生

### 検証方法
- Prefill の最後のトークンと decode の最初のトークンの position を比較
- HuggingFace 実装との出力比較

---

## 推奨修正優先順位

| 優先度 | 問題 | 影響度 | 修正コスト |
|--------|------|--------|-----------|
| 🔴 P0 | Warp reduction (max & sum) | Critical | 中 |
| 🔴 P0 | Shared memory overflow | Critical | 低 |
| 🟡 P1 | Context length calculation | High | 低 |
| 🟢 P2 | RoPE position | Medium | 低 |

---

## テスト計画

### 回帰テスト
1. **Short sequence (128 tokens)**: 既存動作確認
2. **Medium sequence (512 tokens)**: 境界付近
3. **Long sequence (2048 tokens)**: 旧 max_context_len 境界
4. **Very long sequence (4096+ tokens)**: 新しい境界

### 品質メトリクス
- Perplexity 比較 (traditional KV cache vs PagedAttention)
- Top-k token 一致率
- Softmax weights の合計値 (1.0 になるべき)

### 数値精度テスト
```python
# attention weights の合計値検証
attn_sum = attention_weights.sum(dim=-1)
assert torch.allclose(attn_sum, torch.ones_like(attn_sum), atol=1e-5)
```

---

## 0.5.0 で修正するもの

1. ✅ Warp reduction を block-level reduction に修正
2. ✅ max_context_len を動的に計算
3. ✅ BlockManager に実トークン数を追跡
4. ⏳ RoPE position の検証 (要調査)

## 参考資料

- [vLLM PagedAttention Paper](https://arxiv.org/abs/2309.06180)
- [vLLM CUDA Kernels](https://github.com/vllm-project/vllm/tree/main/csrc/attention)
- [FlashAttention](https://github.com/Dao-AILab/flash-attention)
