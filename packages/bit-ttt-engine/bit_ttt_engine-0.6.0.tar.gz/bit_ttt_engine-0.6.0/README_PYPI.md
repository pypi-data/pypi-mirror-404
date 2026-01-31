# Bit-TTT Engine: High-Performance Brain Core

[![Rust](https://img.shields.io/badge/rust-1.70+-orange.svg)](https://www.rust-lang.org/)
[![License: MIT](https://img.shields.io/badge/License-MIT-blue.svg)](LICENSE)
[![PyPI](https://img.shields.io/pypi/v/bit-ttt-engine.svg)](https://pypi.org/project/bit-ttt-engine/)

**1.58-bit Quantization + Test-Time Training (TTT)** Implementation in Pure Rust.

This package provides Python bindings for the Bit-TTT Engine, allowing you to run ultra-light ternary LLMs with real-time adaptation.

## ✨ Features
1. **Ultra-Light**: Runs large LLMs on cheap hardware using **1.58-bit (ternary) weights**.
2. **Adaptive (TTT)**: Learns *while* inferring, adapting to context in real-time.
3. **Pure Rust**: High performance with minimal dependencies.

## 🚀 Installation

```bash
pip install bit-ttt-engine
```

## 💻 Usage

```python
import cortex_rust
import json

# Initialize Configuration
config = cortex_rust.BitLlamaConfig(
    vocab_size=32000,
    hidden_dim=512,
    num_layers=12,
    inner_lr=0.001
)

# Initialize Model (Inference)
model = cortex_rust.BitLlama(
    config=config,
    checkpoint_path="path/to/model.safetensors",
    device="cpu", # or "cuda"
    tokenizer_path="path/to/tokenizer.json"
)

# Generate Text
output = model.generate(prompt="Hello, world!", max_tokens=50)
print(output)
```

## 🏗️ Training (TTT)

```python
trainer = cortex_rust.PyTrainer(
    config=config,
    checkpoint_path="path/to/model.safetensors",
    device="cuda"
)

# Single training step
loss = trainer.train_step(input_ids=[...], targets=[...])
print(f"Loss: {loss}")

# Save checkpoint
trainer.save_checkpoint("model_updated.safetensors")
```

## 📖 Documentation
For more details, please visit the [GitHub repository](https://github.com/imonoonoko/Bit-TTT-Engine).

## 🙏 Acknowledgments
This project incorporates ideas and techniques inspired by the DroPE method published by Sakana AI.

## 💖 License
MIT License
