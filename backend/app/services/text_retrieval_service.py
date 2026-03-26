from __future__ import annotations

import logging
import re
from dataclasses import dataclass
from typing import Any

from app.schemas.product import CatalogProduct
from app.services.catalog_service import CatalogService

logger = logging.getLogger(__name__)


@dataclass(frozen=True)
class TextRetrievalResult:
    product: CatalogProduct
    score: float
    reason: str | None


class TextRetrievalService:
    """Hybrid lexical + semantic retrieval for text recommendations (RAG-style)."""

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

    def __init__(
        self,
        catalog_service: CatalogService,
        semantic_model_name: str = "sentence-transformers/all-MiniLM-L6-v2",
        semantic_weight: float = 0.65,
        lexical_weight: float = 0.35,
        min_combined_score: float = 0.22,
    ) -> None:
        self.catalog_service = catalog_service
        self.semantic_model_name = semantic_model_name
        self.semantic_weight = semantic_weight
        self.lexical_weight = lexical_weight
        self.min_combined_score = min_combined_score

        self._encoder: Any | None = None
        self._semantic_index: dict[str, Any] = {}
        self._semantic_ready = False
        self._semantic_disabled = False

    def retrieve(self, query: str, limit: int = 5) -> list[TextRetrievalResult]:
        return self.retrieve_with_constraints(query=query, limit=limit, min_price=None, max_price=None)

    def retrieve_with_constraints(
        self,
        query: str,
        limit: int = 5,
        min_price: float | None = None,
        max_price: float | None = None,
    ) -> list[TextRetrievalResult]:
        query_terms = self._tokenize(query)
        if not query_terms and not query.strip():
            return []

        lexical_results: list[TextRetrievalResult] = []
        for product in self.catalog_service.get_all_products():
            if min_price is not None and product.price < min_price:
                continue
            if max_price is not None and product.price > max_price:
                continue
            result = self._score_product(product=product, query_terms=query_terms)
            if result:
                lexical_results.append(result)

        lexical_by_id = {result.product.id: result for result in lexical_results}
        lexical_max = max((result.score for result in lexical_results), default=1.0)

        semantic_by_id = self._semantic_search(query=query, limit=max(limit * 8, 40))

        product_by_id = {product.id: product for product in self.catalog_service.get_all_products()}
        candidate_ids = set(lexical_by_id.keys()) | set(semantic_by_id.keys())

        scored_results: list[TextRetrievalResult] = []
        for product_id in candidate_ids:
            product = product_by_id.get(product_id)
            if product is None:
                continue
            if min_price is not None and product.price < min_price:
                continue
            if max_price is not None and product.price > max_price:
                continue

            lexical_result = lexical_by_id.get(product_id)
            lexical_norm = (lexical_result.score / lexical_max) if lexical_result else 0.0
            semantic_score = semantic_by_id.get(product_id, 0.0)
            combined_score = self.semantic_weight * semantic_score + self.lexical_weight * lexical_norm

            if (
                combined_score < self.min_combined_score
                and (lexical_result.score if lexical_result else 0.0) < 2.0
                and semantic_score < 0.32
            ):
                continue

            reasons: list[str] = []
            if lexical_result and lexical_result.reason:
                reasons.append(lexical_result.reason)
            if semantic_score > 0:
                reasons.append(f"semantic match: {semantic_score:.2f}")

            scored_results.append(
                TextRetrievalResult(
                    product=product,
                    score=combined_score,
                    reason="; ".join(reasons) if reasons else None,
                )
            )

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

    def _semantic_search(self, query: str, limit: int) -> dict[str, float]:
        if not query.strip():
            return {}

        try:
            self._ensure_semantic_index()
        except RuntimeError as exc:
            logger.warning("text.semantic_index_unavailable error=%s", str(exc))
            return {}

        if not self._semantic_index:
            return {}

        import numpy as np

        assert self._encoder is not None
        query_vector = self._encoder.encode(
            query,
            convert_to_numpy=True,
            normalize_embeddings=True,
        )

        scored: list[tuple[str, float]] = []
        for product_id, vector in self._semantic_index.items():
            score = float(np.dot(query_vector, vector))
            scored.append((product_id, score))

        scored.sort(key=lambda item: item[1], reverse=True)
        return {product_id: score for product_id, score in scored[:limit]}

    def _ensure_semantic_index(self) -> None:
        if self._semantic_ready:
            return
        if self._semantic_disabled:
            raise RuntimeError("Semantic retrieval is disabled due to previous initialization failure.")

        try:
            from sentence_transformers import SentenceTransformer
            import numpy as np
        except ImportError as exc:
            self._semantic_disabled = True
            raise RuntimeError(
                "RAG text dependencies are missing. Install: pip install sentence-transformers"
            ) from exc

        try:
            self._encoder = SentenceTransformer(self.semantic_model_name)

            products = self.catalog_service.get_all_products()
            docs = [
                self._to_semantic_document(product)
                for product in products
            ]
            vectors = self._encoder.encode(
                docs,
                convert_to_numpy=True,
                normalize_embeddings=True,
            )
            self._semantic_index = {
                product.id: np.asarray(vector)
                for product, vector in zip(products, vectors)
            }
            self._semantic_ready = True
            logger.info(
                "text.semantic_index_ready products=%s model=%s",
                len(self._semantic_index),
                self.semantic_model_name,
            )
        except Exception as exc:
            self._semantic_disabled = True
            raise RuntimeError(str(exc)) from exc

    @staticmethod
    def _to_semantic_document(product: CatalogProduct) -> str:
        tags = ", ".join(product.tags)
        return (
            f"name: {product.name}. "
            f"category: {product.category}. "
            f"description: {product.description}. "
            f"tags: {tags}."
        )

    def _tokenize(self, value: str) -> set[str]:
        normalized = value.lower().replace("t-shirt", "tshirt").replace("t shirts", "tshirts")
        tokens = {
            token
            for token in re.findall(r"[a-z0-9]+", normalized)
            if token not in self._STOP_WORDS and len(token) > 1
        }
        return tokens
