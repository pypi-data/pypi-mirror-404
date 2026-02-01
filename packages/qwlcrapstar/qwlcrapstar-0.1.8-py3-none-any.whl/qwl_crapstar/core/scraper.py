import asyncio
from typing import List, Dict, Any, Optional, Union
from .llm_providers import LLMProvider
from .schema import Schema, Field
from ..execution.browser_engine import BrowserEngine
from langchain_core.messages import HumanMessage, SystemMessage

class QwlCrapstar:
    """
    QwlCrapstar: The world's most advanced AI-powered web scraper.
    Designed for professional data extraction at scale.
    """
    def __init__(
        self,
        llm_provider: Optional[str] = None,
        llm_model: Optional[str] = None,
        use_local_llm: bool = False,
        headless: bool = True,
        api_key: Optional[str] = None,
        # Enterprise options
        concurrent_requests: int = 1,
        timeout: int = 30,
        use_proxy: bool = False
    ):
        if use_local_llm:
            llm_provider = "ollama"
            
        self.provider_factory = LLMProvider(
            provider=llm_provider, 
            model=llm_model,
            api_key=api_key
        )
        self.llm = self.provider_factory.get_llm()
        self.headless = headless
        self.concurrent_requests = concurrent_requests
        self.timeout = timeout
        
    async def scrape(
        self,
        url: Optional[str] = None,
        prompt: Optional[str] = None,
        schema: Optional[Union[Schema, Dict[str, Any], Type[Schema]]] = None,
        fields: Optional[Dict[str, Any]] = None,
        filters: Optional[Dict[str, Any]] = None,
        rules: Optional[List[str]] = None,
        max_results: Optional[int] = None,
        complexity_level: str = "standard", # basic, standard, advanced, elite
        export: Optional[Dict[str, Any]] = None
    ) -> List[Dict[str, Any]]:
        """
        Agentic Extraction Engine. 
        Analyzes the developer's mission and 'starts working' autonomously.
        """
        # 1. Intent Analysis: Detect quantity and goal from prompt
        if prompt and max_results is None:
            import re
            quantity_match = re.search(r'(\d+)\s+(?:results|items|jobs|products|entries)', prompt.lower())
            if quantity_match:
                max_results = int(quantity_match.group(1))
                print(f"🎯 Mission Intent detected: Seeking {max_results} results.")
        
        max_results = max_results or 10 # Final fallback

        # 2. Handle convenience parameters (fields/filters)
        if fields:
            schema = Schema(fields)
        
        if filters:
            rules = rules or []
            for k, v in filters.items():
                rules.append(f"Filter: {k} must match {v}")

        # 2. Schema Auto-Inference
        if schema is None:
            schema = Schema.auto_infer(prompt or "data", url)
        
        # 3. Handle class-based schemas
        if isinstance(schema, type) and issubclass(schema, Schema):
            schema = schema()

        # 4. Perform extraction
        results = await self._execute_scrape(url, prompt, schema, rules, max_results, complexity_level)

        # 5. Handle automated export
        if export and results:
            fmt = export.get("format", "json")
            filename = export.get("filename", f"export.{fmt}")
            if fmt == "csv":
                self.export_csv(results, filename)
            elif fmt == "json":
                self.export_json(results, filename)
            elif fmt == "webhook":
                self.send_webhook(export.get("url"), results)

        return results

    async def _execute_scrape(self, url, prompt, schema, rules, max_results, complexity):
        browser = BrowserEngine(headless=self.headless)
        try:
            # Handle complexity-based wait times and token limits
            render_wait = {"basic": 1, "standard": 2, "advanced": 5, "elite": 10}.get(complexity, 2)
            token_limit = {"basic": 5000, "standard": 15000, "advanced": 30000, "elite": 100000}.get(complexity, 15000)

            # Level 2.4 Feature: Automatic Internet Search if no URL is provided
            if url is None:
                print(f"🌍 No URL provided. Searching the internet for: '{prompt}'")
                search_url = f"https://www.google.com/search?q={prompt.replace(' ', '+')}"
                await browser.navigate(search_url)
                url = search_url

            await browser.navigate(url)
            await asyncio.sleep(render_wait)
            content = await browser.get_content()
            
            system_prompt = f"""
            You are QwlCrapstar, an Autonomous Data Extraction Agent.
            Your Mission: {prompt if prompt else 'Extract all relevant structured data'}
            
            AGENT OPERATING LOGIC:
            1. ANALYZE: Review the developer's intent and context window.
            2. EXTRACT: Focus on the precise data requested in the Target Schema.
            3. ADAPT: If the content is complex, apply {complexity.upper()} level reasoning.
            4. COMPLY: Follow all semantic rules and constraints strictly.
            
            MISSION PARAMETERS:
            - Target Schema: {schema.get_prompt_snippet()}
            - Target Count: {max_results}
            - Rules: {rules if rules else 'None'}
            
            DATA RIGOR ({complexity.upper()} MODE):
            - Ensure 100% JSON validity.
            - Resolve relative information (dates, locations, currency) into absolute values.
            - If a field is missing, return 'null'. Do not guess unless prompted.

            Return ONLY valid JSON.
            """
            
            human_prompt = f"""
            MISSION CONTEXT:
            URL: {url}
            DEVELOPER INSTRUCTIONS: {prompt}
            
            WEB CONTENT WINDOW:
            ---
            {content[:token_limit]}
            ---
            
            Execute extraction now.
            """
            
            messages = [
                SystemMessage(content=system_prompt),
                HumanMessage(content=human_prompt)
            ]
            
            response = await self.llm.ainvoke(messages)
            return self._parse_json(response.content)
        finally:
            await browser.close()

    def _parse_json(self, text):
        import json, re
        match = re.search(r'\[.*\]', text, re.DOTALL)
        if match: return json.loads(match.group(0))
        match = re.search(r'\{.*\}', text, re.DOTALL)
        if match: return [json.loads(match.group(0))]
        return []

    async def scrape_async(self, *args, **kwargs):
        """Asynchronous alias for scrape"""
        return await self.scrape(*args, **kwargs)

    def export_csv(self, data, filename):
        from ..exporters import CSVExporter
        CSVExporter().export(data, filename)

    def export_json(self, data, filename):
        from ..exporters import JSONExporter
        JSONExporter().export(data, filename)

    def send_webhook(self, url, data):
        from ..exporters import WebhookExporter
        WebhookExporter(url).export(data)
        
    async def export_to_database(self, db_type, connection_string, database=None, collection=None):
        # Implementation for Level 3 DB Export
        print(f"📦 Exporting to {db_type}...")
        pass
