use crate::llm::LLM;
use async_trait::async_trait;
use anyhow::{Result, Context};
use reqwest::Client;
use serde::{Deserialize, Serialize};

#[derive(Serialize)]
struct AnthropicRequest {
    model: String,
    messages: Vec<Message>,
    #[serde(skip_serializing_if = "Option::is_none")]
    system: Option<String>, 
    #[serde(skip_serializing_if = "Option::is_none")]
    max_tokens: Option<u32>,
}

#[derive(Serialize)]
struct Message {
    role: String,
    content: String,
}

#[derive(Deserialize)]
struct AnthropicResponse {
    content: Vec<ContentBlock>,
}

#[derive(Deserialize)]
struct ContentBlock {
    text: String,
}

pub struct AnthropicProvider {
    client: Client,
    api_key: String,
    model: String,
    system_prompt: Option<String>,
    max_tokens: Option<u32>,
}

impl AnthropicProvider {
    pub fn new(
        api_key: String,
        model: String,
        system_prompt: Option<String>,
        max_tokens: Option<u32>,
    ) -> Self {
        Self {
            client: Client::new(),
            api_key,
            model,
            system_prompt,
            max_tokens,
        }
    }
}

#[async_trait]
impl LLM for AnthropicProvider {
    async fn generate(&self, prompt: &str) -> Result<String> {
        let messages = vec![Message { role: "user".to_string(), content: prompt.to_string() }];

        let request = AnthropicRequest {
            model: self.model.clone(),
            messages,
            system: self.system_prompt.clone(),
            max_tokens: self.max_tokens.or(Some(1024)), // Default max tokens required by Anthropic
        };

        let res = self.client.post("https://api.anthropic.com/v1/messages")
            .header("x-api-key", &self.api_key)
            .header("anthropic-version", "2023-06-01")
            .header("Content-Type", "application/json")
            .json(&request)
            .send()
            .await
            .context("Failed to send request to Anthropic")?;

        if !res.status().is_success() {
            let error_text = res.text().await.unwrap_or_default();
            return Err(anyhow::anyhow!("Anthropic API Error: {}", error_text));
        }

        let response: AnthropicResponse = res.json().await
            .context("Failed to parse Anthropic response")?;

        response.content.first()
            .map(|c| c.text.clone())
            .ok_or_else(|| anyhow::anyhow!("No content returned from Anthropic"))
    }
}

#[cfg(test)]
mod tests {
    use super::*;

    #[test]
    fn test_anthropic_serialization() {
        let request = AnthropicRequest {
            model: "claude-3".to_string(),
            messages: vec![Message { role: "user".to_string(), content: "hi".to_string() }],
            system: Some("sys".to_string()),
            max_tokens: Some(100),
        };
        let json = serde_json::to_string(&request).unwrap();
        assert!(json.contains("\"model\":\"claude-3\""));
        assert!(json.contains("\"system\":\"sys\""));
        assert!(json.contains("\"max_tokens\":100"));
    }
}
