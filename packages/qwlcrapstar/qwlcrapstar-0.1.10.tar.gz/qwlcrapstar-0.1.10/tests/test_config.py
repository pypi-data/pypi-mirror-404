import os
import pytest
from qwl_crapstar.core.config import Config

def test_config_loading():
    os.environ["OPENAI_API_KEY"] = "test_key"
    cfg = Config()
    assert cfg.openai_api_key == "test_key"

def test_validation():
    cfg = Config()
    os.environ["GROQ_API_KEY"] = "test_groq"
    # Should not raise error
    cfg.validate_provider("groq")
    
    # Should raise error if not set
    if "ANTHROPIC_API_KEY" in os.environ:
        del os.environ["ANTHROPIC_API_KEY"]
    with pytest.raises(ValueError):
        cfg.validate_provider("anthropic")
