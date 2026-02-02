use crate::llm::LLM;
use async_trait::async_trait;
use anyhow::{Result, Context};
use reqwest::Client;
use serde::{Deserialize, Serialize};

#[derive(Serialize)]
struct OllamaRequest {
    model: String,
    messages: Vec<Message>,
    stream: bool,
    #[serde(skip_serializing_if = "Option::is_none")]
    options: Option<OllamaOptions>,
}

#[derive(Serialize)]
struct Message {
    role: String,
    content: String,
}

#[derive(Serialize)]
struct OllamaOptions {
    #[serde(skip_serializing_if = "Option::is_none")]
    temperature: Option<f64>,
}

#[derive(Deserialize)]
struct OllamaResponse {
    message: MessageRes,
}

#[derive(Deserialize)]
struct MessageRes {
    content: String,
}

pub struct OllamaProvider {
    client: Client,
    base_url: String,
    model: String,
    temperature: Option<f64>,
}

impl OllamaProvider {
    pub fn new(
        model: String,
        base_url: Option<String>,
        temperature: Option<f64>,
    ) -> Self {
        Self {
            client: Client::new(),
            base_url: base_url.unwrap_or_else(|| "http://localhost:11434".to_string()),
            model,
            temperature,
        }
    }
}

#[async_trait]
impl LLM for OllamaProvider {
    async fn generate(&self, prompt: &str) -> Result<String> {
        let url = format!("{}/api/chat", self.base_url.trim_end_matches('/'));
        
        let messages = vec![Message { role: "user".to_string(), content: prompt.to_string() }];

        let request = OllamaRequest {
            model: self.model.clone(),
            messages,
            stream: false,
            options: self.temperature.map(|t| OllamaOptions { temperature: Some(t) }),
        };

        let res = self.client.post(&url)
            .header("Content-Type", "application/json")
            .json(&request)
            .send()
            .await
            .context("Failed to send request to Ollama")?;

        if !res.status().is_success() {
            let error_text = res.text().await.unwrap_or_default();
            return Err(anyhow::anyhow!("Ollama API Error: {}", error_text));
        }

        let response: OllamaResponse = res.json().await
            .context("Failed to parse Ollama response")?;

        Ok(response.message.content)
    }
}
