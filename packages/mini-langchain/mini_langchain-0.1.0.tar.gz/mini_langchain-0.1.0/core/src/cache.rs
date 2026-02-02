use std::collections::HashMap;
use std::sync::{Arc, Mutex};
use async_trait::async_trait;

#[async_trait]
pub trait Cache: Send + Sync {
    async fn get(&self, key: &str) -> Option<String>;
    async fn set(&self, key: &str, value: &str);
}

#[derive(Clone, Default)]
pub struct InMemoryCache {
    store: Arc<Mutex<HashMap<String, String>>>,
}

impl InMemoryCache {
    pub fn new() -> Self {
        Self {
            store: Arc::new(Mutex::new(HashMap::new())),
        }
    }
}

#[async_trait]
impl Cache for InMemoryCache {
    async fn get(&self, key: &str) -> Option<String> {
        let store = self.store.lock().unwrap();
        store.get(key).cloned()
    }

    async fn set(&self, key: &str, value: &str) {
        let mut store = self.store.lock().unwrap();
        store.insert(key.to_string(), value.to_string());
    }
}
