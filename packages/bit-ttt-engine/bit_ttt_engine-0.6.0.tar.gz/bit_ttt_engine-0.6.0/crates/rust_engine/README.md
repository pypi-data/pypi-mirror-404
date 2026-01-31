# Cortex Rust Engine - WebAssembly Support

## Prerequisites
- Rust (latest stable version)
- wasm-pack
- Node.js and npm

## Installation
1. Install wasm-pack:
```bash
cargo install wasm-pack
```

2. Add WebAssembly target:
```bash
rustup target add wasm32-unknown-unknown
```

## Building the WebAssembly Package
```bash
# Build WASM package
wasm-pack build --target web --features wasm

# Build npm package
wasm-pack build --target npm --features wasm
```

## Usage in Browser
```javascript
import init, { wasm_infer, wasm_log, init_panic_hook } from './pkg/cortex_rust.js';

async function run() {
  // Initialize WASM module
  await init();
  
  // Set up panic hook for better error reporting
  init_panic_hook();

  // Basic inference
  try {
    const result = wasm_infer("Your input text here");
    console.log(result);
  } catch (error) {
    console.error("Inference error:", error);
  }

  // Optional logging
  wasm_log("WebAssembly module initialized");
}

run();
```

## Limitations
- No CUDA support (CPU-only)
- Limited file I/O capabilities
- Memory constraints inherent to WebAssembly

## Notes
- Requires modern browser with WebAssembly support
- Performance may differ from native Rust execution