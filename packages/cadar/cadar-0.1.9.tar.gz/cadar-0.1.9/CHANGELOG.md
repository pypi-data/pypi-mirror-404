# Changelog

All notable changes to this project will be documented in this file.

The format is based on [Keep a Changelog](https://keepachangelog.com/en/1.0.0/),
and this project adheres to [Semantic Versioning](https://semver.org/spec/v2.0.0.html).

## [Unreleased]

## [0.1.9] - 2026-01-31

### Added

- **Smart vowel handling system** (`src/linguistic/vowels.rs`)
  - Distinguishes between long vowels (aa, ee, ii, oo, uu) and short vowels (a, e, i, o, u)
  - `VowelMode::Darija` for readable informal writing
  - `VowelMode::Standard` for strict Arabic orthography
  - Automatic vowel length detection for Latin input
  - Context-aware vowel writing based on position (start/middle/end)

- **Darija Mode** (default): More readable vowel writing
  - Writes short 'a', 'o', 'u' in middle positions for clarity
  - Skips short 'e', 'i' in middle (absorbed by consonants)
  - Examples:
    - `"salam"` → `"سالام"` (writes middle 'a's)
    - `"imken"` → `"يمكن"` (skips middle 'e')
    - `"daba"` → `"دابا"` (writes middle 'a')

- **Proper long vowel handling**:
  - `"salaam"` (long aa) → `"سالام"`
  - `"salam"` (short a) → `"سالام"`
  - `"kaatb"` → `"كاتب"` (long aa in middle)
  - Double vowels correctly collapsed to single matres lectionis

### Fixed

- ✅ **Critical**: `"imken"` now correctly produces `"يمكن"` (was `"يمكين"`)
- ✅ Short vowels followed by another vowel are properly skipped
- ✅ Vowel position detection (start/middle/end) now accurate
- ✅ Long vs short vowel distinction maintained

### Changed

- Default vowel mode is now **Darija** (more readable)
- Vowel writing rules adapted for informal Darija orthography
- Updated ICR builder to use smart vowel analysis
- Enhanced test suite with vowel mode tests (78 tests total)

### Bidirectional Conversion

- ✅ Arabic → Latin → Arabic: Perfect round-trip preservation
- ✅ Latin → Arabic: Proper Darija-style vowel writing
- ⚠️ Latin → Arabic → Latin: May normalize long vowels (acceptable for informal Darija)

## [0.1.8] - 2026-01-31

### Added

- **Bidirectional punctuation mapping**: Proper conversion between Latin and Arabic punctuation marks
  - Latin → Arabic: `?` → `؟`, `,` → `،`, `;` → `؛`
  - Arabic → Latin: `؟` → `?`, `،` → `,`, `؛` → `;`
  - Common punctuation preserved: `.`, `!`, `:`, `()`, `[]`, `{}`, `"`, `'`, `-`, `/`
- Arabic punctuation support in tokenization (؟، ؛)
- Punctuation classification in ICR character segmentation
- Comprehensive punctuation conversion tests (2 new unit tests)

### Fixed

- Punctuation marks now properly classified as `SegmentType::Punctuation` instead of consonants
- Whitespace correctly classified as `SegmentType::Whitespace` (not `Punctuation`)
- Punctuation preservation in canonical ICR representation
- Latin validator now accepts standalone punctuation marks
- Arabic validator now accepts Arabic punctuation marks

### Changed

- Updated `classify_latin_char()` and `classify_arabic_char()` to properly classify punctuation
- Updated `latin_char_to_canonical()` and `arabic_char_to_canonical()` to preserve punctuation
- Updated tokenization to handle both ASCII and Arabic punctuation
- Enhanced validation to accept punctuation in both Latin and Arabic text

## [0.1.7] - 2026-01-31

### Fixed

- **Critical**: Fixed validator incorrectly rejecting valid numbers in mixed text
  - Numbers (20, 0, 2, 15) now properly validated when appearing as separate tokens
  - Pure punctuation (., !, ?, ,) now accepted in Arabic text
  - Date/number patterns with separators (12/20, 2,15) now validated correctly
- Removed invalid restriction on taa marbuta (ة) at word start
- Fixed unused variable warning in ICR tests

### Changed

- `is_valid_arabic_word()` now accepts:
  - Pure numbers (valid in mixed Arabic/numeric text)
  - Pure punctuation and symbols
  - Date/number patterns with separators (/, ,, ., -, :)
- Validation only checks for invalid diacritics at word start, not other Arabic characters

## [0.1.6] - 2026-01-30

### Added

- **WordContext struct**: Hybrid architecture preserving word-level context in character-level ICR
- Word-level linguistic analysis: root extraction, emphatic detection, aspect marker identification
- Context-aware T/S mapping based on ISSUES.md rules:
  - T → ط (emphatic) for words in emphatic lexicon
  - T → ت (regular) for words with aspect markers (ta-, tay-, ka-)
  - S → ص (emphatic) for words with emphatic roots
  - S → س (regular) for function words and loanwords
- Digit 8 context-aware mapping: 8 → ه in word contexts
- Number sequence preservation with separators (e.g., "50->")
- Integration of linguistic modules (emphatic, patterns, root extraction)

### Fixed

- All 72 tests now passing (100% test coverage)
- Character-level ICR design properly maintained
- Test data corrected to follow character-level segment architecture
- Type mismatch errors in emphatic consonant handling
- Lifetime annotations in script generation functions
- Duplicate pattern warnings in linguistic modules

### Changed

- ICRSegment now includes optional WordContext for linguistic rules
- ICRBuilder extracts word properties once per word (performance optimization)
- Context-aware mapping uses WordContext instead of position-based lookups
- Improved Darija pattern recognition in tokenization (7na, 3la, etc.)

### Documentation

- Removed internal/temporary markdown files
- Clean documentation structure maintained

## [0.1.5] - 2026-01-28

### Fixed

- **Critical**: Fixed clitic attachment - clitics now attach to host words without spaces
- **Critical**: Fixed definite article "l" → "ال" (was "ل")
- Fixed clitic separation issues: "liya" → "اليا" (was "ل يا")
- Fixed compound clitics: "fl" now properly becomes "فال" (not "ف ل")

### Added

- Character mapping for "ch" → "ش" (Darija common spelling)
- Character mapping for "8" → "غ" (context-dependent, default)
- Character mapping for "9" → "ق" (qaf)
- Character mapping for "Dr" sequences → "ض" (Darija verbs)
- Special handling for clitic expansion in ICR builder
- Comprehensive linguistic improvements documentation (LINGUISTIC_IMPROVEMENTS.md)

### Changed

- ICR builder no longer adds spaces after Clitic tokens
- Latin-to-ICR now handles clitic prefixes specially ("l" → "al" → "ال")
- Improved multi-character sequence detection in ICR

### Known Limitations

See LINGUISTIC_IMPROVEMENTS.md for detailed analysis. Key remaining issues:
- Context-dependent "l" (article vs. preposition)
- Context-dependent numerics ("8" can be غ or ه)
- Darija lexicon needed for correct word forms
- Verb morphology patterns need modeling

## [0.1.4] - 2026-01-28

### Fixed

- **Critical**: Fixed spacing not preserved between words in `bizi2ara` output
- **Critical**: Fixed duplicate character removal (e.g., "رر" → "ر", "مبرردين" → "مبردين")
- Improved validation stage to remove all duplicate consecutive characters
- Enhanced ICR builder to preserve word boundaries with space segments

### Added

- Whitespace segment type in ICR for proper space handling
- Comprehensive tests for spacing preservation in both directions
- Tests for duplicate character removal (Arabic and Latin)
- 4 new tests added (total: 45 tests, all passing)

### Changed

- ICR builder now inserts space segments between tokens
- Validation stage uses intelligent duplicate removal algorithm
- Better handling of word boundaries in transliteration

## [0.1.3] - 2026-01-28

### Fixed

- **CI/CD**: Fixed Linux wheel builds in GitHub Actions (removed Docker, unified build process)
- **PyPI**: Added missing source distribution (.tar.gz) to PyPI releases
- **GitHub Pages**: Fixed deployment from tags (now only deploys from main branch)

### Added

- Source distribution build job in CI/CD workflow
- All Python versions now build correctly on Linux

### Changed

- Simplified wheel building across all platforms (no platform-specific logic)
- Updated publish workflow to download both wheels and source distribution

## [0.1.2] - 2026-01-28

### Fixed

- **Security**: Upgraded PyO3 from 0.20.3 to 0.24.2 to fix buffer overflow vulnerability (CVE)
- **Documentation**: Fixed MkDocs directory structure for proper builds
- **Documentation**: Removed Rust API from navigation to fix strict mode build
- **CI/CD**: Fixed GitHub Actions release permissions (403 error)
- **Documentation**: Added comprehensive documentation for all sections

### Added

- Complete user guide with examples
- API reference documentation
- Development and contribution guides
- Installation instructions
- Architecture documentation

### Changed

- Updated Python bindings to use PyO3 0.24+ Bound API
- Moved mkdocs.yml from docs/ to project root
- Updated all documentation paths for new structure

## [0.1.0] - 2026-01-28

### Added

- Initial release of CaDaR
- 6-stage FST-style transliteration pipeline
  - Stage 1: Script Detection
  - Stage 2: Noise Cleaning & Normalization
  - Stage 3: Darija-aware Tokenization
  - Stage 4: Intermediate Canonical Representation (ICR)
  - Stage 5: Target Script Generation
  - Stage 6: Post-validation & Fixes
- Python API with four main functions:
  - `ara2bizi()` - Arabic to Latin transliteration
  - `bizi2ara()` - Latin to Arabic transliteration
  - `ara2ara()` - Arabic text standardization
  - `bizi2bizi()` - Latin text standardization
- `CaDaR` class for reusable transliteration operations
- Convenience functions: `transliterate()` and `standardize()`
- Support for Moroccan Darija (dialect code: "Ma")
- Comprehensive documentation
- 41 unit tests with 100% pass rate
- Example scripts demonstrating usage
- MIT License

### Features

- **Bidirectional transliteration**: Seamless conversion between Arabic and Latin scripts
- **Intelligent normalization**: Handles diacritics, repeated characters, and common variations
- **Darija-aware processing**: Recognizes Darija-specific patterns and constructs
- **High performance**: Rust core with Python bindings via PyO3
- **Extensible architecture**: Designed to support additional Darija dialects in future releases

### Technical Details

- Built with Rust 1.93.0
- Python bindings using PyO3 0.20
- Supports Python 3.8+
- Cross-platform: Linux, macOS, Windows

[Unreleased]: https://github.com/Oit-Technologies/CaDaR/compare/v0.1.5...HEAD
[0.1.5]: https://github.com/Oit-Technologies/CaDaR/compare/v0.1.4...v0.1.5
[0.1.4]: https://github.com/Oit-Technologies/CaDaR/compare/v0.1.3...v0.1.4
[0.1.3]: https://github.com/Oit-Technologies/CaDaR/compare/v0.1.2...v0.1.3
[0.1.2]: https://github.com/Oit-Technologies/CaDaR/compare/v0.1.0...v0.1.2
[0.1.0]: https://github.com/Oit-Technologies/CaDaR/releases/tag/v0.1.0
