use tiktoken_rs::cl100k_base;

pub struct TokenCounter;

impl TokenCounter {
    /// Counts tokens used by a string using cl100k_base (standard for GPT-3.5/4/Llama-3ish)
    pub fn count(text: &str) -> usize {
        // For accurate counting we should ideally use the specific model encoding.
        // But cl100k_base is a safe, high-performance default for modern LLMs.
        let bpe = cl100k_base().unwrap();
        let tokens = bpe.encode_with_special_tokens(text);
        tokens.len()
    }

    /// Estimates cost based on input/output tokens and rate per 1k tokens.
    /// Returns estimated cost in USD.
    pub fn estimate_cost(text: &str, rate_per_1k: f64) -> f64 {
        let count = Self::count(text);
        (count as f64 / 1000.0) * rate_per_1k
    }
}
