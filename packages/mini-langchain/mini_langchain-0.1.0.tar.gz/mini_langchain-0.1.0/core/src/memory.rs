use std::collections::HashMap;
use std::sync::{Arc, Mutex};
use async_trait::async_trait;
use anyhow::Result;

/// Trait for Memory management in Chains.
#[async_trait]
pub trait Memory: Send + Sync {
    /// Load memory variables (e.g. history) into the input context
    async fn load_memory_variables(&self, inputs: &HashMap<String, String>) -> Result<HashMap<String, String>>;
    
    /// Save context from this run to memory
    async fn save_context(&self, inputs: &HashMap<String, String>, outputs: &HashMap<String, String>) -> Result<()>;

    /// Clear memory
    async fn clear(&self) -> Result<()>;
}

/// Simple buffer memory that stores chat history.
#[derive(Clone)]
pub struct ConversationBufferMemory {
    history: Arc<Mutex<Vec<String>>>,
    memory_key: String, // Key to inject into prompt (default: "history")
    human_prefix: String,
    ai_prefix: String,
}

impl ConversationBufferMemory {
    pub fn new() -> Self {
        Self {
            history: Arc::new(Mutex::new(Vec::new())),
            memory_key: "history".to_string(),
            human_prefix: "Human".to_string(),
            ai_prefix: "AI".to_string(),
        }
    }

    pub fn with_key(mut self, key: String) -> Self {
        self.memory_key = key;
        self
    }
}

#[async_trait]
impl Memory for ConversationBufferMemory {
    async fn load_memory_variables(&self, _inputs: &HashMap<String, String>) -> Result<HashMap<String, String>> {
        let history = self.history.lock().unwrap();
        let buffer = history.join("\n");
        
        let mut map = HashMap::new();
        map.insert(self.memory_key.clone(), buffer);
        Ok(map)
    }

    async fn save_context(&self, inputs: &HashMap<String, String>, outputs: &HashMap<String, String>) -> Result<()> {
        // Try specific keys first, fall back to "input" or arbitrary first value
        let input_val = inputs.get("input").map(|s| s.as_str())
            .or_else(|| inputs.values().next().map(|s| s.as_str()))
            .unwrap_or("");
            
        let output_val = outputs.get("output").map(|s| s.as_str())
            .or_else(|| outputs.values().next().map(|s| s.as_str()))
            .unwrap_or("");

        let entry = format!("{}: {}\n{}: {}", self.human_prefix, input_val, self.ai_prefix, output_val);
        
        let mut history = self.history.lock().unwrap();
        history.push(entry);
        
        Ok(())
    }

    async fn clear(&self) -> Result<()> {
        let mut history = self.history.lock().unwrap();
        history.clear();
        Ok(())
    }
}
