from typing import List, Dict, Any, Optional, Callable
import asyncio

class Processor:
    """Base class for data processors."""
    async def process(self, data: List[Dict[str, Any]]) -> List[Dict[str, Any]]:
        return data

class DataValidator(Processor):
    def __init__(self, schema: Any):
        self.schema = schema

    async def process(self, data: List[Dict[str, Any]]) -> List[Dict[str, Any]]:
        valid_data = []
        for item in data:
            try:
                # If schema has a pydantic model, use it to validate
                model = getattr(self.schema, 'pydantic_model', None)
                if model:
                    model(**item)
                valid_data.append(item)
            except Exception:
                continue
        return valid_data

class Normalizer(Processor):
    def __init__(self, mapping: Dict[str, str]):
        self.mapping = mapping

    async def process(self, data: List[Dict[str, Any]]) -> List[Dict[str, Any]]:
        # This is a placeholder for advanced normalization logic
        # In a real app, this would use the mapping to call specific normalizers
        return data

class Deduplicator(Processor):
    def __init__(self, fields: List[str]):
        self.fields = fields

    async def process(self, data: List[Dict[str, Any]]) -> List[Dict[str, Any]]:
        seen = set()
        unique_data = []
        for item in data:
            # Create a unique key based on the fields
            key = tuple(str(item.get(f, "")) for f in self.fields)
            if key not in seen:
                seen.add(key)
                unique_data.append(item)
        return unique_data

class Pipeline:
    """
    Executes a series of processors on scraped data.
    """
    def __init__(self, processors: List[Processor]):
        self.processors = processors

    async def run(self, data: List[Dict[str, Any]]) -> List[Dict[str, Any]]:
        current_data = data
        for processor in self.processors:
            current_data = await processor.process(current_data)
        return current_data
