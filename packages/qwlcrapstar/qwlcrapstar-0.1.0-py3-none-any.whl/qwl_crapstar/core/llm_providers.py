from typing import Any, Optional
from langchain_openai import ChatOpenAI
from langchain_anthropic import ChatAnthropic
from langchain_groq import ChatGroq
from .config import config

class LLMProvider:
    def __init__(
        self, 
        provider: str = "groq", 
        model: Optional[str] = None,
        temperature: float = 0
    ):
        self.provider = provider.lower()
        self.model = model
        self.temperature = temperature
        
        # Only validate if not using a custom object later
        # (Though this class is mostly used when strings are passed)
        config.validate_provider(self.provider)

    def get_llm(self) -> Any:
        if self.provider == "openai":
            return ChatOpenAI(
                model=self.model or "gpt-4o",
                temperature=self.temperature,
                openai_api_key=config.openai_api_key
            )
        elif self.provider == "anthropic":
            return ChatAnthropic(
                model=self.model or "claude-3-5-sonnet-20240620",
                temperature=self.temperature,
                anthropic_api_key=config.anthropic_api_key
            )
        elif self.provider == "groq":
            return ChatGroq(
                model=self.model or "llama3-70b-8192",
                temperature=self.temperature,
                groq_api_key=config.groq_api_key
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
                openai_api_key=config.deepseek_api_key,
                base_url="https://api.deepseek.com/v1"
            )
        else:
            raise ValueError(f"Unsupported LLM provider: {self.provider}")
