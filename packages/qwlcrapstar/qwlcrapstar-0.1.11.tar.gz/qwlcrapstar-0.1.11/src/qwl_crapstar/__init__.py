"""
QwlCrapstar: The Autonomous AI Data Extraction Agent.

QwlCrapstar is a high-performance, agentic web scraping library designed for professional data extraction.
It leverages Large Language Models (LLMs) to transform unstructured web content into validated, 
structured data without the need for brittle CSS selectors or XPaths.

Primary Usage:
    from qwl_crapstar import QwlCrapstar
    
    scraper = QwlCrapstar()
    results = await scraper.scrape(url="...", prompt="Find 10 items")

Key Components:
    - QwlCrapstar: The main extraction engine.
    - Schema: Class-based and dictionary-based data structure definitions.
    - Field: Advanced field-level metadata for AI guidance.
    - Pipeline: Professional post-processing and data sanitization.

Documentation: https://github.com/Ranzim/QwlCrapStar
"""

from .core.scraper import QwlCrapstar
from .core.schema import Schema, PrebuiltSchemas, Field
from .core.config import config

__all__ = ["QwlCrapstar", "Schema", "PrebuiltSchemas", "Field", "config"]
