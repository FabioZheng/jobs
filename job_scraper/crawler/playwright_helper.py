"""Optional Playwright helper for JavaScript-heavy pages."""

from __future__ import annotations

import asyncio
from typing import Optional

from playwright.async_api import TimeoutError as PlaywrightTimeoutError
from playwright.async_api import async_playwright


async def fetch_rendered_html(url: str, timeout_ms: int = 30000) -> Optional[str]:
    """Render a page in headless Chromium and return HTML.

    Returns None when page render fails.
    """
    try:
        async with async_playwright() as p:
            browser = await p.chromium.launch(headless=True)
            page = await browser.new_page()
            await page.goto(url, wait_until="domcontentloaded", timeout=timeout_ms)
            await page.wait_for_timeout(1200)
            content = await page.content()
            await browser.close()
            return content
    except PlaywrightTimeoutError:
        return None
    except Exception:
        return None


def fetch_rendered_html_sync(url: str, timeout_ms: int = 30000) -> Optional[str]:
    """Synchronous adapter for asynchronous renderer."""
    return asyncio.run(fetch_rendered_html(url, timeout_ms=timeout_ms))
