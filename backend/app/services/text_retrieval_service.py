from __future__ import annotations

import re
from dataclasses import dataclass

from app.schemas.product import CatalogProduct
from app.services.catalog_service import CatalogService


@dataclass(frozen=True)
class TextRetrievalResult:
    product: CatalogProduct
    score: float
    reason: str | None


class TextRetrievalService:
    """Keyword and metadata based ranking for text recommendations."""

    _STOP_WORDS = {
        "a",
        "an",
        "and",
        "are",
        "for",
        "from",
        "i",
        "in",
        "is",
        "it",
        "me",
        "my",
        "of",
        "on",
        "or",
        "please",
        "show",
        "something",
        "that",
        "the",
        "to",
        "want",
        "with",
    }

    _CATEGORY_ALIASES = {
        "t-shirt": {"tshirt", "tshirts", "t-shirt", "t-shirts", "tee", "tees", "shirt", "shirts"},
        "hoodie": {"hoodie", "hoodies", "sweatshirt", "sweatshirts"},
        "sneakers": {"sneaker", "sneakers", "shoe", "shoes", "trainer", "trainers", "running"},
        "jacket": {"jacket", "jackets", "coat", "coats", "outerwear"},
        "backpack": {"backpack", "backpacks", "bag", "bags", "daypack", "travelpack"},
    }

    def __init__(self, catalog_service: CatalogService) -> None:
        self.catalog_service = catalog_service

    def retrieve(self, query: str, limit: int = 5) -> list[TextRetrievalResult]:
        query_terms = self._tokenize(query)
        if not query_terms:
            return []

        scored_results: list[TextRetrievalResult] = []
        for product in self.catalog_service.get_all_products():
            result = self._score_product(product=product, query_terms=query_terms)
            if result and result.score >= 2.0:
                scored_results.append(result)

        scored_results.sort(key=lambda item: (-item.score, item.product.price, item.product.id))
        return scored_results[:limit]

    def _score_product(
        self, product: CatalogProduct, query_terms: set[str]
    ) -> TextRetrievalResult | None:
        score = 0.0
        reasons: list[str] = []

        category_aliases = self._CATEGORY_ALIASES.get(product.category.lower(), {product.category.lower()})
        category_hits = query_terms & category_aliases
        if category_hits:
            score += 5.0
            reasons.append(f"category match ({product.category})")

        product_tags = {tag.lower() for tag in product.tags}
        tag_hits = sorted(query_terms & product_tags)
        if tag_hits:
            score += len(tag_hits) * 3.0
            reasons.append(f"tag match: {', '.join(tag_hits)}")

        searchable_terms = self._tokenize(f"{product.name} {product.description}")
        keyword_hits = sorted(query_terms & searchable_terms)
        if keyword_hits:
            score += len(keyword_hits) * 1.5
            reasons.append(f"keyword match: {', '.join(keyword_hits[:3])}")

        if score <= 0:
            return None

        reason_text = "; ".join(reasons) if reasons else None
        return TextRetrievalResult(product=product, score=score, reason=reason_text)

    def _tokenize(self, value: str) -> set[str]:
        normalized = value.lower().replace("t-shirt", "tshirt").replace("t shirts", "tshirts")
        tokens = {
            token
            for token in re.findall(r"[a-z0-9]+", normalized)
            if token not in self._STOP_WORDS and len(token) > 1
        }
        return tokens
