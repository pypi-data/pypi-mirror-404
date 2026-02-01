# Examples

Practical examples of using CaDaR in real-world applications.

## Basic Transliteration

### Arabic to Latin

```python
import cadar

# Simple greeting
result = cadar.ara2bizi("السلام عليكم", darija="Ma")
print(result)  # "salam 3likom"

# Questions
result = cadar.ara2bizi("كيفاش داير؟", darija="Ma")
print(result)  # "kifash dayer?"

# Common phrases
result = cadar.ara2bizi("واخا غير شوية", darija="Ma")
print(result)  # "wakha ghir shwiya"
```

### Latin to Arabic

```python
import cadar

# With numbers as Arabic letters
result = cadar.bizi2ara("salam 3likom", darija="Ma")
print(result)  # "سلام عليكم"

# Common responses
result = cadar.bizi2ara("wakha", darija="Ma")
print(result)  # "واخا"

result = cadar.bizi2ara("bslama", darija="Ma")
print(result)  # "بسلامة"
```

## Text Standardization

### Cleaning Arabic Text

```python
import cadar

# Remove diacritics
text = "أَنَا مِنْ المَغْرِبْ"
result = cadar.ara2ara(text, darija="Ma")
print(result)  # "انا من المغرب"

# Normalize variations
text = "إِسْتَقْلاَل"
result = cadar.ara2ara(text, darija="Ma")
print(result)  # "استقلال"
```

### Cleaning Latin Text

```python
import cadar

# Fix repeated characters (common in chat)
result = cadar.bizi2bizi("salaaaam", darija="Ma")
print(result)  # "salam"

result = cadar.bizi2bizi("hhhhhhh", darija="Ma")
print(result)  # "hh"
```

## Chat Application

Normalize user messages regardless of script:

```python
import cadar

def normalize_chat_message(text):
    """Normalize user input for consistent storage/search"""
    # Detect if text contains Arabic
    has_arabic = any('\u0600' <= c <= '\u06FF' for c in text)

    if has_arabic:
        return cadar.ara2ara(text, darija="Ma")
    else:
        return cadar.bizi2bizi(text, darija="Ma")

# Usage
messages = [
    "salaaaam 3likooom",
    "السَّلاَمْ عَلَيْكُمْ",
    "kiiiifash daaaaayer?",
]

for msg in messages:
    normalized = normalize_chat_message(msg)
    print(f"{msg:30s} → {normalized}")
```

Output:
```
salaaaam 3likooom               → salam 3likom
السَّلاَمْ عَلَيْكُمْ           → السلام عليكم
kiiiifash daaaaayer?           → kifash dayer?
```

## Search Engine

Generate search variants in both scripts:

```python
import cadar

def generate_search_variants(query):
    """Generate search terms in both scripts for better matching"""
    processor = cadar.CaDaR(darija="Ma")

    # Detect script
    has_arabic = any('\u0600' <= c <= '\u06FF' for c in query)

    variants = set()

    if has_arabic:
        # Original Arabic
        variants.add(query)
        # Standardized Arabic
        variants.add(processor.ara2ara(query))
        # Latin transliteration
        variants.add(processor.ara2bizi(query))
    else:
        # Original Latin
        variants.add(query)
        # Standardized Latin
        variants.add(processor.bizi2bizi(query))
        # Arabic transliteration
        variants.add(processor.bizi2ara(query))

    return list(variants)

# Usage
query = "سلام"
variants = generate_search_variants(query)
print(f"Search variants for '{query}':")
for v in variants:
    print(f"  - {v}")
```

Output:
```
Search variants for 'سلام':
  - سلام
  - slam
```

## Batch Processing

Process multiple texts efficiently:

```python
import cadar

processor = cadar.CaDaR(darija="Ma")

# List of Arabic texts
arabic_texts = [
    "سلام",
    "بسلامة",
    "شكرا",
    "بزاف",
    "واخا"
]

# Convert all to Latin
latin_results = [processor.ara2bizi(text) for text in arabic_texts]

print("Arabic → Latin:")
for ar, la in zip(arabic_texts, latin_results):
    print(f"  {ar:10s} → {la}")
```

Output:
```
Arabic → Latin:
  سلام       → slam
  بسلامة     → bslama
  شكرا       → shokran
  بزاف       → bzaf
  واخا       → wakha
```

## Data Pipeline

Standardize a mixed-script dataset:

```python
import cadar
import pandas as pd

# Sample dataset
data = pd.DataFrame({
    'message': [
        'salaaaam',
        'السَّلاَم',
        'kiiiifash',
        'كِيفَاش',
        'waaaakha'
    ]
})

processor = cadar.CaDaR(darija="Ma")

def standardize_text(text):
    """Detect and standardize text"""
    has_arabic = any('\u0600' <= c <= '\u06FF' for c in text)
    if has_arabic:
        return processor.ara2ara(text)
    else:
        return processor.bizi2bizi(text)

# Apply standardization
data['standardized'] = data['message'].apply(standardize_text)

print(data)
```

Output:
```
      message standardized
0   salaaaam        salam
1    السَّلاَم       السلام
2  kiiiifash       kifash
3      كِيفَاش        كيفاش
4   waaaakha        wakha
```

## Round-Trip Conversion

Test conversion accuracy:

```python
import cadar

processor = cadar.CaDaR(darija="Ma")

# Start with Arabic
original = "سلام عليكم"
print(f"Original Arabic: {original}")

# Convert to Latin
latin = processor.ara2bizi(original)
print(f"Latin:           {latin}")

# Convert back to Arabic
back_to_arabic = processor.bizi2ara(latin)
print(f"Back to Arabic:  {back_to_arabic}")

# Standardize both for comparison
orig_std = processor.ara2ara(original)
back_std = processor.ara2ara(back_to_arabic)
print(f"\nStandardized match: {orig_std == back_std}")
```

## Error Handling

Handle invalid input gracefully:

```python
import cadar

try:
    # Invalid dialect
    result = cadar.ara2bizi("سلام", darija="InvalidDialect")
except ValueError as e:
    print(f"Error: {e}")

try:
    # Empty input
    result = cadar.ara2bizi("", darija="Ma")
    print(f"Empty result: '{result}'")
except Exception as e:
    print(f"Error: {e}")
```

For more information, see the [Python API documentation](python-api.md).
