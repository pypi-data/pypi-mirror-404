# 🧠 Cognify AI

<p align="center">
  <strong>Code Cognition — Your AI-Powered Code Assistant</strong>
</p>

<p align="center">
  <a href="#features">Features</a> •
  <a href="#installation">Installation</a> •
  <a href="#providers">Providers</a> •
  <a href="#usage">Usage</a> •
  <a href="#documentation">Docs</a> •
  <a href="#contributing">Contributing</a>
</p>

<p align="center">
  <img src="https://img.shields.io/badge/python-3.9+-blue.svg" alt="Python 3.9+">
  <img src="https://img.shields.io/badge/license-MIT-green.svg" alt="MIT License">
  <img src="https://img.shields.io/badge/tests-144%20passed-brightgreen.svg" alt="Tests">
  <img src="https://img.shields.io/badge/providers-6%20supported-purple.svg" alt="6 Providers">
</p>

---

A powerful CLI tool that brings AI-powered code cognition to your terminal. Review code, generate functions, search your codebase semantically, and refactor projects—with support for **multiple LLM providers** including local (Ollama) and cloud options with free tiers.

## ✨ Features

| Feature | Description |
|---------|-------------|
| 🔍 **Code Review** | Analyze code for bugs, security issues, and style problems |
| ⚡ **Code Generation** | Generate functions, classes, and tests from natural language |
| 🔎 **Semantic Search** | Search your codebase using natural language queries |
| 📝 **AI File Editing** | Edit files with natural language instructions |
| 🔄 **Multi-File Refactor** | Refactor across multiple files at once |
| ��️ **Symbol Renaming** | Rename functions, classes, variables across your project |
| 💬 **Interactive Chat** | Chat with AI about your code |
| 📊 **Codebase Indexing** | Create searchable semantic index with RAG |
| 🌐 **Multi-Provider** | Support for 6 LLM providers (local & cloud) |

## 🤖 Supported Providers

| Provider | Free Tier | API Key | Best For |
|----------|-----------|---------|----------|
| **Ollama** | ✅ Unlimited | ❌ None | Privacy, offline use |
| **Google AI** | ✅ Generous | ✅ Required | 1M+ token context |
| **Groq** | ✅ 1000 req/day | ✅ Required | Fastest inference |
| **Cerebras** | ✅ Available | ✅ Required | Fast inference |
| **OpenRouter** | ✅ Free models | ✅ Required | Model variety |
| **OpenAI** | ❌ Paid only | ✅ Required | GPT-4 quality |

## 🚀 Quick Start

### Option 1: Local with Ollama (No API Key)

```bash
# Install Ollama from https://ollama.ai
ollama pull deepseek-coder:6.7b
ollama serve
```

### Option 2: Cloud with Free Tier

```bash
# Google AI Studio (1M token context, free)
export GOOGLE_API_KEY="your-key"  # Get from https://aistudio.google.com/apikey

# OR Groq (fastest inference, free tier)
export GROQ_API_KEY="your-key"    # Get from https://console.groq.com/keys

# OR OpenRouter (free models available)
export OPENROUTER_API_KEY="your-key"  # Get from https://openrouter.ai/keys
```

### Installation

```bash
# Clone the repository
git clone https://github.com/akkssy/cognify-ai.git
cd cognify-ai

# Create virtual environment
python -m venv .venv
source .venv/bin/activate  # On Windows: .venv\Scripts\activate

# Install the package
pip install -e .
```

### Verify Installation

```bash
# Check status and available providers
ai-assist status
ai-assist providers
```

## 🌐 Provider Management

### List Available Providers
```bash
ai-assist providers
```
Shows all providers with their models, free tier status, and API key requirements.

### Switch Providers
```bash
# Switch to Groq (fast cloud inference)
ai-assist use-provider groq --test

# Switch to Google with specific model
ai-assist use-provider google --model gemini-1.5-pro --test

# Use OpenRouter with free DeepSeek R1
ai-assist use-provider openrouter --model deepseek/deepseek-r1:free --test
```

### Test Provider Connection
```bash
ai-assist test-provider
ai-assist test-provider --provider groq --prompt "Hello world"
```

## 📖 Usage

### Code Review
```bash
ai-assist review path/to/file.py
ai-assist review src/ --format json
```

### Code Generation
```bash
ai-assist generate "binary search function" --language python
ai-assist generate "REST API client class" --mode class
ai-assist generate "unit tests for calculator" --mode test
```

### Semantic Search
```bash
# First, index your codebase
ai-assist index .

# Then search
ai-assist search "error handling"
ai-assist search "database connection" -k 10
```

### File Editing
```bash
ai-assist edit config.py "add logging to all functions" --preview
ai-assist edit utils.py "add type hints" --backup
```

### Multi-File Refactoring
```bash
ai-assist refactor "add docstrings to all functions" -p "src/**/*.py" --dry-run
ai-assist refactor "convert print to logging" --pattern "**/*.py" --confirm
```

### Symbol Renaming
```bash
ai-assist rename old_function new_function --type function --dry-run
ai-assist rename MyClass BetterClass --type class -p "src/**/*.py"
```

### Interactive Chat
```bash
ai-assist chat
```

### All Commands
```bash
ai-assist --help
```

## ⚙️ Configuration

Configuration is managed via `config.yaml`:

```yaml
llm:
  provider: "ollama"          # ollama, google, groq, cerebras, openrouter, openai
  model: "deepseek-coder:6.7b"
  base_url: "http://localhost:11434"  # For Ollama
  temperature: 0.1
  max_tokens: 4096
  timeout: 120

review:
  severity_levels: [critical, warning, suggestion]
  categories: [bugs, security, performance, style]

generation:
  include_type_hints: true
  include_docstrings: true

retrieval:
  embedding_model: "all-MiniLM-L6-v2"
  chunk_size: 50

editor:
  create_backup: true
  show_diff: true

refactor:
  max_files: 20
  require_confirmation: true
```

Or use environment variables:
```bash
export AI_ASSISTANT_LLM_PROVIDER="groq"
export AI_ASSISTANT_LLM_MODEL="llama-3.3-70b-versatile"
export GROQ_API_KEY="your-key"
```

## 📁 Project Structure

```
cognify-ai/
├── src/ai_code_assistant/
│   ├── cli.py              # Command-line interface
│   ├── config.py           # Configuration management
│   ├── llm.py              # LLM integration
│   ├── providers/          # Multi-provider support
│   │   ├── base.py         # Provider base class
│   │   ├── factory.py      # Provider factory
│   │   ├── ollama.py       # Ollama (local)
│   │   ├── google.py       # Google AI Studio
│   │   ├── groq.py         # Groq
│   │   ├── cerebras.py     # Cerebras
│   │   ├── openrouter.py   # OpenRouter
│   │   └── openai.py       # OpenAI
│   ├── reviewer/           # Code review module
│   ├── generator/          # Code generation module
│   ├── retrieval/          # Semantic search & indexing (RAG)
│   ├── editor/             # AI file editing
│   ├── refactor/           # Multi-file refactoring
│   ├── chat/               # Interactive chat
│   └── utils/              # Utilities & formatters
├── tests/                  # 144 unit tests
├── docs/                   # Documentation
├── config.yaml             # Configuration
└── pyproject.toml          # Dependencies
```

## 🧪 Testing

```bash
# Run all tests
PYTHONPATH=src pytest tests/ -v

# Run with coverage
PYTHONPATH=src pytest tests/ --cov=ai_code_assistant
```

## 🛠️ Tech Stack

| Component | Technology |
|-----------|------------|
| LLM Framework | LangChain |
| Local LLM | Ollama |
| Cloud LLMs | Google, Groq, OpenRouter, OpenAI |
| Vector Database | ChromaDB |
| Embeddings | Sentence Transformers |
| CLI | Click + Rich |
| Config | Pydantic |
| Testing | Pytest |

## 🐛 Troubleshooting

**"Connection refused" error (Ollama)**
```bash
ollama serve  # Make sure Ollama is running
```

**API Key errors**
```bash
ai-assist providers  # Check which API keys are set
export GROQ_API_KEY="your-key"  # Set the appropriate key
```

**Test provider connection**
```bash
ai-assist test-provider --provider groq
```

**Import errors**
```bash
pip install -e ".[dev]"
```

## 🤝 Contributing

Contributions are welcome! Please feel free to submit a Pull Request.

1. Fork the repository
2. Create your feature branch (`git checkout -b feature/amazing-feature`)
3. Commit your changes (`git commit -m 'Add amazing feature'`)
4. Push to the branch (`git push origin feature/amazing-feature`)
5. Open a Pull Request

## 📄 License

This project is licensed under the MIT License - see the [LICENSE](LICENSE) file for details.

## 🙏 Acknowledgments

- [Ollama](https://ollama.ai) - Local LLM runtime
- [LangChain](https://langchain.com) - LLM framework
- [Google AI Studio](https://aistudio.google.com) - Gemini models
- [Groq](https://groq.com) - Fast inference
- [OpenRouter](https://openrouter.ai) - Multi-provider access
- [ChromaDB](https://www.trychroma.com) - Vector database

---

<p align="center">
  Made with ❤️ for developers who want flexible AI-powered coding assistance
</p>
