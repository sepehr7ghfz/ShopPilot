from __future__ import annotations

import asyncio
import logging
import re

from fastapi import UploadFile

from app.core.config import settings
from app.schemas.assistant import AssistantResponse, Intent
from app.schemas.product import ProductResponse
from app.services.catalog_service import CatalogService
from app.services.hybrid_retrieval_service import HybridRetrievalService
from app.services.image_retrieval_service import ImageRetrievalService
from app.services.intent_router import IntentRouter
from app.services.llm_agent_service import LLMAgentService
from app.services.query_constraints import parse_price_constraints
from app.services.session_memory_service import SessionMemoryService
from app.services.text_retrieval_service import TextRetrievalService

logger = logging.getLogger(__name__)


class AgentService:
    """Orchestrates request handling for the unified assistant endpoint."""

    _GENERAL_GREETINGS = {
        "hi",
        "hello",
        "hey",
        "good morning",
        "good afternoon",
        "good evening",
    }

    _CAPABILITY_HINTS = {
        "what can you do",
        "help",
        "how can you help",
        "what do you do",
    }

    _IDENTITY_HINTS = {
        "what is your name",
        "what's your name",
        "who are you",
    }

    _IRRELEVANT_HINTS = {
        "weather",
        "news",
        "politics",
        "election",
        "stock",
        "crypto",
        "football",
        "soccer",
        "basketball",
        "movie",
        "song",
        "poem",
        "code",
        "programming",
        "math",
    }

    def __init__(self, intent_router: IntentRouter | None = None) -> None:
        self.intent_router = intent_router or IntentRouter()
        self.catalog_service = CatalogService()
        self.text_retrieval_service = TextRetrievalService(
            self.catalog_service,
            semantic_model_name=settings.rag_model_name,
            semantic_weight=0.65 if settings.use_text_rag else 0.0,
            lexical_weight=0.35 if settings.use_text_rag else 1.0,
            min_combined_score=0.22 if settings.use_text_rag else 0.0,
        )
        self.image_retrieval_service = ImageRetrievalService(self.catalog_service)
        self.hybrid_retrieval_service = HybridRetrievalService(
            text_retrieval_service=self.text_retrieval_service,
            image_retrieval_service=self.image_retrieval_service,
        )
        self.session_memory_service = SessionMemoryService(
            max_messages_per_session=settings.session_memory_turns * 2
        )

        self.llm_agent_service: LLMAgentService | None = None
        if settings.use_llm_orchestrator and settings.openai_api_key:
            try:
                self.llm_agent_service = LLMAgentService(
                    api_key=settings.openai_api_key,
                    model=settings.openai_model,
                    text_retrieval_service=self.text_retrieval_service,
                    image_retrieval_service=self.image_retrieval_service,
                    hybrid_retrieval_service=self.hybrid_retrieval_service,
                )
                logger.info("assistant.llm_orchestrator_enabled model=%s", settings.openai_model)
            except Exception as exc:  # pragma: no cover - defensive fallback
                logger.warning("assistant.llm_orchestrator_init_failed error=%s", str(exc))

    async def respond(
        self,
        message: str | None,
        image: UploadFile | None,
        session_id: str | None,
    ) -> AssistantResponse:
        normalized_message = (message or "").strip() or None
        print(
            "[agent.respond] start",
            {
                "message": (normalized_message or "")[:120],
                "has_image": image is not None,
                "session_id": session_id,
                "llm_enabled": self.llm_agent_service is not None,
            },
        )

        if self._should_fast_path_general_chat(message=normalized_message, image=image):
            print("[agent.respond] fast_path_general_chat")
            response = self._build_general_chat_response(message=normalized_message)
            self.session_memory_service.append_turn(
                session_id=session_id,
                user_message=normalized_message,
                assistant_message=response.response_text,
            )
            print(
                "[agent.respond] fast_path_done",
                {"intent": response.intent.value, "products": len(response.products)},
            )
            return response

        if self.llm_agent_service is not None:
            print("[agent.respond] trying_llm")
            llm_response = await self._try_llm_response(
                message=normalized_message,
                image=image,
                session_id=session_id,
            )
            if llm_response is not None:
                print(
                    "[agent.respond] llm_success",
                    {"intent": llm_response.intent.value, "products": len(llm_response.products)},
                )
                return llm_response
            print("[agent.respond] llm_returned_none_fallback")

        intent = self.intent_router.route(message=message, has_image=image is not None)
        logger.info(
            "assistant.request intent=%s session_id=%s has_message=%s has_image=%s",
            intent.value,
            session_id,
            bool((message or "").strip()),
            image is not None,
        )

        if intent == Intent.GENERAL_CHAT:
            print("[agent.respond] fallback_general")
            response = self._build_general_chat_response(message=normalized_message)
            self.session_memory_service.append_turn(
                session_id=session_id,
                user_message=normalized_message,
                assistant_message=response.response_text,
            )
            return response
        if intent == Intent.TEXT_RECOMMENDATION:
            print("[agent.respond] fallback_text")
            response = self._build_text_recommendation_response(message=message)
            self.session_memory_service.append_turn(
                session_id=session_id,
                user_message=normalized_message,
                assistant_message=response.response_text,
            )
            return response
        if intent == Intent.IMAGE_SEARCH:
            print("[agent.respond] fallback_image")
            response = await self._build_image_search_response(image=image)
            self.session_memory_service.append_turn(
                session_id=session_id,
                user_message=normalized_message,
                assistant_message=response.response_text,
            )
            return response

        print("[agent.respond] fallback_hybrid")
        response = await self._build_hybrid_search_response(message=message, image=image)
        self.session_memory_service.append_turn(
            session_id=session_id,
            user_message=normalized_message,
            assistant_message=response.response_text,
        )
        return response

    async def _try_llm_response(
        self,
        message: str | None,
        image: UploadFile | None,
        session_id: str | None,
    ) -> AssistantResponse | None:
        if self.llm_agent_service is None:
            print("[agent.llm] disabled")
            return None

        try:
            image_bytes = await image.read() if image is not None else None
            if image is not None:
                await image.seek(0)
            history = self.session_memory_service.get_recent_messages(session_id=session_id)
            print(
                "[agent.llm] invoke",
                {
                    "message": (message or "")[:120],
                    "has_image": image_bytes is not None,
                    "history_len": len(history),
                },
            )

            llm_result = await asyncio.to_thread(
                self.llm_agent_service.run,
                message,
                image_bytes,
                history,
            )
            print(
                "[agent.llm] result",
                {"intent": llm_result.intent.value, "products": len(llm_result.products)},
            )

            response = AssistantResponse(
                response_text=llm_result.response_text,
                intent=llm_result.intent,
                products=llm_result.products,
            )
            self.session_memory_service.append_turn(
                session_id=session_id,
                user_message=message,
                assistant_message=response.response_text,
            )
            return response
        except RuntimeError as exc:
            logger.warning("assistant.llm_runtime_error error=%s", str(exc))
            print("[agent.llm] runtime_error", str(exc))
            return None
        except Exception as exc:  # pragma: no cover - defensive fallback
            logger.warning("assistant.llm_failed error=%s", str(exc))
            print("[agent.llm] exception", str(exc))
            return None

    def _should_fast_path_general_chat(self, message: str | None, image: UploadFile | None) -> bool:
        if image is not None:
            return False

        routed_intent = self.intent_router.route(message=message, has_image=False)
        return routed_intent == Intent.GENERAL_CHAT

    def _build_general_chat_response(self, message: str | None) -> AssistantResponse:
        normalized = (message or "").strip().lower()

        if not normalized or normalized in self._GENERAL_GREETINGS:
            response_text = (
                "Hi there. I am ShopPilot, and I am happy to help you find products. "
                "You can ask with text, upload an image, or combine both for better matches."
            )
        elif any(hint in normalized for hint in self._IDENTITY_HINTS):
            response_text = (
                "I am ShopPilot, your shopping assistant for this catalog. "
                "I can help you discover products and narrow down the best options."
            )
        elif any(hint in normalized for hint in self._CAPABILITY_HINTS):
            response_text = (
                "Absolutely. I can help with 3 things: general shopping guidance, "
                "text-based product recommendations, and image-based similarity search. "
                "You can also combine text and image for hybrid results."
            )
        elif self._is_irrelevant_general_question(normalized):
            response_text = (
                "Thanks for the question. I am focused on shopping tasks for this catalog, "
                "so I may not be accurate on unrelated topics. "
                "Please ask me about products, recommendations, or finding similar items from an image."
            )
        else:
            response_text = (
                "I would be glad to help you discover products from the ShopPilot catalog. "
                "Try: 'recommend a black hoodie for casual wear' or upload an image and ask for similar items."
            )

        return AssistantResponse(
            response_text=response_text,
            intent=Intent.GENERAL_CHAT,
            products=[],
        )

    def _is_irrelevant_general_question(self, message: str) -> bool:
        if not message:
            return False

        tokens = set(re.findall(r"[a-z0-9-]+", message))
        if tokens & self._IRRELEVANT_HINTS:
            return True

        if tokens & self.intent_router.SHOPPING_HINTS:
            return False

        # Non-shopping question patterns should stay in assistant scope.
        return message.endswith("?") and "product" not in tokens and "catalog" not in tokens

    def _build_text_recommendation_response(self, message: str | None) -> AssistantResponse:
        if not message or not message.strip():
            return AssistantResponse(
                response_text="Sure. Share what you are looking for, and I will suggest products from the catalog.",
                intent=Intent.TEXT_RECOMMENDATION,
                products=[],
            )

        constraints = parse_price_constraints(message)
        matches = self.text_retrieval_service.retrieve_with_constraints(
            query=message,
            limit=5,
            min_price=constraints.min_price,
            max_price=constraints.max_price,
        )
        if not matches:
            categories = sorted({product.category for product in self.catalog_service.get_all_products()})
            category_list = ", ".join(categories)
            budget_hint = ""
            if constraints.max_price is not None:
                budget_hint = f" under ${constraints.max_price:.2f}"
            elif constraints.min_price is not None:
                budget_hint = f" above ${constraints.min_price:.2f}"
            return AssistantResponse(
                response_text=(
                    "Thanks. I could not find strong matches for that request yet. "
                    f"Try mentioning product type, color, or use case{budget_hint}. "
                    f"Available categories: {category_list}."
                ),
                intent=Intent.TEXT_RECOMMENDATION,
                products=[],
            )

        products: list[ProductResponse] = [
            result.product.to_response(reason=result.reason) for result in matches
        ]
        lead_names = ", ".join(product.name for product in products[:3])
        response_text = (
            f"Great choice. I found {len(products)} strong options for your request. "
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
                response_text="Please upload an image, and I will find visually similar products for you.",
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
                    "Image search is currently unavailable because dependencies are not installed in this environment. "
                    "Install backend image dependencies and try again."
                ),
                intent=Intent.IMAGE_SEARCH,
                products=[],
            )
        except ValueError as exc:
            logger.warning("assistant.image_search_failed error=%s", str(exc))
            return AssistantResponse(
                response_text=(
                    "I could not process that image yet. Please upload a clear product photo in JPG or PNG format, and I will try again."
                ),
                intent=Intent.IMAGE_SEARCH,
                products=[],
            )

        if not matches or matches[0].score < self.image_retrieval_service.min_similarity:
            return AssistantResponse(
                response_text=(
                    "I could not find confident visual matches from the catalog for this image yet. "
                    "Try a clearer product shot or add a short text hint."
                ),
                intent=Intent.IMAGE_SEARCH,
                products=[],
            )

        products = [result.product.to_response(reason=result.reason) for result in matches]
        lead_names = ", ".join(product.name for product in products[:3])
        return AssistantResponse(
            response_text=f"Thanks for sharing the image. I found visually similar products. Top matches: {lead_names}.",
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
            constraints = parse_price_constraints(message)
            matches = self.hybrid_retrieval_service.retrieve_with_constraints(
                query=message,
                image_bytes=image_bytes,
                limit=5,
                min_price=constraints.min_price,
                max_price=constraints.max_price,
            )
        except RuntimeError as exc:
            logger.warning("assistant.hybrid_search_failed error=%s", str(exc))
            return AssistantResponse(
                response_text=(
                    "Hybrid search is currently unavailable because image dependencies are not installed in this environment. "
                    "Install backend image dependencies and try again."
                ),
                intent=Intent.HYBRID_SEARCH,
                products=[],
            )
        except ValueError as exc:
            logger.warning("assistant.hybrid_search_failed error=%s", str(exc))
            return AssistantResponse(
                response_text=(
                    "I could not complete the combined image and text search this time. "
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
            response_text=f"Great request. I combined your image and text input. Best matches: {lead_names}.",
            intent=Intent.HYBRID_SEARCH,
            products=products,
        )
