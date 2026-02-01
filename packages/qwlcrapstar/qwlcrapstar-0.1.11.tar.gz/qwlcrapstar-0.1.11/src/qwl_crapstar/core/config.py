import os
from typing import Optional, List, Dict
from dotenv import load_dotenv

class Config:
    def __init__(self):
        # Automatically look for .env files in current or parent directories
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
    def perplexity_api_key(self) -> Optional[str]:
        return os.getenv("PERPLEXITY_API_KEY")

    @property
    def use_local_llm(self) -> bool:
        return os.getenv("USE_LOCAL_LLM", "false").lower() == "true"

    def get_available_providers(self) -> List[str]:
        """Returns a list of providers that have API keys configured."""
        available = []
        if self.openai_api_key: available.append("openai")
        if self.anthropic_api_key: available.append("anthropic")
        if self.groq_api_key: available.append("groq")
        if self.deepseek_api_key: available.append("deepseek")
        if self.perplexity_api_key: available.append("perplexity")
        return available

    def validate_provider(self, provider: str):
        """Intelligently validates provider and suggests alternatives if key is missing."""
        key_map = {
            "openai": ("OPENAI_API_KEY", self.openai_api_key),
            "anthropic": ("ANTHROPIC_API_KEY", self.anthropic_api_key),
            "groq": ("GROQ_API_KEY", self.groq_api_key),
            "deepseek": ("DEEPSEEK_API_KEY", self.deepseek_api_key),
            "perplexity": ("PERPLEXITY_API_KEY", self.perplexity_api_key),
        }

        if provider not in key_map and provider != "ollama":
            raise ValueError(f"Unknown provider: '{provider}'. Supported: {list(key_map.keys())} or 'ollama'")

        if provider == "ollama":
            return # Local doesn't need a key

        env_var, key_val = key_map[provider]
        
        if not key_val:
            available = self.get_available_providers()
            error_msg = f"\nERROR: Missing API Key for '{provider}' ({env_var}).\n"
            error_msg += f"Suggestion: Please set it in your environment: export {env_var}=your_key\n"
            
            if available:
                error_msg += f"Note: I detected keys for these other providers instead: {available}. \n"
                error_msg += f"   You can use them by setting QwlCrapstar(llm_provider='{available[0]}')"
            else:
                error_msg += "Note: No LLM API keys detected. You can also run locally by setting use_local_llm=True (requires Ollama)."
            
            raise ValueError(error_msg)

config = Config()
