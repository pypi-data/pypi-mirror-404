use std::collections::HashMap;

#[derive(Debug, Clone)]
pub struct Document {
    pub page_content: String,
    pub metadata: HashMap<String, String>,
}

impl Document {
    pub fn new(content: String) -> Self {
        Self {
            page_content: content,
            metadata: HashMap::new(),
        }
    }

    pub fn with_metadata(mut self, key: &str, value: &str) -> Self {
        self.metadata.insert(key.to_string(), value.to_string());
        self
    }
}
