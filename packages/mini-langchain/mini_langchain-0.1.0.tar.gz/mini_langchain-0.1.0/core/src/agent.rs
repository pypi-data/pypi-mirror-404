use async_trait::async_trait;
use anyhow::Result;
use crate::llm::LLM;
use std::collections::HashMap;
use std::sync::Arc;

#[async_trait]
pub trait Tool: Send + Sync {
    fn name(&self) -> String;
    fn description(&self) -> String;
    async fn call(&self, input: &str) -> Result<String>;
}

pub struct AgentExecutor {
    llm: Arc<dyn LLM>,
    tools: HashMap<String, Arc<dyn Tool>>,
}

impl AgentExecutor {
    pub fn new(llm: Arc<dyn LLM>) -> Self {
        Self {
            llm,
            tools: HashMap::new(),
        }
    }

    pub fn with_tool(mut self, tool: Arc<dyn Tool>) -> Self {
        self.tools.insert(tool.name(), tool);
        self
    }

    pub async fn execute(&self, input: &str) -> Result<String> {
        // Very simple "Zero-Shot" style agent:
        // 1. Ask LLM what to do.
        // 2. Parse response (expecting "Action: [Name] Input: [Value]").
        // 3. Execute tool or return final answer.
        
        let prompt = format!(
            "Answer the following: {}\n\nAvailable Tools: {}\n\nFormat:\nAction: [Tool Name]\nInput: [Input]\n\nOR\n\nFinal Answer: [Answer]",
            input,
            self.tools.keys().cloned().collect::<Vec<_>>().join(", ")
        );

        let response = self.llm.generate(&prompt).await?;
        
        if let Some(final_answer) = response.split("Final Answer:").nth(1) {
            return Ok(final_answer.trim().to_string());
        }

        if let Some(action_part) = response.split("Action:").nth(1) {
            let parts: Vec<&str> = action_part.split("Input:").collect();
            if parts.len() >= 2 {
                let tool_name = parts[0].trim();
                let tool_input = parts[1].trim();

                if let Some(tool) = self.tools.get(tool_name) {
                    let tool_output = tool.call(tool_input).await?;
                    // In a real agent, we'd loop back. Here we just return the tool output for simplicity.
                    return Ok(format!("Tool Output: {}", tool_output));
                }
            }
        }

        Ok(response)
    }
}
