use crate::{types::Dialect, CaDaR as RustCaDaR};
use pyo3::exceptions::PyValueError;
use pyo3::prelude::*;
use std::str::FromStr;

/// Python wrapper for CaDaR processor
#[pyclass(name = "CaDaR")]
pub struct PyCaDaR {
    inner: RustCaDaR,
}

#[pymethods]
impl PyCaDaR {
    /// Create a new CaDaR processor
    ///
    /// Args:
    ///     darija: Dialect code (default: "Ma" for Moroccan Darija)
    ///             Supported values: "Ma", "moroccan", "morocco"
    #[new]
    #[pyo3(signature = (darija="Ma"))]
    fn new(darija: &str) -> PyResult<Self> {
        let dialect = Dialect::from_str(darija).map_err(|e| PyValueError::new_err(e))?;

        Ok(PyCaDaR {
            inner: RustCaDaR::new(dialect),
        })
    }

    /// Convert Arabic script to Latin (Bizi) script
    ///
    /// Args:
    ///     text: Input text in Arabic script
    ///
    /// Returns:
    ///     Text in Latin (Bizi) script
    ///
    /// Example:
    ///     >>> cadar = CaDaR(darija="Ma")
    ///     >>> cadar.ara2bizi("سلام")
    ///     'slam'
    fn ara2bizi(&self, text: &str) -> PyResult<String> {
        self.inner
            .ara2bizi(text)
            .map_err(|e| PyValueError::new_err(e.to_string()))
    }

    /// Convert Latin (Bizi) script to Arabic script
    ///
    /// Args:
    ///     text: Input text in Latin (Bizi) script
    ///
    /// Returns:
    ///     Text in Arabic script
    ///
    /// Example:
    ///     >>> cadar = CaDaR(darija="Ma")
    ///     >>> cadar.bizi2ara("salam")
    ///     'سلام'
    fn bizi2ara(&self, text: &str) -> PyResult<String> {
        self.inner
            .bizi2ara(text)
            .map_err(|e| PyValueError::new_err(e.to_string()))
    }

    /// Standardize Arabic text
    ///
    /// Args:
    ///     text: Input text in Arabic script
    ///
    /// Returns:
    ///     Standardized text in Arabic script
    ///
    /// Example:
    ///     >>> cadar = CaDaR(darija="Ma")
    ///     >>> cadar.ara2ara("أنَا مِنْ المَغْرِب")
    ///     'انا من المغرب'
    fn ara2ara(&self, text: &str) -> PyResult<String> {
        self.inner
            .ara2ara(text)
            .map_err(|e| PyValueError::new_err(e.to_string()))
    }

    /// Standardize Latin (Bizi) text
    ///
    /// Args:
    ///     text: Input text in Latin (Bizi) script
    ///
    /// Returns:
    ///     Standardized text in Latin (Bizi) script
    ///
    /// Example:
    ///     >>> cadar = CaDaR(darija="Ma")
    ///     >>> cadar.bizi2bizi("salaaaam")
    ///     'salam'
    fn bizi2bizi(&self, text: &str) -> PyResult<String> {
        self.inner
            .bizi2bizi(text)
            .map_err(|e| PyValueError::new_err(e.to_string()))
    }

    /// Get the current dialect
    ///
    /// Returns:
    ///     Dialect name
    fn get_dialect(&self) -> String {
        self.inner.dialect().name().to_string()
    }

    /// String representation
    fn __repr__(&self) -> String {
        format!("CaDaR(dialect='{}')", self.inner.dialect().code())
    }

    /// String representation
    fn __str__(&self) -> String {
        format!("CaDaR processor for {}", self.inner.dialect().name())
    }
}

/// Convenience functions that use default Moroccan dialect
/// These match the API requested by the user

/// Convert Arabic script to Latin (Bizi) script
///
/// Args:
///     text: Input text in Arabic script
///     darija: Dialect code (default: "Ma" for Moroccan Darija)
///
/// Returns:
///     Text in Latin (Bizi) script
///
/// Example:
///     >>> import cadar
///     >>> cadar.ara2bizi("سلام", darija="Ma")
///     'slam'
#[pyfunction]
#[pyo3(signature = (text, darija="Ma"))]
fn ara2bizi(text: &str, darija: &str) -> PyResult<String> {
    let dialect = Dialect::from_str(darija).map_err(|e| PyValueError::new_err(e))?;

    let processor = RustCaDaR::new(dialect);
    processor
        .ara2bizi(text)
        .map_err(|e| PyValueError::new_err(e.to_string()))
}

/// Convert Latin (Bizi) script to Arabic script
///
/// Args:
///     text: Input text in Latin (Bizi) script
///     darija: Dialect code (default: "Ma" for Moroccan Darija)
///
/// Returns:
///     Text in Arabic script
///
/// Example:
///     >>> import cadar
///     >>> cadar.bizi2ara("salam", darija="Ma")
///     'سلام'
#[pyfunction]
#[pyo3(signature = (text, darija="Ma"))]
fn bizi2ara(text: &str, darija: &str) -> PyResult<String> {
    let dialect = Dialect::from_str(darija).map_err(|e| PyValueError::new_err(e))?;

    let processor = RustCaDaR::new(dialect);
    processor
        .bizi2ara(text)
        .map_err(|e| PyValueError::new_err(e.to_string()))
}

/// Standardize Arabic text
///
/// Args:
///     text: Input text in Arabic script
///     darija: Dialect code (default: "Ma" for Moroccan Darija)
///
/// Returns:
///     Standardized text in Arabic script
///
/// Example:
///     >>> import cadar
///     >>> cadar.ara2ara("أنَا مِنْ المَغْرِب", darija="Ma")
///     'انا من المغرب'
#[pyfunction]
#[pyo3(signature = (text, darija="Ma"))]
fn ara2ara(text: &str, darija: &str) -> PyResult<String> {
    let dialect = Dialect::from_str(darija).map_err(|e| PyValueError::new_err(e))?;

    let processor = RustCaDaR::new(dialect);
    processor
        .ara2ara(text)
        .map_err(|e| PyValueError::new_err(e.to_string()))
}

/// Standardize Latin (Bizi) text
///
/// Args:
///     text: Input text in Latin (Bizi) script
///     darija: Dialect code (default: "Ma" for Moroccan Darija)
///
/// Returns:
///     Standardized text in Latin (Bizi) script
///
/// Example:
///     >>> import cadar
///     >>> cadar.bizi2bizi("salaaaam", darija="Ma")
///     'salam'
#[pyfunction]
#[pyo3(signature = (text, darija="Ma"))]
fn bizi2bizi(text: &str, darija: &str) -> PyResult<String> {
    let dialect = Dialect::from_str(darija).map_err(|e| PyValueError::new_err(e))?;

    let processor = RustCaDaR::new(dialect);
    processor
        .bizi2bizi(text)
        .map_err(|e| PyValueError::new_err(e.to_string()))
}

/// CaDaR Python module
#[pymodule]
fn _cadar(m: &Bound<'_, PyModule>) -> PyResult<()> {
    m.add_class::<PyCaDaR>()?;
    m.add_function(wrap_pyfunction!(ara2bizi, m)?)?;
    m.add_function(wrap_pyfunction!(bizi2ara, m)?)?;
    m.add_function(wrap_pyfunction!(ara2ara, m)?)?;
    m.add_function(wrap_pyfunction!(bizi2bizi, m)?)?;

    // Module metadata
    m.add("__version__", env!("CARGO_PKG_VERSION"))?;
    m.add("__author__", "Ouail LAAMIRI")?;
    m.add("__doc__", "CaDaR: Canonicalization and Darija Representation - Bidirectional transliteration for Darija")?;

    Ok(())
}
