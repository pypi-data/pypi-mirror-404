from typing import Any, Optional
from langchain_openai import ChatOpenAI
from langchain_anthropic import ChatAnthropic
from langchain_groq import ChatGroq
from .config import config

class LLMProvider:
    """
    Factory for LLM providers.
    Supports auto-detection of available keys to feel more 'intelligent'.
    """
    def __init__(
        self, 
        provider: Optional[str] = None, 
        model: Optional[str] = None,
        temperature: float = 0,
        api_key: Optional[str] = None
    ):
        self.api_key = api_key
        self.temperature = temperature
        self.model = model
        
        # Intelligent Auto-Detection
        if not provider:
            available = config.get_available_providers()
            if available:
                # Priority: OpenAI > Anthropic > Groq > Others
                priority = ["openai", "anthropic", "groq", "deepseek", "perplexity"]
                for p in priority:
                    if p in available:
                        self.provider = p
                        break
                else:
                    self.provider = available[0]
                print(f"Auto-detected available LLM provider: {self.provider}")
            else:
                self.provider = "groq" # Default assumption
        else:
            self.provider = provider.lower()
        
        # Only validate if no explicit key is provided and not using local Ollama
        if not self.api_key and self.provider != "ollama":
            config.validate_provider(self.provider)

    def get_llm(self) -> Any:
        """Returns the initialized LangChain chat model."""
        if self.provider == "openai":
            return ChatOpenAI(
                model=self.model or "gpt-4o",
                temperature=self.temperature,
                openai_api_key=self.api_key or config.openai_api_key
            )
        elif self.provider == "anthropic":
            return ChatAnthropic(
                model=self.model or "claude-3-5-sonnet-20240620",
                temperature=self.temperature,
                anthropic_api_key=self.api_key or config.anthropic_api_key
            )
        elif self.provider == "groq":
            return ChatGroq(
                model=self.model or "llama3-70b-8192",
                temperature=self.temperature,
                groq_api_key=self.api_key or config.groq_api_key
            )
        elif self.provider == "ollama":
            from langchain_community.chat_models import ChatOllama
            return ChatOllama(
                model=self.model or "llama3",
                temperature=self.temperature
            )
        elif self.provider == "deepseek":
            return ChatOpenAI(
                model=self.model or "deepseek-chat",
                temperature=self.temperature,
                openai_api_key=self.api_key or config.deepseek_api_key,
                base_url="https://api.deepseek.com/v1"
            )
        elif self.provider == "perplexity":
            return ChatOpenAI(
                model=self.model or "llama-3-sonar-large-32k-online",
                temperature=self.temperature,
                openai_api_key=self.api_key or config.perplexity_api_key,
                base_url="https://api.perplexity.ai"
            )
        else:
            raise ValueError(f"Unsupported LLM provider: {self.provider}")
