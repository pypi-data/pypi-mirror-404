use pyo3::prelude::*;
use std::sync::{Arc, Mutex};
use mini_langchain_core::memory::{ConversationBufferMemory as CoreBufferMemory};
use mini_langchain_core::cache::InMemoryCache as CoreInMemoryCache;

#[pyclass]
pub struct ConversationBufferMemory {
    pub(crate) inner: Arc<Mutex<CoreBufferMemory>>, 
}

#[pymethods]
impl ConversationBufferMemory {
    #[new]
    fn new() -> Self {
        Self {
            inner: Arc::new(Mutex::new(CoreBufferMemory::new())),
        }
    }
}

#[pyclass]
pub struct InMemoryCache {
    pub(crate) inner: Arc<CoreInMemoryCache>,
}

#[pymethods]
impl InMemoryCache {
    #[new]
    fn new() -> Self {
        Self {
            inner: Arc::new(CoreInMemoryCache::new()),
        }
    }
}
