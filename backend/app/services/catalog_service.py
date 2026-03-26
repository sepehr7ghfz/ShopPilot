from __future__ import annotations

import json
from pathlib import Path

from app.schemas.product import CatalogProduct


class CatalogService:
    """Loads and serves product catalog data from local JSON."""

    def __init__(self, catalog_path: Path | None = None) -> None:
        self._catalog_path = catalog_path or self._default_catalog_path()
        self._products = self._load_products()
        self._product_by_id = {product.id: product for product in self._products}

    def get_all_products(self) -> list[CatalogProduct]:
        return self._products

    def get_product_by_id(self, product_id: str) -> CatalogProduct | None:
        return self._product_by_id.get(product_id)

    def get_products_by_category(self, category: str) -> list[CatalogProduct]:
        normalized = category.strip().lower()
        return [product for product in self._products if product.category.lower() == normalized]

    def _load_products(self) -> list[CatalogProduct]:
        with self._catalog_path.open("r", encoding="utf-8") as handle:
            raw_items = json.load(handle)

        products: list[CatalogProduct] = []
        seen_ids: set[str] = set()

        for item in raw_items:
            product = CatalogProduct.model_validate(item)
            if product.id in seen_ids:
                raise ValueError(f"Duplicate product id detected: {product.id}")
            seen_ids.add(product.id)
            products.append(product)

        if not products:
            raise ValueError("Catalog is empty. Add products to products.json.")

        return products

    @staticmethod
    def _default_catalog_path() -> Path:
        return Path(__file__).resolve().parents[2] / "data" / "catalog" / "products.json"
