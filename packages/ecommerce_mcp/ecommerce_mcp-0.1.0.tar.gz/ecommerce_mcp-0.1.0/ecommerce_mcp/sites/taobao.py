"""Taobao e-commerce site implementation."""

from pathlib import Path
from typing import Optional
from ..models import ProductListing
from .base import Scraper


class Taobao(Scraper):
    """Taobao e-commerce site implementation."""

    async def get_product_price_value(self, card):
        """Get product price as a float by parsing split int/float elements."""
        int_part = await card.locator('[class*="priceInt--"]').inner_text()
        float_part = await card.locator('[class*="priceFloat--"]').inner_text()
        return float(f"{int_part}{float_part}")

    async def search(self, query: str) -> list[ProductListing]:
        """Perform a search and return results."""
        page = await self.context.new_page()
        search_url = f"https://s.taobao.com/search?page=1&q={query}"
        await page.goto(search_url)

        # TODO: don't use timeouts
        await self.page.wait_for_timeout(3000)

        cards = await page.locator('a[class*="doubleCardWrapperAdapt--"]').all()

        results = []
        for card in cards:
            product_link = await card.get_attribute("href")
            listing_name = await card.locator('[class*="title--"]').inner_text()
            unit_price = str(await self.get_product_price_value(card))
            seller_name = await card.locator('[class*="shopNameText--"]').inner_text()
            listing = ProductListing(
                product_link=product_link,
                seller_name= seller_name,
                unit_price=unit_price,
                listing_name=listing_name,
            )
            results.append(listing)
        return results

    async def is_logged_in(self) -> bool:
        """Check if logged into Taobao."""
        try:
            self.page = await self.context.new_page()
            if "taobao.com" in self.page.url:
                pass
            else:
                await self.page.goto("https://www.taobao.com")
            return "请登录" not in (await self.page.content())
        except Exception:
            return False

    async def open_homepage(self) -> None:
        """Open the Taobao homepage so user can log in."""
        self.page = self.context.pages[0] if self.context.pages else await self.context.new_page()
        if "taobao.com" in self.page.url:
            return
        await self.page.goto("https://www.taobao.com")
