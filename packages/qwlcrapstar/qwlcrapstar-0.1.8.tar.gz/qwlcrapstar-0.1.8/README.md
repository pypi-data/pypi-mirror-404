# QwlCrapstar: Universal AI-Powered Web Scraper

QwlCrapstar is a robust, AI-driven web scraping library designed for structured data extraction from any website. By leveraging Large Language Models (LLMs), it understands the semantic context of web pages, making it resilient to layout changes and capable of extracting complex data with natural language instructions.

## Key Features

- **Semantic Extraction**: Targeted data extraction based on meaning rather than brittle CSS selectors or XPaths.
- **Self-Healing Architecture**: Automatically adapts to changes in website structure without requiring code updates.
- **Universal LLM Support**: Native integration with OpenAI, Anthropic, Groq, DeepSeek, and local models via Ollama.
- **Advanced Browser Automation**: Built-in Playwright engine with human-like interaction patterns and anti-bot mitigation.
- **Schema-Driven**: Define extraction targets using simple dictionaries or pre-built industry schemas (e.g., E-commerce, Jobs, Real Estate).
- **Privacy & Control**: All credentials remain local; users provide their own API keys or use local models for full data sovereignty.

## Installation

```bash
pip install qwlcrapstar
playwright install chromium
```

## Configuration

QwlCrapstar supports multiple LLM providers. To use a specific provider, ensure the corresponding environment variable is set.

| Provider | Environment Variable | Model (Default) |
|----------|----------------------|-----------------|
| **Groq** | `GROQ_API_KEY` | `llama3-70b-8192` |
| **OpenAI** | `OPENAI_API_KEY` | `gpt-4o` |
| **Anthropic** | `ANTHROPIC_API_KEY` | `claude-3-5-sonnet` |
| **DeepSeek** | `DEEPSEEK_API_KEY` | `deepseek-chat` |
| **Perplexity** | `PERPLEXITY_API_KEY` | `llama-3-sonar-large-32k-online` |
| **Ollama** | N/A (Local) | `llama3` |

### Initialization Example

```python
from qwl_crapstar import QwlCrapstar

# Using Groq (Default)
scraper = QwlCrapstar(llm_provider="groq")

# Using local Ollama
scraper = QwlCrapstar(use_local_llm=True)

# Professional Extraction with Complexity Controls
results = scraper.scrape(
    prompt="Extract high-frequency trading data across Berlin tech sectors",
    complexity_level="elite",  # basic, standard, advanced, elite
    rules=["Must resolve all relative dates to ISO", "Strict deduplication"]
)
```

## Handling Content "Hardness"
QwlCrapstar is built to handle the "hardness" of any internet content based on the developer's purpose:

- **BASIC**: Best for simple landing pages and fast text extraction.
- **STANDARD**: The default mode. Good for job boards, products, and news.
- **ADVANCED**: Deeper DOM analysis. Resolves inferred data and hidden context.
- **ELITE**: Maximum power. Complete structural reconstruction for complex, dynamic, or protected web applications.

## Usage Guide

### 1. Defining Schemas
You can define what you want to extract using a simple dictionary where the key is the field name and the value is a description for the LLM.

```python
# Custom Schema
schema = {
    "product_name": "The full name of the product",
    "price_usd": "Price of the product in USD",
    "availability": "Boolean indicating if the item is in stock"
}
```

### 2. Using Pre-built Schemas
QwlCrapstar provides standard schemas for common use cases:

```python
from qwl_crapstar import PrebuiltSchemas

job_schema = PrebuiltSchemas.job_posting()
product_schema = PrebuiltSchemas.ecommerce_product()
real_estate_schema = PrebuiltSchemas.real_estate_listing()
```

### 3. Extracting Data
Execute a scrape by providing a URL, a prompt, and a schema.

```python
import asyncio
from qwl_crapstar import QwlCrapstar

async def main():
    scraper = QwlCrapstar(llm_provider="groq")
    
    results = await scraper.scrape(
        url="https://news.ycombinator.com",
        prompt="Extract the top 5 stories ranking by points",
        schema={
            "title": "Story headline",
            "points": "Number of points",
            "link": "URL of the story"
        }
    )
    
    for item in results:
        print(item)

if __name__ == "__main__":
    asyncio.run(main())
```

## Data Export

Easily save your results in standard formats:

```python
scraper.export_json(results, "data.json")
scraper.export_csv(results, "data.csv")
scraper.send_webhook("https://api.example.com/webhook", results)
```

## License

This project is licensed under the MIT License.
