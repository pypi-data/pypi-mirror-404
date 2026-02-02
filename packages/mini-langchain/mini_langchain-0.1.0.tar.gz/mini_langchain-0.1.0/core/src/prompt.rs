use std::collections::HashMap;
use anyhow::{Result, anyhow};
use serde::{Deserialize, Serialize};

#[derive(Debug, Clone, Serialize, Deserialize)]
pub struct PromptTemplate {
    template: String,
    input_variables: Vec<String>,
}

impl PromptTemplate {
    pub fn new(template: &str, input_variables: Vec<String>) -> Self {
        Self {
            template: template.to_string(),
            input_variables,
        }
    }

    /// Formats the template by replacing {variable} with values.
    /// Also performs basic cost-saving minification (trimming).
    pub fn format(&self, values: &HashMap<String, String>) -> Result<String> {
        let mut result = self.template.clone();
        for var in &self.input_variables {
            let value = values.get(var).ok_or_else(|| anyhow!("Missing variable: {}", var))?;
            result = result.replace(&format!("{{{}}}", var), value);
        }
        Ok(result)
    }

    /// Aggressive minification to reduce token cost.
    /// 1. Trims whitespace.
    /// 2. Replaces multiple spaces/newlines with single ones (context dependent).
    pub fn minify(&self, populated_prompt: &str) -> String {
        // Simple implementation: 
        // 1. Split by whitespace and rejoin with single space
        // This is safe for many LLM prompts but risky for code generation or markdown.
        // For "Low Cost" mode, we assume the user wants this.
        // A better approach would be to preserve newlines but trim indentation.
        
        // Strategy: 
        // 1. Trim lines.
        // 2. Remove empty lines.
        populated_prompt
            .lines()
            .map(|l| l.trim())
            .filter(|l| !l.is_empty())
            .collect::<Vec<&str>>()
            .join("\n")
    }
}

#[cfg(test)]
mod tests {
    use super::*;

    #[test]
    fn test_format() {
        let tmpl = PromptTemplate::new("Hello {name}!", vec!["name".to_string()]);
        let mut values = HashMap::new();
        values.insert("name".to_string(), "World".to_string());
        
        assert_eq!(tmpl.format(&values).unwrap(), "Hello World!");
    }

    #[test]
    fn test_minify() {
        let tmpl = PromptTemplate::new("", vec![]);
        let input = "
        Hello   
        
        World
        ";
        // Should become "Hello\nWorld"
        assert_eq!(tmpl.minify(input), "Hello\nWorld");
    }
}
