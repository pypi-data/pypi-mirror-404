use super::{StageError, StageResult};
use crate::types::Script;
use regex::Regex;
use unicode_normalization::UnicodeNormalization;

/// Stage 2: Noise Cleaning & Normalization
/// Cleans and normalizes text input
pub struct Normalizer {
    /// Regex for excessive spaces
    excessive_spaces: Regex,
}

impl Normalizer {
    pub fn new() -> Self {
        Normalizer {
            excessive_spaces: Regex::new(r"\s+").unwrap(),
        }
    }

    /// Normalize text based on detected script
    pub fn normalize(&self, text: &str, script: Script) -> StageResult<String> {
        let mut normalized = text.to_string();

        // Step 1: Unicode normalization (NFD decomposition then NFC composition)
        normalized = normalized.nfc().collect::<String>();

        // Step 2: Remove zero-width characters and other invisible characters
        normalized = self.remove_invisible_chars(&normalized);

        // Step 3: Normalize Arabic-specific characters
        if matches!(script, Script::Arabic | Script::Mixed) {
            normalized = self.normalize_arabic(&normalized);
        }

        // Step 4: Normalize Latin-specific characters
        if matches!(script, Script::Latin | Script::Mixed) {
            normalized = self.normalize_latin(&normalized);
        }

        // Step 5: Remove repeated characters (e.g., "hellooooo" -> "hello")
        normalized = self.fix_repeated_chars(&normalized);

        // Step 6: Normalize whitespace
        normalized = self.normalize_whitespace(&normalized);

        // Step 7: Trim edges
        normalized = normalized.trim().to_string();

        if normalized.is_empty() {
            return Err(StageError::Normalization(
                "Normalization resulted in empty text".to_string(),
            ));
        }

        Ok(normalized)
    }

    /// Remove invisible Unicode characters
    fn remove_invisible_chars(&self, text: &str) -> String {
        text.chars()
            .filter(|c| {
                !matches!(
                    *c,
                    '\u{200B}' | // Zero-width space
                    '\u{200C}' | // Zero-width non-joiner
                    '\u{200D}' | // Zero-width joiner
                    '\u{FEFF}' | // Zero-width no-break space
                    '\u{202A}' | // Left-to-right embedding
                    '\u{202B}' | // Right-to-left embedding
                    '\u{202C}' | // Pop directional formatting
                    '\u{202D}' | // Left-to-right override
                    '\u{202E}' // Right-to-left override
                )
            })
            .collect()
    }

    /// Normalize Arabic-specific characters
    fn normalize_arabic(&self, text: &str) -> String {
        text.chars()
            .map(|c| match c {
                // Normalize Alef variants to standard Alef
                '\u{0622}' | '\u{0623}' | '\u{0625}' => '\u{0627}', // أ، إ، آ -> ا

                // Normalize Teh Marbuta
                '\u{0629}' => '\u{0629}', // ة (keep as is for now)

                // Remove Tatweel (kashida)
                '\u{0640}' => ' ',

                // Normalize Yeh variants
                '\u{0649}' | '\u{06CC}' => '\u{064A}', // ى، ی -> ي

                // Remove diacritics (tashkeel)
                '\u{064B}'..='\u{065F}' => '\0', // Fatha, Damma, Kasra, Sukun, etc.
                '\u{0670}' => '\0',              // Superscript Alef

                _ => c,
            })
            .filter(|&c| c != '\0')
            .collect()
    }

    /// Normalize Latin-specific characters
    fn normalize_latin(&self, text: &str) -> String {
        text.chars()
            .map(|c| match c {
                // Common Darija Latin variations
                '3' => 'ε', // Use epsilon for 'ayn
                '7' => 'ḥ', // Use h with dot below
                '9' => 'q', // 9 often represents qaf

                // Normalize case (lowercase for consistency)
                'A'..='Z' => c.to_ascii_lowercase(),

                _ => c,
            })
            .collect()
    }

    /// Fix repeated characters (allow max 2 repetitions)
    fn fix_repeated_chars(&self, text: &str) -> String {
        let mut result = String::new();
        let mut chars = text.chars().peekable();

        while let Some(ch) = chars.next() {
            result.push(ch);
            let mut count = 1;

            // Count consecutive identical characters
            while let Some(&next_ch) = chars.peek() {
                if next_ch == ch {
                    count += 1;
                    chars.next();
                } else {
                    break;
                }
            }

            // If more than 2 repetitions, add one more (max 2 total)
            if count >= 2 {
                result.push(ch);
            }
        }

        result
    }

    /// Normalize whitespace
    fn normalize_whitespace(&self, text: &str) -> String {
        self.excessive_spaces.replace_all(text, " ").to_string()
    }
}

impl Default for Normalizer {
    fn default() -> Self {
        Self::new()
    }
}

#[cfg(test)]
mod tests {
    use super::*;

    #[test]
    fn test_arabic_normalization() {
        let normalizer = Normalizer::new();
        let result = normalizer
            .normalize("أنَا مِنْ المَغْرِب", Script::Arabic)
            .unwrap();
        // Should remove diacritics and normalize Alef
        assert!(!result.contains('\u{064E}')); // No Fatha
        assert!(result.contains('ا')); // Standard Alef
    }

    #[test]
    fn test_latin_normalization() {
        let normalizer = Normalizer::new();
        let result = normalizer
            .normalize("ana mn l m3rib", Script::Latin)
            .unwrap();
        // Should normalize 3 to epsilon
        assert!(result.contains('ε'));
    }

    #[test]
    fn test_repeated_chars() {
        let normalizer = Normalizer::new();
        let result = normalizer.normalize("hellooooo", Script::Latin).unwrap();
        assert_eq!(result, "helloo"); // Max 2 repetitions
    }

    #[test]
    fn test_whitespace_normalization() {
        let normalizer = Normalizer::new();
        let result = normalizer
            .normalize("hello    world  test", Script::Latin)
            .unwrap();
        assert_eq!(result, "hello world test");
    }

    #[test]
    fn test_remove_invisible_chars() {
        let normalizer = Normalizer::new();
        let text = "hello\u{200B}world"; // With zero-width space
        let result = normalizer.remove_invisible_chars(text);
        assert_eq!(result, "helloworld");
    }
}
