# CaDaR: Canonicalization and Darija Representation

[![PyPI version](https://badge.fury.io/py/cadar.svg)](https://pypi.org/project/cadar/)
[![Python 3.8+](https://img.shields.io/badge/python-3.8+-blue.svg)](https://www.python.org/downloads/)
[![License: MIT](https://img.shields.io/badge/License-MIT-yellow.svg)](https://opensource.org/licenses/MIT)

**High-performance bidirectional transliteration for Darija (Moroccan Arabic)**

CaDaR is a robust, FST-style (Finite State Transducer) transliteration library that provides seamless conversion between Arabic script and Latin (Romanized/Bizi) script for Darija, with text standardization capabilities.

## Features

- 🔄 **Bidirectional transliteration**: Arabic ↔ Latin
- 🎯 **Darija-aware processing**: Moroccan Arabic linguistic patterns
- 🚀 **High performance**: Rust core with Python bindings
- ✨ **Text standardization**: Normalize both Arabic and Latin text
- 🧪 **Well tested**: 41 passing unit tests

## Installation

```bash
pip install cadar
```

## Quick Start

### Arabic to Latin (Bizi)

```python
import cadar

result = cadar.ara2bizi("كيفاش داير؟", darija="Ma")
print(result)  # Output: "kifash dayer?"
```

### Latin to Arabic

```python
import cadar

result = cadar.bizi2ara("salam 3likom", darija="Ma")
print(result)  # Output: "سلام عليكم"
```

### Text Standardization

```python
import cadar

# Standardize Arabic (remove diacritics, normalize)
result = cadar.ara2ara("أنَا مِنْ المَغْرِب", darija="Ma")
print(result)  # Output: "انا من المغرب"

# Standardize Latin (fix repeated chars)
result = cadar.bizi2bizi("salaaaam", darija="Ma")
print(result)  # Output: "salam"
```

### Using the CaDaR Class

```python
import cadar

# Create a reusable processor
processor = cadar.CaDaR(darija="Ma")

# Convert between scripts
arabic = processor.bizi2ara("wakha ghir shwiya")
latin = processor.ara2bizi("واخا غير شوية")

print(f"Dialect: {processor.get_dialect()}")
```

## API Reference

### Main Functions

- **`ara2bizi(text, darija="Ma")`** - Convert Arabic to Latin script
- **`bizi2ara(text, darija="Ma")`** - Convert Latin to Arabic script
- **`ara2ara(text, darija="Ma")`** - Standardize Arabic text
- **`bizi2bizi(text, darija="Ma")`** - Standardize Latin text

### CaDaR Class

```python
processor = cadar.CaDaR(darija="Ma")
processor.ara2bizi(text)    # Arabic to Latin
processor.bizi2ara(text)    # Latin to Arabic
processor.ara2ara(text)     # Standardize Arabic
processor.bizi2bizi(text)   # Standardize Latin
processor.get_dialect()     # Get current dialect
```

### Convenience Functions

```python
# Auto-detect and transliterate
cadar.transliterate(text, target="latin", darija="Ma")

# Auto-detect and standardize
cadar.standardize(text, script="auto", darija="Ma")
```

## Use Cases

- **Chat Applications**: Support users writing in both scripts
- **Search Engines**: Match queries regardless of script
- **Data Processing**: Standardize mixed-script datasets
- **NLP Pipelines**: Normalize Darija text for machine learning
- **Language Learning**: See connections between scripts

## How It Works

CaDaR uses a 6-stage FST-style pipeline:

1. **Script Detection**: Identify Arabic, Latin, or mixed scripts
2. **Normalization**: Clean and standardize input
3. **Tokenization**: Darija-aware word segmentation
4. **ICR Generation**: Convert to Intermediate Canonical Representation
5. **Script Generation**: Produce target script output
6. **Validation**: Apply final fixes and quality checks

The **Intermediate Canonical Representation (ICR)** is the core innovation - a script-independent phonological representation that enables accurate bidirectional conversion.

## Supported Dialects

- **Ma** (Moroccan Darija) - Default

*Support for Algerian, Tunisian, Libyan, and Egyptian dialects planned for future releases.*

## Examples

### Chat Normalization

```python
import cadar

def normalize_message(text):
    """Normalize user input regardless of script"""
    has_arabic = any('\u0600' <= c <= '\u06FF' for c in text)

    if has_arabic:
        return cadar.ara2ara(text, darija="Ma")
    else:
        return cadar.bizi2bizi(text, darija="Ma")

# Usage
user_input = "salaaaam 3likooom"
normalized = normalize_message(user_input)
print(normalized)  # "salam 3likom"
```

### Search Variants

```python
import cadar

def generate_search_variants(query):
    """Generate search terms in both scripts"""
    processor = cadar.CaDaR(darija="Ma")

    has_arabic = any('\u0600' <= c <= '\u06FF' for c in query)

    if has_arabic:
        return [
            query,
            processor.ara2bizi(query),
            processor.ara2ara(query)
        ]
    else:
        return [
            query,
            processor.bizi2ara(query),
            processor.bizi2bizi(query)
        ]

# Usage
variants = generate_search_variants("سلام")
print(variants)  # ['سلام', 'slam', 'سلام']
```

### Batch Processing

```python
import cadar

processor = cadar.CaDaR(darija="Ma")

texts = ["سلام", "بسلامة", "شكرا", "بزاف"]
results = [processor.ara2bizi(text) for text in texts]

print(results)  # ['slam', 'bslama', 'shokran', 'bzaf']
```

## Performance

- **Fast**: ~1-2ms per sentence
- **Efficient**: Rust core with minimal overhead
- **Scalable**: Linear scaling for batch processing

## Documentation

- **Full Documentation**: [https://oit-technologies.github.io/CaDaR/](https://oit-technologies.github.io/CaDaR/)
- **GitHub Repository**: [https://github.com/Oit-Technologies/CaDaR](https://github.com/Oit-Technologies/CaDaR)
- **API Reference**: [https://oit-technologies.github.io/CaDaR/api/python/](https://oit-technologies.github.io/CaDaR/api/python/)

## License

MIT License - see [LICENSE](https://github.com/Oit-Technologies/CaDaR/blob/main/LICENSE) file for details.

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

## Support

- **Issues**: [GitHub Issues](https://github.com/Oit-Technologies/CaDaR/issues)
- **Documentation**: [https://oit-technologies.github.io/CaDaR/](https://oit-technologies.github.io/CaDaR/)

---

Made with ❤️ for the Darija community by [Oit Technologies](https://github.com/Oit-Technologies)
