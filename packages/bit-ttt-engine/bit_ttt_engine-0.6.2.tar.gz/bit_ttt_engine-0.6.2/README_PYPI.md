# Bit-TTT Engine: High-Performance Brain Core

[![Rust](https://img.shields.io/badge/rust-1.70+-orange.svg)](https://www.rust-lang.org/)
[![License: MIT](https://img.shields.io/badge/License-MIT-blue.svg)](LICENSE)
[![PyPI](https://img.shields.io/pypi/v/bit-ttt-engine.svg)](https://pypi.org/project/bit-ttt-engine/)

**4-bit Quantization + Test-Time Training (TTT)** Implementation in Pure Rust.

## ✨ Features
1. **Fast**: **40 tokens/second** on GPU (RTX 4060 Ti).
2. **Adaptive (TTT)**: Learns *while* inferring - unique to Bit-TTT!
3. **Pure Rust**: High performance with minimal dependencies.
4. **Easy**: Load GGUF models directly.

## 🚀 Installation

```bash
pip install bit-ttt-engine
```

## 💻 Quick Start (GGUF Models)

```python
from cortex_rust import GgufModel

# Load model
model = GgufModel("model.gguf", tokenizer="tokenizer.json")

# Generate text
output = model.generate(
    "Hello, how are you?",
    max_tokens=50,
    temperature=0.7
)
print(output)

# Streaming output
model.generate_with_callback(
    "Tell me a story",
    lambda t: print(t, end="", flush=True),
    max_tokens=100
)
```

## 🧠 TTT (Test-Time Training)

**TTT makes the model adapt during inference** - something no other local LLM can do!

```python
from cortex_rust import GgufModel

model = GgufModel("model.gguf", tokenizer="tokenizer.json")

# Enable TTT
model.enable_ttt(layers=4, learning_rate=0.1)

# Without TTT: Pass 1 == Pass 2 (same output)
# With TTT:    Pass 1 != Pass 2 (model is learning!)

out1 = model.generate("My name is Alice.", max_tokens=20)
out2 = model.generate("My name is Alice.", max_tokens=20)
print(f"Different: {out1 != out2}")  # True!

# TTT controls
model.disable_ttt()
model.reset_ttt_state()
print(model.ttt_enabled)  # False
```

## 🏗️ Legacy API (BitLlama)

```python
import cortex_rust

config = cortex_rust.BitLlamaConfig(
    vocab_size=32000,
    hidden_dim=512,
    num_layers=12,
    inner_lr=0.001
)

model = cortex_rust.BitLlama(
    config=config,
    checkpoint_path="path/to/model.safetensors",
    device="cpu",
    tokenizer_path="path/to/tokenizer.json"
)

output = model.generate(prompt="Hello!", max_tokens=50)
```

## 📖 Documentation
For more details, please visit the [GitHub repository](https://github.com/imonoonoko/Bit-TTT-Engine).

## 🙏 Acknowledgments
This project incorporates ideas and techniques inspired by the DroPE method published by Sakana AI.

## 💖 License
MIT License
