"""Main MCP server implementation using FastMCP."""

import asyncio
import os
from pathlib import Path
from typing import List, Tuple
from contextlib import asynccontextmanager
from pydantic import BaseModel
from mcp.server.fastmcp import FastMCP, Context
from .models import ProductListing
from .sites import Taobao
from playwright.async_api import async_playwright


class DoneSchema(BaseModel):
    """Schema for Done confirmation."""
    done: bool = True


# Shared scraper instances for lifespan management
scrapers = {}
_playwright = None  # Store reference for cleanup
_context = None


@asynccontextmanager
async def lifespan(app):
    """Async context manager for MCP lifespan (startup/shutdown)."""
    global _playwright, _context

    # Startup: Initialize scrapers
    data_dir = Path.home() / ".local" / "share" / "ecommerce_mcp"
    data_dir.mkdir(parents=True, exist_ok=True)

    _playwright = await async_playwright().start()
    _context = await _playwright.chromium.launch_persistent_context(
        user_data_dir=str(data_dir),
        headless=False,
        args=["--no-sandbox", "--disable-blink-features=AutomationControlled"],
    )
    scrapers["taobao"] = Taobao(_context)
    # scrapers["jingdong"] = Jingdong(_context)

    yield

    # Shutdown: Cleanup
    if _context:
        await _context.close()
    if _playwright:
        await _playwright.stop()


# Create MCP with lifespan
mcp = FastMCP("ecommerce_mcp", lifespan=lifespan)


# Tools at module level - can be imported and called directly


@mcp.tool()
async def search_taobao(query: str, ctx: Context = None) -> List[Tuple[str, str, str, str]]:
    """
    Search for products on Taobao.

    Args:
        query: The search query (product name, keyword, etc.)

    Returns:
        List of tuples: (product_link, seller_name, unit_price, listing_name)
    """
    return await _search_site("taobao", query, ctx)


@mcp.tool()
async def search_jingdong(query: str, ctx: Context = None) -> List[Tuple[str, str, str, str]]:
    """
    Search for products on Jingdong (JD.com).

    Args:
        query: The search query (product name, keyword, etc.)

    Returns:
        List of tuples: (product_link, seller_name, unit_price, listing_name)
    """
    return await _search_site("jingdong", query, ctx)


@mcp.tool()
async def check_login_status(site: str, ctx: Context = None) -> dict:
    """
    Check login status for an e-commerce site.

    Args:
        site: Site name ("taobao" or "jingdong")

    Returns:
        Boolean
    """
    site = site.lower()
    if site not in ("taobao",):
        return {"success": False, "message": f"Unknown site: {site}"}
    site_impl = scrapers[site]
    return await site_impl.is_logged_in()


async def _search_site(
    site: str,
    query: str,
    ctx: Context = None
) -> List[Tuple[str, str, str, str]]:
    """Internal helper to search a site."""

    scraper = scrapers[site]
    if not await scraper.is_logged_in():
        # Open homepage so user can log in
        await scraper.open_homepage()

        if ctx:
            await ctx.elicit(
                f"Please log in to {site} in the browser. Click Done when finished.",
                DoneSchema
            )

        # Recheck after user confirmation
        if not await scraper.is_logged_in():
            raise Exception(f"Not logged in to {site}. Please try logging in again.")

    listings = await scraper.search(query)

    return [listing.to_tuple() for listing in listings]
