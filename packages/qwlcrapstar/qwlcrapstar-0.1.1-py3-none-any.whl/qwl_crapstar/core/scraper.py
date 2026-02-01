import asyncio
from typing import List, Dict, Any, Optional, Union
from .llm_providers import LLMProvider
from .schema import Schema
from ..execution.browser_engine import BrowserEngine
from langchain_core.messages import HumanMessage, SystemMessage
from pydantic import BaseModel

class QwlCrapstar:
    def __init__(
        self,
        llm_provider: str = "groq",
        llm_model: Optional[str] = None,
        use_local_llm: bool = False,
        headless: bool = True,
        custom_llm: Optional[Any] = None
    ):
        if custom_llm:
            self.llm = custom_llm
        else:
            if use_local_llm:
                llm_provider = "ollama"
                
            self.provider = LLMProvider(provider=llm_provider, model=llm_model)
            self.llm = self.provider.get_llm()
            
        self.browser = BrowserEngine(headless=headless)

    async def scrape(
        self,
        url: str,
        prompt: str,
        schema: Union[Schema, Dict[str, str]],
        max_results: int = 10
    ) -> List[Dict[str, Any]]:
        """
        Scrapes a URL based on a natural language prompt and a schema.
        """
        if isinstance(schema, dict):
            schema = Schema(schema)
            
        try:
            await self.browser.navigate(url)
            # Give it a moment to render
            await asyncio.sleep(2)
            
            content = await self.browser.get_content()
            
            system_prompt = f"""
            You are a professional web scraping assistant named QwlCrapstar.
            Your task is to extract structured data from the provided web content.
            Target Schema:
            {schema.get_prompt_snippet()}
            
            Return the data as a JSON list of objects matching the schema.
            If a field is not found, use null.
            Return ONLY valid JSON.
            """
            
            human_prompt = f"""
            URL: {url}
            User Request: {prompt}
            Max Results: {max_results}
            
            Web Content:
            {content[:15000]} # Truncate for token limits if necessary
            """
            
            messages = [
                SystemMessage(content=system_prompt),
                HumanMessage(content=human_prompt)
            ]
            
            # Using structured output if supported, otherwise manual parsing
            # For simplicity in this initial version, we use string parsing or let LangChain handle it
            response = await self.llm.ainvoke(messages)
            
            # Parse the response (basic version)
            # In a more robust version, we'd use LangChain's OutputParsers or function calling
            import json
            import re
            
            text = response.content
            # Extract JSON list using regex if there's preamble/postamble
            match = re.search(r'\[.*\]', text, re.DOTALL)
            if match:
                data = json.loads(match.group(0))
            else:
                # Try parsing as a single object if it's not a list
                match = re.search(r'\{.*\}', text, re.DOTALL)
                if match:
                    data = [json.loads(match.group(0))]
                else:
                    data = []
            
            return data
            
        finally:
            await self.browser.close()

    def run_scrape(self, *args, **kwargs):
        """Synchronous wrapper for scrape"""
        return asyncio.run(self.scrape(*args, **kwargs))

    async def scrape_multiple(
        self,
        urls: List[str],
        prompt: str,
        schema: Union[Schema, Dict[str, str]],
        concurrent: bool = True,
        max_results_per_url: int = 10
    ) -> List[Dict[str, Any]]:
        if concurrent:
            tasks = [
                self.scrape(url, prompt, schema, max_results_per_url)
                for url in urls
            ]
            results = await asyncio.gather(*tasks)
            # Flatten results
            return [item for sublist in results for item in sublist]
        else:
            all_results = []
            for url in urls:
                res = await self.scrape(url, prompt, schema, max_results_per_url)
                all_results.extend(res)
            return all_results

    def export_json(self, data: List[Dict[str, Any]], filename: str):
        from ..exporters import JSONExporter
        JSONExporter().export(data, filename)

    def export_csv(self, data: List[Dict[str, Any]], filename: str):
        from ..exporters import CSVExporter
        CSVExporter().export(data, filename)

    def send_webhook(self, url: str, data: List[Dict[str, Any]]):
        from ..exporters import WebhookExporter
        WebhookExporter(url).export(data)
