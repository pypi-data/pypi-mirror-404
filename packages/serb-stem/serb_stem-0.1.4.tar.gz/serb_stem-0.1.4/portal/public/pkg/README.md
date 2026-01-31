# SerbStem

A high-performance Serbian stemming library written in Rust, with bindings for Python and WebAssembly.

## Features

- **Extreme Performance**: Built with Rust for speed and safety.
- **Dual Script Support**: Automatically handles both Cyrillic and Latin (Ekavica) inputs.
- **Modern Logic**: Advanced suffix stripping and voice change reversal rules.
- **Cross-Platform**: Use it in Rust, Python, or directly in the browser via WASM.

## Installation

### Python
```bash
pip install serb-stem
```

### Rust
```toml
[dependencies]
serb_stem = "0.1.0"
```

## Usage

### Python
```python
import serb_stem

# Latin input
print(serb_stem.stem_py("knjigama"))  # Output: "knjig"

# Cyrillic input
print(serb_stem.stem_py("књигама"))  # Output: "књиг"

# Ekavization
print(serb_stem.stem_py("певајући"))  # Output: "pev"
```

### Rust
```rust
use serb_stem::stem;

let result = stem("učenici");
assert_eq!(result, "učenik");
```

## License

MIT
