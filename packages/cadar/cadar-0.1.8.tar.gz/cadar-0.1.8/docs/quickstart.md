# Quick Start

Get up and running with CaDaR in 5 minutes!

## Installation

### From PyPI

```bash
pip install cadar
```

### From Source

```bash
git clone https://github.com/Oit-Technologies/CaDaR.git
cd CaDaR
pip install maturin
maturin develop
```

## Basic Usage

### Import the Library

```python
import cadar
```

### Arabic to Latin Translation

```python
# Convert Arabic script to Latin (Bizi)
result = cadar.ara2bizi("كيفاش داير؟", darija="Ma")
print(result)
# Output: "kifash dayer?"
```

### Latin to Arabic Translation

```python
# Convert Latin script to Arabic
result = cadar.bizi2ara("salam 3likom", darija="Ma")
print(result)
# Output: "سلام عليكم"
```

### Text Standardization

```python
# Standardize Arabic text (remove diacritics)
result = cadar.ara2ara("أنَا مِنْ المَغْرِب", darija="Ma")
print(result)
# Output: "انا من المغرب"

# Standardize Latin text (fix repeated chars)
result = cadar.bizi2bizi("salaaaam", darija="Ma")
print(result)
# Output: "salam"
```

### Using the CaDaR Class

```python
# Create a reusable processor
processor = cadar.CaDaR(darija="Ma")

# Use it for multiple operations
arabic = processor.bizi2ara("wakha")
latin = processor.ara2bizi("واخا")

print(f"Dialect: {processor.get_dialect()}")
# Output: "Moroccan Darija"
```

## Common Examples

### Chat Application

```python
def process_user_message(message):
    """Detect and normalize user input"""
    # Auto-detect script
    has_arabic = any('\u0600' <= c <= '\u06FF' for c in message)

    if has_arabic:
        # Normalize Arabic
        return cadar.ara2ara(message, darija="Ma")
    else:
        # Normalize Latin
        return cadar.bizi2bizi(message, darija="Ma")

user_input = "سلااااام"
normalized = process_user_message(user_input)
print(normalized)  # "سلام"
```

### Search Engine

```python
def create_search_variants(query):
    """Generate search variants in both scripts"""
    processor = cadar.CaDaR(darija="Ma")

    variants = set()

    # Add original query
    variants.add(query)

    # Detect script and generate variants
    has_arabic = any('\u0600' <= c <= '\u06FF' for c in query)

    if has_arabic:
        # Generate Latin variant
        variants.add(processor.ara2bizi(query))
        # Standardized Arabic
        variants.add(processor.ara2ara(query))
    else:
        # Generate Arabic variant
        variants.add(processor.bizi2ara(query))
        # Standardized Latin
        variants.add(processor.bizi2bizi(query))

    return list(variants)

query = "سلام"
print(create_search_variants(query))
# ['سلام', 'slam', 'سلام']
```

## Next Steps

- [Read the full User Guide](guide/overview.md)
- [Explore the API Reference](api/python.md)
- [Check out more examples](guide/examples.md)
- [Learn about the architecture](guide/architecture.md)
