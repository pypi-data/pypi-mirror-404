use pyo3::prelude::*;
use std::sync::Arc;
use mini_langchain_core::agent::{AgentExecutor as CoreAgentExecutor};
use mini_langchain_core::llm::LLM;
use crate::llm::{SambaNovaLLM, OpenAILLM, AnthropicLLM, GoogleGenAILLM, OllamaLLM, PyLLMBridge};

#[pyclass]
pub struct AgentExecutor {
    inner: Arc<CoreAgentExecutor>,
}

#[pymethods]
impl AgentExecutor {
    #[new]
    fn new(llm_model: Py<PyAny>, py: Python<'_>) -> PyResult<Self> {
        // Must extract LLM just like in Chain
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
             Arc::new(PyLLMBridge { py_obj: llm_model })
        };
        
        Ok(Self {
            inner: Arc::new(CoreAgentExecutor::new(llm)),
        })
    }

    fn execute(&self, py: Python<'_>, input: String) -> PyResult<String> {
        let inner = self.inner.clone();
        let result = py.detach(move || {
            let rt = tokio::runtime::Builder::new_current_thread().enable_all().build().unwrap();
            rt.block_on(inner.execute(&input))
               .map_err(|e| e.to_string())
        });
        
        result.map_err(|e| pyo3::exceptions::PyValueError::new_err(e))
    }
}
