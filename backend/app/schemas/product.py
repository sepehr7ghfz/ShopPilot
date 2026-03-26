from __future__ import annotations

from pydantic import BaseModel, Field


class CatalogProduct(BaseModel):
    id: str = Field(..., description="Unique product identifier")
    name: str
    category: str
    description: str
    tags: list[str]
    price: float
    image_path: str

    def to_response(self, reason: str | None = None) -> "ProductResponse":
        return ProductResponse(
            id=self.id,
            name=self.name,
            category=self.category,
            price=self.price,
            description=self.description,
            image_path=self.image_path,
            reason=reason,
        )


class ProductResponse(BaseModel):
    id: str = Field(..., description="Unique product identifier")
    name: str
    category: str
    price: float
    description: str
    image_path: str
    reason: str | None = None
