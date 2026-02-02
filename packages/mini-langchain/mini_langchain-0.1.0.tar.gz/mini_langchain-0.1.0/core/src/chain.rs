use std::collections::HashMap;
use anyhow::Result;
use crate::llm::LLM;
use crate::prompt::PromptTemplate;
use crate::cache::Cache;
use crate::memory::Memory;
use std::sync::Arc;

#[derive(Clone)]
pub struct LLMChain {
    prompt: PromptTemplate,
    llm: Arc<dyn LLM>,
    cache: Option<Arc<dyn Cache>>,
    memory: Option<Arc<dyn Memory>>,
}

impl LLMChain {
    pub fn new(prompt: PromptTemplate, llm: Arc<dyn LLM>) -> Self {
        Self {
            prompt,
            llm,
            cache: None, // Default no cache
            memory: None, // Default no memory
        }
    }

    pub fn with_cache(mut self, cache: Arc<dyn Cache>) -> Self {
        self.cache = Some(cache);
        self
    }

    pub fn with_memory(mut self, memory: Arc<dyn Memory>) -> Self {
        self.memory = Some(memory);
        self
    }

    pub async fn call(&self, mut inputs: HashMap<String, String>) -> Result<String> {
        // 0. Load Memory
        if let Some(memory) = &self.memory {
            let mem_vars = memory.load_memory_variables(&inputs).await?;
            inputs.extend(mem_vars);
        }

        // 1. Format Prompt
        let formatted = self.prompt.format(&inputs)?;
        
        // 2. Minify (Cost Saving!)
        let minified = self.prompt.minify(&formatted);

        // 3. Check Cache
        if let Some(cache) = &self.cache {
            if let Some(cached_response) = cache.get(&minified).await {
                // Determine mechanism to signal it was cached? 
                // For now just return the string.
                return Ok(cached_response);
            }
        }

        // 4. Call LLM
        let result = self.llm.generate(&minified).await?;

        // 5. Store in Cache
        if let Some(cache) = &self.cache {
            cache.set(&minified, &result).await;
        }

        // 5. Store in Cache
        if let Some(cache) = &self.cache {
            cache.set(&minified, &result).await;
        }

        // 6. Save Context to Memory
        if let Some(memory) = &self.memory {
            // Need output variables
            let mut outputs = HashMap::new();
            outputs.insert("output".to_string(), result.clone());
            memory.save_context(&inputs, &outputs).await?;
        }

        Ok(result)
    }
}
