# Mini LangChain ⚡
> **Next-Gen LLM Framework.** Built in Rust. Bindings for Python & Node.js.
> *High Performance. Low Token Overhead. Type Safe.*

[![Rust](https://img.shields.io/badge/Core-Rust_🦀-orange.svg)]()
[![Python](https://img.shields.io/badge/Bindings-Python_🐍-blue.svg)]()
[![Node.js](https://img.shields.io/badge/Bindings-Node.js_💚-green.svg)]()
[![License](https://img.shields.io/badge/License-MIT-purple.svg)]()

---

## 🔮 Why Mini LangChain?

Standard frameworks are bloated. **Mini LangChain** is stripped down to the bare metal.

*   **🚀 Blazing Fast**: Core logic runs in native Rust. No GIL bottlenecks for heavy lifting.
*   **💰 Token Efficient**: Native token counting and automatic prompt minification.
*   **🌐 Cross-Language**: Write your logic in Python or Node.js; let Rust handle the heavy lifting.
*   **🧠 Smart Memory**: Thread-safe `ConversationBufferMemory` shared across chains.

---

## ⚡ Features (Ready)

| Module | Status | Description |
| :--- | :---: | :--- |
| **🧠 Memory** | ✅ | `ConversationBufferMemory` (Context preservation) |
| **📂 Loaders** | ✅ | `TextLoader` & `Document` Schema |
| **🔍 RAG** | ✅ | `InMemoryVectorStore` & `Embeddings` (Cosine Sim) |
| **🤖 Agents** | ✅ | `AgentExecutor` (Zero-shot Tool Use) |
| **⛓️ Chains** | ✅ | `LLMChain` with Prompt Templates |

---

## 🛠️ Installation

### Python 🐍
```bash
pip install mini_langchain
```

### Node.js 💚
```bash
npm install mini-langchain-node
```

---

## 💻 Usage

### 1. RAG & Vector Search 🔍
*Embed documents and search by semantic similarity.*

**Rust Core 🦀**
```rust
use mini_langchain_core::{
    vectorstore::{VectorStore, InMemoryVectorStore},
    embedding::MockEmbeddings,
    schema::Document
};
use std::sync::Arc;

#[tokio::main]
async fn main() -> anyhow::Result<()> {
    // 1. Initialize
    let store = InMemoryVectorStore::new(Arc::new(MockEmbeddings));

    // 2. Add Documents
    let docs = vec![
        Document::new("Rust is memory safe 🦀".to_string())
            .with_metadata("tag", "tech"),
        Document::new("Node.js is async 💚".to_string())
            .with_metadata("tag", "tech"),
    ];
    store.add_documents(&docs).await?;

    // 3. Search
    let results = store.similarity_search("memory", 1).await?;
    println!("{}", results[0].page_content); // "Rust is memory safe 🦀"
    
    Ok(())
}
```

**Python**
```python
from mini_langchain import InMemoryVectorStore, MockEmbeddings, Document

# 1. Initialize
store = InMemoryVectorStore(MockEmbeddings())

# 2. Add Documents
store.add_documents([
    Document("Rust is memory safe 🦀", {"tag": "tech"}),
    Document("Node.js is async 💚", {"tag": "tech"})
])

# 3. Search
docs = store.similarity_search("memory", 1)
print(docs[0].page_content) # "Rust is memory safe 🦀"
```

**Node.js**
```javascript
const { InMemoryVectorStore, MockEmbeddings, Document } = require('mini-langchain-node');

// 1. Initialize
const store = new InMemoryVectorStore(new MockEmbeddings());

// 2. Add Documents
await store.addDocuments([
    new Document("Rust is memory safe 🦀", { tag: "tech" }),
    new Document("Node.js is async 💚", { tag: "tech" })
]);

// 3. Search
const docs = await store.similaritySearch("memory", 1);
console.log(docs[0].pageContent);
```

### 2. Conversational Chains 💬
*Maintain context effortlessly.*

```python
from mini_langchain import Chain, PromptTemplate, SambaNovaLLM, ConversationBufferMemory

# 1. Setup
llm = SambaNovaLLM("Meta-Llama-3.1-8B-Instruct", "your-api-key")
memory = ConversationBufferMemory()
prompt = PromptTemplate("History: {history} \nUser: {input}", ["history", "input"])

# 2. Run
chain = Chain(prompt, llm, memory)
print(chain.invoke({"input": "Hello!"}))
print(chain.invoke({"input": "My name is User."})) # Memory remembers!
```

---

## 🗺️ Roadmap
- [ ] **Embeddings**: Integration with SambaNova/OpenAI embeddings.
- [ ] **Persistent Storage**: SQLite/PGVector support.
- [ ] **Tools**: Search & Calculator implementations.

---

<center>
<i>Built with ❤️ by GrandpaEJ</i>
</center>
