/// Vowel handling for Darija transliteration
///
/// Darija distinguishes between:
/// - Long vowels (aa, ee, ii, oo, uu) → written as matres lectionis (ا، ي، و)
/// - Short vowels (a, e, i, o, u) → context-dependent, often omitted

#[derive(Debug, Clone, Copy, PartialEq)]
pub enum VowelMode {
    /// Standard Arabic mode: skip most short middle vowels (more compact)
    Standard,
    /// Darija mode: write more vowels for readability (informal style)
    Darija,
}

#[derive(Debug, Clone, Copy, PartialEq)]
pub enum VowelLength {
    Short,  // a, e, i, o, u
    Long,   // aa, ee, ii, oo, uu
}

#[derive(Debug, Clone, Copy, PartialEq)]
pub enum VowelType {
    A,  // a/aa → ا
    I,  // i/ii/e/ee → ي
    U,  // u/uu/o/oo → و
}

#[derive(Debug, Clone, PartialEq)]
pub struct VowelInfo {
    pub vowel_type: VowelType,
    pub length: VowelLength,
    pub position_in_word: VowelPosition,
}

#[derive(Debug, Clone, Copy, PartialEq)]
pub enum VowelPosition {
    Start,
    Middle,
    End,
}

/// Analyze vowel context in a word
pub struct VowelAnalyzer;

impl VowelAnalyzer {
    /// Detect if character at position is part of a long vowel
    /// Returns: (is_long_vowel, chars_to_skip)
    pub fn detect_long_vowel(chars: &[char], pos: usize) -> (bool, usize) {
        if pos >= chars.len() {
            return (false, 0);
        }

        let current = chars[pos];

        // Check if current char is a vowel
        if !Self::is_vowel_char(current) {
            return (false, 0);
        }

        // Check for double vowel (aa, ee, ii, oo, uu)
        if pos + 1 < chars.len() && chars[pos + 1] == current {
            return (true, 2); // Skip both characters
        }

        // Single vowel
        (false, 1)
    }

    /// Check if character is a vowel
    pub fn is_vowel_char(ch: char) -> bool {
        matches!(ch, 'a' | 'e' | 'i' | 'o' | 'u' | 'A' | 'E' | 'I' | 'O' | 'U')
    }

    /// Get vowel type from character
    pub fn get_vowel_type(ch: char) -> Option<VowelType> {
        match ch.to_ascii_lowercase() {
            'a' => Some(VowelType::A),
            'e' | 'i' => Some(VowelType::I),
            'o' | 'u' => Some(VowelType::U),
            _ => None,
        }
    }

    /// Determine vowel position in word
    pub fn get_vowel_position(pos: usize, word_len: usize) -> VowelPosition {
        if pos == 0 {
            VowelPosition::Start
        } else if pos >= word_len - 1 {
            VowelPosition::End
        } else {
            VowelPosition::Middle
        }
    }

    /// Analyze vowel at position
    pub fn analyze_vowel(chars: &[char], pos: usize) -> Option<VowelInfo> {
        if pos >= chars.len() {
            return None;
        }

        let ch = chars[pos];
        let vowel_type = Self::get_vowel_type(ch)?;
        let (is_long, _) = Self::detect_long_vowel(chars, pos);
        let length = if is_long {
            VowelLength::Long
        } else {
            VowelLength::Short
        };
        let position_in_word = Self::get_vowel_position(pos, chars.len());

        Some(VowelInfo {
            vowel_type,
            length,
            position_in_word,
        })
    }

    /// Should this vowel be written in Arabic?
    ///
    /// Rules depend on mode:
    ///
    /// **Standard Mode** (strict Arabic orthography):
    /// 1. Long vowels (aa, ee, ii, oo, uu) → always written
    /// 2. Short vowels at start → written
    /// 3. Short vowels at end → written (Darija characteristic)
    /// 4. Short vowels in middle → NOT written
    ///
    /// **Darija Mode** (informal, readable):
    /// 1. Long vowels → always written
    /// 2. Short vowels at start → written
    /// 3. Short vowels at end → written
    /// 4. Short 'a', 'o', 'u' in middle → written (more readable)
    /// 5. Short 'e', 'i' in middle → skipped (often absorbed)
    pub fn should_write_vowel_in_arabic(vowel_info: &VowelInfo, mode: VowelMode) -> bool {
        match vowel_info.length {
            VowelLength::Long => true, // Always write long vowels
            VowelLength::Short => {
                match vowel_info.position_in_word {
                    VowelPosition::Start => true, // Write all initial vowels
                    VowelPosition::End => true,   // Write all final vowels (Darija)
                    VowelPosition::Middle => {
                        match mode {
                            VowelMode::Standard => false, // Skip ALL short middle vowels
                            VowelMode::Darija => {
                                // In Darija mode, write 'a', 'o', 'u' for readability
                                // Skip 'e', 'i' (often absorbed in Darija)
                                match vowel_info.vowel_type {
                                    VowelType::A | VowelType::U => true,  // Write a/o/u
                                    VowelType::I => false, // Skip e/i (like "imken")
                                }
                            }
                        }
                    }
                }
            }
        }
    }

    /// Map vowel to canonical form based on analysis and mode
    pub fn vowel_to_canonical(vowel_info: &VowelInfo, mode: VowelMode) -> &'static str {
        if !Self::should_write_vowel_in_arabic(vowel_info, mode) {
            return ""; // Skip this vowel
        }

        match vowel_info.vowel_type {
            VowelType::A => "A", // → ا
            VowelType::I => "I", // → ي
            VowelType::U => "U", // → و
        }
    }

    /// Detect if Arabic mater lectionis represents a long vowel
    /// Used for Arabic → Latin conversion
    ///
    /// Rules:
    /// 1. ا between consonants in middle → usually long "aa"
    /// 2. ا at word end → short "a"
    /// 3. ي between consonants → could be long "ii"/"ee" or consonant "y"
    /// 4. و between consonants → could be long "oo"/"uu" or consonant "w"
    pub fn is_long_vowel_in_arabic(
        ch: char,
        pos: usize,
        chars: &[char],
    ) -> bool {
        if pos >= chars.len() {
            return false;
        }

        // Check previous and next characters
        let has_prev_consonant = if pos > 0 {
            let prev = chars[pos - 1];
            Self::is_arabic_consonant(prev)
        } else {
            false
        };

        let has_next_consonant = if pos + 1 < chars.len() {
            let next = chars[pos + 1];
            Self::is_arabic_consonant(next)
        } else {
            false
        };

        match ch {
            'ا' => {
                // Alef between consonants → long "aa"
                // Alef at end or start → short "a"
                has_prev_consonant && has_next_consonant
            }
            'ي' => {
                // Ya between consonants → could be long "ii" or consonant "y"
                // For now, treat as long vowel if between consonants in middle
                has_prev_consonant && has_next_consonant && pos > 0 && pos < chars.len() - 1
            }
            'و' => {
                // Waw between consonants → could be long "oo" or consonant "w"
                // For now, treat as long vowel if between consonants in middle
                has_prev_consonant && has_next_consonant && pos > 0 && pos < chars.len() - 1
            }
            _ => false,
        }
    }

    /// Check if character is an Arabic consonant
    fn is_arabic_consonant(ch: char) -> bool {
        matches!(ch,
            'ب' | 'ت' | 'ث' | 'ج' | 'ح' | 'خ' | 'د' | 'ذ' | 'ر' | 'ز' |
            'س' | 'ش' | 'ص' | 'ض' | 'ط' | 'ظ' | 'ع' | 'غ' | 'ف' | 'ق' |
            'ك' | 'ل' | 'م' | 'ن' | 'ه' | 'ة'
        )
    }

    /// Convert Arabic mater lectionis to Latin (considering length)
    pub fn arabic_vowel_to_latin(ch: char, is_long: bool) -> &'static str {
        match ch {
            'ا' => if is_long { "aa" } else { "a" },
            'ي' | 'ى' => if is_long { "ii" } else { "i" },
            'و' => if is_long { "uu" } else { "u" },
            _ => "",
        }
    }
}

#[cfg(test)]
mod tests {
    use super::*;

    #[test]
    fn test_long_vowel_detection() {
        let word1: Vec<char> = "salaam".chars().collect();
        let (is_long, skip) = VowelAnalyzer::detect_long_vowel(&word1, 3); // First 'a' in 'aa'
        assert!(is_long);
        assert_eq!(skip, 2);

        let word2: Vec<char> = "salam".chars().collect();
        let (is_long, skip) = VowelAnalyzer::detect_long_vowel(&word2, 1); // Single 'a'
        assert!(!is_long);
        assert_eq!(skip, 1);
    }

    #[test]
    fn test_vowel_type_detection() {
        assert_eq!(VowelAnalyzer::get_vowel_type('a'), Some(VowelType::A));
        assert_eq!(VowelAnalyzer::get_vowel_type('e'), Some(VowelType::I));
        assert_eq!(VowelAnalyzer::get_vowel_type('i'), Some(VowelType::I));
        assert_eq!(VowelAnalyzer::get_vowel_type('o'), Some(VowelType::U));
        assert_eq!(VowelAnalyzer::get_vowel_type('u'), Some(VowelType::U));
    }

    #[test]
    fn test_should_write_vowel_standard_mode() {
        // Long vowel - always write
        let long_a = VowelInfo {
            vowel_type: VowelType::A,
            length: VowelLength::Long,
            position_in_word: VowelPosition::Middle,
        };
        assert!(VowelAnalyzer::should_write_vowel_in_arabic(&long_a, VowelMode::Standard));

        // Short vowel in middle - skip in standard mode
        let short_a_middle = VowelInfo {
            vowel_type: VowelType::A,
            length: VowelLength::Short,
            position_in_word: VowelPosition::Middle,
        };
        assert!(!VowelAnalyzer::should_write_vowel_in_arabic(&short_a_middle, VowelMode::Standard));

        // Short 'a' at start - write
        let short_a_start = VowelInfo {
            vowel_type: VowelType::A,
            length: VowelLength::Short,
            position_in_word: VowelPosition::Start,
        };
        assert!(VowelAnalyzer::should_write_vowel_in_arabic(&short_a_start, VowelMode::Standard));

        // Short vowel at end - write (Darija specific)
        let short_a_end = VowelInfo {
            vowel_type: VowelType::A,
            length: VowelLength::Short,
            position_in_word: VowelPosition::End,
        };
        assert!(VowelAnalyzer::should_write_vowel_in_arabic(&short_a_end, VowelMode::Standard));
    }

    #[test]
    fn test_should_write_vowel_darija_mode() {
        // Short 'a' in middle - write in Darija mode
        let short_a_middle = VowelInfo {
            vowel_type: VowelType::A,
            length: VowelLength::Short,
            position_in_word: VowelPosition::Middle,
        };
        assert!(VowelAnalyzer::should_write_vowel_in_arabic(&short_a_middle, VowelMode::Darija));

        // Short 'e'/'i' in middle - skip even in Darija mode
        let short_e_middle = VowelInfo {
            vowel_type: VowelType::I,
            length: VowelLength::Short,
            position_in_word: VowelPosition::Middle,
        };
        assert!(!VowelAnalyzer::should_write_vowel_in_arabic(&short_e_middle, VowelMode::Darija));
    }
}
