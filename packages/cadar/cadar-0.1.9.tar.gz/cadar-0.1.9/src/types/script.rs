use serde::{Deserialize, Serialize};

/// Represents different writing scripts
#[derive(Debug, Clone, Copy, PartialEq, Eq, Hash, Serialize, Deserialize)]
pub enum Script {
    /// Arabic script (ا، ب، ت، etc.)
    Arabic,
    /// Latin/Romanized script (a, b, t, etc.) - also known as "Bizi"
    Latin,
    /// Mixed script (contains both Arabic and Latin)
    Mixed,
    /// Unknown or undetermined script
    Unknown,
}

impl Script {
    /// Detect the script type from a character
    pub fn from_char(c: char) -> Self {
        match c {
            // Arabic Unicode ranges
            '\u{0600}'..='\u{06FF}' | // Arabic
            '\u{0750}'..='\u{077F}' | // Arabic Supplement
            '\u{08A0}'..='\u{08FF}' | // Arabic Extended-A
            '\u{FB50}'..='\u{FDFF}' | // Arabic Presentation Forms-A
            '\u{FE70}'..='\u{FEFF}' => Script::Arabic,

            // Latin alphabet
            'a'..='z' | 'A'..='Z' => Script::Latin,

            // Digits and punctuation are neutral
            '0'..='9' | ' ' | '.' | ',' | '!' | '?' | ';' | ':' => Script::Unknown,

            _ => Script::Unknown,
        }
    }

    /// Detect the dominant script in a text
    pub fn detect(text: &str) -> Self {
        let mut arabic_count = 0;
        let mut latin_count = 0;

        for c in text.chars() {
            match Self::from_char(c) {
                Script::Arabic => arabic_count += 1,
                Script::Latin => latin_count += 1,
                _ => {}
            }
        }

        if arabic_count > 0 && latin_count > 0 {
            Script::Mixed
        } else if arabic_count > latin_count {
            Script::Arabic
        } else if latin_count > 0 {
            Script::Latin
        } else {
            Script::Unknown
        }
    }
}

#[cfg(test)]
mod tests {
    use super::*;

    #[test]
    fn test_script_detection() {
        assert_eq!(Script::detect("مرحبا"), Script::Arabic);
        assert_eq!(Script::detect("marhaba"), Script::Latin);
        assert_eq!(Script::detect("مرحبا marhaba"), Script::Mixed);
        assert_eq!(Script::detect("123"), Script::Unknown);
    }

    #[test]
    fn test_char_detection() {
        assert_eq!(Script::from_char('م'), Script::Arabic);
        assert_eq!(Script::from_char('a'), Script::Latin);
        assert_eq!(Script::from_char('5'), Script::Unknown);
    }
}
