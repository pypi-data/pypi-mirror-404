# CaDaR: Canonicalization and Darija Representation

<div align="center">

**High-performance bidirectional transliteration for Darija (Moroccan Arabic)**

[![License: MIT](https://img.shields.io/badge/License-MIT-yellow.svg)](https://opensource.org/licenses/MIT)
[![Python 3.8+](https://img.shields.io/badge/python-3.8+-blue.svg)](https://www.python.org/downloads/)
[![Rust](https://img.shields.io/badge/rust-stable-orange.svg)](https://www.rust-lang.org/)

</div>

## Overview

CaDaR is a robust, FST-style (Finite State Transducer) transliteration library designed specifically for Darija (Moroccan Arabic). It provides bidirectional conversion between Arabic script and Latin (Romanized/Bizi) script, along with standardization capabilities for both scripts.

### Key Features

- **Bidirectional Transliteration**: Convert seamlessly between Arabic and Latin scripts
- **Intelligent Normalization**: Handles noise, diacritics, and common variations
- **Darija-Aware Processing**: Respects Darija-specific linguistic patterns
- **Intermediate Canonical Representation (ICR)**: Unified internal representation for accurate conversion
- **High Performance**: Written in Rust with Python bindings for optimal speed
- **Extensible**: Designed to support multiple Darija dialects (currently Moroccan)

## Architecture

CaDaR uses a 6-stage pipeline with an Intermediate Canonical Representation (ICR):

```
Raw Input
   ↓
Stage 1: Script Detection
   ↓
Stage 2: Noise Cleaning & Normalization
   ↓
Stage 3: Tokenization (Darija-aware)
   ↓
Stage 4: Canonical Darija Representation (ICR)
   ↓
Stage 5: Target Script Generation
   ↓
Stage 6: Post-validation & Fixes
   ↓
Clean Standard Output
```

### What is ICR?

The **Intermediate Canonical Representation (ICR)** is the core innovation of CaDaR. It's a script-independent, phonologically-grounded representation that:

- Abstracts away script-specific quirks
- Preserves Darija phonological distinctions
- Enables lossless round-trip conversions
- Allows for consistent normalization across scripts

## Installation

### From PyPI (Coming Soon)

```bash
pip install cadar
```

### From Source

#### Prerequisites

- Python 3.8 or higher
- Rust toolchain (for building from source)
- Maturin (for Python packaging)

#### Build and Install

```bash
# Clone the repository
git clone https://github.com/Oit-Technologies/CaDaR.git
cd CaDaR

# Install Maturin
pip install maturin

# Build and install in development mode
maturin develop

# Or build a wheel for distribution
maturin build --release
```

## Usage

### Python API

CaDaR provides four main functions that match the requested API:

#### 1. `ara2bizi()` - Arabic to Latin/Bizi

```python
import cadar

# Convert Arabic script to Latin (Bizi)
result = cadar.ara2bizi("كيفاش داير؟", darija="Ma")
print(result)  # Output: "kifash dayer?"
```

#### 2. `bizi2ara()` - Latin/Bizi to Arabic

```python
import cadar

# Convert Latin script to Arabic
result = cadar.bizi2ara("salam 3likom", darija="Ma")
print(result)  # Output: "سلام عليكم"
```

#### 3. `ara2ara()` - Arabic Standardization

```python
import cadar

# Standardize Arabic text (remove diacritics, normalize characters)
result = cadar.ara2ara("أنَا مِنْ المَغْرِب", darija="Ma")
print(result)  # Output: "انا من المغرب"
```

#### 4. `bizi2bizi()` - Latin Standardization

```python
import cadar

# Standardize Latin text (fix repeated chars, normalize spelling)
result = cadar.bizi2bizi("salaaaam kifaaash", darija="Ma")
print(result)  # Output: "salam kifash"
```

### Using the CaDaR Class

For processing multiple texts with the same dialect, create a `CaDaR` instance:

```python
import cadar

# Create a processor for Moroccan Darija
processor = cadar.CaDaR(darija="Ma")

# Use the methods
arabic_text = processor.bizi2ara("wakha ghir shwiya")
latin_text = processor.ara2bizi("واخا غير شوية")
standardized = processor.ara2ara("أنَا كَنْتْكَلَّم دَارِيجَة")

print(f"Dialect: {processor.get_dialect()}")
```

### Convenience Functions

```python
import cadar

# Auto-detect and transliterate
result = cadar.transliterate("سلام", target="latin", darija="Ma")

# Auto-detect and standardize
result = cadar.standardize("salaaaam", script="auto", darija="Ma")
```

## Examples

### Common Darija Phrases

```python
import cadar

phrases = [
    "كيفاش داير؟",  # How are you?
    "بخير الحمد لله",  # Fine, thank God
    "شنو كدير؟",  # What are you doing?
    "غير كنقرا",  # Just studying
    "واخا نمشيو",  # Let's go
]

for phrase in phrases:
    latin = cadar.ara2bizi(phrase, darija="Ma")
    print(f"{phrase} → {latin}")
```

### Working with Mixed Text

```python
import cadar

# CaDaR handles mixed scripts gracefully
text = "ana men Morocco و نتكلم darija bzaf"

# Process each part appropriately
standardized = cadar.standardize(text, script="auto")
```

### Batch Processing

```python
import cadar

processor = cadar.CaDaR(darija="Ma")

texts = ["سلام", "بسلامة", "شكرا", "بزاف"]
results = [processor.ara2bizi(text) for text in texts]

print(results)  # ['slam', 'bslama', 'shokran', 'bzaf']
```

## Supported Dialects

Currently supported:
- **Ma** (Moroccan Darija) - Default

Planned for future releases:
- Algerian Darija
- Tunisian Darija
- Libyan Darija
- Egyptian Darija

## Technical Details

### Script Detection

CaDaR automatically detects the input script (Arabic, Latin, Mixed) and processes accordingly.

### Normalization

- **Arabic**: Removes diacritics, normalizes Alef variants, handles Teh Marbuta
- **Latin**: Normalizes common Darija Latin representations (3 → ع, 7 → ح, 9 → ق)

### Darija-Specific Features

- Recognition of Darija function words (من، في، ديال)
- Handling of Darija-specific constructs (بزاف، غير، واخا)
- Clitic splitting (prefixes like و، ف، ب، ل)

### ICR Phoneme Mapping

The ICR uses a standardized set of symbols:

| Arabic | Latin | ICR | Description |
|--------|-------|-----|-------------|
| ا | a | A | Alef |
| ب | b | B | Ba |
| ت | t | T | Ta |
| ع | 3 | ε | Ain |
| ح | 7 | Ḥ | Strong H |
| خ | kh | X | Kha |
| ش | sh | Š | Shin |
| غ | gh | Ġ | Ghain |

## Development

### Running Tests

```bash
# Rust tests
cargo test

# Python tests (after installation)
pytest tests/
```

### Building Documentation

```bash
# Rust documentation
cargo doc --open

# Python documentation
cd docs && make html
```

### Contributing

Contributions are welcome! Please see [CONTRIBUTING.md](CONTRIBUTING.md) for guidelines.

## Performance

CaDaR is built in Rust for high performance:

- **Transliteration**: ~1-2ms per sentence
- **Batch processing**: Scales linearly
- **Memory efficient**: Minimal allocations

## Roadmap

- [ ] Add support for more Darija dialects
- [ ] Implement advanced morphological analysis
- [ ] Create web API
- [ ] Add CLI tool
- [ ] Improve ICR with machine learning enhancements
- [ ] Build browser-based demo

## License

This project is licensed under the MIT License - see the [LICENSE](LICENSE) file for details.

## Citation

If you use CaDaR in your research, please cite:

```bibtex
@software{cadar2026,
  title={CaDaR: Canonicalization and Darija Representation},
  author={Ouail LAAMIRI},
  year={2026},
  url={https://github.com/Oit-Technologies/CaDaR}
}
```

## Acknowledgments

- Built with [PyO3](https://github.com/PyO3/pyo3) for Rust-Python interoperability
- Uses [Maturin](https://github.com/PyO3/maturin) for packaging

## Contact

- **Organization**: Oit Technologies
- **Repository**: [https://github.com/Oit-Technologies/CaDaR](https://github.com/Oit-Technologies/CaDaR)
- **Issues**: [https://github.com/Oit-Technologies/CaDaR/issues](https://github.com/Oit-Technologies/CaDaR/issues)

---

Made with ❤️ for the Darija community
