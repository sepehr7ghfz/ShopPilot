from __future__ import annotations

import logging

from fastapi import UploadFile

from app.schemas.assistant import AssistantResponse, Intent
from app.schemas.product import ProductResponse
from app.services.catalog_service import CatalogService
from app.services.hybrid_retrieval_service import HybridRetrievalService
from app.services.image_retrieval_service import ImageRetrievalService
from app.services.intent_router import IntentRouter
from app.services.text_retrieval_service import TextRetrievalService

logger = logging.getLogger(__name__)


class AgentService:
    """Orchestrates request handling for the unified assistant endpoint."""

    def __init__(self, intent_router: IntentRouter | None = None) -> None:
        self.intent_router = intent_router or IntentRouter()
        self.catalog_service = CatalogService()
        self.text_retrieval_service = TextRetrievalService(self.catalog_service)
        self.image_retrieval_service = ImageRetrievalService(self.catalog_service)
        self.hybrid_retrieval_service = HybridRetrievalService(
            text_retrieval_service=self.text_retrieval_service,
            image_retrieval_service=self.image_retrieval_service,
        )

    async def respond(
        self,
        message: str | None,
        image: UploadFile | None,
        session_id: str | None,
    ) -> AssistantResponse:
        intent = self.intent_router.route(message=message, has_image=image is not None)
        logger.info(
            "assistant.request intent=%s session_id=%s has_message=%s has_image=%s",
            intent.value,
            session_id,
            bool((message or "").strip()),
            image is not None,
        )

        if intent == Intent.GENERAL_CHAT:
            return self._build_general_chat_response()
        if intent == Intent.TEXT_RECOMMENDATION:
            return self._build_text_recommendation_response(message=message)
        if intent == Intent.IMAGE_SEARCH:
            return await self._build_image_search_response(image=image)

        return await self._build_hybrid_search_response(message=message, image=image)

    def _build_general_chat_response(self) -> AssistantResponse:
        return AssistantResponse(
            response_text=(
                "I can help you discover products from the ShopPilot catalog. "
                "Try requests like 'recommend a black hoodie' or 'I need a travel backpack'."
            ),
            intent=Intent.GENERAL_CHAT,
            products=[],
        )

    def _build_text_recommendation_response(self, message: str | None) -> AssistantResponse:
        if not message or not message.strip():
            return AssistantResponse(
                response_text="Share what you need and I will suggest products from the catalog.",
                intent=Intent.TEXT_RECOMMENDATION,
                products=[],
            )

        matches = self.text_retrieval_service.retrieve(query=message, limit=5)
        if not matches:
            categories = sorted({product.category for product in self.catalog_service.get_all_products()})
            category_list = ", ".join(categories)
            return AssistantResponse(
                response_text=(
                    "I could not find strong matches for that request yet. "
                    f"Try mentioning product type, color, or use case. Available categories: {category_list}."
                ),
                intent=Intent.TEXT_RECOMMENDATION,
                products=[],
            )

        products: list[ProductResponse] = [
            result.product.to_response(reason=result.reason) for result in matches
        ]
        lead_names = ", ".join(product.name for product in products[:3])
        response_text = (
            f"I found {len(products)} strong options for your request. "
            f"Top picks: {lead_names}."
        )

        return AssistantResponse(
            response_text=response_text,
            intent=Intent.TEXT_RECOMMENDATION,
            products=products,
        )

    async def _build_image_search_response(self, image: UploadFile | None) -> AssistantResponse:
        if image is None:
            return AssistantResponse(
                response_text="Please upload an image so I can find visually similar products.",
                intent=Intent.IMAGE_SEARCH,
                products=[],
            )

        try:
            image_bytes = await image.read()
            matches = self.image_retrieval_service.retrieve_from_bytes(image_bytes=image_bytes, limit=5)
        except RuntimeError as exc:
            logger.warning("assistant.image_search_failed error=%s", str(exc))
            return AssistantResponse(
                response_text=(
                    "Image search dependencies are not installed in this environment yet. "
                    "Install backend image dependencies and retry."
                ),
                intent=Intent.IMAGE_SEARCH,
                products=[],
            )
        except ValueError as exc:
            logger.warning("assistant.image_search_failed error=%s", str(exc))
            return AssistantResponse(
                response_text=(
                    "I could not process that image yet. Please upload a clear product photo in JPG or PNG format."
                ),
                intent=Intent.IMAGE_SEARCH,
                products=[],
            )

        if not matches or matches[0].score < self.image_retrieval_service.min_similarity:
            return AssistantResponse(
                response_text=(
                    "I could not find confident visual matches from the catalog for this image. "
                    "Try a clearer product shot or add a short text hint."
                ),
                intent=Intent.IMAGE_SEARCH,
                products=[],
            )

        products = [result.product.to_response(reason=result.reason) for result in matches]
        lead_names = ", ".join(product.name for product in products[:3])
        return AssistantResponse(
            response_text=f"I found visually similar products. Top matches: {lead_names}.",
            intent=Intent.IMAGE_SEARCH,
            products=products,
        )

    async def _build_hybrid_search_response(
        self,
        message: str | None,
        image: UploadFile | None,
    ) -> AssistantResponse:
        if image is None:
            return self._build_text_recommendation_response(message=message)
        if not message or not message.strip():
            return await self._build_image_search_response(image=image)

        try:
            image_bytes = await image.read()
            matches = self.hybrid_retrieval_service.retrieve(
                query=message,
                image_bytes=image_bytes,
                limit=5,
            )
        except RuntimeError as exc:
            logger.warning("assistant.hybrid_search_failed error=%s", str(exc))
            return AssistantResponse(
                response_text=(
                    "Hybrid search dependencies are not installed in this environment yet. "
                    "Install backend image dependencies and retry."
                ),
                intent=Intent.HYBRID_SEARCH,
                products=[],
            )
        except ValueError as exc:
            logger.warning("assistant.hybrid_search_failed error=%s", str(exc))
            return AssistantResponse(
                response_text=(
                    "I could not complete the combined image and text search. "
                    "Please try a clearer image or simplify the text request."
                ),
                intent=Intent.HYBRID_SEARCH,
                products=[],
            )

        if not matches or matches[0].score < 0.25:
            return AssistantResponse(
                response_text=(
                    "I could not find confident combined matches yet. "
                    "Try adding a specific product type, color, or use case with the image."
                ),
                intent=Intent.HYBRID_SEARCH,
                products=[],
            )

        products = [result.product.to_response(reason=result.reason) for result in matches]
        lead_names = ", ".join(product.name for product in products[:3])
        return AssistantResponse(
            response_text=f"I combined your image and text request. Best matches: {lead_names}.",
            intent=Intent.HYBRID_SEARCH,
            products=products,
        )
