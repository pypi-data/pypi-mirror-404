pub mod linguistic;
pub mod stages;
pub mod types;

// Python bindings module
mod python_bindings;
pub use python_bindings::*;

use stages::{
    ICRBuilder, Normalizer, ScriptDetector, ScriptGenerator, StageResult, Tokenizer, Validator,
};
use types::{Dialect, Script};

/// Main CaDaR processor
/// Handles the complete transliteration pipeline
pub struct CaDaR {
    dialect: Dialect,
    detector: ScriptDetector,
    normalizer: Normalizer,
    tokenizer: Tokenizer,
    icr_builder: ICRBuilder,
    generator: ScriptGenerator,
    validator: Validator,
}

impl CaDaR {
    /// Create a new CaDaR processor for a specific dialect
    pub fn new(dialect: Dialect) -> Self {
        CaDaR {
            dialect,
            detector: ScriptDetector::new(),
            normalizer: Normalizer::new(),
            tokenizer: Tokenizer::new(dialect),
            icr_builder: ICRBuilder::new(dialect),
            generator: ScriptGenerator::new(),
            validator: Validator::new(dialect),
        }
    }

    /// Convert Arabic script to Latin (Bizi) script
    pub fn ara2bizi(&self, text: &str) -> StageResult<String> {
        self.transliterate(text, Script::Latin)
    }

    /// Convert Latin (Bizi) script to Arabic script
    pub fn bizi2ara(&self, text: &str) -> StageResult<String> {
        self.transliterate(text, Script::Arabic)
    }

    /// Standardize Arabic text (Arabic to canonical Arabic)
    pub fn ara2ara(&self, text: &str) -> StageResult<String> {
        self.transliterate(text, Script::Arabic)
    }

    /// Standardize Latin text (Bizi to canonical Bizi)
    pub fn bizi2bizi(&self, text: &str) -> StageResult<String> {
        self.transliterate(text, Script::Latin)
    }

    /// Core transliteration pipeline
    fn transliterate(&self, text: &str, target_script: Script) -> StageResult<String> {
        // Stage 1: Script Detection
        let detection_result = self.detector.detect(text)?;
        let source_script = detection_result.script;

        // Stage 2: Noise Cleaning & Normalization
        let normalized = self.normalizer.normalize(text, source_script)?;

        // Stage 3: Tokenization (Darija-aware)
        let tokens = self.tokenizer.tokenize(&normalized, source_script)?;

        // Stage 4: Convert to ICR (Intermediate Canonical Representation)
        let icr = self.icr_builder.build_from_tokens(&tokens, source_script)?;

        // Stage 5: Generate target script from ICR
        let generated = self.generator.generate(&icr, target_script)?;

        // Stage 6: Post-validation & Fixes
        let validated = self.validator.validate_and_fix(&generated, target_script)?;

        Ok(validated)
    }

    /// Get the current dialect
    pub fn dialect(&self) -> Dialect {
        self.dialect
    }

    /// Process text with detailed information at each stage
    pub fn transliterate_with_details(
        &self,
        text: &str,
        target_script: Script,
    ) -> StageResult<TransliterationDetails> {
        // Stage 1: Script Detection
        let detection_result = self.detector.detect(text)?;
        let source_script = detection_result.script;

        // Stage 2: Normalization
        let normalized = self.normalizer.normalize(text, source_script)?;

        // Stage 3: Tokenization
        let tokens = self.tokenizer.tokenize(&normalized, source_script)?;

        // Stage 4: ICR
        let icr = self.icr_builder.build_from_tokens(&tokens, source_script)?;

        // Stage 5: Generate
        let generated = self.generator.generate(&icr, target_script)?;

        // Stage 6: Validate
        let validated = self.validator.validate_and_fix(&generated, target_script)?;

        Ok(TransliterationDetails {
            original: text.to_string(),
            source_script,
            target_script,
            normalized,
            token_count: tokens.len(),
            icr_segments: icr.segments.len(),
            generated,
            final_output: validated,
        })
    }
}

/// Detailed information about the transliteration process
#[derive(Debug, Clone)]
pub struct TransliterationDetails {
    pub original: String,
    pub source_script: Script,
    pub target_script: Script,
    pub normalized: String,
    pub token_count: usize,
    pub icr_segments: usize,
    pub generated: String,
    pub final_output: String,
}

impl Default for CaDaR {
    fn default() -> Self {
        Self::new(Dialect::Moroccan)
    }
}

#[cfg(test)]
mod tests {
    use super::*;

    #[test]
    fn test_ara2bizi() {
        let cadar = CaDaR::new(Dialect::Moroccan);
        let result = cadar.ara2bizi("سلام").unwrap();
        assert!(!result.is_empty());
        assert_eq!(Script::detect(&result), Script::Latin);
    }

    #[test]
    fn test_bizi2ara() {
        let cadar = CaDaR::new(Dialect::Moroccan);
        let result = cadar.bizi2ara("salam").unwrap();
        assert!(!result.is_empty());
        assert_eq!(Script::detect(&result), Script::Arabic);
    }

    #[test]
    fn test_ara2ara_standardization() {
        let cadar = CaDaR::new(Dialect::Moroccan);
        let result = cadar.ara2ara("أنَا مِنْ المَغْرِب").unwrap();
        assert!(!result.is_empty());
        assert_eq!(Script::detect(&result), Script::Arabic);
        // Should remove diacritics
        assert!(!result.contains('\u{064E}'));
    }

    #[test]
    fn test_bizi2bizi_standardization() {
        let cadar = CaDaR::new(Dialect::Moroccan);
        let result = cadar.bizi2bizi("salaaaam").unwrap();
        assert!(!result.is_empty());
        assert_eq!(Script::detect(&result), Script::Latin);
    }

    #[test]
    fn test_round_trip() {
        let cadar = CaDaR::new(Dialect::Moroccan);

        // Start with Latin
        let original = "salam";
        let arabic = cadar.bizi2ara(original).unwrap();
        let back_to_latin = cadar.ara2bizi(&arabic).unwrap();

        // They should be similar (though not necessarily identical due to normalization)
        assert!(!back_to_latin.is_empty());
    }

    #[test]
    fn test_moroccan_specific() {
        let cadar = CaDaR::new(Dialect::Moroccan);

        // Test Moroccan-specific word
        let result = cadar.bizi2ara("bzaf").unwrap();
        assert!(!result.is_empty());
        assert_eq!(Script::detect(&result), Script::Arabic);
    }

    #[test]
    fn test_with_details() {
        let cadar = CaDaR::new(Dialect::Moroccan);
        let details = cadar
            .transliterate_with_details("salam", Script::Arabic)
            .unwrap();

        assert_eq!(details.source_script, Script::Latin);
        assert_eq!(details.target_script, Script::Arabic);
        assert!(details.token_count > 0);
        assert!(details.icr_segments > 0);
        assert!(!details.final_output.is_empty());
    }

    #[test]
    fn test_empty_input() {
        let cadar = CaDaR::new(Dialect::Moroccan);
        assert!(cadar.ara2bizi("").is_err());
    }

    #[test]
    fn test_bizi2ara_spacing() {
        let cadar = CaDaR::new(Dialect::Moroccan);
        let result = cadar.bizi2ara("salam 3likom").unwrap();

        // Should preserve spaces between words
        assert!(
            result.contains(' '),
            "Result should contain spaces: {}",
            result
        );

        // Count spaces
        let space_count = result.chars().filter(|&c| c == ' ').count();
        assert!(space_count >= 1, "Should have at least one space");
    }

    #[test]
    fn test_ara2bizi_spacing() {
        let cadar = CaDaR::new(Dialect::Moroccan);
        let result = cadar.ara2bizi("سلام عليكم").unwrap();

        // Should preserve spaces between words
        assert!(
            result.contains(' '),
            "Result should contain spaces: {}",
            result
        );

        // Count spaces
        let space_count = result.chars().filter(|&c| c == ' ').count();
        assert!(space_count >= 1, "Should have at least one space");
    }
}
