use async_trait::async_trait;
use anyhow::Result;

#[async_trait]
pub trait Embeddings: Send + Sync {
    async fn embed_query(&self, text: &str) -> Result<Vec<f32>>;
    async fn embed_documents(&self, texts: &[String]) -> Result<Vec<Vec<f32>>>;
}

pub struct MockEmbeddings;

#[async_trait]
impl Embeddings for MockEmbeddings {
    async fn embed_query(&self, text: &str) -> Result<Vec<f32>> {
        // Deterministic mock embedding based on length (for testing)
        // In reality, this would call an API.
        let len = text.len() as f32;
        Ok(vec![len, len / 2.0, len / 3.0])
    }

    async fn embed_documents(&self, texts: &[String]) -> Result<Vec<Vec<f32>>> {
        let mut vecs = Vec::new();
        for text in texts {
            vecs.push(self.embed_query(text).await?);
        }
        Ok(vecs)
    }
}
