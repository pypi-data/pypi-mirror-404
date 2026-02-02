use crate::schema::Document;
use crate::embedding::Embeddings;
use async_trait::async_trait;
use anyhow::Result;
use std::sync::{Arc, Mutex};
use std::cmp::Ordering;

#[async_trait]
pub trait VectorStore: Send + Sync {
    async fn add_documents(&self, docs: &[Document]) -> Result<Vec<String>>;
    async fn similarity_search(&self, query: &str, k: usize) -> Result<Vec<Document>>;
}

pub struct InMemoryVectorStore {
    documents: Arc<Mutex<Vec<Document>>>,
    embeddings: Arc<dyn Embeddings>,
    vectors: Arc<Mutex<Vec<Vec<f32>>>>,
}

impl InMemoryVectorStore {
    pub fn new(embeddings: Arc<dyn Embeddings>) -> Self {
        Self {
            documents: Arc::new(Mutex::new(Vec::new())),
            embeddings,
            vectors: Arc::new(Mutex::new(Vec::new())),
        }
    }

    fn cosine_similarity(v1: &[f32], v2: &[f32]) -> f32 {
        let dot_product: f32 = v1.iter().zip(v2.iter()).map(|(a, b)| a * b).sum();
        let norm_a: f32 = v1.iter().map(|a| a * a).sum::<f32>().sqrt();
        let norm_b: f32 = v2.iter().map(|b| b * b).sum::<f32>().sqrt();
        
        if norm_a == 0.0 || norm_b == 0.0 {
            return 0.0;
        }
        
        dot_product / (norm_a * norm_b)
    }
}

#[async_trait]
impl VectorStore for InMemoryVectorStore {
    async fn add_documents(&self, docs: &[Document]) -> Result<Vec<String>> {
        let texts: Vec<String> = docs.iter().map(|d| d.page_content.clone()).collect();
        let new_vectors = self.embeddings.embed_documents(&texts).await?;
        
        let mut stored_docs = self.documents.lock().unwrap();
        let mut stored_vectors = self.vectors.lock().unwrap();
        
        // Simple ID generation
        let mut ids = Vec::new();
        for (i, doc) in docs.iter().enumerate() {
            stored_docs.push(doc.clone());
            stored_vectors.push(new_vectors[i].clone());
            ids.push(format!("{}", stored_docs.len() - 1));
        }
        
        Ok(ids)
    }

    async fn similarity_search(&self, query: &str, k: usize) -> Result<Vec<Document>> {
        let query_vector = self.embeddings.embed_query(query).await?;
        let stored_vectors = self.vectors.lock().unwrap();
        let stored_docs = self.documents.lock().unwrap();
        
        let mut scores: Vec<(usize, f32)> = stored_vectors.iter().enumerate()
            .map(|(i, vec)| (i, Self::cosine_similarity(&query_vector, vec)))
            .collect();
            
        // Sort by similarity descending
        scores.sort_by(|a, b| b.1.partial_cmp(&a.1).unwrap_or(Ordering::Equal));
        
        let top_k = scores.into_iter().take(k)
            .map(|(i, _)| stored_docs[i].clone())
            .collect();
            
        Ok(top_k)
    }
}
