import asyncio
from playwright.async_api import async_playwright
import time

async def run(playwright):
    ws_endpoint = "ws://127.0.0.1:9222/devtools/browser/9ec11a33-2374-47cd-ab34-9d1f0334f712"

    chromium = playwright.chromium
    browser = await chromium.connect_over_cdp(ws_endpoint)
    context = await browser.new_context()
    page = await context.new_page()
    page2 = await context.new_page()
    await page.goto("https://example.com")
    await page2.goto("https://heise.com")
    await browser.close()

async def main():
    async with async_playwright() as playwright:
        await run(playwright)
asyncio.run(main())