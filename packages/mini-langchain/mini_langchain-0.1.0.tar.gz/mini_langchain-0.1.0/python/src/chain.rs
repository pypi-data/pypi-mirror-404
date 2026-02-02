use pyo3::prelude::*;
use std::collections::HashMap;
use std::sync::{Arc, Mutex};
use mini_langchain_core::prompt::PromptTemplate as CorePromptTemplate;
use mini_langchain_core::chain::LLMChain as CoreLLMChain;
use mini_langchain_core::llm::LLM;

use crate::llm::{SambaNovaLLM, OpenAILLM, AnthropicLLM, GoogleGenAILLM, OllamaLLM, PyLLMBridge};
use crate::memory::{ConversationBufferMemory, InMemoryCache};

#[pyclass]
pub struct PromptTemplate {
    pub(crate) inner: CorePromptTemplate,
}

#[pymethods]
impl PromptTemplate {
    #[new]
    fn new(template: String, variables: Vec<String>) -> Self {
        Self {
            inner: CorePromptTemplate::new(&template, variables),
        }
    }

    fn format(&self, values: HashMap<String, String>) -> PyResult<String> {
        self.inner.format(&values).map_err(|e| pyo3::exceptions::PyValueError::new_err(e.to_string()))
    }
}

#[pyclass]
pub struct Chain {
    inner: Arc<Mutex<Option<CoreLLMChain>>>,
}

#[pymethods]
impl Chain {
    #[new]
    #[pyo3(signature = (prompt, llm_model, memory=None))]
    fn new(py: Python<'_>, prompt: &PromptTemplate, llm_model: Py<PyAny>, memory: Option<&ConversationBufferMemory>) -> PyResult<Self> {
        // Try to extract known Rust LLMs
        let llm: Arc<dyn LLM> = if let Ok(samba) = llm_model.extract::<SambaNovaLLM>(py) {
             samba.inner.clone()
        } else if let Ok(openai) = llm_model.extract::<OpenAILLM>(py) {
             openai.inner.clone()
        } else if let Ok(claude) = llm_model.extract::<AnthropicLLM>(py) {
             claude.inner.clone()
        } else if let Ok(gemini) = llm_model.extract::<GoogleGenAILLM>(py) {
             gemini.inner.clone()
        } else if let Ok(ollama) = llm_model.extract::<OllamaLLM>(py) {
             ollama.inner.clone()
        } else {
             // Fallback to Python Bridge
             Arc::new(PyLLMBridge { py_obj: llm_model })
        };
        
        let mut chain = CoreLLMChain::new(prompt.inner.clone(), llm);
        
        if let Some(mem) = memory {
             let core_mem = mem.inner.lock().unwrap().clone();
             chain = chain.with_memory(Arc::new(core_mem));
        }

        Ok(Self {
            inner: Arc::new(Mutex::new(Some(chain))),
        })
    }

    fn set_cache(&self, cache: &InMemoryCache) -> PyResult<()> {
        let mut guard = self.inner.lock().unwrap();
        if let Some(chain) = guard.take() {
            let new_chain = chain.with_cache(cache.inner.clone());
            *guard = Some(new_chain);
            Ok(())
        } else {
            Err(pyo3::exceptions::PyRuntimeError::new_err("Chain not initialized"))
        }
    }

    #[pyo3(signature = (inputs))]
    fn invoke(&self, py: Python<'_>, inputs: HashMap<String, String>) -> PyResult<String> {
        let inner_clone = self.inner.clone();
        
        let result: Result<String, String> = py.detach(move || {
            let rt = tokio::runtime::Builder::new_current_thread()
                .enable_all()
                .build()
                .unwrap();

            rt.block_on(async {
                let mut chain_opt = inner_clone.lock().unwrap();
                if let Some(chain) = chain_opt.as_mut() {
                    chain.call(inputs).await.map_err(|e| e.to_string())
                } else {
                     Err("Chain not initialized".to_string())
                }
            })
        });

        result.map_err(|e| pyo3::exceptions::PyRuntimeError::new_err(e))
    }
}
