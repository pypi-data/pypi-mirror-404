use pyo3::prelude::*;
use std::sync::Arc;
use std::collections::HashMap;
use mini_langchain_core::loader::{Loader, TextLoader as CoreTextLoader};
use mini_langchain_core::schema::Document as CoreDocument;
use mini_langchain_core::embedding::{Embeddings, MockEmbeddings as CoreMockEmbeddings};
use mini_langchain_core::vectorstore::{VectorStore, InMemoryVectorStore as CoreInMemoryVectorStore};

#[pyclass]
pub struct Document {
    pub(crate) inner: CoreDocument,
}

#[pymethods]
impl Document {
    #[new]
    #[pyo3(signature = (page_content, metadata=None))]
    fn new(page_content: String, metadata: Option<HashMap<String, String>>) -> Self {
        let mut doc = CoreDocument::new(page_content);
        if let Some(meta) = metadata {
            doc.metadata = meta;
        }
        Self { inner: doc }
    }

    #[getter]
    fn page_content(&self) -> String {
        self.inner.page_content.clone()
    }
    
    #[getter]
    fn metadata(&self) -> HashMap<String, String> {
        self.inner.metadata.clone()
    }
}

#[pyclass]
pub struct TextLoader {
    inner: CoreTextLoader,
}

#[pymethods]
impl TextLoader {
    #[new]
    fn new(file_path: String) -> Self {
        Self {
            inner: CoreTextLoader::new(file_path),
        }
    }

    fn load(&self) -> PyResult<Vec<Document>> {
        let docs = self.inner.load()
            .map_err(|e| pyo3::exceptions::PyIOError::new_err(e.to_string()))?;
            
        Ok(docs.into_iter().map(|d| Document { inner: d }).collect())
    }
}

#[pyclass]
pub struct MockEmbeddings {
    pub(crate) inner: Arc<CoreMockEmbeddings>,
}

#[pymethods]
impl MockEmbeddings {
    #[new]
    fn new() -> Self {
        Self {
            inner: Arc::new(CoreMockEmbeddings),
        }
    }

    fn embed_query(&self, text: &str) -> PyResult<Vec<f32>> {
        let rt = tokio::runtime::Builder::new_current_thread().enable_all().build().unwrap();
        rt.block_on(self.inner.embed_query(text))
           .map_err(|e| pyo3::exceptions::PyValueError::new_err(e.to_string()))
    }
}

#[pyclass]
pub struct InMemoryVectorStore {
    inner: Arc<CoreInMemoryVectorStore>,
}

#[pymethods]
impl InMemoryVectorStore {
    #[new]
    fn new(embeddings: &MockEmbeddings) -> Self {
        Self {
            inner: Arc::new(CoreInMemoryVectorStore::new(embeddings.inner.clone())),
        }
    }

    fn add_documents(&self, docs: Vec<PyRef<Document>>) -> PyResult<Vec<String>> {
         let rt = tokio::runtime::Builder::new_current_thread().enable_all().build().unwrap();
         let core_docs: Vec<CoreDocument> = docs.iter().map(|d| d.inner.clone()).collect();
         
         rt.block_on(self.inner.add_documents(&core_docs))
            .map_err(|e| pyo3::exceptions::PyValueError::new_err(e.to_string()))
    }

    fn similarity_search(&self, query: String, k: usize) -> PyResult<Vec<Document>> {
         let rt = tokio::runtime::Builder::new_current_thread().enable_all().build().unwrap();
         let results = rt.block_on(self.inner.similarity_search(&query, k))
            .map_err(|e| pyo3::exceptions::PyValueError::new_err(e.to_string()))?;
            
         Ok(results.into_iter().map(|d| Document { inner: d }).collect())
    }
}
