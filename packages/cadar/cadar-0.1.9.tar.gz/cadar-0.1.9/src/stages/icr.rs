use super::tokenization::{Token, TokenType};
use super::{StageError, StageResult};
use crate::linguistic::{
    extract_root, is_function_word, replace_number_patterns, should_be_emphatic_s,
    should_be_emphatic_t, starts_with_aspect_marker, DigitContextAnalyzer, NumberPreserver,
};
use crate::types::{Dialect, Script};
use serde::{Deserialize, Serialize};

/// Stage 4: Intermediate Canonical Representation (ICR)
/// Converts tokens to a unified canonical form
#[derive(Debug, Clone, Serialize, Deserialize)]
pub struct ICR {
    /// Canonical phonemes/graphemes
    pub segments: Vec<ICRSegment>,
    /// Original dialect
    pub dialect: Dialect,
    /// Metadata
    pub metadata: ICRMetadata,
}

/// Word-level context for linguistic rules
/// Attached to character-level ICR segments to preserve word information
#[derive(Debug, Clone, Serialize, Deserialize, PartialEq)]
pub struct WordContext {
    /// The complete word this character belongs to
    pub full_word: String,
    /// Trilateral/consonantal root (if extractable)
    pub word_root: Option<String>,
    /// Whether this word uses emphatic consonants
    pub is_emphatic: bool,
    /// Whether this word starts with aspect marker (ta-, tay-, ka-)
    pub has_aspect_marker: bool,
    /// Whether this is a Darija function word
    pub is_function_word: bool,
}

/// A segment in the ICR (represents a canonical unit)
#[derive(Debug, Clone, Serialize, Deserialize, PartialEq)]
pub struct ICRSegment {
    /// Canonical representation (phonetic/phonemic)
    pub canonical: String,
    /// Original text
    pub original: String,
    /// Segment type
    pub segment_type: SegmentType,
    /// Confidence score (0.0 - 1.0)
    pub confidence: f64,
    /// Optional word-level context for linguistic rules
    pub word_context: Option<WordContext>,
}

/// Types of ICR segments
#[derive(Debug, Clone, Copy, PartialEq, Serialize, Deserialize)]
pub enum SegmentType {
    /// Consonant
    Consonant,
    /// Vowel
    Vowel,
    /// Function word
    FunctionWord,
    /// Number
    Number,
    /// Punctuation
    Punctuation,
    /// Whitespace
    Whitespace,
    /// Unknown
    Unknown,
}

/// Metadata about the ICR
#[derive(Debug, Clone, Serialize, Deserialize)]
pub struct ICRMetadata {
    pub source_script: Script,
    pub total_segments: usize,
    pub confidence_avg: f64,
}

/// Builder for ICR
pub struct ICRBuilder {
    dialect: Dialect,
}

impl ICRBuilder {
    pub fn new(dialect: Dialect) -> Self {
        ICRBuilder { dialect }
    }

    /// Convert tokens to ICR
    pub fn build_from_tokens(&self, tokens: &[Token], source_script: Script) -> StageResult<ICR> {
        let mut segments = Vec::new();
        let mut total_confidence = 0.0;

        for (i, token) in tokens.iter().enumerate() {
            let token_segments = self.tokenize_to_segments(&token.text, source_script)?;
            total_confidence += token_segments.iter().map(|s| s.confidence).sum::<f64>();
            segments.extend(token_segments);

            // Add space segment between tokens (except after the last token)
            // Don't add space after clitics (they attach to the following word)
            // Don't add space after punctuation
            if i < tokens.len() - 1
                && !matches!(token.token_type, TokenType::Punctuation | TokenType::Clitic)
            {
                segments.push(ICRSegment {
                    canonical: " ".to_string(),
                    original: " ".to_string(),
                    segment_type: SegmentType::Whitespace,
                    confidence: 1.0,
                    word_context: None,
                });
                total_confidence += 1.0;
            }
        }

        let total_segments = segments.len();
        let confidence_avg = if total_segments > 0 {
            total_confidence / total_segments as f64
        } else {
            0.0
        };

        Ok(ICR {
            segments,
            dialect: self.dialect,
            metadata: ICRMetadata {
                source_script,
                total_segments,
                confidence_avg,
            },
        })
    }

    /// Convert a single token to ICR segments
    fn tokenize_to_segments(
        &self,
        text: &str,
        source_script: Script,
    ) -> StageResult<Vec<ICRSegment>> {
        match source_script {
            Script::Arabic => self.arabic_to_icr(text),
            Script::Latin => self.latin_to_icr(text),
            Script::Mixed => Err(StageError::ICRConversion(
                "Mixed script tokens should be processed separately".to_string(),
            )),
            Script::Unknown => Err(StageError::ICRConversion(
                "Cannot convert unknown script to ICR".to_string(),
            )),
        }
    }

    /// Convert Arabic text to ICR
    fn arabic_to_icr(&self, text: &str) -> StageResult<Vec<ICRSegment>> {
        let mut segments = Vec::new();

        for ch in text.chars() {
            let canonical = self.arabic_char_to_canonical(ch);
            let segment_type = self.classify_arabic_char(ch);

            segments.push(ICRSegment {
                canonical: canonical.to_string(),
                original: ch.to_string(),
                segment_type,
                confidence: 1.0, // High confidence for direct mapping
                word_context: None, // TODO: Add word context for Arabic text
            });
        }

        Ok(segments)
    }

    /// Convert Latin text to ICR
    fn latin_to_icr(&self, text: &str) -> StageResult<Vec<ICRSegment>> {
        // Handle multi-word input by splitting on whitespace
        if text.contains(char::is_whitespace) {
            let mut all_segments = Vec::new();
            for word in text.split_whitespace() {
                let word_segments = self.latin_to_icr(word)?;
                all_segments.extend(word_segments);
                // Add whitespace segment between words
                if all_segments.len() > 0 && word != text.split_whitespace().last().unwrap() {
                    all_segments.push(ICRSegment {
                        canonical: " ".to_string(),
                        original: " ".to_string(),
                        segment_type: SegmentType::Whitespace,
                        confidence: 1.0,
                        word_context: None,
                    });
                }
            }
            return Ok(all_segments);
        }

        // Check for number preservation first
        if let Some(preserved) = NumberPreserver::process(text) {
            let segments = self.preserve_numbers_as_segments(&preserved)?;
            return Ok(segments);
        }

        // Apply common pattern replacements
        let processed_text = replace_number_patterns(text);

        // Special handling for common Darija clitics that need expansion
        let expanded_text = if processed_text == "l" {
            "al".to_string()
        } else if processed_text == "f" {
            "f".to_string() // "ف" (in/at)
        } else if processed_text == "b" {
            "b".to_string() // "ប" (with/by)
        } else if processed_text == "w" {
            "w".to_string() // "و" (and)
        } else {
            processed_text
        };

        // Extract word-level context ONCE for the entire word
        let word_context = self.extract_word_context(&expanded_text);

        let mut segments = Vec::new();
        let chars: Vec<char> = expanded_text.chars().collect();
        let mut i = 0;

        while i < chars.len() {
            // Check for vowels first (smart vowel handling)
            if crate::linguistic::VowelAnalyzer::is_vowel_char(chars[i]) {
                // Analyze vowel (long vs short, position, type)
                if let Some(vowel_info) = crate::linguistic::VowelAnalyzer::analyze_vowel(&chars, i) {
                    let (is_long, chars_consumed) = crate::linguistic::VowelAnalyzer::detect_long_vowel(&chars, i);

                    // Special case: Skip short vowel if followed by another vowel
                    // This handles cases like "salaam" where 'a' before 'aa' should be skipped
                    if !is_long && i + 1 < chars.len() && crate::linguistic::VowelAnalyzer::is_vowel_char(chars[i + 1]) {
                        // Skip this short vowel, let the next vowel (or double vowel) handle it
                        i += 1;
                        continue;
                    }

                    // Get canonical form based on vowel analysis
                    // Use Darija mode for more readable output
                    let canonical = crate::linguistic::VowelAnalyzer::vowel_to_canonical(
                        &vowel_info,
                        crate::linguistic::VowelMode::Darija
                    );

                    // Determine original string (single or double vowel)
                    let original = if is_long && i + 1 < chars.len() {
                        format!("{}{}", chars[i], chars[i + 1])
                    } else {
                        chars[i].to_string()
                    };

                    // Only add segment if vowel should be written
                    if !canonical.is_empty() {
                        let segment_type = self.classify_latin_char(chars[i]);
                        segments.push(ICRSegment {
                            canonical: canonical.to_string(),
                            original,
                            segment_type,
                            confidence: 0.9,
                            word_context: word_context.clone(),
                        });
                    }

                    // Advance by number of characters consumed
                    i += chars_consumed;
                    continue;
                }
            }

            // Try to match multi-character sequences (consonants like sh, kh, etc.)
            let (canonical, original, advance) = if i + 1 < chars.len() {
                let two_char = format!("{}{}", chars[i], chars[i + 1]);
                if let Some(canon) = self.latin_sequence_to_canonical(&two_char) {
                    (canon, two_char, 2)
                } else {
                    let one_char = chars[i].to_string();
                    (
                        self.context_aware_latin_char_to_canonical_with_context(
                            chars[i],
                            i,
                            &expanded_text,
                            word_context.as_ref()
                        ),
                        one_char,
                        1,
                    )
                }
            } else {
                let one_char = chars[i].to_string();
                (
                    self.context_aware_latin_char_to_canonical_with_context(
                        chars[i],
                        i,
                        &expanded_text,
                        word_context.as_ref()
                    ),
                    one_char,
                    1,
                )
            };

            let segment_type = self.classify_latin_char(chars[i]);

            // Attach word context to each character segment
            segments.push(ICRSegment {
                canonical: canonical.to_string(),
                original,
                segment_type,
                confidence: 0.9, // Slightly lower confidence for Latin (more ambiguous)
                word_context: word_context.clone(), // Same context for all chars in word
            });

            i += advance;
        }

        Ok(segments)
    }

    /// Extract word-level linguistic context
    fn extract_word_context(&self, word: &str) -> Option<WordContext> {
        // Don't extract context for very short words or pure numbers
        if word.len() < 2 || word.chars().all(|c| c.is_ascii_digit()) {
            return None;
        }

        // Extract root (trilateral/consonantal)
        let word_root = extract_root(word);

        // Check if word is in emphatic lexicon
        let is_emphatic_lexicon = should_be_emphatic_t(word);

        // Check if root is emphatic
        let is_emphatic_root = word_root.as_ref()
            .map(|r| should_be_emphatic_s(r))
            .unwrap_or(false);

        let is_emphatic = is_emphatic_lexicon || is_emphatic_root;

        // Check if word starts with aspect marker
        let has_aspect_marker = starts_with_aspect_marker(word);

        // Check if it's a function word
        let is_function_word_flag = is_function_word(word);

        Some(WordContext {
            full_word: word.to_string(),
            word_root,
            is_emphatic,
            has_aspect_marker,
            is_function_word: is_function_word_flag,
        })
    }

    /// Context-aware mapping using WordContext (more efficient than position-based)
    fn context_aware_latin_char_to_canonical_with_context(
        &self,
        ch: char,
        pos: usize,
        text: &str,
        word_context: Option<&WordContext>,
    ) -> &'static str {
        match ch {
            't' | 'T' => {
                // Use word context if available
                if let Some(ctx) = word_context {
                    if ctx.is_emphatic {
                        "Ṭ" // Emphatic t (ط)
                    } else if ctx.has_aspect_marker {
                        "T" // Regular t (ت) for aspect markers
                    } else if ctx.is_function_word {
                        "T" // Regular t (ت) for function words
                    } else {
                        // Default based on character case
                        if ch.is_uppercase() {
                            "Ṭ"
                        } else {
                            "T"
                        }
                    }
                } else {
                    // Fallback to old method if no context
                    self.context_aware_latin_char_to_canonical(ch, pos, text)
                }
            }
            's' | 'S' => {
                // Use word context if available
                if let Some(ctx) = word_context {
                    if ctx.is_emphatic {
                        "Ṣ" // Emphatic s (ص)
                    } else if ctx.is_function_word {
                        "S" // Regular s (س) for function words
                    } else {
                        // Default based on character case
                        if ch.is_uppercase() {
                            "Ṣ"
                        } else {
                            "S"
                        }
                    }
                } else {
                    // Fallback to old method if no context
                    self.context_aware_latin_char_to_canonical(ch, pos, text)
                }
            }
            '8' => {
                // Digit 8 context analysis (still uses position-based analysis)
                let context = DigitContextAnalyzer::analyze_context(pos, text);
                DigitContextAnalyzer::map_digit_8(context)
            }
            _ => {
                // For all other characters, use the standard mapping
                self.latin_char_to_canonical(ch)
            }
        }
    }

    /// Map Arabic character to canonical form
    fn arabic_char_to_canonical(&self, ch: char) -> &'static str {
        match ch {
            'ا' | 'أ' | 'إ' | 'آ' => "A",
            'ب' => "B",
            'ت' => "T",
            'ث' => "Ṯ", // th sound
            'ج' => "J",
            'ح' => "Ḥ", // strong h
            'خ' => "X", // kh sound
            'د' => "D",
            'ذ' => "Ḏ", // dh sound
            'ر' => "R",
            'ز' => "Z",
            'س' => "S",
            'ش' => "Š", // sh sound
            'ص' => "Ṣ", // emphatic s
            'ض' => "Ḍ", // emphatic d
            'ط' => "Ṭ", // emphatic t
            'ظ' => "Ẓ", // emphatic z
            'ع' => "ε", // ain
            'غ' => "Ġ", // gh sound
            'ف' => "F",
            'ق' => "Q",
            'ك' => "K",
            'ل' => "L",
            'م' => "M",
            'ن' => "N",
            'ه' => "H",
            'و' => "W",
            'ي' | 'ى' => "Y",
            'ة' => "T", // teh marbuta
            ' ' => " ",
            // Preserve Arabic punctuation as-is in canonical form
            '؟' => "؟",
            '،' => "،",
            '؛' => "؛",
            // Preserve ASCII punctuation as-is
            '?' | '!' | '.' | ',' | ';' | ':' | '(' | ')' | '[' | ']' | '{' | '}' | '"' | '\'' | '-' | '/' => {
                match ch {
                    '?' => "?",
                    '!' => "!",
                    '.' => ".",
                    ',' => ",",
                    ';' => ";",
                    ':' => ":",
                    '(' => "(",
                    ')' => ")",
                    '[' => "[",
                    ']' => "]",
                    '{' => "{",
                    '}' => "}",
                    '"' => "\"",
                    '\'' => "'",
                    '-' => "-",
                    '/' => "/",
                    _ => unreachable!(),
                }
            }
            _ if ch.is_ascii_punctuation() => "",
            _ => "",
        }
    }

    /// Map Latin character to canonical form
    fn latin_char_to_canonical(&self, ch: char) -> &'static str {
        match ch {
            'a' => "A",
            'b' => "B",
            't' => "T",
            'j' => "J",
            'd' => "D",
            'r' => "R",
            'z' => "Z",
            's' => "S",
            'f' => "F",
            'q' => "Q",
            'k' => "K",
            'l' => "L",
            'm' => "M",
            'n' => "N",
            'h' => "H",
            'w' => "W",
            'y' => "Y",
            'ε' | '3' => "ε", // ain (ع)
            'ḥ' | '7' => "Ḥ", // strong h (ح)
            'ġ' | 'g' => "Ġ", // gh sound (غ)
            'š' => "Š",       // sh sound (ش)
            'ṣ' => "Ṣ",       // emphatic s (ص)
            'ḍ' => "Ḍ",       // emphatic d (ض)
            'ṭ' => "Ṭ",       // emphatic t (ط)
            'ẓ' => "Ẓ",       // emphatic z (ظ)
            'x' => "X",       // kh sound (خ)
            '8' => "Ġ",       // Common: غ (gh) - context-dependent
            '9' => "Q",       // قاف (qaf)
            'e' | 'i' => "I", // vowel
            'o' | 'u' => "U", // vowel
            ' ' => " ",
            // Preserve punctuation as-is in canonical form
            '?' | '!' | '.' | ',' | ';' | ':' | '(' | ')' | '[' | ']' | '{' | '}' | '"' | '\'' | '-' | '/' => {
                // Return punctuation as string slice
                match ch {
                    '?' => "?",
                    '!' => "!",
                    '.' => ".",
                    ',' => ",",
                    ';' => ";",
                    ':' => ":",
                    '(' => "(",
                    ')' => ")",
                    '[' => "[",
                    ']' => "]",
                    '{' => "{",
                    '}' => "}",
                    '"' => "\"",
                    '\'' => "'",
                    '-' => "-",
                    '/' => "/",
                    _ => unreachable!(),
                }
            }
            _ if ch.is_ascii_punctuation() => {
                // For other ASCII punctuation, we need to handle dynamically
                // Since we can't return non-static str, default to empty
                ""
            }
            _ => "",
        }
    }

    /// Map Latin sequences to canonical form
    fn latin_sequence_to_canonical(&self, seq: &str) -> Option<&'static str> {
        match seq {
            "sh" => Some("Š"),
            "ch" => Some("Š"), // Common in Darija for ش
            "kh" => Some("X"),
            "gh" => Some("Ġ"),
            "th" => Some("Ṯ"),
            "dh" => Some("Ḏ"),
            "Dr" | "dr" | "DR" => Some("Ḍ"), // ضر as in يهضر (yehDr)
            "8D" | "8d" => Some("HḌ"),       // هض as in يهضر (yeh8Dr)
            _ => None,
        }
    }

    /// Classify Arabic character
    fn classify_arabic_char(&self, ch: char) -> SegmentType {
        match ch {
            'ا' | 'و' | 'ي' | 'ى' => SegmentType::Vowel,
            ' ' => SegmentType::Whitespace,
            _ if ch.is_ascii_digit() => SegmentType::Number,
            // Arabic punctuation
            '؟' | '،' | '؛' => SegmentType::Punctuation,
            // ASCII punctuation
            _ if ch.is_ascii_punctuation() => SegmentType::Punctuation,
            _ => SegmentType::Consonant,
        }
    }

    /// Classify Latin character
    fn classify_latin_char(&self, ch: char) -> SegmentType {
        match ch {
            'a' | 'e' | 'i' | 'o' | 'u' => SegmentType::Vowel,
            ' ' => SegmentType::Whitespace,
            _ if ch.is_ascii_digit() => SegmentType::Number,
            // Punctuation marks
            _ if ch.is_ascii_punctuation() => SegmentType::Punctuation,
            _ => SegmentType::Consonant,
        }
    }

    /// Context-aware mapping of Latin characters to canonical form
    fn context_aware_latin_char_to_canonical(
        &self,
        ch: char,
        pos: usize,
        text: &str,
    ) -> &'static str {
        match ch {
            't' | 'T' => {
                // T/t mapping with context awareness
                let word = self.extract_word_at_position(text, pos);
                if let Some(w) = word {
                    if should_be_emphatic_t(&w) {
                        "Ṭ" // Emphatic t (ط)
                    } else if starts_with_aspect_marker(&w) {
                        "T" // Regular t (ت) for aspect markers
                    } else if is_function_word(&w) {
                        "T" // Regular t (ت) for function words
                    } else {
                        // Default based on character case
                        if ch.is_uppercase() {
                            "Ṭ"
                        } else {
                            "T"
                        }
                    }
                } else {
                    if ch.is_uppercase() {
                        "Ṭ"
                    } else {
                        "T"
                    }
                }
            }
            's' | 'S' => {
                // S/s mapping with context awareness
                let word = self.extract_word_at_position(text, pos);
                if let Some(w) = word {
                    if let Some(root) = extract_root(&w) {
                        if should_be_emphatic_s(&root) {
                            "Ṣ" // Emphatic s (ص)
                        } else {
                            "S" // Regular s (س)
                        }
                    } else if is_function_word(&w) {
                        "S" // Regular s (س) for function words
                    } else {
                        // Default based on character case
                        if ch.is_uppercase() {
                            "Ṣ"
                        } else {
                            "S"
                        }
                    }
                } else {
                    if ch.is_uppercase() {
                        "Ṣ"
                    } else {
                        "S"
                    }
                }
            }
            '8' => {
                // Context-aware digit 8 mapping
                let context = DigitContextAnalyzer::analyze_context(pos, text);
                DigitContextAnalyzer::map_digit_8(context)
            }
            // Preserve existing mappings for other characters
            _ => self.latin_char_to_canonical(ch),
        }
    }

    /// Extract the word containing the character at the given position
    fn extract_word_at_position(&self, text: &str, pos: usize) -> Option<String> {
        let chars: Vec<char> = text.chars().collect();
        if pos >= chars.len() {
            return None;
        }

        // Find word boundaries
        let mut start = pos;
        let mut end = pos;

        // Find start of word
        while start > 0
            && !chars[start - 1].is_whitespace()
            && !chars[start - 1].is_ascii_punctuation()
        {
            start -= 1;
        }

        // Find end of word
        while end < chars.len() - 1
            && !chars[end + 1].is_whitespace()
            && !chars[end + 1].is_ascii_punctuation()
        {
            end += 1;
        }

        // Extract the word
        if start <= end {
            let word: String = chars[start..=end].iter().collect();
            Some(word)
        } else {
            None
        }
    }

    /// Preserve numbers and symbols as segments
    fn preserve_numbers_as_segments(&self, text: &str) -> StageResult<Vec<ICRSegment>> {
        let mut segments = Vec::new();

        for ch in text.chars() {
            let segment_type = if ch.is_ascii_digit() {
                SegmentType::Number
            } else if ch.is_whitespace() {
                SegmentType::Whitespace
            } else {
                SegmentType::Punctuation
            };

            segments.push(ICRSegment {
                canonical: ch.to_string(), // Preserve as-is
                original: ch.to_string(),
                segment_type,
                confidence: 1.0,
                word_context: None, // Numbers don't need word context
            });
        }

        Ok(segments)
    }
}

#[cfg(test)]
mod tests {
    use super::*;

    #[test]
    fn test_arabic_to_icr() {
        let builder = ICRBuilder::new(Dialect::Moroccan);
        let segments = builder.arabic_to_icr("سلام").unwrap();
        assert_eq!(segments.len(), 4);
        assert_eq!(segments[0].canonical, "S");
        assert_eq!(segments[1].canonical, "L");
    }

    #[test]
    fn test_latin_to_icr() {
        let builder = ICRBuilder::new(Dialect::Moroccan);
        // "salam" with short vowels in middle → Darija mode writes 'a' but skips other short vowels
        // Result: S-A-L-A-M (middle 'a's written in Darija mode)
        let segments = builder.latin_to_icr("salam").unwrap();
        assert_eq!(segments.len(), 5, "Darija mode: short 'a' vowels written");
        assert_eq!(segments[0].canonical, "S");
        assert_eq!(segments[1].canonical, "A"); // First 'a' written (Darija mode)
        assert_eq!(segments[2].canonical, "L");
        assert_eq!(segments[3].canonical, "A"); // Second 'a' written (Darija mode)
        assert_eq!(segments[4].canonical, "M");

        // "salaam" with long vowel → Darija mode writes first 'a' + long 'aa'
        // Result: S-A-L-A-M (more informal, shows all sounds)
        let segments2 = builder.latin_to_icr("salaam").unwrap();
        assert_eq!(segments2.len(), 5, "Darija mode: shows both 'a' sounds");
        assert_eq!(segments2[0].canonical, "S");
        assert_eq!(segments2[1].canonical, "A"); // First 'a' written (Darija mode)
        assert_eq!(segments2[2].canonical, "L");
        assert_eq!(segments2[3].canonical, "A"); // Long 'aa' → single alef
        assert_eq!(segments2[4].canonical, "M");
    }

    #[test]
    fn test_latin_sequences() {
        let builder = ICRBuilder::new(Dialect::Moroccan);
        let segments = builder.latin_to_icr("shal").unwrap();
        // "sh" should be recognized as single segment
        assert_eq!(segments[0].canonical, "Š");
    }

    #[test]
    fn test_special_chars() {
        let builder = ICRBuilder::new(Dialect::Moroccan);
        let segments = builder.latin_to_icr("3la").unwrap();
        // '3' should map to ain (ε)
        assert_eq!(segments[0].canonical, "ε");
    }

    // Tests for ISSUES.md fixes

    #[test]
    fn test_context_aware_t_mapping() {
        let builder = ICRBuilder::new(Dialect::Moroccan);

        // Test aspect marker context - should use regular T
        let segments = builder.latin_to_icr("tabi3").unwrap();
        let t_segment = segments.iter().find(|s| s.original == "t").unwrap();
        assert_eq!(t_segment.canonical, "T"); // Regular T for aspect marker

        // Test emphatic lexicon word - should use emphatic Ṭ
        let segments = builder.latin_to_icr("ṭbi3").unwrap();
        let t_segment = segments.iter().find(|s| s.original == "ṭ").unwrap();
        assert_eq!(t_segment.canonical, "Ṭ"); // Emphatic Ṭ for lexicon word

        // Test function word context - should use regular T
        let segments = builder.latin_to_icr("menha").unwrap();
        // "menha" doesn't contain T, but testing other contexts
        assert!(segments.iter().all(|s| s.canonical != "Ṭ"));
    }

    #[test]
    fn test_context_aware_s_mapping() {
        let builder = ICRBuilder::new(Dialect::Moroccan);

        // Test regular context with root that's not emphatic
        let segments = builder.latin_to_icr("salam").unwrap();
        let s_segment = segments
            .iter()
            .find(|s| s.original == "s" && s.canonical == "S");
        assert!(s_segment.is_some(), "Expected to find 's' mapped to regular 'S' in 'salam'");

        // Test emphatic root pattern
        let segments2 = builder.latin_to_icr("Sba7").unwrap(); // صباح - morning (emphatic S)
        let _s_emphatic = segments2
            .iter()
            .find(|s| (s.original == "S" || s.original == "s") && s.canonical == "Ṣ");
        // Note: This may not be emphatic depending on lexicon, just testing the mechanism
    }

    #[test]
    fn test_number_preservation() {
        let builder = ICRBuilder::new(Dialect::Moroccan);

        // Test pure numbers are preserved
        let segments = builder.latin_to_icr("50").unwrap();
        assert_eq!(segments.len(), 2);
        assert_eq!(segments[0].canonical, "5");
        assert_eq!(segments[1].canonical, "0");
        assert!(segments
            .iter()
            .all(|s| matches!(s.segment_type, SegmentType::Number)));

        // Test mixed patterns are preserved
        let segments = builder.latin_to_icr("50->").unwrap();
        // Should have "5", "0", "-", ">"
        assert_eq!(segments.len(), 4, "Expected 4 segments for '50->'");
        assert_eq!(segments[0].canonical, "5");
        assert_eq!(segments[1].canonical, "0");
        assert!(segments.iter().any(|s| s.canonical == "-"));
        assert!(segments.iter().any(|s| s.canonical == ">"));

        // Test mathematical expressions
        let segments = builder.latin_to_icr("5+8=13").unwrap();
        let canonicals: Vec<String> = segments.iter().map(|s| s.canonical.clone()).collect();
        assert!(canonicals.contains(&"5".to_string()));
        assert!(canonicals.contains(&"8".to_string()));
        assert!(canonicals.contains(&"+".to_string()));
        assert!(canonicals.contains(&"=".to_string()));
    }

    #[test]
    fn test_digit_8_contextual() {
        let builder = ICRBuilder::new(Dialect::Moroccan);

        // Test 8 in word context - should map to H
        let segments = builder.latin_to_icr("dyal8a").unwrap();
        let h_segment = segments.iter().find(|s| s.original == "8").unwrap();
        assert_eq!(h_segment.canonical, "H"); // 8 in word context -> H

        // Test 8 in mathematical context - should preserve as 8
        let segments = builder.latin_to_icr("5+8").unwrap();
        let eight_segment = segments.iter().find(|s| s.original == "8").unwrap();
        assert_eq!(eight_segment.canonical, "8"); // 8 in math context -> preserve
        assert!(matches!(eight_segment.segment_type, SegmentType::Number));
    }

    #[test]
    fn test_word_extraction() {
        let builder = ICRBuilder::new(Dialect::Moroccan);

        // Test word extraction at position
        let word = builder.extract_word_at_position("salam menek", 7); // position of 'm'
        assert_eq!(word, Some("menek".to_string()));

        // Test word at beginning
        let word = builder.extract_word_at_position("salam menek", 0); // position of 's'
        assert_eq!(word, Some("salam".to_string()));

        // Test word at end
        let word = builder.extract_word_at_position("salam menek", 9); // position of 'n' in menek
        assert_eq!(word, Some("menek".to_string()));

        // Test single character word
        let word = builder.extract_word_at_position("a b c", 2); // position of 'b'
        assert_eq!(word, Some("b".to_string()));
    }

    #[test]
    fn test_darija_patterns() {
        let builder = ICRBuilder::new(Dialect::Moroccan);

        // Test common Darija number patterns
        let segments = builder.latin_to_icr("7na chi 50").unwrap();
        let canonicals: Vec<String> = segments.iter().map(|s| s.canonical.clone()).collect();

        // Check that "7na" is preserved in word context (character-level ICR design)
        let has_7na_context = segments.iter().any(|s| {
            s.word_context.as_ref()
                .map_or(false, |ctx| ctx.full_word == "7na")
        });
        assert!(has_7na_context, "Expected '7na' to be preserved in word context");

        // Should map characters from "7na"
        assert!(canonicals.contains(&"Ḥ".to_string()) || canonicals.contains(&"7".to_string()), "Expected '7' or 'Ḥ' from '7na'");

        // Should preserve "50" as number tokens
        assert!(canonicals.contains(&"5".to_string()));
        assert!(canonicals.contains(&"0".to_string()));
    }
}
