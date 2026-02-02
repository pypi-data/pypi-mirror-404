use pyo3::prelude::*;
use std::sync::Arc;
use mini_langchain_core::llm::LLM;
use mini_langchain_core::providers::sambanova::SambaNovaProvider;
use mini_langchain_core::providers::openai::OpenAIProvider;
use mini_langchain_core::providers::anthropic::AnthropicProvider;
use mini_langchain_core::providers::google::GoogleGenAIProvider;
use mini_langchain_core::providers::ollama::OllamaProvider;
use async_trait::async_trait;

// --- Wrapper for Python LLMs ---
pub struct PyLLMBridge {
    pub(crate) py_obj: Py<PyAny>,
}

#[async_trait]
impl LLM for PyLLMBridge {
    async fn generate(&self, prompt: &str) -> anyhow::Result<String> {
        let prompt_string = prompt.to_string();
        let py_obj = Python::attach(|py| self.py_obj.clone_ref(py));
        
        let output = tokio::task::spawn_blocking(move || {
            Python::attach(|py| {
                let obj = py_obj.bind(py);
                let args = (prompt_string,);
                let result = obj.call_method1("generate", args)?;
                let s: String = result.extract()?;
                Ok::<String, PyErr>(s)
            })
        }).await??;
        
        Ok(output)
    }
}

// --- SambaNova ---
#[pyclass]
#[derive(Clone)]
pub struct SambaNovaLLM {
    pub(crate) inner: Arc<SambaNovaProvider>,
}

#[pymethods]
impl SambaNovaLLM {
    #[new]
    #[pyo3(signature = (model, api_key=None, system_prompt=None, temperature=None, max_tokens=None, top_k=None, top_p=None))]
    fn new(
        model: String, 
        api_key: Option<String>,
        system_prompt: Option<String>,
        temperature: Option<f64>,
        max_tokens: Option<u32>,
        top_k: Option<u32>,
        top_p: Option<f64>
    ) -> PyResult<Self> {
        let provider = SambaNovaProvider::new(api_key, model, system_prompt, temperature, max_tokens, top_k, top_p)
            .map_err(|e| pyo3::exceptions::PyValueError::new_err(e.to_string()))?;
        Ok(Self { inner: Arc::new(provider) })
    }
}

// --- OpenAI (and OpenRouter) ---
#[pyclass]
#[derive(Clone)]
pub struct OpenAILLM {
    pub(crate) inner: Arc<OpenAIProvider>,
}

#[pymethods]
impl OpenAILLM {
    #[new]
    #[pyo3(signature = (api_key, model, base_url=None, system_prompt=None, temperature=None, max_tokens=None))]
    fn new(
        api_key: String,
        model: String,
        base_url: Option<String>,
        system_prompt: Option<String>,
        temperature: Option<f64>,
        max_tokens: Option<u32>,
    ) -> Self {
        let provider = OpenAIProvider::new(api_key, model, base_url, system_prompt, temperature, max_tokens);
        Self { inner: Arc::new(provider) }
    }
}

// --- Anthropic ---
#[pyclass]
#[derive(Clone)]
pub struct AnthropicLLM {
    pub(crate) inner: Arc<AnthropicProvider>,
}

#[pymethods]
impl AnthropicLLM {
    #[new]
    #[pyo3(signature = (api_key, model, system_prompt=None, max_tokens=None))]
    fn new(
        api_key: String,
        model: String,
        system_prompt: Option<String>,
        max_tokens: Option<u32>,
    ) -> Self {
        let provider = AnthropicProvider::new(api_key, model, system_prompt, max_tokens);
        Self { inner: Arc::new(provider) }
    }
}

// --- Google Gemini ---
#[pyclass]
#[derive(Clone)]
pub struct GoogleGenAILLM {
    pub(crate) inner: Arc<GoogleGenAIProvider>,
}

#[pymethods]
impl GoogleGenAILLM {
    #[new]
    #[pyo3(signature = (api_key, model, temperature=None, max_tokens=None))]
    fn new(
        api_key: String,
        model: String,
        temperature: Option<f64>,
        max_tokens: Option<u32>,
    ) -> Self {
        let provider = GoogleGenAIProvider::new(api_key, model, temperature, max_tokens);
        Self { inner: Arc::new(provider) }
    }
}

// --- Ollama ---
#[pyclass]
#[derive(Clone)]
pub struct OllamaLLM {
    pub(crate) inner: Arc<OllamaProvider>,
}

#[pymethods]
impl OllamaLLM {
    #[new]
    #[pyo3(signature = (model, base_url=None, temperature=None))]
    fn new(
        model: String,
        base_url: Option<String>,
        temperature: Option<f64>,
    ) -> Self {
        let provider = OllamaProvider::new(model, base_url, temperature);
        Self { inner: Arc::new(provider) }
    }
}
