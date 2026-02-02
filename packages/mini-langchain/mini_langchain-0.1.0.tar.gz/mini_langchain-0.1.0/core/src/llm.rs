use async_trait::async_trait;
use anyhow::Result;

#[async_trait]
pub trait LLM: Send + Sync {
    /// Generate a response solely based on the prompt.
    async fn generate(&self, prompt: &str) -> Result<String>;
}
