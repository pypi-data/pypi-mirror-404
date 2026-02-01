use super::icr::{SegmentType, ICR};
use super::{StageError, StageResult};
use crate::types::Script;

/// Stage 5: Target Script Generation
/// Converts ICR to target script (Arabic or Latin)
pub struct ScriptGenerator;

impl ScriptGenerator {
    pub fn new() -> Self {
        ScriptGenerator
    }

    /// Generate target script from ICR
    pub fn generate(&self, icr: &ICR, target_script: Script) -> StageResult<String> {
        match target_script {
            Script::Arabic => self.icr_to_arabic(icr),
            Script::Latin => self.icr_to_latin(icr),
            Script::Mixed => Err(StageError::ScriptGeneration(
                "Cannot generate mixed script directly".to_string(),
            )),
            Script::Unknown => Err(StageError::ScriptGeneration(
                "Cannot generate unknown script".to_string(),
            )),
        }
    }

    /// Convert ICR to Arabic script
    fn icr_to_arabic(&self, icr: &ICR) -> StageResult<String> {
        let mut result = String::new();
        let mut prev_was_vowel = false;

        for segment in &icr.segments {
            let arabic_char = self.canonical_to_arabic(&segment.canonical, segment.segment_type);

            // Handle different segment types appropriately
            match segment.segment_type {
                SegmentType::Number | SegmentType::Punctuation => {
                    // Preserve numbers and symbols as-is
                    result.push_str(arabic_char);
                    prev_was_vowel = false;
                }
                SegmentType::Whitespace => {
                    result.push(' ');
                    prev_was_vowel = false;
                }
                SegmentType::Vowel => {
                    // Handle vowel placement in Arabic
                    if !prev_was_vowel {
                        result.push_str(arabic_char);
                    }
                    prev_was_vowel = true;
                }
                _ => {
                    // Regular consonants and other types
                    result.push_str(arabic_char);
                    prev_was_vowel = false;
                }
            }
        }

        if result.is_empty() {
            return Err(StageError::ScriptGeneration(
                "Generated Arabic text is empty".to_string(),
            ));
        }

        Ok(result)
    }

    /// Convert ICR to Latin script
    fn icr_to_latin(&self, icr: &ICR) -> StageResult<String> {
        let mut result = String::new();

        for segment in &icr.segments {
            let latin_char = self.canonical_to_latin(&segment.canonical, segment.segment_type);

            // Handle different segment types appropriately
            match segment.segment_type {
                SegmentType::Number | SegmentType::Punctuation => {
                    // Preserve numbers and symbols as-is
                    result.push_str(latin_char);
                }
                SegmentType::Whitespace => {
                    result.push(' ');
                }
                _ => {
                    // Regular characters
                    result.push_str(latin_char);
                }
            }
        }

        if result.is_empty() {
            return Err(StageError::ScriptGeneration(
                "Generated Latin text is empty".to_string(),
            ));
        }

        Ok(result)
    }

    /// Map canonical form to Arabic character
    fn canonical_to_arabic<'a>(&self, canonical: &'a str, segment_type: SegmentType) -> &'a str {
        // Handle preserved numbers and symbols directly
        if matches!(segment_type, SegmentType::Number | SegmentType::Punctuation) {
            return canonical; // Preserve as-is
        }

        match canonical {
            "A" => "ا",
            "B" => "ب",
            "T" => "ت", // Regular taa (ت)
            "Ṯ" => "ث",
            "J" => "ج",
            "Ḥ" => "ح",
            "X" => "خ",
            "D" => "د",
            "Ḏ" => "ذ",
            "R" => "ر",
            "Z" => "ز",
            "S" => "س", // Regular seen (س)
            "Š" => "ش",
            "Ṣ" => "ص", // Emphatic seen (ص)
            "Ḍ" => "ض",
            "Ṭ" => "ط", // Emphatic taa (ط)
            "Ẓ" => "ظ",
            "ε" => "ع",
            "Ġ" => "غ",
            "F" => "ف",
            "Q" => "ق",
            "K" => "ك",
            "L" => "ل",
            "M" => "م",
            "N" => "ن",
            "H" => "ه",
            "W" => "و",
            "Y" => "ي",
            "I" => "ي",
            "U" => "و",
            " " => " ",
            // Handle digits that should be preserved
            "0" | "1" | "2" | "3" | "4" | "5" | "6" | "7" | "8" | "9" => canonical,
            // Handle common symbols
            "+" | "-" | "*" | "/" | "=" | ">" | "<" | "|" | ":" | "." | "," | "(" | ")" | "["
            | "]" | "{" | "}" => canonical,
            _ => "",
        }
    }

    /// Map canonical form to Latin character
    fn canonical_to_latin<'a>(&self, canonical: &'a str, segment_type: SegmentType) -> &'a str {
        // Handle preserved numbers and symbols directly
        if matches!(segment_type, SegmentType::Number | SegmentType::Punctuation) {
            return canonical; // Preserve as-is
        }

        match canonical {
            "A" => "a",
            "B" => "b",
            "T" => "t", // Regular t (ت)
            "Ṯ" => "th",
            "J" => "j",
            "Ḥ" => "7", // Using common Darija notation
            "X" => "kh",
            "D" => "d",
            "Ḏ" => "dh",
            "R" => "r",
            "Z" => "z",
            "S" => "s", // Regular s (س)
            "Š" => "sh",
            "Ṣ" => "S", // Emphatic s (ص) - use capital for distinction
            "Ḍ" => "D", // Emphatic d (ض) - use capital for distinction
            "Ṭ" => "T", // Emphatic t (ط) - use capital for distinction
            "Ẓ" => "Z", // Emphatic z (ظ) - use capital for distinction
            "ε" => "3", // Using common Darija notation
            "Ġ" => "gh",
            "F" => "f",
            "Q" => "q",
            "K" => "k",
            "L" => "l",
            "M" => "m",
            "N" => "n",
            "H" => "h",
            "W" => "w",
            "Y" => "y",
            "I" => "i",
            "U" => "u",
            " " => " ",
            // Handle digits that should be preserved
            "0" | "1" | "2" | "3" | "4" | "5" | "6" | "7" | "8" | "9" => canonical,
            // Handle common symbols
            "+" | "-" | "*" | "/" | "=" | ">" | "<" | "|" | ":" | "." | "," | "(" | ")" | "["
            | "]" | "{" | "}" => canonical,
            _ => "",
        }
    }
}

impl Default for ScriptGenerator {
    fn default() -> Self {
        Self::new()
    }
}

#[cfg(test)]
mod tests {
    use super::*;
    use crate::stages::icr::{ICRMetadata, ICRSegment};
    use crate::types::Dialect;

    #[test]
    fn test_icr_to_arabic() {
        let generator = ScriptGenerator::new();

        // Create a simple ICR
        let icr = ICR {
            segments: vec![
                ICRSegment {
                    canonical: "S".to_string(),
                    original: "s".to_string(),
                    segment_type: SegmentType::Consonant,
                    confidence: 1.0,
                    word_context: None,
                },
                ICRSegment {
                    canonical: "L".to_string(),
                    original: "l".to_string(),
                    segment_type: SegmentType::Consonant,
                    confidence: 1.0,
                    word_context: None,
                },
                ICRSegment {
                    canonical: "A".to_string(),
                    original: "a".to_string(),
                    segment_type: SegmentType::Vowel,
                    confidence: 1.0,
                    word_context: None,
                },
                ICRSegment {
                    canonical: "M".to_string(),
                    original: "m".to_string(),
                    segment_type: SegmentType::Consonant,
                    confidence: 1.0,
                    word_context: None,
                },
            ],
            dialect: Dialect::Moroccan,
            metadata: ICRMetadata {
                source_script: Script::Latin,
                total_segments: 4,
                confidence_avg: 1.0,
            },
        };

        let result = generator.generate(&icr, Script::Arabic).unwrap();
        assert_eq!(result, "سلام");
    }

    #[test]
    fn test_icr_to_latin() {
        let generator = ScriptGenerator::new();

        // Create a simple ICR
        let icr = ICR {
            segments: vec![
                ICRSegment {
                    canonical: "S".to_string(),
                    original: "س".to_string(),
                    segment_type: SegmentType::Consonant,
                    confidence: 1.0,
                    word_context: None,
                },
                ICRSegment {
                    canonical: "L".to_string(),
                    original: "ل".to_string(),
                    segment_type: SegmentType::Consonant,
                    confidence: 1.0,
                    word_context: None,
                },
                ICRSegment {
                    canonical: "A".to_string(),
                    original: "ا".to_string(),
                    segment_type: SegmentType::Vowel,
                    confidence: 1.0,
                    word_context: None,
                },
                ICRSegment {
                    canonical: "M".to_string(),
                    original: "م".to_string(),
                    segment_type: SegmentType::Consonant,
                    confidence: 1.0,
                    word_context: None,
                },
            ],
            dialect: Dialect::Moroccan,
            metadata: ICRMetadata {
                source_script: Script::Arabic,
                total_segments: 4,
                confidence_avg: 1.0,
            },
        };

        let result = generator.generate(&icr, Script::Latin).unwrap();
        assert_eq!(result, "slam");
    }

    #[test]
    fn test_special_chars_to_latin() {
        let generator = ScriptGenerator::new();

        let icr = ICR {
            segments: vec![
                ICRSegment {
                    canonical: "ε".to_string(),
                    original: "ع".to_string(),
                    segment_type: SegmentType::Consonant,
                    confidence: 1.0,
                    word_context: None,
                },
                ICRSegment {
                    canonical: "L".to_string(),
                    original: "ل".to_string(),
                    segment_type: SegmentType::Consonant,
                    confidence: 1.0,
                    word_context: None,
                },
                ICRSegment {
                    canonical: "A".to_string(),
                    original: "ا".to_string(),
                    segment_type: SegmentType::Vowel,
                    confidence: 1.0,
                    word_context: None,
                },
            ],
            dialect: Dialect::Moroccan,
            metadata: ICRMetadata {
                source_script: Script::Arabic,
                total_segments: 3,
                confidence_avg: 1.0,
            },
        };

        let result = generator.generate(&icr, Script::Latin).unwrap();
        assert_eq!(result, "3la"); // 'ayn represented as 3
    }

    // Tests for ISSUES.md fixes

    #[test]
    fn test_emphatic_t_mapping() {
        let generator = ScriptGenerator::new();

        // Test regular T (ت)
        let icr_regular = ICR {
            segments: vec![
                ICRSegment {
                    canonical: "T".to_string(), // Regular T
                    original: "t".to_string(),
                    segment_type: SegmentType::Consonant,
                    confidence: 1.0,
                    word_context: None,
                },
                ICRSegment {
                    canonical: "A".to_string(),
                    original: "a".to_string(),
                    segment_type: SegmentType::Vowel,
                    confidence: 1.0,
                    word_context: None,
                },
            ],
            dialect: Dialect::Moroccan,
            metadata: ICRMetadata {
                source_script: Script::Latin,
                total_segments: 2,
                confidence_avg: 1.0,
            },
        };

        let result_arabic = generator.generate(&icr_regular, Script::Arabic).unwrap();
        assert_eq!(result_arabic, "تا");

        let result_latin = generator.generate(&icr_regular, Script::Latin).unwrap();
        assert_eq!(result_latin, "ta");

        // Test emphatic Ṭ (ط)
        let icr_emphatic = ICR {
            segments: vec![
                ICRSegment {
                    canonical: "Ṭ".to_string(), // Emphatic Ṭ
                    original: "T".to_string(),
                    segment_type: SegmentType::Consonant,
                    confidence: 1.0,
                    word_context: None,
                },
                ICRSegment {
                    canonical: "A".to_string(),
                    original: "a".to_string(),
                    segment_type: SegmentType::Vowel,
                    confidence: 1.0,
                    word_context: None,
                },
            ],
            dialect: Dialect::Moroccan,
            metadata: ICRMetadata {
                source_script: Script::Latin,
                total_segments: 2,
                confidence_avg: 1.0,
            },
        };

        let result_arabic_emphatic = generator.generate(&icr_emphatic, Script::Arabic).unwrap();
        assert_eq!(result_arabic_emphatic, "طا");

        let result_latin_emphatic = generator.generate(&icr_emphatic, Script::Latin).unwrap();
        assert_eq!(result_latin_emphatic, "Ta"); // Capital T for emphatic
    }

    #[test]
    fn test_emphatic_s_mapping() {
        let generator = ScriptGenerator::new();

        // Test regular S (س)
        let icr_regular = ICR {
            segments: vec![
                ICRSegment {
                    canonical: "S".to_string(), // Regular S
                    original: "s".to_string(),
                    segment_type: SegmentType::Consonant,
                    confidence: 1.0,
                    word_context: None,
                },
                ICRSegment {
                    canonical: "A".to_string(),
                    original: "a".to_string(),
                    segment_type: SegmentType::Vowel,
                    confidence: 1.0,
                    word_context: None,
                },
            ],
            dialect: Dialect::Moroccan,
            metadata: ICRMetadata {
                source_script: Script::Latin,
                total_segments: 2,
                confidence_avg: 1.0,
            },
        };

        let result_arabic = generator.generate(&icr_regular, Script::Arabic).unwrap();
        assert_eq!(result_arabic, "سا");

        let result_latin = generator.generate(&icr_regular, Script::Latin).unwrap();
        assert_eq!(result_latin, "sa");

        // Test emphatic Ṣ (ص)
        let icr_emphatic = ICR {
            segments: vec![
                ICRSegment {
                    canonical: "Ṣ".to_string(), // Emphatic Ṣ
                    original: "S".to_string(),
                    segment_type: SegmentType::Consonant,
                    confidence: 1.0,
                    word_context: None,
                },
                ICRSegment {
                    canonical: "A".to_string(),
                    original: "a".to_string(),
                    segment_type: SegmentType::Vowel,
                    confidence: 1.0,
                    word_context: None,
                },
            ],
            dialect: Dialect::Moroccan,
            metadata: ICRMetadata {
                source_script: Script::Latin,
                total_segments: 2,
                confidence_avg: 1.0,
            },
        };

        let result_arabic_emphatic = generator.generate(&icr_emphatic, Script::Arabic).unwrap();
        assert_eq!(result_arabic_emphatic, "صا");

        let result_latin_emphatic = generator.generate(&icr_emphatic, Script::Latin).unwrap();
        assert_eq!(result_latin_emphatic, "Sa"); // Capital S for emphatic
    }

    #[test]
    fn test_number_preservation() {
        let generator = ScriptGenerator::new();

        // Test numbers are preserved (character-level ICR: "50->h")
        let icr_numbers = ICR {
            segments: vec![
                ICRSegment {
                    canonical: "5".to_string(),
                    original: "5".to_string(),
                    segment_type: SegmentType::Number,
                    confidence: 1.0,
                    word_context: None,
                },
                ICRSegment {
                    canonical: "0".to_string(),
                    original: "0".to_string(),
                    segment_type: SegmentType::Number,
                    confidence: 1.0,
                    word_context: None,
                },
                ICRSegment {
                    canonical: "-".to_string(),
                    original: "-".to_string(),
                    segment_type: SegmentType::Punctuation,
                    confidence: 1.0,
                    word_context: None,
                },
                ICRSegment {
                    canonical: ">".to_string(),
                    original: ">".to_string(),
                    segment_type: SegmentType::Punctuation,
                    confidence: 1.0,
                    word_context: None,
                },
                ICRSegment {
                    canonical: "H".to_string(),
                    original: "h".to_string(),
                    segment_type: SegmentType::Consonant,
                    confidence: 1.0,
                    word_context: None,
                },
            ],
            dialect: Dialect::Moroccan,
            metadata: ICRMetadata {
                source_script: Script::Latin,
                total_segments: 5,
                confidence_avg: 1.0,
            },
        };

        let result_arabic = generator.generate(&icr_numbers, Script::Arabic).unwrap();
        assert_eq!(result_arabic, "50->ه");

        let result_latin = generator.generate(&icr_numbers, Script::Latin).unwrap();
        assert_eq!(result_latin, "50->h");
    }

    #[test]
    fn test_digit_8_contextual_mapping() {
        let generator = ScriptGenerator::new();

        // Test digit 8 in word context (should map to ه/H)
        // Character-level ICR: "dyal8a" -> D,Y,A,L,H,A
        let icr_word_context = ICR {
            segments: vec![
                ICRSegment {
                    canonical: "D".to_string(),
                    original: "d".to_string(),
                    segment_type: SegmentType::Consonant,
                    confidence: 1.0,
                    word_context: None,
                },
                ICRSegment {
                    canonical: "Y".to_string(),
                    original: "y".to_string(),
                    segment_type: SegmentType::Consonant,
                    confidence: 1.0,
                    word_context: None,
                },
                ICRSegment {
                    canonical: "A".to_string(),
                    original: "a".to_string(),
                    segment_type: SegmentType::Vowel,
                    confidence: 1.0,
                    word_context: None,
                },
                ICRSegment {
                    canonical: "L".to_string(),
                    original: "l".to_string(),
                    segment_type: SegmentType::Consonant,
                    confidence: 1.0,
                    word_context: None,
                },
                ICRSegment {
                    canonical: "H".to_string(), // 8 in word context -> H -> ه
                    original: "8".to_string(),
                    segment_type: SegmentType::Consonant,
                    confidence: 1.0,
                    word_context: None,
                },
                ICRSegment {
                    canonical: "A".to_string(),
                    original: "a".to_string(),
                    segment_type: SegmentType::Vowel,
                    confidence: 1.0,
                    word_context: None,
                },
            ],
            dialect: Dialect::Moroccan,
            metadata: ICRMetadata {
                source_script: Script::Latin,
                total_segments: 6,
                confidence_avg: 1.0,
            },
        };

        let result_arabic = generator
            .generate(&icr_word_context, Script::Arabic)
            .unwrap();
        assert_eq!(result_arabic, "ديالها");

        let result_latin = generator
            .generate(&icr_word_context, Script::Latin)
            .unwrap();
        assert_eq!(result_latin, "dyalha");

        // Test digit 8 in mathematical context (should preserve as 8)
        let icr_math_context = ICR {
            segments: vec![
                ICRSegment {
                    canonical: "5".to_string(),
                    original: "5".to_string(),
                    segment_type: SegmentType::Number,
                    confidence: 1.0,
                    word_context: None,
                },
                ICRSegment {
                    canonical: "+".to_string(),
                    original: "+".to_string(),
                    segment_type: SegmentType::Punctuation,
                    confidence: 1.0,
                    word_context: None,
                },
                ICRSegment {
                    canonical: "8".to_string(), // 8 in math context -> preserve as 8
                    original: "8".to_string(),
                    segment_type: SegmentType::Number,
                    confidence: 1.0,
                    word_context: None,
                },
                ICRSegment {
                    canonical: "=".to_string(),
                    original: "=".to_string(),
                    segment_type: SegmentType::Punctuation,
                    confidence: 1.0,
                    word_context: None,
                },
                ICRSegment {
                    canonical: "13".to_string(),
                    original: "13".to_string(),
                    segment_type: SegmentType::Number,
                    confidence: 1.0,
                    word_context: None,
                },
            ],
            dialect: Dialect::Moroccan,
            metadata: ICRMetadata {
                source_script: Script::Latin,
                total_segments: 5,
                confidence_avg: 1.0,
            },
        };

        let result_arabic_math = generator
            .generate(&icr_math_context, Script::Arabic)
            .unwrap();
        assert_eq!(result_arabic_math, "5+8=13");

        let result_latin_math = generator
            .generate(&icr_math_context, Script::Latin)
            .unwrap();
        assert_eq!(result_latin_math, "5+8=13");
    }
}
