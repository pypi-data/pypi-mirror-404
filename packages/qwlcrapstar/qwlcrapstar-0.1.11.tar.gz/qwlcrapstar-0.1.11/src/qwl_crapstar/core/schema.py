from typing import Dict, Any, Optional, List, Union, Type, Callable
from pydantic import BaseModel, create_model, Field as PydanticField

class Field:
    """
    Defines a field for extraction with validation and processing rules.
    Used in building powerful enterprise-grade schemas.
    """
    def __init__(
        self, 
        description: str, 
        type: Any = str, 
        required: bool = False,
        validation: Optional[str] = None,
        processing: Optional[Dict[str, Any]] = None,
        hint: Optional[str] = None
    ):
        self.description = description
        self.type = type
        self.required = required
        self.validation = validation
        self.processing = processing or {}
        self.hint = hint

class Schema:
    """
    Universal Schema definition system.
    Supports simple dicts, nested objects, and class-based definitions.
    """
    def __init__(
        self, 
        fields: Optional[Dict[str, Any]] = None, 
        name: str = "ExtractedData",
        rules: Optional[List[str]] = None
    ):
        # Support for class-based definitions
        if fields is None:
            fields = self._collect_class_fields()
        
        self.fields = fields
        self.name = name
        self.rules = rules or []
        self.pydantic_model = self._create_pydantic_model(fields, name)

    def _collect_class_fields(self) -> Dict[str, Any]:
        """Collects Field attributes from subclasses."""
        fields = {}
        for attr_name, attr_value in self.__class__.__dict__.items():
            if isinstance(attr_value, Field):
                fields[attr_name] = attr_value
        return fields

    def _create_pydantic_model(self, fields: Dict[str, Any], model_name: str):
        field_definitions = {}
        
        for name, definition in fields.items():
            if isinstance(definition, str):
                field_definitions[name] = (Optional[str], PydanticField(default=None, description=definition))
            
            elif isinstance(definition, Field):
                # Advanced Field object
                field_definitions[name] = (
                    definition.type if definition.required else Optional[definition.type], 
                    PydanticField(default=None, description=definition.description)
                )

            elif isinstance(definition, tuple) and len(definition) == 2:
                data_type, description = definition
                field_definitions[name] = (Optional[data_type], PydanticField(default=None, description=description))
            
            elif isinstance(definition, dict):
                nested_model = self._create_pydantic_model(definition, f"{model_name}_{name}")
                field_definitions[name] = (Optional[nested_model], PydanticField(default=None))
            
            elif isinstance(definition, list) and len(definition) > 0:
                item = definition[0]
                if isinstance(item, dict):
                    nested_model = self._create_pydantic_model(item, f"{model_name}_{name}_Item")
                    field_definitions[name] = (Optional[List[nested_model]], PydanticField(default_factory=list))
                elif isinstance(item, tuple): # [(int, "desc")]
                    field_definitions[name] = (Optional[List[item[0]]], PydanticField(default_factory=list, description=item[1]))
                else:
                    field_definitions[name] = (Optional[List[item]], PydanticField(default_factory=list))
            
            elif isinstance(definition, Schema):
                field_definitions[name] = (Optional[definition.pydantic_model], PydanticField(default=None))

        return create_model(model_name, **field_definitions)

    def get_prompt_snippet(self) -> str:
        snippet = self._generate_snippet(self.fields)
        if self.rules:
            snippet += "\nCRITICAL SEMANTIC RULES:\n"
            for rule in self.rules:
                snippet += f"[RULE] {rule}\n"
        return snippet

    def _generate_snippet(self, fields: Dict[str, Any], indent: int = 0) -> str:
        snippet = ""
        prefix = "  " * indent
        for name, definition in fields.items():
            if isinstance(definition, str):
                snippet += f"{prefix}- {name}: {definition}\n"
            elif isinstance(definition, Field):
                snippet += f"{prefix}- {name} ({definition.type}): {definition.description}\n"
                if definition.hint:
                    snippet += f"{prefix}  Hint: {definition.hint}\n"
            elif isinstance(definition, tuple):
                snippet += f"{prefix}- {name} ({definition[0].__name__}): {definition[1]}\n"
            elif isinstance(definition, dict):
                snippet += f"{prefix}- {name} (Object):\n"
                snippet += self._generate_snippet(definition, indent + 1)
            elif isinstance(definition, list):
                snippet += f"{prefix}- {name} (List):\n"
                if isinstance(definition[0], dict):
                    snippet += self._generate_snippet(definition[0], indent + 1)
        return snippet

    @classmethod
    def auto_infer(cls, prompt: str, url: str) -> 'Schema':
        prompt_lower = prompt.lower()
        if "job" in prompt_lower:
            return PrebuiltSchemas.job_posting()
        elif "product" in prompt_lower or "price" in prompt_lower or "shop" in prompt_lower:
            return PrebuiltSchemas.ecommerce_product()
        elif "real estate" in prompt_lower or "property" in prompt_lower or "rent" in prompt_lower:
            return PrebuiltSchemas.real_estate_listing()
        elif "news" in prompt_lower or "article" in prompt_lower or "post" in prompt_lower:
            return PrebuiltSchemas.article_listing()
        
        return Schema({
            "title": "Main identifier or title",
            "content": "Description or main text content",
            "date": "Associated date if applicable"
        }, name="GenericExtraction")

class PrebuiltSchemas:
    @staticmethod
    def job_posting():
        return Schema({
            "title": "Job title/position",
            "company": "Company name",
            "location": "Location (city, state, or remote)",
            "salary": {
                "amount": (float, "Numeric salary amount"),
                "currency": "Currency code (e.g. USD, EUR)",
                "period": "Pay period (yearly, monthly, hourly)"
            },
            "description": "Short summary of the job description",
            "requirements": [(str, "Individual requirement or skill")]
        }, name="JobPosting")

    @staticmethod
    def ecommerce_product():
        return Schema({
            "name": "Product name",
            "pricing": {
                "current_price": (float, "Active selling price"),
                "currency": "Currency (default USD)"
            },
            "rating": (float, "Star rating"),
            "image_url": "Main image link"
        }, name="Product")

    @staticmethod
    def real_estate_listing():
        return Schema({
            "address": "Full property address",
            "price": "Property price",
            "bedrooms": (int, "Number of bedrooms"),
            "sqft": (int, "Size in square feet")
        }, name="RealEstateListing")
    @staticmethod
    def article_listing():
        return Schema({
            "headline": "Main article headline",
            "author": "Author name",
            "date": "Publish date",
            "summary": "Short content summary",
            "tags": [(str, "Category tags")],
            "url": "Article link"
        }, name="Article")
