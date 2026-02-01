use super::{StageError, StageResult};
use crate::types::Script;

/// Stage 1: Script Detection
/// Detects the input script type (Arabic, Latin, Mixed)
pub struct ScriptDetector;

impl ScriptDetector {
    pub fn new() -> Self {
        ScriptDetector
    }

    /// Detect the script type with detailed statistics
    pub fn detect(&self, text: &str) -> StageResult<DetectionResult> {
        if text.is_empty() {
            return Err(StageError::ScriptDetection("Empty input".to_string()));
        }

        let mut stats = ScriptStats::default();

        for c in text.chars() {
            match Script::from_char(c) {
                Script::Arabic => stats.arabic_count += 1,
                Script::Latin => stats.latin_count += 1,
                Script::Unknown => stats.neutral_count += 1,
                Script::Mixed => {} // Should not occur for single char
            }
        }

        let total = stats.arabic_count + stats.latin_count;
        if total == 0 {
            return Err(StageError::ScriptDetection(
                "No recognizable script characters found".to_string(),
            ));
        }

        let script = if stats.arabic_count > 0 && stats.latin_count > 0 {
            Script::Mixed
        } else if stats.arabic_count > stats.latin_count {
            Script::Arabic
        } else {
            Script::Latin
        };

        stats.arabic_ratio = stats.arabic_count as f64 / total as f64;
        stats.latin_ratio = stats.latin_count as f64 / total as f64;

        Ok(DetectionResult {
            script,
            stats,
            original_text: text.to_string(),
        })
    }
}

/// Statistics about script detection
#[derive(Debug, Clone, Default)]
pub struct ScriptStats {
    pub arabic_count: usize,
    pub latin_count: usize,
    pub neutral_count: usize,
    pub arabic_ratio: f64,
    pub latin_ratio: f64,
}

/// Result of script detection
#[derive(Debug, Clone)]
pub struct DetectionResult {
    pub script: Script,
    pub stats: ScriptStats,
    pub original_text: String,
}

impl DetectionResult {
    /// Check if the text is predominantly Arabic
    pub fn is_predominantly_arabic(&self) -> bool {
        self.stats.arabic_ratio > 0.7
    }

    /// Check if the text is predominantly Latin
    pub fn is_predominantly_latin(&self) -> bool {
        self.stats.latin_ratio > 0.7
    }

    /// Check if the text is truly mixed (significant amount of both scripts)
    pub fn is_truly_mixed(&self) -> bool {
        self.stats.arabic_ratio >= 0.3 && self.stats.latin_ratio >= 0.3
    }
}

#[cfg(test)]
mod tests {
    use super::*;

    #[test]
    fn test_arabic_detection() {
        let detector = ScriptDetector::new();
        let result = detector.detect("كيفاش داير؟").unwrap();
        assert_eq!(result.script, Script::Arabic);
        assert!(result.is_predominantly_arabic());
    }

    #[test]
    fn test_latin_detection() {
        let detector = ScriptDetector::new();
        let result = detector.detect("kifash dayer?").unwrap();
        assert_eq!(result.script, Script::Latin);
        assert!(result.is_predominantly_latin());
    }

    #[test]
    fn test_mixed_detection() {
        let detector = ScriptDetector::new();
        let result = detector.detect("كيفاش dayer?").unwrap();
        assert_eq!(result.script, Script::Mixed);
    }

    #[test]
    fn test_empty_input() {
        let detector = ScriptDetector::new();
        assert!(detector.detect("").is_err());
    }

    #[test]
    fn test_only_numbers() {
        let detector = ScriptDetector::new();
        assert!(detector.detect("123456").is_err());
    }
}
