import asyncio
from typing import Optional, Dict
from playwright.async_api import async_playwright

class BrowserEngine:
    def __init__(self, headless: bool = True):
        self.headless = headless
        self.browser = None
        self.context = None
        self.page = None

    async def start(self):
        self.playwright = await async_playwright().start()
        self.browser = await self.playwright.chromium.launch(headless=self.headless)
        self.context = await self.browser.new_context(
            user_agent="Mozilla/5.0 (Macintosh; Intel Mac OS X 10_15_7) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/120.0.0.0 Safari/537.36"
        )
        self.page = await self.context.new_page()

    async def navigate(self, url: str):
        if not self.page:
            await self.start()
        await self.page.goto(url, wait_until="networkidle")

    async def get_content(self) -> str:
        if not self.page:
            return ""
        # Get simplified HTML or text content
        # For now, let's just get the visible text to avoid overwhelming the LLM
        # But for more complex scraping, we might need the full DOM or structure
        content = await self.page.evaluate("() => document.body.innerText")
        return content

    async def get_html(self) -> str:
        if not self.page:
            return ""
        return await self.page.content()

    async def close(self):
        if self.browser:
            await self.browser.close()
        if hasattr(self, 'playwright'):
            await self.playwright.stop()

    async def scroll_down(self):
        if self.page:
            await self.page.evaluate("window.scrollTo(0, document.body.scrollHeight)")
            await asyncio.sleep(1)
