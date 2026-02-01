#!/usr/bin/env python3
"""
Generate Python API documentation for CaDaR
"""

import os
import sys

# Add parent directory to path to import cadar
sys.path.insert(0, os.path.join(os.path.dirname(__file__), '..'))

try:
    import cadar
except ImportError:
    print("Error: cadar module not found. Please build it first with 'maturin develop'")
    sys.exit(1)


def generate_python_api_docs():
    """Generate Python API reference documentation"""

    api_doc = """# Python API Reference

## Overview

CaDaR provides a simple Python API for bidirectional Darija transliteration.

## Module: `cadar`

The main module providing transliteration functions and classes.

---

## Functions

### `ara2bizi(text, darija="Ma")`

Convert Arabic script to Latin (Bizi) script.

**Parameters:**

- `text` (str): Input text in Arabic script
- `darija` (str, optional): Dialect code. Default: "Ma" (Moroccan Darija)

**Returns:**

- `str`: Text in Latin (Bizi) script

**Raises:**

- `ValueError`: If the input is invalid or empty

**Example:**

```python
import cadar

result = cadar.ara2bizi("كيفاش داير؟", darija="Ma")
print(result)  # Output: "kifash dayer?"
```

---

### `bizi2ara(text, darija="Ma")`

Convert Latin (Bizi) script to Arabic script.

**Parameters:**

- `text` (str): Input text in Latin (Bizi) script
- `darija` (str, optional): Dialect code. Default: "Ma" (Moroccan Darija)

**Returns:**

- `str`: Text in Arabic script

**Raises:**

- `ValueError`: If the input is invalid or empty

**Example:**

```python
import cadar

result = cadar.bizi2ara("salam 3likom", darija="Ma")
print(result)  # Output: "سلام عليكم"
```

---

### `ara2ara(text, darija="Ma")`

Standardize Arabic text (removes diacritics, normalizes characters).

**Parameters:**

- `text` (str): Input text in Arabic script
- `darija` (str, optional): Dialect code. Default: "Ma" (Moroccan Darija)

**Returns:**

- `str`: Standardized text in Arabic script

**Raises:**

- `ValueError`: If the input is invalid or empty

**Example:**

```python
import cadar

result = cadar.ara2ara("أنَا مِنْ المَغْرِب", darija="Ma")
print(result)  # Output: "انا من المغرب"
```

---

### `bizi2bizi(text, darija="Ma")`

Standardize Latin (Bizi) text (fixes repeated characters, normalizes spelling).

**Parameters:**

- `text` (str): Input text in Latin (Bizi) script
- `darija` (str, optional): Dialect code. Default: "Ma" (Moroccan Darija)

**Returns:**

- `str`: Standardized text in Latin (Bizi) script

**Raises:**

- `ValueError`: If the input is invalid or empty

**Example:**

```python
import cadar

result = cadar.bizi2bizi("salaaaam", darija="Ma")
print(result)  # Output: "salam"
```

---

### `transliterate(text, target="latin", darija="Ma")`

General-purpose transliteration function with auto-detection.

**Parameters:**

- `text` (str): Input text to transliterate
- `target` (str, optional): Target script - "latin" or "arabic". Default: "latin"
- `darija` (str, optional): Dialect code. Default: "Ma"

**Returns:**

- `str`: Transliterated text

**Raises:**

- `ValueError`: If the target script is unknown

**Example:**

```python
import cadar

result = cadar.transliterate("سلام", target="latin")
print(result)  # Output: "slam"
```

---

### `standardize(text, script="auto", darija="Ma")`

Standardize text in the same script.

**Parameters:**

- `text` (str): Input text to standardize
- `script` (str, optional): Script type - "arabic", "latin", or "auto". Default: "auto"
- `darija` (str, optional): Dialect code. Default: "Ma"

**Returns:**

- `str`: Standardized text

**Raises:**

- `ValueError`: If the script is unknown

**Example:**

```python
import cadar

result = cadar.standardize("salaaaam", script="auto")
print(result)  # Output: "salam"
```

---

## Classes

### `class CaDaR(darija="Ma")`

Main CaDaR processor class for reusable transliteration operations.

**Parameters:**

- `darija` (str, optional): Dialect code. Default: "Ma" (Moroccan Darija)

**Methods:**

#### `ara2bizi(text)`

Convert Arabic script to Latin (Bizi) script.

**Parameters:**

- `text` (str): Input text in Arabic script

**Returns:**

- `str`: Text in Latin (Bizi) script

**Example:**

```python
processor = cadar.CaDaR(darija="Ma")
result = processor.ara2bizi("مرحبا")
print(result)  # Output: "mr7ba"
```

#### `bizi2ara(text)`

Convert Latin (Bizi) script to Arabic script.

**Parameters:**

- `text` (str): Input text in Latin (Bizi) script

**Returns:**

- `str`: Text in Arabic script

**Example:**

```python
processor = cadar.CaDaR(darija="Ma")
result = processor.bizi2ara("salam")
print(result)  # Output: "سلام"
```

#### `ara2ara(text)`

Standardize Arabic text.

**Parameters:**

- `text` (str): Input text in Arabic script

**Returns:**

- `str`: Standardized text in Arabic script

**Example:**

```python
processor = cadar.CaDaR(darija="Ma")
result = processor.ara2ara("أنَا مِنْ المَغْرِب")
print(result)  # Output: "انا من المغرب"
```

#### `bizi2bizi(text)`

Standardize Latin (Bizi) text.

**Parameters:**

- `text` (str): Input text in Latin (Bizi) script

**Returns:**

- `str`: Standardized text in Latin (Bizi) script

**Example:**

```python
processor = cadar.CaDaR(darija="Ma")
result = processor.bizi2bizi("salaaaam")
print(result)  # Output: "salam"
```

#### `get_dialect()`

Get the current dialect name.

**Returns:**

- `str`: Dialect name (e.g., "Moroccan Darija")

**Example:**

```python
processor = cadar.CaDaR(darija="Ma")
print(processor.get_dialect())  # Output: "Moroccan Darija"
```

---

## Module Attributes

### `__version__`

The version of the CaDaR library.

**Type:** `str`

**Example:**

```python
import cadar
print(cadar.__version__)  # Output: "0.1.0"
```

### `__author__`

The author of the CaDaR library.

**Type:** `str`

**Example:**

```python
import cadar
print(cadar.__author__)  # Output: "Oit Technologies"
```

---

## Supported Dialects

Currently supported dialect codes:

- `"Ma"`: Moroccan Darija (default)
- `"moroccan"`: Moroccan Darija (alias)
- `"morocco"`: Moroccan Darija (alias)

Future releases will add support for:

- Algerian Darija
- Tunisian Darija
- Libyan Darija
- Egyptian Darija

---

## Error Handling

All functions raise `ValueError` for:

- Empty input text
- Invalid dialect codes
- Malformed text that cannot be processed

**Example:**

```python
import cadar

try:
    result = cadar.ara2bizi("", darija="Ma")
except ValueError as e:
    print(f"Error: {e}")
```

---

## Performance Tips

1. **Reuse the CaDaR instance** for multiple operations:
   ```python
   processor = cadar.CaDaR(darija="Ma")
   for text in texts:
       result = processor.ara2bizi(text)
   ```

2. **Batch processing** for large datasets:
   ```python
   results = [cadar.ara2bizi(text, darija="Ma") for text in texts]
   ```

3. **Use the appropriate function** - standardizers are faster than transliterators:
   ```python
   # If you just need to normalize, use ara2ara instead of ara2bizi then bizi2ara
   normalized = cadar.ara2ara(text, darija="Ma")
   ```
"""

    # Write to file
    output_path = os.path.join(os.path.dirname(__file__), 'api', 'python.md')
    os.makedirs(os.path.dirname(output_path), exist_ok=True)

    with open(output_path, 'w', encoding='utf-8') as f:
        f.write(api_doc)

    print(f"✓ Generated Python API documentation: {output_path}")


if __name__ == '__main__':
    generate_python_api_docs()
