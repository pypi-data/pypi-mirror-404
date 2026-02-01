use serde::{Deserialize, Serialize};
use std::fmt;
use std::str::FromStr;

/// Represents different Darija dialects
#[derive(Debug, Clone, Copy, PartialEq, Eq, Hash, Serialize, Deserialize)]
pub enum Dialect {
    /// Moroccan Darija
    Moroccan,
    // Future dialects can be added here:
    // Algerian,
    // Tunisian,
    // Libyan,
    // Egyptian,
}

impl Dialect {
    /// Get the two-letter code for the dialect
    pub fn code(&self) -> &'static str {
        match self {
            Dialect::Moroccan => "Ma",
        }
    }

    /// Get the full name of the dialect
    pub fn name(&self) -> &'static str {
        match self {
            Dialect::Moroccan => "Moroccan Darija",
        }
    }
}

impl FromStr for Dialect {
    type Err = String;

    fn from_str(s: &str) -> Result<Self, Self::Err> {
        match s.to_lowercase().as_str() {
            "ma" | "moroccan" | "morocco" => Ok(Dialect::Moroccan),
            _ => Err(format!("Unknown dialect: {}", s)),
        }
    }
}

impl fmt::Display for Dialect {
    fn fmt(&self, f: &mut fmt::Formatter<'_>) -> fmt::Result {
        write!(f, "{}", self.name())
    }
}

impl Default for Dialect {
    fn default() -> Self {
        Dialect::Moroccan
    }
}

#[cfg(test)]
mod tests {
    use super::*;

    #[test]
    fn test_dialect_from_str() {
        assert_eq!("Ma".parse::<Dialect>().unwrap(), Dialect::Moroccan);
        assert_eq!("moroccan".parse::<Dialect>().unwrap(), Dialect::Moroccan);
        assert!("Unknown".parse::<Dialect>().is_err());
    }

    #[test]
    fn test_dialect_code() {
        assert_eq!(Dialect::Moroccan.code(), "Ma");
    }

    #[test]
    fn test_default_dialect() {
        assert_eq!(Dialect::default(), Dialect::Moroccan);
    }
}
