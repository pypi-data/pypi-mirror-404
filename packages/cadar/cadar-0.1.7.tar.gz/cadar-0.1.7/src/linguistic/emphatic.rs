/// Simple check for emphatic lexicon - basic implementation
/// In a real system, this would be a proper database
pub fn should_be_emphatic_t(word: &str) -> bool {
    // Normalize uppercase T to emphatic ṭ before lowercasing
    let word = word.replace('T', "ṭ").replace('S', "ṣ");
    let word = word.to_lowercase();

    // Words that use emphatic ṭ (ط) - simplified list
    matches!(
        word.as_str(),
        "ṭb3"
            | "ṭbi3"
            | "ṭalab"
            | "ṭari"
            | "ṭayr"
            | "ṭawila"
            | "ṭeb3"
            | "ṭebqa"
            | "ṭob"
            | "ṭob9"
            | "ṭor"
            | "ṭob9a"
            | "ṭla"
            | "ṭleb"
            | "ṭlo7"
            | "ṭlo7a"
            | "ṭli7"
            | "ṭli7a"
            | "ṭma"
            | "ṭmag"
            | "ṭm"
            | "ṭmi"
            | "ṭnin"
            | "ṭnina"
            | "ṭrin"
            | "ṭrine"
            | "ṭsen"
            | "ṭsena"
            | "ṭsin"
            | "ṭsina"
    )
}

/// Simple check for emphatic roots - basic implementation
/// In a real system, this would be a proper database
pub fn should_be_emphatic_s(root: &str) -> bool {
    // Normalize uppercase T to emphatic ṭ and S to ṣ before lowercasing
    let root = root.replace('T', "ṭ").replace('S', "ṣ");
    let root = root.to_lowercase();

    // Roots with emphatic patterns - simplified list
    matches!(
        root.as_str(),
        // Emphatic ṭ (ط) patterns
        "ṭb3" | "ṭlb" | "ṭry" | "ṭwr" | "ṭbq" | "ṭb9" | "ṭl7" | "ṭly7" | "ṭmg" | "ṭmn" | "ṭny" | "ṭryn" |

        // Emphatic ṣ (ص) patterns
        "ṣb7" | "ṣdy" | "ṣbn" | "ṣbr" | "ṣghr" | "ṣgr" | "ṣhr" | "ṣmr" | "ṣnm" | "ṣrf" | "ṣrh" |
        "ṣry" | "ṣrw" | "ṣr7" | "ṣr9" | "ṣkl" | "ṣkb" | "ṣkr" | "ṣk3" | "ṣkhb" | "ṣkhr" | "ṣkhs" | "ṣkhl" |
        "ṣkm" | "ṣkm3" | "ṣkn" | "ṣk3l" | "ṣk3n"
    )
}

/// Simple check for function words - basic implementation
/// In a real system, this would be a proper database
pub fn is_function_word(word: &str) -> bool {
    let word = word.to_lowercase();

    // Common function words that rarely use emphatic forms
    matches!(
        word.as_str(),
        "men"
            | "min"
            | "fi"
            | "f"
            | "3la"
            | "3l"
            | "b"
            | "bl"
            | "l"
            | "li"
            | "la"
            | "ln"
            | "lchi"
            | "l7e"
            | "lkhe"
            | "lka"
            | "lkan"
            | "lkin"
            | "lma"
            | "lman"
            | "lmen"
            | "lmi"
            | "lmor"
            | "lmra"
            | "lm3a"
            | "l3ech"
            | "l9ed"
            | "l9od"
            | "lli"
            | "ll"
            | "kan"
            | "k"
            | "nta"
            | "nti"
            | "ntouma"
            | "7na"
            | "houa"
            | "houma"
            | "ana"
            | "ach"
            | "wech"
            | "wach"
            | "fin"
            | "fash"
            | "3ach"
            | "alach"
            | "lach"
            | "ila"
            | "yak"
            | "ma"
            | "mach"
            | "machi"
    )
}

/// Aspect markers that indicate non-emphatic forms
pub static ASPECT_MARKERS: [&str; 6] = ["ta", "tay", "ti", "tina", "tou", "tiou"];

/// Check if a word starts with an aspect marker (indicates non-emphatic)
pub fn starts_with_aspect_marker(word: &str) -> bool {
    let word = word.to_lowercase();
    ASPECT_MARKERS.iter().any(|marker| word.starts_with(marker))
}

/// Extract a simple root from a word (basic pattern matching)
/// This is a simplified root extraction for Darija
pub fn extract_root(word: &str) -> Option<String> {
    let word = word.to_lowercase();

    // Remove common suffixes first
    let mut word_root = word.strip_suffix("at").unwrap_or(&word);
    word_root = word_root.strip_suffix("a").unwrap_or(word_root);
    word_root = word_root.strip_suffix("i").unwrap_or(word_root);
    word_root = word_root.strip_suffix("in").unwrap_or(word_root);
    word_root = word_root.strip_suffix("an").unwrap_or(word_root);

    // Remove common aspect marker prefixes (check longer ones first)
    let word_no_prefix = word_root.strip_prefix("tay").unwrap_or(word_root);
    let word_no_prefix = word_no_prefix.strip_prefix("ka").unwrap_or(word_no_prefix);

    // Extract consonantal root by removing vowels
    let consonants: String = word_no_prefix
        .chars()
        .filter(|c| !matches!(c, 'a' | 'i' | 'u' | 'e' | 'o'))
        .collect();

    // Basic 3-letter root extraction
    if consonants.len() >= 3 {
        Some(consonants.chars().take(3).collect())
    } else if consonants.len() >= 2 {
        Some(consonants.to_string())
    } else {
        None
    }
}

#[cfg(test)]
mod tests {
    use super::*;

    #[test]
    fn test_emphatic_lexicon() {
        assert!(should_be_emphatic_t("ṭbi3"));
        assert!(should_be_emphatic_t("TB3"));
        assert!(!should_be_emphatic_t("tabi3"));
        assert!(!should_be_emphatic_t("tab3"));
    }

    #[test]
    fn test_emphatic_roots() {
        assert!(should_be_emphatic_s("ṭb3"));
        assert!(should_be_emphatic_s("TB3"));
        assert!(!should_be_emphatic_s("tb3"));
        assert!(should_be_emphatic_s("ṣb7"));
        assert!(should_be_emphatic_s("SB7"));
        assert!(!should_be_emphatic_s("sb7"));
    }

    #[test]
    fn test_function_words() {
        assert!(is_function_word("men"));
        assert!(is_function_word("fi"));
        assert!(is_function_word("3la"));
        assert!(is_function_word("lli"));
        assert!(!is_function_word("ṭbi3"));
        assert!(!is_function_word("ktab"));
    }

    #[test]
    fn test_aspect_markers() {
        assert!(starts_with_aspect_marker("tabi3"));
        assert!(starts_with_aspect_marker("tayeb"));
        assert!(starts_with_aspect_marker("tiina"));
        assert!(starts_with_aspect_marker("touka"));
        assert!(starts_with_aspect_marker("tiouma"));
        assert!(!starts_with_aspect_marker("ṭbi3"));
        assert!(!starts_with_aspect_marker("ktab"));
    }

    #[test]
    fn test_root_extraction() {
        assert_eq!(extract_root("tabi3a"), Some("tb3".to_string()));
        assert_eq!(extract_root("ktab"), Some("ktb".to_string()));
        assert_eq!(extract_root("mchawi"), Some("mch".to_string()));
        assert_eq!(extract_root("sa"), None);
    }
}
