# Python API Reference

Complete API reference for CaDaR's Python interface.

## Module: cadar

### Functions

#### ara2bizi(text, darija="Ma")

Convert Arabic script to Latin (Bizi) script.

**Parameters:**

- `text` (str): Input text in Arabic script
- `darija` (str, optional): Dialect code. Default: "Ma" (Moroccan Darija)

**Returns:**

- `str`: Transliterated text in Latin script

**Raises:**

- `ValueError`: If dialect code is invalid or text cannot be processed

**Example:**

```python
import cadar

result = cadar.ara2bizi("كيفاش داير؟", darija="Ma")
print(result)  # Output: "kifash dayer?"
```

---

#### bizi2ara(text, darija="Ma")

Convert Latin (Bizi) script to Arabic script.

**Parameters:**

- `text` (str): Input text in Latin script
- `darija` (str, optional): Dialect code. Default: "Ma"

**Returns:**

- `str`: Transliterated text in Arabic script

**Raises:**

- `ValueError`: If dialect code is invalid or text cannot be processed

**Example:**

```python
import cadar

result = cadar.bizi2ara("salam 3likom", darija="Ma")
print(result)  # Output: "سلام عليكم"
```

---

#### ara2ara(text, darija="Ma")

Standardize Arabic text by removing diacritics and normalizing characters.

**Parameters:**

- `text` (str): Input text in Arabic script
- `darija` (str, optional): Dialect code. Default: "Ma"

**Returns:**

- `str`: Standardized Arabic text

**Raises:**

- `ValueError`: If dialect code is invalid or text cannot be processed

**Example:**

```python
import cadar

result = cadar.ara2ara("أنَا مِنْ المَغْرِب", darija="Ma")
print(result)  # Output: "انا من المغرب"
```

---

#### bizi2bizi(text, darija="Ma")

Standardize Latin text by fixing repeated characters and normalizing.

**Parameters:**

- `text` (str): Input text in Latin script
- `darija` (str, optional): Dialect code. Default: "Ma"

**Returns:**

- `str`: Standardized Latin text

**Raises:**

- `ValueError`: If dialect code is invalid or text cannot be processed

**Example:**

```python
import cadar

result = cadar.bizi2bizi("salaaaam", darija="Ma")
print(result)  # Output: "salam"
```

---

### Class: CaDaR

Reusable processor for multiple transliteration operations.

#### Constructor

```python
CaDaR(darija="Ma")
```

**Parameters:**

- `darija` (str, optional): Dialect code. Default: "Ma"

**Example:**

```python
import cadar

processor = cadar.CaDaR(darija="Ma")
```

#### Methods

##### ara2bizi(text)

Convert Arabic to Latin script.

**Parameters:**

- `text` (str): Input text in Arabic script

**Returns:**

- `str`: Transliterated text

**Example:**

```python
processor = cadar.CaDaR(darija="Ma")
result = processor.ara2bizi("واخا غير شوية")
print(result)  # Output: "wakha ghir shwiya"
```

---

##### bizi2ara(text)

Convert Latin to Arabic script.

**Parameters:**

- `text` (str): Input text in Latin script

**Returns:**

- `str`: Transliterated text

**Example:**

```python
processor = cadar.CaDaR(darija="Ma")
result = processor.bizi2ara("wakha")
print(result)  # Output: "واخا"
```

---

##### ara2ara(text)

Standardize Arabic text.

**Parameters:**

- `text` (str): Input text in Arabic script

**Returns:**

- `str`: Standardized text

**Example:**

```python
processor = cadar.CaDaR(darija="Ma")
result = processor.ara2ara("سَلاَم")
print(result)  # Output: "سلام"
```

---

##### bizi2bizi(text)

Standardize Latin text.

**Parameters:**

- `text` (str): Input text in Latin script

**Returns:**

- `str`: Standardized text

**Example:**

```python
processor = cadar.CaDaR(darija="Ma")
result = processor.bizi2bizi("salaaaam")
print(result)  # Output: "salam"
```

---

##### get_dialect()

Get the current dialect code.

**Returns:**

- `str`: Dialect code (e.g., "Ma")

**Example:**

```python
processor = cadar.CaDaR(darija="Ma")
print(processor.get_dialect())  # Output: "Ma"
```

---

### Module Attributes

#### __version__

Current version of the CaDaR package.

```python
import cadar
print(cadar.__version__)  # e.g., "0.1.0"
```

#### __author__

Package author information.

```python
import cadar
print(cadar.__author__)  # "Oit Technologies"
```

---

## Supported Dialect Codes

| Code | Dialect | Status |
|------|---------|--------|
| `Ma` | Moroccan Darija | ✅ Supported |

Future support planned for:
- Algerian Darija
- Tunisian Darija
- Libyan Darija
- Egyptian Arabic

---

## Error Handling

All functions may raise `ValueError` for:

- Invalid dialect codes
- Malformed input text
- Internal processing errors

**Example:**

```python
import cadar

try:
    result = cadar.ara2bizi("سلام", darija="INVALID")
except ValueError as e:
    print(f"Error: {e}")
```

---

## Type Hints

The module includes type hints for better IDE support:

```python
from typing import Optional

def ara2bizi(text: str, darija: str = "Ma") -> str: ...
def bizi2ara(text: str, darija: str = "Ma") -> str: ...
def ara2ara(text: str, darija: str = "Ma") -> str: ...
def bizi2bizi(text: str, darija: str = "Ma") -> str: ...
```

---

## Rust API Documentation

For developers interested in the Rust implementation, the complete Rust API documentation is also generated and available in the deployed documentation.

The Rust API includes:
- Core library modules
- Internal pipeline stages
- Type definitions
- Implementation details

You can access it by navigating to `/rust/cadar/index.html` in the deployed documentation site.

---

## See Also

- [User Guide](../guide/python-api.md) - Practical usage examples
- [Examples](../guide/examples.md) - Real-world use cases
- [Architecture](../guide/architecture.md) - How CaDaR works internally
