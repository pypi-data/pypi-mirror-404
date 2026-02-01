use serde::{Deserialize, Serialize};

/// Context-aware digit mappings for Darija
#[derive(Debug, Clone, Copy, PartialEq, Eq, Hash, Serialize, Deserialize)]
pub enum DigitContext {
    /// Used in mathematical expressions (preserve as digit)
    Mathematical,
    /// Used as part of a word (map to appropriate letter)
    WordContext,
    /// Used as separator or punctuation (preserve)
    Separator,
}

/// Context patterns for digit 8 mapping
pub struct DigitContextAnalyzer;

impl DigitContextAnalyzer {
    pub fn new() -> Self {
        Self
    }

    /// Determine the context type for a digit based on surrounding characters
    pub fn analyze_context(digit_pos: usize, text: &str) -> DigitContext {
        let chars: Vec<char> = text.chars().collect();

        if digit_pos >= chars.len() {
            return DigitContext::WordContext;
        }

        let char = chars[digit_pos];

        // Check if it's surrounded by mathematical operators
        let prev_char = if digit_pos > 0 {
            Some(chars[digit_pos - 1])
        } else {
            None
        };
        let next_char = if digit_pos + 1 < chars.len() {
            Some(chars[digit_pos + 1])
        } else {
            None
        };

        // If current char is a separator symbol, check if it's part of a number pattern
        if matches!(char, ':' | '-' | '>') {
            // Check if preceded by a digit
            if prev_char.map_or(false, |c| c.is_ascii_digit()) {
                return DigitContext::Separator;
            }
        }

        // For digits, check separator patterns first before mathematical context
        if char.is_ascii_digit() {
            // Separator context: part of number patterns with special symbols
            if Self::is_separator_pattern(digit_pos, &chars) {
                return DigitContext::Separator;
            }

            // Mathematical context: surrounded by operators or other digits
            let is_math_prev = matches!(
                prev_char,
                Some('+' | '-' | '*' | '/' | '=' | '>' | '<' | '|')
            ) || prev_char
                .map_or(false, |c| c.is_ascii_digit() || c.is_whitespace());
            let is_math_next = matches!(
                next_char,
                Some('+' | '-' | '*' | '/' | '=' | '>' | '<' | '|')
            ) || next_char
                .map_or(false, |c| c.is_ascii_digit() || c.is_whitespace());

            if is_math_prev || is_math_next {
                return DigitContext::Mathematical;
            }
        }

        // Default to word context
        DigitContext::WordContext
    }

    /// Check if this is part of a separator pattern like "->"
    fn is_separator_pattern(pos: usize, chars: &[char]) -> bool {
        // Look for patterns like "82:" "50->" etc.
        let prev_char = if pos > 0 { chars[pos - 1] } else { '\0' };
        let next_char = if pos + 1 < chars.len() {
            chars[pos + 1]
        } else {
            '\0'
        };

        // Check for colon after number (line numbers, etc.)
        if prev_char.is_ascii_digit() && next_char == ':' {
            return true;
        }

        // Check for arrow pattern (50->, etc.)
        if prev_char.is_ascii_digit()
            && (next_char == '-' || (pos + 2 < chars.len() && chars[pos + 2] == '>'))
        {
            return true;
        }

        false
    }

    /// Map digit 8 to appropriate form based on context
    pub fn map_digit_8(context: DigitContext) -> &'static str {
        match context {
            DigitContext::Mathematical => "8", // Preserve as digit
            DigitContext::Separator => "8",    // Preserve as separator
            DigitContext::WordContext => {
                // For word context, determine between 'ه' and 'غ'
                // Most common in Darija is 'ه' (h) when it's part of possessive/conjunctive patterns
                "H" // Map to H (ه) which becomes 'h' in Latin, 'ه' in Arabic
            }
        }
    }
}

/// Number and symbol preservation patterns
pub struct NumberPreserver;

impl NumberPreserver {
    pub fn new() -> Self {
        Self
    }

    /// Check if text segment should be preserved as-is (numbers, symbols, separators)
    pub fn should_preserve(text: &str) -> bool {
        // All digits should be preserved
        if text.chars().all(|c| c.is_ascii_digit()) {
            return true;
        }

        // Common mathematical and separator symbols
        if text.chars().all(|c| {
            matches!(
                c,
                '+' | '-'
                    | '*'
                    | '/'
                    | '='
                    | '>'
                    | '<'
                    | '|'
                    | ':'
                    | '.'
                    | ','
                    | '('
                    | ')'
                    | '['
                    | ']'
                    | '{'
                    | '}'
            )
        }) {
            return true;
        }

        // Mixed number-symbol patterns like "50->" or "82:"
        if text.chars().any(|c| c.is_ascii_digit())
            && text.chars().any(|c| {
                matches!(
                    c,
                    '+' | '-'
                        | '*'
                        | '/'
                        | '='
                        | '>'
                        | '<'
                        | '|'
                        | ':'
                        | '.'
                        | ','
                        | '('
                        | ')'
                        | '['
                        | ']'
                        | '{'
                        | '}'
                )
            })
        {
            return true;
        }

        false
    }

    /// Process text segment, returning preserved form or None for normal processing
    pub fn process(text: &str) -> Option<String> {
        if Self::should_preserve(text) {
            Some(text.to_string())
        } else {
            None
        }
    }
}

/// Common Darija patterns involving numbers and symbols
pub static NUMBER_PATTERNS: &[(&str, &str)] = &[
    ("->", "->"),         // Preserve arrow
    ("<-", "<-"),         // Preserve arrow
    ("<->", "<->"),       // Preserve bidirectional arrow
    ("=>", "=>"),         // Preserve implies
    ("<=", "<="),         // Preserve less than or equal
    (">=", ">="),         // Preserve greater than or equal
    ("7na", "7na"),       // Common: حنا (we) - preserve 7 notation
    ("3la", "3la"),       // Common: على (on) - preserve 3 notation
    ("3lik", "3lik"),     // Common: عليك (to you) - preserve 3 notation
    ("3likom", "3likom"), // Common: عليكم (to you plural) - preserve 3 notation
    ("3end", "3end"),     // Common: عند (at) - preserve 3 notation
    ("3endi", "3endi"),   // Common: عندي (I have) - preserve 3 notation
    ("3endek", "3endek"), // Common: عندك (you have) - preserve 3 notation
    ("3endou", "3endou"), // Common: عندهم (they have) - preserve 3 notation
];

/// Replace common number-based patterns
pub fn replace_number_patterns(text: &str) -> String {
    let mut result = text.to_string();

    for (pattern, replacement) in NUMBER_PATTERNS {
        result = result.replace(pattern, replacement);
    }

    result
}

#[cfg(test)]
mod tests {
    use super::*;

    #[test]
    fn test_digit_context_separator() {
        // Test separator context
        let context = DigitContextAnalyzer::analyze_context(2, "50->here");
        assert_eq!(context, DigitContext::Separator);

        let context = DigitContextAnalyzer::analyze_context(1, "82:");
        assert_eq!(context, DigitContext::Separator);
    }

    #[test]
    fn test_digit_context_word() {
        // Test word context
        let context = DigitContextAnalyzer::analyze_context(4, "sala8om");
        assert_eq!(context, DigitContext::WordContext);

        let context = DigitContextAnalyzer::analyze_context(1, "dyal8a");
        assert_eq!(context, DigitContext::WordContext);
    }

    #[test]
    fn test_digit_8_mapping() {
        // Mathematical context
        assert_eq!(
            DigitContextAnalyzer::map_digit_8(DigitContext::Mathematical),
            "8"
        );

        // Separator context
        assert_eq!(
            DigitContextAnalyzer::map_digit_8(DigitContext::Separator),
            "8"
        );

        // Word context (most common in Darija is 'h'/'ه')
        assert_eq!(
            DigitContextAnalyzer::map_digit_8(DigitContext::WordContext),
            "H" // Maps to H -> ه
        );
    }

    #[test]
    fn test_number_preservation() {
        assert!(NumberPreserver::should_preserve("50"));
        assert!(NumberPreserver::should_preserve("82"));
        assert!(NumberPreserver::should_preserve("50->"));
        assert!(NumberPreserver::should_preserve("82:"));
        assert!(!NumberPreserver::should_preserve("salam"));
        assert!(!NumberPreserver::should_preserve("katb"));
    }

    #[test]
    fn test_pattern_replacement() {
        assert_eq!(replace_number_patterns("7na"), "7na");
        assert_eq!(replace_number_patterns("3la"), "3la");
        assert_eq!(replace_number_patterns("50->"), "50->");
        assert_eq!(replace_number_patterns("82:"), "82:");
        assert_eq!(replace_number_patterns("5+8=13"), "5+8=13");
    }
}
