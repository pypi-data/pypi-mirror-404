from qwl_crapstar.core.schema import Schema, PrebuiltSchemas

def test_custom_schema():
    fields = {"test_field": "test description"}
    s = Schema(fields)
    assert "test_field" in s.fields
    assert s.pydantic_model.__name__ == "ExtractedData"
    assert "test_field" in s.pydantic_model.model_fields

def test_prebuilt_schemas():
    job_s = PrebuiltSchemas.job_posting()
    assert "title" in job_s.fields
    assert "company" in job_s.fields
    
    prod_s = PrebuiltSchemas.ecommerce_product()
    assert "price" in prod_s.fields
