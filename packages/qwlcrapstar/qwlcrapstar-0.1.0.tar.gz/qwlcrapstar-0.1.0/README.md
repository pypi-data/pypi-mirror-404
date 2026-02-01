# QwlCrapstar: Universal AI-Powered Web Scraper 

**QwlCrapstar** is a universal, AI-driven web scraping library that empowers you to extract ANY data from ANY website using natural language and schema-driven configuration.

Unlike traditional scrapers that break when sites change, QwlCrapstar uses LLMs to understand semantic meaning, making it self-healing and universally applicable.

## ✨ Key Features

- 🧠 **Universal Scraper**: Extract data based on meaning, not just CSS selectors.
- 🛡️ **Self-Healing**: Adapts automatically when website structures change.
- 🔌 **Universal LLM Support**: Choose any provider that fits your budget or privacy needs:
  - **Local**: Ollama (Llama 3, Mistral, etc.)
  - **Free API**: Groq (Lightning-fast Llama 3)
  - **Premium**: OpenAI (GPT-4o), Anthropic (Claude 3.5), DeepSeek
  - **Custom**: Pass any LangChain-compatible model directly
- 🕵️ **Anti-Bot Defenses**: Built-in Playwright-based browser automation with human-like behavior.
- 📊 **Universal Schemas**: Pre-built schemas for Jobs, E-commerce, Real Estate, and more.
- 🔒 **Privacy First**: You provide your own API keys; your data and credentials stay with you.

## 🚀 Quick Start (Coming Soon)

```python
from qwl_crapstar import QwlCrapstar, PrebuiltSchemas

# Initialize with your preferred provider
scraper = QwlCrapstar(llm_provider="groq")

# Scrape any site with a natural language prompt
jobs = scraper.scrape(
    url="https://example.com/jobs",
    prompt="Extract all senior software engineer positions",
    schema=PrebuiltSchemas.job_posting()
)

print(jobs)
```

## 🛠️ Installation

```bash
pip install qwlcrapstar
# Install playwright browsers
playwright install chromium
```

## ⚖️ License

MIT License - feel free to use it for anything!
