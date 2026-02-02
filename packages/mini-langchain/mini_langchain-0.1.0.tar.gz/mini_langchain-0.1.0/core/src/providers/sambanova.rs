use async_trait::async_trait;
use anyhow::{Result, anyhow, Context};
use crate::llm::LLM;
use serde_json::json;
use std::env;

pub struct SambaNovaProvider {
    api_key: String,
    model: String,
    client: reqwest::Client,
    pub system_prompt: String,
    pub temperature: Option<f64>,
    pub max_tokens: Option<u32>,
    pub top_k: Option<u32>,
    pub top_p: Option<f64>,
}

impl SambaNovaProvider {
    pub fn new(
        api_key: Option<String>, 
        model: String,
        system_prompt: Option<String>,
        temperature: Option<f64>,
        max_tokens: Option<u32>,
        top_k: Option<u32>,
        top_p: Option<f64>,
    ) -> Result<Self> {
        let key = api_key.or_else(|| env::var("SAMBANOVA_API_KEY").ok())
            .ok_or_else(|| anyhow!("SambaNova API Key must be provided or set in SAMBANOVA_API_KEY env var"))?;
            
        Ok(Self {
            api_key: key,
            model,
            client: reqwest::Client::new(),
            system_prompt: system_prompt.unwrap_or_else(|| "You are a helpful assistant.".to_string()),
            temperature,
            max_tokens,
            top_k,
            top_p,
        })
    }
}

#[async_trait]
impl LLM for SambaNovaProvider {
    async fn generate(&self, prompt: &str) -> Result<String> {
        let url = "https://api.sambanova.ai/v1/chat/completions";
        
        let mut body = json!({
            "stream": false,
            "model": self.model,
            "messages": [
                {
                    "role": "system",
                    "content": self.system_prompt
                },
                {
                    "role": "user",
                    "content": prompt
                }
            ]
        });

        if let Some(temp) = self.temperature {
            body.as_object_mut().unwrap().insert("temperature".to_string(), json!(temp));
        }
        if let Some(max_t) = self.max_tokens {
            body.as_object_mut().unwrap().insert("max_tokens".to_string(), json!(max_t));
        }
        if let Some(k) = self.top_k {
            body.as_object_mut().unwrap().insert("top_k".to_string(), json!(k));
        }
        if let Some(p) = self.top_p {
            body.as_object_mut().unwrap().insert("top_p".to_string(), json!(p));
        }

        let resp = self.client.post(url)
            .header("Authorization", format!("Bearer {}", self.api_key))
            .header("Content-Type", "application/json")
            .json(&body)
            .send()
            .await
            .context("Failed to send request to SambaNova")?;

        if !resp.status().is_success() {
            let error_text = resp.text().await.unwrap_or_default();
            return Err(anyhow!("SambaNova API error: {}", error_text));
        }

        let json_resp: serde_json::Value = resp.json().await
            .context("Failed to parse SambaNova response")?;

        // Extract content from choices[0].message.content
        let content = json_resp["choices"][0]["message"]["content"]
            .as_str()
            .ok_or_else(|| anyhow!("Invalid response structure from SambaNova"))?
            .to_string();

        Ok(content)
    }
}
