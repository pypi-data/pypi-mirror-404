import os
from typing import Optional
from dotenv import load_dotenv

class Config:
    def __init__(self):
        load_dotenv()
        
    @property
    def openai_api_key(self) -> Optional[str]:
        return os.getenv("OPENAI_API_KEY")

    @property
    def anthropic_api_key(self) -> Optional[str]:
        return os.getenv("ANTHROPIC_API_KEY")

    @property
    def groq_api_key(self) -> Optional[str]:
        return os.getenv("GROQ_API_KEY")

    @property
    def deepseek_api_key(self) -> Optional[str]:
        return os.getenv("DEEPSEEK_API_KEY")

    @property
    def use_local_llm(self) -> bool:
        return os.getenv("USE_LOCAL_LLM", "false").lower() == "true"

    def validate_provider(self, provider: str):
        if provider == "openai" and not self.openai_api_key:
            raise ValueError("OPENAI_API_KEY not found in environment")
        elif provider == "anthropic" and not self.anthropic_api_key:
            raise ValueError("ANTHROPIC_API_KEY not found in environment")
        elif provider == "groq" and not self.groq_api_key:
            raise ValueError("GROQ_API_KEY not found in environment")
        elif provider == "deepseek" and not self.deepseek_api_key:
            raise ValueError("DEEPSEEK_API_KEY not found in environment")

config = Config()
