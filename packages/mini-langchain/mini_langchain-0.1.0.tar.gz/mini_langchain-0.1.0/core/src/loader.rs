use crate::schema::Document;
use anyhow::Result;
use std::fs;
use std::path::Path;

pub trait Loader {
    fn load(&self) -> Result<Vec<Document>>;
}

pub struct TextLoader {
    file_path: String,
}

impl TextLoader {
    pub fn new(file_path: String) -> Self {
        Self { file_path }
    }
}

impl Loader for TextLoader {
    fn load(&self) -> Result<Vec<Document>> {
        let content = fs::read_to_string(Path::new(&self.file_path))?;
        let doc = Document::new(content)
            .with_metadata("source", &self.file_path);
        
        Ok(vec![doc])
    }
}
