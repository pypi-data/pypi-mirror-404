# SQLAgent Community

**SQLAgent Community** is a Python library for creating intelligent agents that can query SQLite databases using LLMs, generate SQL from natural language, and maintain conversation memory. Ideal for exploratory data analysis, conversational dashboards, or automating complex queries.

---

## Requirements

- Python >= 3.10
- SQLite
- [Ollama](https://ollama.com/) installed and configured
  - Ollama provides the LLM and embedding models used by SQLAgent
- Pandas (for reading Excel files)
- Rich (optional, for nice logs)

## Installation

You can install via pip (once published on PyPI):

```bash
pip install sqlagent-community
```

---

## Configuration

### Suggested file structure

```
dataset/
├─ data.db                  # SQLite database
├─ excels/                   # Excel files to build the DB
vector_db/
├─ schema_embeddings.pkl     # Schema embeddings
context/
├─ file.md                   # Additional context for the agent
```

### Initialize Builder and database

```python
from sqlagent_community.Builder import SQLBuilder

builder = SQLBuilder(
    excel_dir="dataset/excels",
    db_file="dataset/data.db",
    embed_file="vector_db/schema_embeddings.pkl",
    embed_model="qwen3-embedding:0.6b",
    verbose=True
)

builder.build()
```

### Set up Chat and Memory

```python
from sqlagent_community.memory.ChatManager import ChatManager
from sqlagent_community.memory.ConversationSummaryBufferMemory import ConversationSummaryBufferMemory

manager = ChatManager()
chat_id = manager.create_chat()

memory = ConversationSummaryBufferMemory(chat_id=chat_id)
```

### Initialize the Agent

```python
from sqlagent_community.Agent import SQLAgent

agent = SQLAgent(
    db_path="dataset/data.db",
    embed_file="vector_db/schema_embeddings.pkl",
    embedding_model="qwen3-embedding:0.6b",
    llm_model="qwen2.5:7b",
    text2sql="qwen2.5-coder:7b",
    memory=memory,
    context="./context/file.md",
    verbose=True
)
```

### Asking questions to the agent

```python
question = "What is the average altitude per municipality of the collections?"
result = agent.run(question)

print(result)
```

The agent converts the question into SQL, executes it on the database, and returns the result, while maintaining conversation history and context.

---

## Features

* Automatic SQLite database construction from Excel files.
* SQL generation via LLM from natural language.
* Summarized conversational memory per chat.
* Additional context from Markdown files.
* Detailed logs for debugging.

---

## License

MIT License – see the LICENSE file for details.

---
