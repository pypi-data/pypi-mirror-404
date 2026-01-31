# StateBase Python SDK

The official Python client for [StateBase](https://statebase.org) - The Reliability Layer for Production AI Agents.

[![PyPI version](https://badge.fury.io/py/statebase.svg)](https://badge.fury.io/py/statebase)

## 📦 Installation

```bash
pip install statebase
```

## 🚀 Quick Start

### 1. Initialize

```python
from statebase import StateBase

sb = StateBase(api_key="sb_live_...")
```

### 2. Sessions (The Interaction Loop)

```python
# Create a session
session = sb.sessions.create(
    agent_id="coding-assistant",
    user_id="user_123"
)

# ... inside your chat loop ...
user_input = "How do I fix this bug?"

# Get Context (RAG + State + History)
ctx = sb.sessions.get_context(session.id, query=user_input)

# Generate with LLM
# ... call openai ...
ai_response = "You should check the stack trace."

# Log the Turn
sb.sessions.add_turn(
    session_id=session.id,
    input=user_input,
    output=ai_response
)
```

### 3. Memory (Long-term Knowledge)

```python
# Add a fact
sb.memory.add(
    user_id="user_123",
    content="User prefers TypeScript over JavaScript",
    tags=["preference", "coding"]
)

# Search
facts = sb.memory.search(
    user_id="user_123",
    query="coding preferences"
)
```

## 📚 Documentation

Full docs: [docs.statebase.org](https://docs.statebase.org)
