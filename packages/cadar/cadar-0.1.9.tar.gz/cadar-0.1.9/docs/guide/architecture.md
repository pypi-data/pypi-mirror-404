# Architecture

CaDaR is built with a modular FST-style (Finite State Transducer) pipeline architecture that ensures clean separation of concerns and makes each stage testable and maintainable.

## Pipeline Stages

### Stage 1: Script Detection

Identifies the script of the input text:
- Arabic script (U+0600-U+06FF)
- Latin script (ASCII + extended Latin)
- Mixed script
- Numbers and punctuation

**Module:** `src/stages/script_detection.rs`

### Stage 2: Normalization

Cleans and standardizes input text:
- Unicode normalization (NFC)
- Removes invisible characters
- Fixes whitespace
- Handles repeated characters
- Normalizes Arabic forms (ا إ أ آ → ا)

**Module:** `src/stages/normalization.rs`

### Stage 3: Tokenization

Darija-aware word segmentation:
- Clitic splitting (و، ف، ب، ال)
- Function word detection
- Handles Latin numbers in Arabic text (3 → ع)
- Preserves punctuation

**Module:** `src/stages/tokenization.rs`

### Stage 4: ICR Generation

Converts tokens to Intermediate Canonical Representation:
- Script-independent phonological representation
- Preserves Darija-specific sounds
- Maintains semantic information
- Handles special cases

**Module:** `src/stages/icr.rs`

### Stage 5: Script Generation

Produces target script from ICR:
- Arabic script generation from phonemes
- Latin script generation from phonemes
- Handles special characters
- Preserves spacing and punctuation

**Module:** `src/stages/script_generation.rs`

### Stage 6: Validation

Final quality checks and fixes:
- Fixes double characters
- Adjusts spacing
- Applies Darija-specific patterns
- Validates output

**Module:** `src/stages/validation.rs`

## Intermediate Canonical Representation (ICR)

The ICR is the central innovation that enables bidirectional conversion:

```rust
pub struct ICR {
    pub segments: Vec<ICRSegment>,
    pub dialect: Dialect,
    pub metadata: ICRMetadata,
}

pub struct ICRSegment {
    pub canonical: String,    // Phonological form
    pub original: String,     // Original text
    pub segment_type: SegmentType,
    pub confidence: f64,
}
```

### Phoneme Mapping Examples

Arabic to ICR:
- ا → "A"
- ب → "b"
- ت → "t"
- ع → "ε"
- ح → "Ḥ"
- خ → "x"

Latin to ICR:
- a → "A"
- b → "b"
- 3 → "ε"
- 7 → "Ḥ"
- kh → "x"

## Implementation Details

### Rust Core

CaDaR is implemented in Rust for:
- High performance
- Memory safety
- Type safety
- Zero-cost abstractions

**Main module:** `src/lib.rs`

### Python Bindings

Python bindings use PyO3:
- Seamless integration
- Native performance
- Idiomatic Python API
- No dependencies required

**Bindings module:** `src/python_bindings.rs`

### Build System

Uses Maturin for building Python wheels:
- Cross-platform support
- PyPI-ready packages
- Automatic wheel generation

## Design Principles

1. **Modularity** - Each stage is independent and testable
2. **Type Safety** - Strong typing throughout the pipeline
3. **Performance** - Optimized for speed and memory efficiency
4. **Extensibility** - Easy to add new dialects and features
5. **Reliability** - Comprehensive test coverage (41 tests)

## Performance Characteristics

- **Speed:** ~1-2ms per sentence
- **Memory:** Linear with input size
- **Scalability:** Handles batch processing efficiently

For implementation examples, see the [Examples](examples.md) page.
