import asyncio
import os
from qwl_crapstar import QwlCrapstar

async def main():
    # TEST 1: Intelligent Auto-Detection & Helpful Errors
    # We will temporarily hide the keys to see the proactive error message
    original_groq = os.environ.get("GROQ_API_KEY")
    original_perplex = os.environ.get("PERPLEXITY_API_KEY")
    
    if "GROQ_API_KEY" in os.environ: del os.environ["GROQ_API_KEY"]
    if "PERPLEXITY_API_KEY" in os.environ: del os.environ["PERPLEXITY_API_KEY"]
    
    print("🧪 Test 1: Testing Proactive Error Messaging...")
    try:
        # This should fail and show a helpful suggestion
        scraper = QwlCrapstar()
    except ValueError as e:
        print(f"PASS: Caught expected error:\n{str(e)}")

    # Restore keys for Test 2
    if original_groq: os.environ["GROQ_API_KEY"] = original_groq
    if original_perplex: os.environ["PERPLEXITY_API_KEY"] = original_perplex

    # TEST 2: Complex Nested Schema
    print("\n🧪 Test 2: Testing Complex Nested Schema...")
    scraper = QwlCrapstar(llm_provider="perplexity")
    
    # Defining a very complex nested schema
    complex_schema = {
        "article_title": "Main title",
        "metadata": {
            "author_name": "Name of author",
            "publish_date": (str, "ISO date"),
            "word_count": (int, "Estimated word count")
        },
        "statistics": {
            "score": (float, "Numerical score"),
            "is_top_voted": (bool, "True if heavily upvoted")
        }
    }

    results = await scraper.scrape(
        url="https://news.ycombinator.com",
        prompt="Extract the top 1 story with deep metadata and stats",
        schema=complex_schema,
        max_results=1
    )

    print("\n✅ Complex Data Extracted:")
    import json
    print(json.dumps(results, indent=2))

if __name__ == "__main__":
    asyncio.run(main())
