from __future__ import annotations

from dataclasses import dataclass

from app.schemas.product import CatalogProduct
from app.services.image_retrieval_service import ImageRetrievalService
from app.services.text_retrieval_service import TextRetrievalService


@dataclass(frozen=True)
class HybridRetrievalResult:
    product: CatalogProduct
    score: float
    reason: str | None


class HybridRetrievalService:
    """Deterministic weighted fusion over text and image retrieval results."""

    def __init__(
        self,
        text_retrieval_service: TextRetrievalService,
        image_retrieval_service: ImageRetrievalService,
        image_weight: float = 0.6,
        text_weight: float = 0.4,
    ) -> None:
        self.text_retrieval_service = text_retrieval_service
        self.image_retrieval_service = image_retrieval_service
        self.image_weight = image_weight
        self.text_weight = text_weight

    def retrieve(self, query: str, image_bytes: bytes, limit: int = 5) -> list[HybridRetrievalResult]:
        image_results = self.image_retrieval_service.retrieve_from_bytes(image_bytes=image_bytes, limit=limit * 3)
        text_results = self.text_retrieval_service.retrieve(query=query, limit=limit * 3)

        if not image_results:
            return []

        image_norm = self._normalize_scores({result.product.id: result.score for result in image_results})
        text_norm = self._normalize_scores({result.product.id: result.score for result in text_results})

        product_by_id = {
            result.product.id: result.product for result in image_results
        }
        for result in text_results:
            product_by_id[result.product.id] = result.product

        image_reason_by_id = {result.product.id: result.reason for result in image_results}
        text_reason_by_id = {result.product.id: result.reason for result in text_results}

        fused_results: list[HybridRetrievalResult] = []
        for product_id, product in product_by_id.items():
            image_component = image_norm.get(product_id, 0.0)
            text_component = text_norm.get(product_id, 0.0)
            fused_score = self.image_weight * image_component + self.text_weight * text_component

            reason_parts: list[str] = []
            if image_reason_by_id.get(product_id):
                reason_parts.append(image_reason_by_id[product_id] or "")
            if text_reason_by_id.get(product_id):
                reason_parts.append(text_reason_by_id[product_id] or "")

            fused_results.append(
                HybridRetrievalResult(
                    product=product,
                    score=fused_score,
                    reason="; ".join(part for part in reason_parts if part) or None,
                )
            )

        fused_results.sort(key=lambda item: (-item.score, item.product.price, item.product.id))
        return fused_results[:limit]

    @staticmethod
    def _normalize_scores(score_by_product_id: dict[str, float]) -> dict[str, float]:
        if not score_by_product_id:
            return {}

        min_score = min(score_by_product_id.values())
        max_score = max(score_by_product_id.values())
        if max_score == min_score:
            return {product_id: 1.0 for product_id in score_by_product_id}

        return {
            product_id: (score - min_score) / (max_score - min_score)
            for product_id, score in score_by_product_id.items()
        }
