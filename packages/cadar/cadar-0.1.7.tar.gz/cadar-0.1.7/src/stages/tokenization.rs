use super::{StageError, StageResult};
use crate::types::{Dialect, Script};

/// Represents a token in the text
#[derive(Debug, Clone, PartialEq)]
pub struct Token {
    pub text: String,
    pub token_type: TokenType,
    pub start_pos: usize,
    pub end_pos: usize,
    pub script: Script,
}

/// Types of tokens
#[derive(Debug, Clone, Copy, PartialEq)]
pub enum TokenType {
    Word,
    Number,
    Punctuation,
    FunctionWord,
    DarijaSpecific,
    Clitic,
}

/// Stage 3: Darija-aware Tokenization
/// Tokenizes text while respecting Darija-specific patterns
pub struct Tokenizer {
    dialect: Dialect,
}

impl Tokenizer {
    pub fn new(dialect: Dialect) -> Self {
        Tokenizer { dialect }
    }

    /// Tokenize text into words
    pub fn tokenize(&self, text: &str, script: Script) -> StageResult<Vec<Token>> {
        if text.is_empty() {
            return Err(StageError::Tokenization("Empty input".to_string()));
        }

        let tokens = self.advanced_tokenize(text, script)?;

        // Second pass: handle clitics and prefixes for Darija
        let processed_tokens = self.handle_clitics(tokens, script)?;

        Ok(processed_tokens)
    }

    /// Advanced tokenization that handles numbers, symbols, and mixed patterns
    fn advanced_tokenize(&self, text: &str, script: Script) -> StageResult<Vec<Token>> {
        let mut tokens = Vec::new();
        let chars: Vec<char> = text.chars().collect();
        let mut i = 0;

        while i < chars.len() {
            // Skip whitespace but record position
            if chars[i].is_whitespace() {
                i += 1;
                continue;
            }

            // Try to extract different token types
            if let Some((token_text, token_type, consumed)) =
                self.extract_next_token(&chars, i, script)
            {
                let start_pos = i;
                let end_pos = i + consumed;

                tokens.push(Token {
                    text: token_text,
                    token_type,
                    start_pos,
                    end_pos,
                    script,
                });

                i += consumed;
            } else {
                // Fallback: treat single character as word
                tokens.push(Token {
                    text: chars[i].to_string(),
                    token_type: TokenType::Word,
                    start_pos: i,
                    end_pos: i + 1,
                    script,
                });
                i += 1;
            }
        }

        Ok(tokens)
    }

    /// Extract the next token starting at position i
    fn extract_next_token(
        &self,
        chars: &[char],
        pos: usize,
        script: Script,
    ) -> Option<(String, TokenType, usize)> {
        if pos >= chars.len() {
            return None;
        }

        let current_char = chars[pos];

        // Darija specific patterns (like 7na, 3la, etc.) - check FIRST before treating as number
        if self.is_darija_number_pattern(chars, pos) {
            return self.extract_darija_pattern(chars, pos, script);
        }

        // Numbers and mixed number-symbol patterns
        if current_char.is_ascii_digit()
            || matches!(
                current_char,
                '٠' | '١' | '٢' | '٣' | '٤' | '٥' | '٦' | '٧' | '٨' | '٩'
            )
        {
            return self.extract_number_or_mixed_token(chars, pos);
        }

        // Symbol sequences (operators, arrows, etc.)
        if current_char.is_ascii_punctuation()
            || matches!(current_char, '>' | '<' | '=' | '|' | '-')
        {
            return self.extract_symbol_sequence(chars, pos);
        }

        // Regular words
        self.extract_word_token(chars, pos, script)
    }

    /// Extract number or mixed number-symbol tokens
    fn extract_number_or_mixed_token(
        &self,
        chars: &[char],
        pos: usize,
    ) -> Option<(String, TokenType, usize)> {
        let mut token_chars = Vec::new();
        let mut i = pos;

        while i < chars.len() {
            let ch = chars[i];

            if ch.is_ascii_digit()
                || matches!(
                    ch,
                    '٠' | '١' | '٢' | '٣' | '٤' | '٥' | '٦' | '٧' | '٨' | '٩'
                )
            {
                token_chars.push(ch);
            } else if ch.is_ascii_punctuation() || matches!(ch, '>' | '<' | '=' | '|' | '-') {
                // Allow symbols that are commonly used with numbers
                token_chars.push(ch);
            } else if ch.is_whitespace() {
                break;
            } else {
                // Letter encountered, stop number token
                break;
            }
            i += 1;
        }

        if token_chars.is_empty() {
            None
        } else {
            let token_text: String = token_chars.iter().collect();
            Some((token_text, TokenType::Number, i - pos))
        }
    }

    /// Extract symbol sequences (operators, arrows, etc.)
    fn extract_symbol_sequence(
        &self,
        chars: &[char],
        pos: usize,
    ) -> Option<(String, TokenType, usize)> {
        let mut token_chars = Vec::new();
        let mut i = pos;

        while i < chars.len() {
            let ch = chars[i];
            if ch.is_ascii_punctuation() || matches!(ch, '>' | '<' | '=' | '|' | '-') {
                token_chars.push(ch);
            } else {
                break;
            }
            i += 1;
        }

        if token_chars.is_empty() {
            None
        } else {
            let token_text: String = token_chars.iter().collect();
            let token_type = if token_text.len() == 1
                && token_text.chars().next().unwrap().is_ascii_punctuation()
            {
                TokenType::Punctuation
            } else {
                TokenType::Number // Treat multi-symbol sequences as number-type tokens
            };
            Some((token_text, token_type, i - pos))
        }
    }

    /// Check if this is a Darija number pattern (like 7na, 3la, etc.)
    /// A Darija pattern is a digit followed by letters forming a word
    fn is_darija_number_pattern(&self, chars: &[char], pos: usize) -> bool {
        if pos >= chars.len() {
            return false;
        }

        let ch = chars[pos];

        // Must start with a Darija digit
        if !matches!(ch, '3' | '7' | '9' | '5' | '6' | '8') {
            return false;
        }

        // Must be followed by at least one letter (not another digit)
        if pos + 1 < chars.len() {
            let next_char = chars[pos + 1];
            // Check if next char is a letter (not a digit, not punctuation, not whitespace)
            return next_char.is_alphabetic() || next_char == 'h' || next_char == 'H';
        }

        false
    }

    /// Extract Darija number patterns
    fn extract_darija_pattern(
        &self,
        chars: &[char],
        pos: usize,
        _script: Script,
    ) -> Option<(String, TokenType, usize)> {
        let mut token_chars = Vec::new();
        let mut i = pos;

        // Start with the number character
        token_chars.push(chars[i]);
        i += 1;

        // Continue with letters until we hit a boundary
        while i < chars.len() {
            let ch = chars[i];
            if ch.is_alphabetic() || ch == '_' {
                token_chars.push(ch);
            } else if ch.is_whitespace() || ch.is_ascii_punctuation() {
                break;
            } else {
                // Other symbols or numbers - break the token
                break;
            }
            i += 1;
        }

        if token_chars.len() > 1 {
            // Must be more than just the number
            let token_text: String = token_chars.iter().collect();
            Some((token_text, TokenType::Word, i - pos))
        } else {
            None
        }
    }

    /// Extract regular word tokens
    fn extract_word_token(
        &self,
        chars: &[char],
        pos: usize,
        script: Script,
    ) -> Option<(String, TokenType, usize)> {
        let mut token_chars = Vec::new();
        let mut i = pos;

        while i < chars.len() {
            let ch = chars[i];
            if ch.is_alphabetic() || ch == '_' {
                token_chars.push(ch);
            } else {
                break;
            }
            i += 1;
        }

        if token_chars.is_empty() {
            None
        } else {
            let token_text: String = token_chars.iter().collect();
            let token_type = self.classify_token(&token_text, script);
            Some((token_text, token_type, i - pos))
        }
    }

    /// Classify a token based on its characteristics
    fn classify_token(&self, word: &str, script: Script) -> TokenType {
        // Enhanced number and symbol detection
        if self.is_number_or_symbol_token(word) {
            return TokenType::Number; // Use Number type for all numbers and mixed patterns
        }

        // Check for punctuation (pure punctuation, not mixed with numbers)
        if word.chars().all(|c| c.is_ascii_punctuation()) {
            return TokenType::Punctuation;
        }

        // Check for common Darija function words (Articles, prepositions)
        if self.is_function_word(word, script) {
            return TokenType::FunctionWord;
        }

        // Check for Darija-specific constructs
        if self.is_darija_specific(word, script) {
            return TokenType::DarijaSpecific;
        }

        TokenType::Word
    }

    /// Enhanced detection for numbers and mixed number-symbol patterns
    fn is_number_or_symbol_token(&self, word: &str) -> bool {
        if word.is_empty() {
            return false;
        }

        // Pure digits
        if word.chars().all(|c| c.is_ascii_digit()) {
            return true;
        }

        // Pure symbols/mathematical operators
        if word.chars().all(|c| c.is_ascii_punctuation()) {
            return false; // Let this fall through to punctuation check
        }

        // Mixed patterns: numbers with symbols/special characters
        // This handles patterns like: 50, 82, 50->, 82:, 3la, 7na, etc.
        let has_digits = word.chars().any(|c| c.is_ascii_digit());
        let has_symbols = word
            .chars()
            .any(|c| c.is_ascii_punctuation() || matches!(c, '>' | '<' | '=' | '|'));
        let has_arabic_numeral = word
            .chars()
            .any(|c| matches!(c, '٠' | '١' | '٢' | '٣' | '٤' | '٥' | '٦' | '٧' | '٨' | '٩'));

        has_digits || has_arabic_numeral || (has_symbols && word.len() <= 3) // Short symbol sequences
    }

    /// Check if a word is a function word (article, preposition, etc.)
    fn is_function_word(&self, word: &str, script: Script) -> bool {
        match script {
            Script::Arabic => {
                matches!(
                    word,
                    "من" | "في"
                        | "على"
                        | "إلى"
                        | "مع"
                        | "عن"
                        | "ال"
                        | "و"
                        | "ف"
                        | "ب"
                        | "ل"
                        | "ك"
                )
            }
            Script::Latin => {
                matches!(
                    word.to_lowercase().as_str(),
                    "f" | "men" | "m3a" | "3la" | "l" | "b" | "w" | "li" | "dial" | "dyal"
                )
            }
            _ => false,
        }
    }

    /// Check if a word is Darija-specific
    fn is_darija_specific(&self, word: &str, script: Script) -> bool {
        match self.dialect {
            Dialect::Moroccan => match script {
                Script::Arabic => {
                    matches!(
                        word,
                        "غير" | "بزاف" | "شوية" | "واخا" | "كيفاش" | "شنو" | "فين"
                    )
                }
                Script::Latin => {
                    matches!(
                        word.to_lowercase().as_str(),
                        "ghir" | "bzaf" | "shwiya" | "wakha" | "kifash" | "shno" | "fin" | "feen"
                    )
                }
                _ => false,
            },
        }
    }

    /// Handle Darija clitics (prefixes and suffixes that attach to words)
    fn handle_clitics(&self, tokens: Vec<Token>, script: Script) -> StageResult<Vec<Token>> {
        let mut result = Vec::new();

        for token in tokens {
            // Only process word tokens
            if !matches!(
                token.token_type,
                TokenType::Word | TokenType::DarijaSpecific
            ) {
                result.push(token);
                continue;
            }

            // Split clitics if needed
            let split_tokens = self.split_clitics(&token, script);
            result.extend(split_tokens);
        }

        Ok(result)
    }

    /// Split clitics from a token
    fn split_clitics(&self, token: &Token, script: Script) -> Vec<Token> {
        let word = &token.text;

        match script {
            Script::Arabic => {
                // Handle Arabic prefixes: و، ف، ب، ل، ال
                if word.starts_with("وال") && word.chars().count() > 3 {
                    let rest: String = word.chars().skip(3).collect();
                    return self.create_split_tokens(token, vec!["و", "ال"], &rest);
                } else if word.starts_with('و') && word.chars().count() > 1 {
                    let rest: String = word.chars().skip(1).collect();
                    return self.create_split_tokens(token, vec!["و"], &rest);
                } else if word.starts_with("ال") && word.chars().count() > 2 {
                    let rest: String = word.chars().skip(2).collect();
                    return self.create_split_tokens(token, vec!["ال"], &rest);
                }
            }
            Script::Latin => {
                // Handle Latin prefixes: l-, f-, b-, w-
                if word.starts_with("l") && word.len() > 1 {
                    let rest = &word[1..];
                    if rest
                        .chars()
                        .next()
                        .map(|c| c.is_alphabetic())
                        .unwrap_or(false)
                    {
                        return self.create_split_tokens(token, vec!["l"], rest);
                    }
                } else if word.starts_with("f") && word.len() > 1 {
                    let rest = &word[1..];
                    if rest
                        .chars()
                        .next()
                        .map(|c| c.is_alphabetic())
                        .unwrap_or(false)
                    {
                        return self.create_split_tokens(token, vec!["f"], rest);
                    }
                }
            }
            _ => {}
        }

        // No split needed
        vec![token.clone()]
    }

    /// Create split tokens from clitics
    fn create_split_tokens(&self, original: &Token, prefixes: Vec<&str>, stem: &str) -> Vec<Token> {
        let mut tokens = Vec::new();
        let mut pos = original.start_pos;

        for prefix in prefixes {
            tokens.push(Token {
                text: prefix.to_string(),
                token_type: TokenType::Clitic,
                start_pos: pos,
                end_pos: pos + prefix.len(),
                script: original.script,
            });
            pos += prefix.len();
        }

        tokens.push(Token {
            text: stem.to_string(),
            token_type: original.token_type,
            start_pos: pos,
            end_pos: original.end_pos,
            script: original.script,
        });

        tokens
    }
}

#[cfg(test)]
mod tests {
    use super::*;

    #[test]
    fn test_basic_tokenization() {
        let tokenizer = Tokenizer::new(Dialect::Moroccan);
        let tokens = tokenizer.tokenize("salam menek", Script::Latin).unwrap();
        assert_eq!(tokens.len(), 2);
        assert_eq!(tokens[0].text, "salam");
        assert_eq!(tokens[1].text, "menek");
    }

    #[test]
    fn test_clitic_splitting_latin() {
        let tokenizer = Tokenizer::new(Dialect::Moroccan);
        let tokens = tokenizer.tokenize("lsalam", Script::Latin).unwrap();
        assert_eq!(tokens.len(), 2);
        assert_eq!(tokens[0].text, "l");
        assert_eq!(tokens[1].text, "salam");
    }

    #[test]
    fn test_darija_specific_detection() {
        let tokenizer = Tokenizer::new(Dialect::Moroccan);
        let tokens = tokenizer.tokenize("bzaf", Script::Latin).unwrap();
        assert_eq!(tokens[0].token_type, TokenType::DarijaSpecific);
    }

    #[test]
    fn test_function_word_detection() {
        let tokenizer = Tokenizer::new(Dialect::Moroccan);
        let tokens = tokenizer.tokenize("men", Script::Latin).unwrap();
        assert_eq!(tokens[0].token_type, TokenType::FunctionWord);
    }

    // Tests for ISSUES.md fixes

    #[test]
    fn test_number_tokenization() {
        let tokenizer = Tokenizer::new(Dialect::Moroccan);

        // Test pure numbers
        let tokens = tokenizer.tokenize("50", Script::Latin).unwrap();
        assert_eq!(tokens.len(), 1);
        assert_eq!(tokens[0].text, "50");
        assert_eq!(tokens[0].token_type, TokenType::Number);

        let tokens = tokenizer.tokenize("82", Script::Latin).unwrap();
        assert_eq!(tokens.len(), 1);
        assert_eq!(tokens[0].text, "82");
        assert_eq!(tokens[0].token_type, TokenType::Number);
    }

    #[test]
    fn test_mixed_number_symbol_patterns() {
        let tokenizer = Tokenizer::new(Dialect::Moroccan);

        // Test arrow patterns
        let tokens = tokenizer.tokenize("50->", Script::Latin).unwrap();
        assert_eq!(tokens.len(), 1);
        assert_eq!(tokens[0].text, "50->");
        assert_eq!(tokens[0].token_type, TokenType::Number);

        // Test colon patterns
        let tokens = tokenizer.tokenize("82:", Script::Latin).unwrap();
        assert_eq!(tokens.len(), 1);
        assert_eq!(tokens[0].text, "82:");
        assert_eq!(tokens[0].token_type, TokenType::Number);

        // Test mathematical expressions
        let tokens = tokenizer.tokenize("5+8=13", Script::Latin).unwrap();
        assert!(tokens
            .iter()
            .any(|t| t.text == "5+8=13" || t.text.contains("5")));
        assert!(tokens.iter().any(|t| t.token_type == TokenType::Number));
    }

    #[test]
    fn test_darija_number_patterns() {
        let tokenizer = Tokenizer::new(Dialect::Moroccan);

        // Test 7na (حنا) pattern
        let tokens = tokenizer.tokenize("7na", Script::Latin).unwrap();
        assert_eq!(tokens.len(), 1);
        assert_eq!(tokens[0].text, "7na");
        assert_eq!(tokens[0].token_type, TokenType::Word);

        // Test 3la (على) pattern
        let tokens = tokenizer.tokenize("3la", Script::Latin).unwrap();
        assert_eq!(tokens.len(), 1);
        assert_eq!(tokens[0].text, "3la");
        assert_eq!(tokens[0].token_type, TokenType::Word);

        // Test 3end (عند) pattern
        let tokens = tokenizer.tokenize("3end", Script::Latin).unwrap();
        assert_eq!(tokens.len(), 1);
        assert_eq!(tokens[0].text, "3end");
        assert_eq!(tokens[0].token_type, TokenType::Word);
    }

    #[test]
    fn test_mixed_text_tokenization() {
        let tokenizer = Tokenizer::new(Dialect::Moroccan);

        // Test the exact example from ISSUES.md: "7na chi 50->حنا شي"
        let tokens = tokenizer.tokenize("7na chi 50->", Script::Latin).unwrap();
        let token_texts: Vec<String> = tokens.iter().map(|t| t.text.clone()).collect();

        assert!(token_texts.contains(&"7na".to_string()));
        assert!(token_texts.contains(&"chi".to_string()));
        assert!(token_texts.contains(&"50->".to_string()));

        // Check token types
        let na_token = tokens.iter().find(|t| t.text == "7na").unwrap();
        assert_eq!(na_token.token_type, TokenType::Word);

        let number_token = tokens.iter().find(|t| t.text == "50->").unwrap();
        assert_eq!(number_token.token_type, TokenType::Number);
    }

    #[test]
    fn test_advanced_token_extraction() {
        let tokenizer = Tokenizer::new(Dialect::Moroccan);

        // Test extraction of different token types
        let tokens = tokenizer
            .tokenize("82: 7na chi 50->salam", Script::Latin)
            .unwrap();

        // Should find all expected tokens
        let token_texts: Vec<String> = tokens.iter().map(|t| t.text.clone()).collect();
        assert!(token_texts.contains(&"82:".to_string()));
        assert!(token_texts.contains(&"7na".to_string()));
        assert!(token_texts.contains(&"chi".to_string()));
        assert!(token_texts.contains(&"50->".to_string()));
        assert!(token_texts.contains(&"salam".to_string()));
    }

    #[test]
    fn test_is_number_or_symbol_token() {
        let tokenizer = Tokenizer::new(Dialect::Moroccan);

        // Pure digits
        assert!(tokenizer.is_number_or_symbol_token("50"));
        assert!(tokenizer.is_number_or_symbol_token("123"));

        // Mixed number-symbol
        assert!(tokenizer.is_number_or_symbol_token("50->"));
        assert!(tokenizer.is_number_or_symbol_token("82:"));
        assert!(tokenizer.is_number_or_symbol_token("5+8"));

        // Pure symbols should return false (let it fall through to punctuation)
        assert!(!tokenizer.is_number_or_symbol_token("->"));
        assert!(!tokenizer.is_number_or_symbol_token("+"));

        // Regular words should return false
        assert!(!tokenizer.is_number_or_symbol_token("salam"));
        assert!(!tokenizer.is_number_or_symbol_token("chi"));
    }

    #[test]
    fn test_edge_cases() {
        let tokenizer = Tokenizer::new(Dialect::Moroccan);

        // Empty string should error
        assert!(tokenizer.tokenize("", Script::Latin).is_err());

        // Single character tokens
        let tokens = tokenizer.tokenize("a b c", Script::Latin).unwrap();
        assert_eq!(tokens.len(), 3);
        assert!(tokens.iter().all(|t| t.text.len() == 1));

        // Complex mixed patterns
        let tokens = tokenizer.tokenize("test123->456", Script::Latin).unwrap();
        assert!(tokens.iter().any(|t| t.text.contains("123")));
        assert!(tokens.iter().any(|t| t.text.contains("456")));
    }
}
