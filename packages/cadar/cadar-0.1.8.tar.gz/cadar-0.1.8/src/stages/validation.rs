use super::{StageError, StageResult};
use crate::types::{Dialect, Script};
use regex::Regex;

/// Stage 6: Post-validation & Fixes
/// Validates and fixes the generated output
pub struct Validator {
    dialect: Dialect,
    /// Common Arabic patterns for validation
    _arabic_word_pattern: Regex,
    /// Common Latin patterns for validation
    _latin_word_pattern: Regex,
}

impl Validator {
    pub fn new(dialect: Dialect) -> Self {
        Validator {
            dialect,
            _arabic_word_pattern: Regex::new(r"[\u{0600}-\u{06FF}]+").unwrap(),
            _latin_word_pattern: Regex::new(r"[a-zA-Z0-9]+").unwrap(),
        }
    }

    /// Validate and fix the generated text
    pub fn validate_and_fix(&self, text: &str, target_script: Script) -> StageResult<String> {
        if text.is_empty() {
            return Err(StageError::Validation("Empty text".to_string()));
        }

        let mut fixed = text.to_string();

        // Step 1: Script consistency check
        fixed = self.ensure_script_consistency(&fixed, target_script)?;

        // Step 2: Fix common transliteration errors
        fixed = self.fix_common_errors(&fixed, target_script);

        // Step 3: Validate word structure
        self.validate_word_structure(&fixed, target_script)?;

        // Step 4: Fix spacing issues
        fixed = self.fix_spacing(&fixed);

        // Step 5: Apply dialect-specific fixes
        fixed = self.apply_dialect_fixes(&fixed, target_script);

        Ok(fixed)
    }

    /// Ensure script consistency
    fn ensure_script_consistency(&self, text: &str, target_script: Script) -> StageResult<String> {
        let detected = Script::detect(text);

        match (target_script, detected) {
            (Script::Arabic, Script::Arabic) | (Script::Latin, Script::Latin) => {
                Ok(text.to_string())
            }

            (Script::Arabic, Script::Mixed) => {
                // Remove Latin characters from Arabic text
                Ok(text
                    .chars()
                    .filter(|c| Script::from_char(*c) != Script::Latin)
                    .collect())
            }

            (Script::Latin, Script::Mixed) => {
                // Remove Arabic characters from Latin text
                Ok(text
                    .chars()
                    .filter(|c| Script::from_char(*c) != Script::Arabic)
                    .collect())
            }

            _ => Err(StageError::Validation(format!(
                "Script mismatch: expected {:?}, got {:?}",
                target_script, detected
            ))),
        }
    }

    /// Fix common transliteration errors
    fn fix_common_errors(&self, text: &str, target_script: Script) -> String {
        let mut fixed = text.to_string();

        match target_script {
            Script::Arabic => {
                // Fix duplicate Arabic characters
                fixed = self.remove_duplicate_chars(&fixed);

                // Fix teh marbuta at end of words
                fixed = Regex::new(r"ت(\s|$)")
                    .unwrap()
                    .replace_all(&fixed, "ة$1")
                    .to_string();
            }

            Script::Latin => {
                // Fix duplicate Latin characters
                fixed = self.remove_duplicate_chars(&fixed);

                // Normalize common Darija representations
                fixed = fixed.replace("33", "3"); // Double 'ayn
                fixed = fixed.replace("77", "7"); // Double 7a
            }

            _ => {}
        }

        fixed
    }

    /// Remove duplicate consecutive characters
    fn remove_duplicate_chars(&self, text: &str) -> String {
        let mut result = String::new();
        let mut chars = text.chars().peekable();

        while let Some(ch) = chars.next() {
            result.push(ch);

            // Skip consecutive duplicates of the same character
            // But preserve spaces and punctuation
            if !ch.is_whitespace() && !matches!(ch, '.' | ',' | '!' | '?' | ';' | ':') {
                while let Some(&next_ch) = chars.peek() {
                    if next_ch == ch {
                        chars.next(); // Skip the duplicate
                    } else {
                        break;
                    }
                }
            }
        }

        result
    }

    /// Validate word structure
    fn validate_word_structure(&self, text: &str, target_script: Script) -> StageResult<()> {
        let words: Vec<&str> = text.split_whitespace().collect();

        if words.is_empty() {
            return Err(StageError::Validation("No words found".to_string()));
        }

        for word in words {
            match target_script {
                Script::Arabic => {
                    if !self.is_valid_arabic_word(word) {
                        return Err(StageError::Validation(format!(
                            "Invalid Arabic word structure: {}",
                            word
                        )));
                    }
                }
                Script::Latin => {
                    if !self.is_valid_latin_word(word) {
                        return Err(StageError::Validation(format!(
                            "Invalid Latin word structure: {}",
                            word
                        )));
                    }
                }
                _ => {}
            }
        }

        Ok(())
    }

    /// Check if word is valid Arabic
    fn is_valid_arabic_word(&self, word: &str) -> bool {
        if word.is_empty() {
            return false;
        }

        // Allow pure numbers (valid in mixed Arabic/numeric text)
        if word.chars().all(|c| c.is_ascii_digit()) {
            return true;
        }

        // Allow punctuation and symbols (valid in Arabic text)
        // Include both ASCII punctuation and Arabic punctuation
        if word.chars().all(|c| c.is_ascii_punctuation() || matches!(c, '؟' | '،' | '؛')) {
            return true;
        }

        // Allow date/number patterns with separators (e.g., "12/20", "2,15")
        // Include both ASCII and Arabic separators
        if word.chars().all(|c| c.is_ascii_digit() || matches!(c, '/' | ',' | '.' | '-' | ':' | '،')) {
            return true;
        }

        // Should contain at least some Arabic characters
        let has_arabic = word
            .chars()
            .any(|c| matches!(Script::from_char(c), Script::Arabic));

        // Only check start character if word has Arabic characters
        if has_arabic {
            let first_char = word.chars().next().unwrap();
            // Don't allow starting with diacritics (but taa marbuta ة is OK in middle/end)
            let valid_start = !matches!(first_char, 'ّ' | 'ً' | 'ٌ' | 'ٍ');
            return valid_start;
        }

        // If no Arabic chars and not number/punct, it's invalid
        false
    }

    /// Check if word is valid Latin
    fn is_valid_latin_word(&self, word: &str) -> bool {
        if word.is_empty() {
            return false;
        }

        // Allow pure numbers (valid in mixed Latin/numeric text)
        if word.chars().all(|c| c.is_ascii_digit()) {
            return true;
        }

        // Allow punctuation and symbols (valid in Latin text)
        if word.chars().all(|c| c.is_ascii_punctuation()) {
            return true;
        }

        // Allow date/number patterns with separators
        if word.chars().all(|c| c.is_ascii_digit() || matches!(c, '/' | ',' | '.' | '-' | ':')) {
            return true;
        }

        // Should contain at least some Latin or numeric characters
        let has_latin = word
            .chars()
            .any(|c| c.is_ascii_alphanumeric() || matches!(c, '3' | '7' | '9'));

        has_latin
    }

    /// Fix spacing issues
    fn fix_spacing(&self, text: &str) -> String {
        let mut fixed = text.to_string();

        // Normalize multiple spaces to single space
        fixed = Regex::new(r"\s+")
            .unwrap()
            .replace_all(&fixed, " ")
            .to_string();

        // Fix spacing around punctuation
        fixed = Regex::new(r"\s+([.,!?;:])")
            .unwrap()
            .replace_all(&fixed, "$1")
            .to_string();

        fixed = Regex::new(r"([.,!?;:])\s*")
            .unwrap()
            .replace_all(&fixed, "$1 ")
            .to_string();

        // Trim
        fixed.trim().to_string()
    }

    /// Apply dialect-specific fixes
    fn apply_dialect_fixes(&self, text: &str, target_script: Script) -> String {
        match self.dialect {
            Dialect::Moroccan => self.apply_moroccan_fixes(text, target_script),
        }
    }

    /// Apply Moroccan Darija specific fixes
    fn apply_moroccan_fixes(&self, text: &str, target_script: Script) -> String {
        let mut fixed = text.to_string();

        match target_script {
            Script::Arabic => {
                // Common Moroccan patterns
                fixed = fixed.replace("كيف اش", "كيفاش");
                fixed = fixed.replace("شن و", "شنو");
                fixed = fixed.replace("في ن", "فين");
            }

            Script::Latin => {
                // Common Moroccan patterns in Latin
                fixed = fixed.replace("ki fash", "kifash");
                fixed = fixed.replace("sh no", "shno");
                fixed = fixed.replace("wa kha", "wakha");
                fixed = fixed.replace("b zaf", "bzaf");
            }

            _ => {}
        }

        fixed
    }
}

#[cfg(test)]
mod tests {
    use super::*;

    #[test]
    fn test_arabic_validation() {
        let validator = Validator::new(Dialect::Moroccan);
        let result = validator
            .validate_and_fix("كيفاش داير", Script::Arabic)
            .unwrap();
        assert!(!result.is_empty());
    }

    #[test]
    fn test_latin_validation() {
        let validator = Validator::new(Dialect::Moroccan);
        let result = validator
            .validate_and_fix("kifash dayer", Script::Latin)
            .unwrap();
        assert!(!result.is_empty());
    }

    #[test]
    fn test_double_char_fix_arabic() {
        let validator = Validator::new(Dialect::Moroccan);
        let result = validator.validate_and_fix("ساالام", Script::Arabic).unwrap();
        assert!(!result.contains("اا"), "Should remove duplicate alef");
    }

    #[test]
    fn test_double_char_fix_latin() {
        let validator = Validator::new(Dialect::Moroccan);
        let result = validator.validate_and_fix("salaam", Script::Latin).unwrap();
        assert!(!result.contains("aa"), "Should remove duplicate a");
    }

    #[test]
    fn test_remove_all_duplicates_arabic() {
        let validator = Validator::new(Dialect::Moroccan);
        let result = validator
            .validate_and_fix("مبررردين", Script::Arabic)
            .unwrap();
        assert_eq!(result, "مبردين", "Should remove all duplicate ر");
    }

    #[test]
    fn test_remove_all_duplicates_latin() {
        let validator = Validator::new(Dialect::Moroccan);
        let result = validator
            .validate_and_fix("hellooo worrlld", Script::Latin)
            .unwrap();
        assert!(!result.contains("ooo"), "Should remove duplicate o");
        assert!(!result.contains("rr"), "Should remove duplicate r");
    }

    #[test]
    fn test_spacing_fix() {
        let validator = Validator::new(Dialect::Moroccan);
        let result = validator
            .validate_and_fix("helo    world  test", Script::Latin)
            .unwrap();
        // Multiple spaces should be normalized to single space
        let space_count = result.chars().filter(|&c| c == ' ').count();
        assert_eq!(space_count, 2, "Should have exactly 2 spaces");
        assert!(!result.contains("  "), "Should not have double spaces");
    }

    #[test]
    fn test_moroccan_pattern_fix() {
        let validator = Validator::new(Dialect::Moroccan);
        let result = validator
            .validate_and_fix("ki fash dayer", Script::Latin)
            .unwrap();
        assert!(result.contains("kifash"));
    }

    #[test]
    fn test_empty_text() {
        let validator = Validator::new(Dialect::Moroccan);
        assert!(validator.validate_and_fix("", Script::Arabic).is_err());
    }
}
