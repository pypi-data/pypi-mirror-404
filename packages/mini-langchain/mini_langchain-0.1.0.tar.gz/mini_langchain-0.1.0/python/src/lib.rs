use pyo3::prelude::*;

pub mod llm;
pub mod chain;
pub mod memory;
pub mod rag;
pub mod agent;
pub mod utils;

use llm::{SambaNovaLLM, OpenAILLM, AnthropicLLM, GoogleGenAILLM, OllamaLLM};
use chain::{Chain, PromptTemplate};
use memory::{ConversationBufferMemory, InMemoryCache};
use rag::{Document, TextLoader, MockEmbeddings, InMemoryVectorStore};
use agent::AgentExecutor;
use utils::TokenCalculator;

#[pymodule]
fn mini_langchain(m: &Bound<'_, PyModule>) -> PyResult<()> {
    m.add_class::<PromptTemplate>()?;
    m.add_class::<InMemoryCache>()?;
    m.add_class::<Chain>()?;
    m.add_class::<SambaNovaLLM>()?;
    m.add_class::<OpenAILLM>()?;
    m.add_class::<AnthropicLLM>()?;
    m.add_class::<GoogleGenAILLM>()?;
    m.add_class::<OllamaLLM>()?;
    m.add_class::<ConversationBufferMemory>()?;
    m.add_class::<Document>()?;
    m.add_class::<TextLoader>()?;
    m.add_class::<MockEmbeddings>()?;
    m.add_class::<InMemoryVectorStore>()?;
    m.add_class::<AgentExecutor>()?;
    m.add_class::<TokenCalculator>()?;
    Ok(())
}
