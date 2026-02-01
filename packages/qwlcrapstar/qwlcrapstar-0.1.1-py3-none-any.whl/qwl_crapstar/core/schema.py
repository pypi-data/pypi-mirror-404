from typing import Dict, Any, Optional, List
from pydantic import BaseModel, create_model

class Schema:
    """
    Universal Schema definition system.
    Users can pass a dictionary of field names and descriptions.
    """
    def __init__(self, fields: Dict[str, str], name: str = "ExtractedData"):
        self.fields = fields
        self.name = name
        self.pydantic_model = self._create_pydantic_model()

    def _create_pydantic_model(self):
        # Create a dynamic Pydantic model where each field is a string with a description
        field_definitions = {
            name: (Optional[str], ...) for name in self.fields.keys()
        }
        return create_model(self.name, **field_definitions)

    def get_prompt_snippet(self) -> str:
        snippet = "Extract the following fields:\n"
        for name, desc in self.fields.items():
            snippet += f"- {name}: {desc}\n"
        return snippet

class PrebuiltSchemas:
    @staticmethod
    def job_posting():
        return Schema({
            "title": "Job title/position",
            "company": "Company name",
            "location": "Location (city, state, or remote)",
            "salary": "Salary range or specific amount",
            "description": "Short summary of the job description",
            "skills": "Key skills or technologies required",
            "posted_date": "Date when the job was posted"
        }, name="JobPosting")

    @staticmethod
    def ecommerce_product():
        return Schema({
            "name": "Product name",
            "price": "Current price",
            "original_price": "Original price before discount",
            "rating": "Product rating (e.g. 4.5/5)",
            "reviews_count": "Number of reviews",
            "availability": "Is the product in stock?",
            "description": "Product description",
            "image_url": "URL of the main product image"
        }, name="Product")

    @staticmethod
    def real_estate_listing():
        return Schema({
            "address": "Full property address",
            "price": "Property price",
            "bedrooms": "Number of bedrooms",
            "bathrooms": "Number of bathrooms",
            "sqft": "Size in square feet",
            "property_type": "Type of property (house, apt, etc)",
            "agent": "Listing agent name"
        }, name="RealEstateListing")
