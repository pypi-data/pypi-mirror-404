#!/bin/bash

# CaDaR Build Script
# This script builds the CaDaR library and prepares it for use

set -e  # Exit on error

echo "════════════════════════════════════════════════════"
echo "  CaDaR Build Script"
echo "════════════════════════════════════════════════════"
echo ""

# Check if Rust is installed
if ! command -v rustc &> /dev/null; then
    echo "❌ Error: Rust is not installed"
    echo "Please install Rust from https://rustup.rs/"
    exit 1
fi

echo "✓ Rust version: $(rustc --version)"

# Check if Python is installed
if ! command -v python3 &> /dev/null; then
    echo "❌ Error: Python 3 is not installed"
    exit 1
fi

echo "✓ Python version: $(python3 --version)"

# Check if Maturin is installed
if ! command -v maturin &> /dev/null; then
    echo "⚠️  Maturin is not installed. Installing..."
    pip install maturin
fi

echo "✓ Maturin version: $(maturin --version)"
echo ""

# Build type
BUILD_TYPE="${1:-dev}"

if [ "$BUILD_TYPE" = "release" ]; then
    echo "Building CaDaR in RELEASE mode..."
    maturin build --release
    echo ""
    echo "✓ Release build completed!"
    echo "Wheel files are in: target/wheels/"
elif [ "$BUILD_TYPE" = "dev" ]; then
    echo "Building CaDaR in DEVELOPMENT mode..."
    maturin develop
    echo ""
    echo "✓ Development build completed!"
    echo "CaDaR is now installed in your Python environment"
else
    echo "❌ Unknown build type: $BUILD_TYPE"
    echo "Usage: $0 [dev|release]"
    exit 1
fi

echo ""
echo "════════════════════════════════════════════════════"
echo "  Build completed successfully!"
echo "════════════════════════════════════════════════════"
echo ""
echo "Next steps:"
echo "  1. Test the installation:"
echo "     python3 -c 'import cadar; print(cadar.ara2bizi(\"سلام\", darija=\"Ma\"))'"
echo ""
echo "  2. Run examples:"
echo "     python3 examples/basic_usage.py"
echo ""
echo "  3. Run tests:"
echo "     cargo test"
echo ""
