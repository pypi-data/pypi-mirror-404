# Cortexa

Cortexa is a **fast, local-first AI assistant for Python**. It lets you use a real large language model (LLM) directly from Python with a clean, minimal API.

- ✅ Runs **locally** (no API keys required)
- ✅ Uses **Ollama** as the AI engine
- ✅ Streams responses (fast, ChatGPT-style typing)
- ✅ Concise, readable terminal output
- ✅ Simple `import cortexa` usage

---

## What Cortexa Is (and Is Not)

**Cortexa is:**
- A Python library that talks to a local AI model
- Free and offline after setup
- Ideal for learning, projects, and experimentation

**Cortexa is not:**
- A hosted cloud service
- A replacement for installing an AI runtime

Cortexa uses **Ollama** to run models locally. Ollama is required.

---

## Requirements

- Python **3.8+**
- Ollama installed (one-time)

Download Ollama from:
https://ollama.com

---

## Installation

### 1. Install Ollama

After installing Ollama, restart your computer.

Pull a model:
```bash
ollama pull llama3
```

Make sure Ollama is running:
```bash
ollama serve
```
(Or just open the Ollama app.)

---

### 2. Install Cortexa

Once published to PyPI:
```bash
pip install cortexa
```

For local development:
```bash
pip install requests
```

---

## Basic Usage

```python
import cortexa

ai = cortexa.Cortexa()

ai.chat("Explain recursion simply")
ai.chat("Write a Python function to reverse a list")
```

Responses stream live in the terminal.

---

## Features

- **Streaming output** (fast, responsive)
- **Concise answers** by default
- **Terminal-friendly formatting**
- **Conversation memory** (limited for speed)
- **Offline & private**

---

## Configuration

```python
ai = cortexa.Cortexa(
    model="llama3",     # Any Ollama model
    max_history=4,      # Context window size
    width=80            # Terminal wrap width
)
```

Smaller models = faster responses.

---

## Troubleshooting

### Ollama already running error
This is normal:
```
Only one usage of each socket address is permitted
```
It means Ollama is already running.

### Slow responses
- Use a smaller model
- Reduce `max_history`
- Make sure no other heavy apps are running

---

## Project Structure

```text
cortexa/
│
├── cortexa/
│   ├── __init__.py
│   ├── core.py
│   ├── llm.py
│   ├── memory.py
│   └── prompts.py
│
└── test.py
```

---

## License

MIT License

---

## Disclaimer

Cortexa runs AI models locally using Ollama. Model quality, speed, and hardware usage depend on your system and chosen model.

---

## Roadmap (Planned)

- CLI interface (`cortexa chat`)
- Hybrid local / API mode
- Tool usage (files, calculator)
- Persistent memory

---

## Author
Samarth Ankit Chugh

