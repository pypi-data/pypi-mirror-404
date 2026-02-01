# Overview

CaDaR (Canonicalization and Darija Representation) is a high-performance bidirectional transliteration library for Darija (Moroccan Arabic).

## Architecture

CaDaR uses a 6-stage FST-style (Finite State Transducer) pipeline:

1. **Script Detection** - Identifies Arabic, Latin, or mixed scripts
2. **Normalization** - Cleans and standardizes input text
3. **Tokenization** - Darija-aware word segmentation
4. **ICR Generation** - Converts to Intermediate Canonical Representation
5. **Script Generation** - Produces target script output
6. **Validation** - Applies final fixes and quality checks

## Intermediate Canonical Representation (ICR)

The ICR is the core innovation of CaDaR - a script-independent phonological representation that enables accurate bidirectional conversion between Arabic and Latin scripts.

## Key Features

- Bidirectional transliteration (Arabic ↔ Latin)
- Text standardization for both scripts
- Darija-specific linguistic patterns
- High performance with Rust core
- Easy-to-use Python API

## Use Cases

- Chat applications with mixed-script input
- Search engines requiring script-agnostic matching
- Data processing for Darija datasets
- NLP pipelines for Moroccan Arabic
- Language learning tools

For more details, see:
- [Python API Guide](python-api.md)
- [Architecture Details](architecture.md)
- [Examples](examples.md)
