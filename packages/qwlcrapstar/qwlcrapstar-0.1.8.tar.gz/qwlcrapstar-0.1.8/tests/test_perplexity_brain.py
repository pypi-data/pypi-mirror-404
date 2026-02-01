import asyncio
from qwl_crapstar import QwlCrapstar
from langchain_core.messages import HumanMessage

async def main():
    # TEST: Only testing the LLM Brain connection with your key
    scraper = QwlCrapstar(llm_provider="perplexity")
    
    print("🧠 Testing Perplexity Brain Only...")
    
    # Manually simulate some web content so we don't get blocked by browser
    simulated_content = """
    Jobs at Acme Corp:
    1. AI Engineer - $200k - Remote
    2. Data Scientist - $180k - New York
    """
    
    # Directly ask the scraper's LLM to parse this
    # This proves the PERPLEXITY_API_KEY is working!
    schema_snippet = "Extract: title, salary, location"
    
    prompt = f"Extract data from this text: {simulated_content}"
    
    messages = [
        HumanMessage(content=f"System: Return JSON list. Schema: {schema_snippet}\n\nContent: {simulated_content}")
    ]
    
    response = await scraper.llm.ainvoke(messages)
    
    print("\n✅ Perplexity Response:")
    print(response.content)

if __name__ == "__main__":
    asyncio.run(main())
