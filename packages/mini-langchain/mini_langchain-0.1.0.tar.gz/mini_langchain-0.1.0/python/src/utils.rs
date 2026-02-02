use pyo3::prelude::*;
use mini_langchain_core::token::TokenCounter;

#[pyclass]
pub struct TokenCalculator;

#[pymethods]
impl TokenCalculator {
    #[staticmethod]
    fn count(text: &str) -> usize {
        TokenCounter::count(text)
    }

    #[staticmethod]
    fn estimate_cost(text: &str, rate_per_1k: f64) -> f64 {
        TokenCounter::estimate_cost(text, rate_per_1k)
    }
}
