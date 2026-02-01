# Changelog

All notable changes to this project will be documented in this file.

The format is based on [Keep a Changelog](https://keepachangelog.com/en/1.0.0/),
and this project adheres to [Semantic Versioning](https://semver.org/spec/v2.0.0.html).

## [Unreleased]

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
