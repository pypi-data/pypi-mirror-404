use crate::llm::LLM;
use async_trait::async_trait;
use anyhow::{Result, Context};
use reqwest::Client;
use serde::{Deserialize, Serialize};

#[derive(Serialize)]
struct GeminiRequest {
    contents: Vec<Content>,
    #[serde(skip_serializing_if = "Option::is_none")]
    generation_config: Option<GenerationConfig>,
}

#[derive(Serialize)]
struct Content {
    parts: Vec<Part>,
    #[serde(skip_serializing_if = "Option::is_none")]
    role: Option<String>,
}

#[derive(Serialize)]
struct Part {
    text: String,
}

#[derive(Serialize)]
struct GenerationConfig {
    #[serde(skip_serializing_if = "Option::is_none")]
    temperature: Option<f64>,
    #[serde(skip_serializing_if = "Option::is_none")]
    max_output_tokens: Option<u32>,
}

#[derive(Deserialize)]
struct GeminiResponse {
    candidates: Option<Vec<Candidate>>,
}

#[derive(Deserialize)]
struct Candidate {
    content: ContentRes,
}

#[derive(Deserialize)]
struct ContentRes {
    parts: Vec<PartRes>,
}

#[derive(Deserialize)]
struct PartRes {
    text: String,
}

pub struct GoogleGenAIProvider {
    client: Client,
    api_key: String,
    model: String,
    temperature: Option<f64>,
    max_tokens: Option<u32>,
}

impl GoogleGenAIProvider {
    pub fn new(
        api_key: String,
        model: String, // e.g., "gemini-pro"
        temperature: Option<f64>,
        max_tokens: Option<u32>,
    ) -> Self {
        Self {
            client: Client::new(),
            api_key,
            model,
            temperature,
            max_tokens,
        }
    }
}

#[async_trait]
impl LLM for GoogleGenAIProvider {
    async fn generate(&self, prompt: &str) -> Result<String> {
        // Construct standard URL for Gemini
        let url = format!(
            "https://generativelanguage.googleapis.com/v1beta/models/{}:generateContent?key={}",
            self.model, self.api_key
        );

        let parts = vec![Part { text: prompt.to_string() }];
        let contents = vec![Content { parts, role: Some("user".to_string()) }];

        let config = if self.temperature.is_some() || self.max_tokens.is_some() {
            Some(GenerationConfig {
                temperature: self.temperature,
                max_output_tokens: self.max_tokens,
            })
        } else {
            None
        };

        let request = GeminiRequest {
            contents,
            generation_config: config,
        };

        let res = self.client.post(&url)
            .header("Content-Type", "application/json")
            .json(&request)
            .send()
            .await
            .context("Failed to send request to Google Gemini")?;

        if !res.status().is_success() {
            let error_text = res.text().await.unwrap_or_default();
            return Err(anyhow::anyhow!("Google Gemini API Error: {}", error_text));
        }

        let response: GeminiResponse = res.json().await
            .context("Failed to parse Google Gemini response")?;

        if let Some(candidates) = response.candidates {
            if let Some(first) = candidates.first() {
                if let Some(part) = first.content.parts.first() {
                    return Ok(part.text.clone());
                }
            }
        }
        
        Err(anyhow::anyhow!("No content returned from Google Gemini"))
    }
}

#[cfg(test)]
mod tests {
    use super::*;

    #[test]
    fn test_gemini_serialization() {
        let parts = vec![Part { text: "hi".to_string() }];
        let contents = vec![Content { parts, role: Some("user".to_string()) }];
        let request = GeminiRequest { contents, generation_config: None };
        
        let json = serde_json::to_string(&request).unwrap();
        assert!(json.contains("\"text\":\"hi\""));
        assert!(json.contains("\"role\":\"user\""));
    }
}
