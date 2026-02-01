"""Base class for e-commerce site implementations."""

from abc import ABC, abstractmethod
from pathlib import Path
from typing import Optional
from playwright.async_api import async_playwright, BrowserContext, Page


class Scraper(ABC):
    """Abstract base class for e-commerce site implementations."""

    def __init__(self, context: BrowserContext):
        """Initialize the site implementation."""
        self.context = context
        
    @abstractmethod
    async def search(self, query: str):
        """Perform a search and return results."""
        ...

    @abstractmethod
    async def is_logged_in(self) -> bool:
        """Check if the user is logged in."""
        ...

    @abstractmethod
    async def open_homepage(self) -> None:
        """Open the site homepage so user can log in."""
        ...
