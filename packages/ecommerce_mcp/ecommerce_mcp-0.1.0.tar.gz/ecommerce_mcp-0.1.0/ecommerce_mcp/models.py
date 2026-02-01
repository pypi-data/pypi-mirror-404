"""Data classes for e-commerce MCP types."""

from dataclasses import dataclass


@dataclass
class ProductListing:
    """Represents a product listing from search results."""
    product_link: str
    seller_name: str
    unit_price: str
    listing_name: str

    def to_tuple(self) -> tuple[str, str, str, str]:
        """Return a tuple representation of the listing."""
        return (
            self.product_link,
            self.seller_name,
            self.unit_price,
            self.listing_name,
        )
