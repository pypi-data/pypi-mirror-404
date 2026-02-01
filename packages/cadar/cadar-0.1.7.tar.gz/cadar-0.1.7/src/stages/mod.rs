pub mod icr;
pub mod normalization;
pub mod script_detection;
pub mod script_generation;
pub mod tokenization;
pub mod validation;

pub use icr::{ICRBuilder, ICR};
pub use normalization::Normalizer;
pub use script_detection::ScriptDetector;
pub use script_generation::ScriptGenerator;
pub use tokenization::Tokenizer;
pub use validation::Validator;

// Note: Dialect and Script are not used in this module but kept for future use
#[allow(unused_imports)]
use crate::types::{Dialect, Script};

/// Result type for stage operations
pub type StageResult<T> = Result<T, StageError>;

/// Errors that can occur during pipeline stages
#[derive(Debug, thiserror::Error)]
pub enum StageError {
    #[error("Script detection failed: {0}")]
    ScriptDetection(String),

    #[error("Normalization failed: {0}")]
    Normalization(String),

    #[error("Tokenization failed: {0}")]
    Tokenization(String),

    #[error("ICR conversion failed: {0}")]
    ICRConversion(String),

    #[error("Script generation failed: {0}")]
    ScriptGeneration(String),

    #[error("Validation failed: {0}")]
    Validation(String),

    #[error("Unsupported dialect: {0}")]
    UnsupportedDialect(String),

    #[error("Invalid input: {0}")]
    InvalidInput(String),
}
