use crate::llm::LLM;
use async_trait::async_trait;
use anyhow::{Result, Context};
use reqwest::Client;
use serde::{Deserialize, Serialize};

#[derive(Serialize)]
struct OpenAIRequest {
    model: String,
    messages: Vec<Message>,
    #[serde(skip_serializing_if = "Option::is_none")]
    temperature: Option<f64>,
    #[serde(skip_serializing_if = "Option::is_none")]
    max_tokens: Option<u32>,
}

#[derive(Serialize)]
struct Message {
    role: String,
    content: String,
}

#[derive(Deserialize)]
struct OpenAIResponse {
    choices: Vec<Choice>,
}

#[derive(Deserialize)]
struct Choice {
    message: MessageRes,
}

#[derive(Deserialize)]
struct MessageRes {
    content: String,
}

pub struct OpenAIProvider {
    client: Client,
    api_key: String,
    base_url: String,
    model: String,
    system_prompt: Option<String>,
    temperature: Option<f64>,
    max_tokens: Option<u32>,
}

impl OpenAIProvider {
    pub fn new(
        api_key: String,
        model: String,
        base_url: Option<String>,
        system_prompt: Option<String>,
        temperature: Option<f64>,
        max_tokens: Option<u32>,
    ) -> Self {
        let base = base_url.unwrap_or_else(|| "https://api.openai.com/v1/chat/completions".to_string());
        Self {
            client: Client::new(),
            api_key,
            base_url: base,
            model,
            system_prompt,
            temperature,
            max_tokens,
        }
    }
}

#[async_trait]
impl LLM for OpenAIProvider {
    async fn generate(&self, prompt: &str) -> Result<String> {
        let mut messages = Vec::new();
        if let Some(sys) = &self.system_prompt {
            messages.push(Message { role: "system".to_string(), content: sys.clone() });
        }
        messages.push(Message { role: "user".to_string(), content: prompt.to_string() });

        let request = OpenAIRequest {
            model: self.model.clone(),
            messages,
            temperature: self.temperature,
            max_tokens: self.max_tokens,
        };

        let res = self.client.post(&self.base_url)
            .header("Authorization", format!("Bearer {}", self.api_key))
            .header("Content-Type", "application/json")
            .json(&request)
            .send()
            .await
            .context("Failed to send request to OpenAI")?;

        if !res.status().is_success() {
            let error_text = res.text().await.unwrap_or_default();
            return Err(anyhow::anyhow!("OpenAI API Error: {}", error_text));
        }

        let response: OpenAIResponse = res.json().await
            .context("Failed to parse OpenAI response")?;

        response.choices.first()
            .map(|c| c.message.content.clone())
            .ok_or_else(|| anyhow::anyhow!("No choices returned from OpenAI"))
    }
}

#[cfg(test)]
mod tests {
    use super::*;

    #[test]
    fn test_openai_serialization() {
        let request = OpenAIRequest {
            model: "gpt-4".to_string(),
            messages: vec![Message { role: "user".to_string(), content: "hello".to_string() }],
            temperature: Some(0.7),
            max_tokens: None,
        };
        let json = serde_json::to_string(&request).unwrap();
        assert!(json.contains("\"model\":\"gpt-4\""));
        assert!(json.contains("\"role\":\"user\""));
        assert!(json.contains("\"content\":\"hello\""));
        assert!(json.contains("\"temperature\":0.7"));
    }
}
