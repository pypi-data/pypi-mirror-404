# Building from Source

This guide explains how to build CaDaR from source code.

## Prerequisites

### Required Tools

1. **Rust** (1.70 or later)
   ```bash
   curl --proto '=https' --tlsv1.2 -sSf https://sh.rustup.rs | sh
   source $HOME/.cargo/env
   ```

2. **Python** (3.8 or later)
   ```bash
   python --version  # Verify Python 3.8+
   ```

3. **Maturin** (Build tool for Rust+Python)
   ```bash
   pip install maturin
   ```

### Optional Tools

- **Git** - For cloning the repository
- **Make** - For using Makefile commands

## Clone the Repository

```bash
git clone https://github.com/Oit-Technologies/CaDaR.git
cd CaDaR
```

## Build Options

### Development Build

For local development and testing:

```bash
# Create virtual environment
python -m venv venv
source venv/bin/activate  # On Windows: venv\Scripts\activate

# Build and install in editable mode
maturin develop
```

This creates an unoptimized debug build with fast compilation.

### Release Build

For production use:

```bash
# Build optimized wheel
maturin build --release

# Install the wheel
pip install target/wheels/*.whl
```

### Specific Python Version

Target a specific Python version:

```bash
# Using specific Python
maturin develop --python /usr/bin/python3.11
```

## Testing the Build

After building, test the installation:

```python
import cadar

# Test version
print(f"CaDaR version: {cadar.__version__}")

# Test functionality
result = cadar.ara2bizi("سلام", darija="Ma")
print(f"Test: سلام → {result}")
assert result == "slam", "Test failed!"
print("✓ Build successful!")
```

## Build Artifacts

After building, you'll find:

- `target/debug/` - Debug build artifacts
- `target/release/` - Release build artifacts
- `target/wheels/` - Python wheel files

## Platform-Specific Notes

### Linux

No special requirements. Standard build should work.

### macOS

Make sure Xcode command line tools are installed:

```bash
xcode-select --install
```

### Windows

Requires:
- Microsoft Visual C++ Build Tools
- Rust toolchain with MSVC target

```bash
rustup target add x86_64-pc-windows-msvc
```

## Troubleshooting

### Rust Not Found

```bash
# Reload shell environment
source $HOME/.cargo/env

# Or add to your shell profile
echo 'source $HOME/.cargo/env' >> ~/.bashrc
```

### Python Version Mismatch

Ensure you're using Python 3.8+:

```bash
python --version
pip install --upgrade pip
```

### Build Errors

Clean build artifacts and retry:

```bash
cargo clean
rm -rf target/
maturin develop --release
```

### Permission Errors

On Linux/macOS, you may need to fix permissions:

```bash
chmod +x scripts/*.sh
```

## Advanced Build Options

### Cross-Compilation

Build for different platforms:

```bash
# For Linux (musl)
maturin build --target x86_64-unknown-linux-musl

# For macOS ARM
maturin build --target aarch64-apple-darwin
```

### Custom Features

Build with specific features:

```bash
# Build with all features
cargo build --all-features

# Build with no default features
cargo build --no-default-features
```

## Development Workflow

Recommended workflow for contributors:

```bash
# 1. Create feature branch
git checkout -b feature/my-feature

# 2. Make changes to Rust code
# ... edit src/*.rs files ...

# 3. Rebuild
maturin develop

# 4. Test
cargo test
python -c "import cadar; print(cadar.ara2bizi('سلام'))"

# 5. Commit
git add .
git commit -m "Add: my feature"

# 6. Push and create PR
git push origin feature/my-feature
```

For more information, see [Testing](testing.md) and [Contributing](contributing.md).
