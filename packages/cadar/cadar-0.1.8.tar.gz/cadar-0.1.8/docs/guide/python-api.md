# Python API

CaDaR provides a simple and intuitive Python API for transliteration and text standardization.

## Functions

### ara2bizi()

Convert Arabic script to Latin (Bizi) script.

```python
import cadar

result = cadar.ara2bizi("كيفاش داير؟", darija="Ma")
print(result)  # Output: "kifash dayer?"
```

**Parameters:**
- `text` (str): Input text in Arabic script
- `darija` (str): Dialect code (default: "Ma" for Moroccan Darija)

**Returns:** `str` - Transliterated text in Latin script

---

### bizi2ara()

Convert Latin (Bizi) script to Arabic script.

```python
import cadar

result = cadar.bizi2ara("salam 3likom", darija="Ma")
print(result)  # Output: "سلام عليكم"
```

**Parameters:**
- `text` (str): Input text in Latin script
- `darija` (str): Dialect code (default: "Ma")

**Returns:** `str` - Transliterated text in Arabic script

---

### ara2ara()

Standardize Arabic text (remove diacritics, normalize characters).

```python
import cadar

result = cadar.ara2ara("أنَا مِنْ المَغْرِب", darija="Ma")
print(result)  # Output: "انا من المغرب"
```

**Parameters:**
- `text` (str): Input text in Arabic script
- `darija` (str): Dialect code (default: "Ma")

**Returns:** `str` - Standardized Arabic text

---

### bizi2bizi()

Standardize Latin text (fix repeated characters, normalize).

```python
import cadar

result = cadar.bizi2bizi("salaaaam", darija="Ma")
print(result)  # Output: "salam"
```

**Parameters:**
- `text` (str): Input text in Latin script
- `darija` (str): Dialect code (default: "Ma")

**Returns:** `str` - Standardized Latin text

---

## CaDaR Class

For multiple operations, create a reusable processor:

```python
import cadar

processor = cadar.CaDaR(darija="Ma")

# Convert between scripts
arabic = processor.bizi2ara("wakha ghir shwiya")
latin = processor.ara2bizi("واخا غير شوية")

# Standardize text
clean_arabic = processor.ara2ara("سَلاَمْ")
clean_latin = processor.bizi2bizi("salaaaam")

# Get dialect info
print(processor.get_dialect())  # Output: "Ma"
```

**Methods:**
- `ara2bizi(text)` - Arabic to Latin
- `bizi2ara(text)` - Latin to Arabic
- `ara2ara(text)` - Standardize Arabic
- `bizi2bizi(text)` - Standardize Latin
- `get_dialect()` - Get current dialect

---

## Supported Dialects

Currently supported:
- **Ma** - Moroccan Darija (default)

Future support planned for:
- Algerian Darija
- Tunisian Darija
- Libyan Darija
- Egyptian Arabic

---

## Error Handling

All functions may raise exceptions for invalid input:

```python
try:
    result = cadar.ara2bizi("سلام", darija="Invalid")
except ValueError as e:
    print(f"Error: {e}")
```

For more examples, see the [Examples](examples.md) page.
