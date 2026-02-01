"""Entry point for the e-commerce MCP server."""

import asyncio
import sys
from pathlib import Path

from playwright.async_api import async_playwright
from .sites import Taobao

# Shared state (mirrors server.py for debug mode)
scrapers = {}
_playwright = None
_context = None


async def setup():
    """Setup Playwright and scrapers for debug mode."""
    global _playwright, _context

    data_dir = Path.home() / ".local" / "share" / "ecommerce_mcp"
    data_dir.mkdir(parents=True, exist_ok=True)

    _playwright = await async_playwright().start()
    _context = await _playwright.chromium.launch_persistent_context(
        user_data_dir=str(data_dir),
        headless=False,
        args=["--no-sandbox", "--disable-blink-features=AutomationControlled"],
    )
    scrapers["taobao"] = Taobao(_context)


async def cleanup():
    """Cleanup Playwright resources."""
    global _playwright, _context
    if _context:
        await _context.close()
        _context = None
    if _playwright:
        await _playwright.stop()
        _playwright = None


async def debug():
    """Debug mode - call tools directly."""
    from .server import search_taobao

    await setup()
    try:
        result = await search_taobao("机顶盒")
        print(result)
    finally:
        await cleanup()


def main():
    """Run the MCP server."""
    from .server import mcp
    mcp.run()


if __name__ == "__main__":
    if len(sys.argv) > 1 and sys.argv[1] == "--debug":
        asyncio.run(debug())
    else:
        main()
