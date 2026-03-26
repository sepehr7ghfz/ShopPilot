from __future__ import annotations

import json
import logging
import importlib
from dataclasses import dataclass
from typing import Any

from app.schemas.assistant import Intent
from app.schemas.product import ProductResponse
from app.services.hybrid_retrieval_service import HybridRetrievalService
from app.services.image_retrieval_service import ImageRetrievalService
from app.services.session_memory_service import SessionMessage
from app.services.text_retrieval_service import TextRetrievalService

logger = logging.getLogger(__name__)


@dataclass(frozen=True)
class LLMAgentResult:
    intent: Intent
    response_text: str
    products: list[ProductResponse]


class LLMAgentService:
    """OpenAI-powered orchestrator with tool-calling over local retrieval services."""

    def __init__(
        self,
        api_key: str,
        model: str,
        text_retrieval_service: TextRetrievalService,
        image_retrieval_service: ImageRetrievalService,
        hybrid_retrieval_service: HybridRetrievalService,
    ) -> None:
        openai_module = importlib.import_module("openai")
        self.client = openai_module.OpenAI(api_key=api_key)
        self.model = model
        self.text_retrieval_service = text_retrieval_service
        self.image_retrieval_service = image_retrieval_service
        self.hybrid_retrieval_service = hybrid_retrieval_service

    def run(
        self,
        message: str | None,
        image_bytes: bytes | None,
        history: list[SessionMessage],
    ) -> LLMAgentResult:
        tools = self._build_tools()
        chat_messages: list[dict[str, Any]] = [
            {
                "role": "system",
                "content": (
                    "You are ShopPilot, a shopping assistant for a fixed catalog. "
                    "Use tools for product retrieval. "
                    "Rules: "
                    "1) If user asks product recommendations with text, call search_text_products. "
                    "2) If user sends image without text request, call search_image_products. "
                    "3) If both text intent and image are present, call search_hybrid_products. "
                    "4) If user is doing small talk/help questions, answer directly without tools. "
                    "5) Keep answers concise and practical. "
                    "6) Use a friendly, polite, and supportive tone. "
                    "Start naturally, avoid robotic wording, and keep recommendations easy to scan. "
                    "7) If user asks unrelated topics (news, politics, coding, sports, weather), "
                    "politely say you focus on shopping support for this catalog."
                ),
            }
        ]

        for item in history[-8:]:
            if item.role in {"user", "assistant"} and item.content.strip():
                chat_messages.append({"role": item.role, "content": item.content})

        user_payload = {
            "message": (message or "").strip(),
            "has_image": image_bytes is not None,
        }
        chat_messages.append(
            {
                "role": "user",
                "content": json.dumps(user_payload),
            }
        )

        first_response = self.client.chat.completions.create(
            model=self.model,
            messages=chat_messages,
            tools=tools,
            tool_choice="auto",
            temperature=0.2,
        )

        first_message = first_response.choices[0].message
        tool_calls = first_message.tool_calls or []

        if not tool_calls:
            general_text = (first_message.content or "I am here to help with shopping questions.").strip()
            return LLMAgentResult(intent=Intent.GENERAL_CHAT, response_text=general_text, products=[])

        selected_intent = Intent.GENERAL_CHAT
        selected_products: list[ProductResponse] = []

        tool_message_payload: list[dict[str, Any]] = []

        for tool_call in tool_calls:
            tool_name = tool_call.function.name
            tool_args = self._safe_json_loads(tool_call.function.arguments)
            logger.info("assistant.llm_tool_call tool=%s args=%s", tool_name, tool_args)

            if tool_name == "search_text_products":
                selected_intent = Intent.TEXT_RECOMMENDATION
                query = str(tool_args.get("query") or message or "").strip()
                matches = self.text_retrieval_service.retrieve(query=query, limit=5) if query else []
                selected_products = [match.product.to_response(reason=match.reason) for match in matches]
                tool_output = {
                    "intent": selected_intent.value,
                    "query": query,
                    "count": len(selected_products),
                    "products": [self._product_for_tool(product) for product in selected_products],
                }
            elif tool_name == "search_image_products":
                selected_intent = Intent.IMAGE_SEARCH
                if image_bytes is None:
                    tool_output = {
                        "intent": selected_intent.value,
                        "error": "Image not provided.",
                        "count": 0,
                        "products": [],
                    }
                    selected_products = []
                else:
                    matches = self.image_retrieval_service.retrieve_from_bytes(image_bytes=image_bytes, limit=5)
                    selected_products = [match.product.to_response(reason=match.reason) for match in matches]
                    tool_output = {
                        "intent": selected_intent.value,
                        "count": len(selected_products),
                        "products": [self._product_for_tool(product) for product in selected_products],
                    }
            elif tool_name == "search_hybrid_products":
                selected_intent = Intent.HYBRID_SEARCH
                query = str(tool_args.get("query") or message or "").strip()
                if image_bytes is None:
                    tool_output = {
                        "intent": selected_intent.value,
                        "error": "Image not provided.",
                        "query": query,
                        "count": 0,
                        "products": [],
                    }
                    selected_products = []
                else:
                    matches = self.hybrid_retrieval_service.retrieve(query=query, image_bytes=image_bytes, limit=5)
                    selected_products = [match.product.to_response(reason=match.reason) for match in matches]
                    tool_output = {
                        "intent": selected_intent.value,
                        "query": query,
                        "count": len(selected_products),
                        "products": [self._product_for_tool(product) for product in selected_products],
                    }
            else:
                tool_output = {
                    "intent": Intent.GENERAL_CHAT.value,
                    "error": f"Unsupported tool: {tool_name}",
                    "count": 0,
                    "products": [],
                }

            tool_message_payload.append(
                {
                    "role": "tool",
                    "tool_call_id": tool_call.id,
                    "name": tool_name,
                    "content": json.dumps(tool_output),
                }
            )

        second_messages = list(chat_messages)
        second_messages.append(first_message.model_dump(exclude_none=True))
        second_messages.extend(tool_message_payload)

        second_response = self.client.chat.completions.create(
            model=self.model,
            messages=second_messages,
            temperature=0.3,
        )

        response_text = (
            second_response.choices[0].message.content
            or "I checked the catalog and prepared recommendations for you."
        ).strip()

        return LLMAgentResult(
            intent=selected_intent,
            response_text=response_text,
            products=selected_products,
        )

    @staticmethod
    def _build_tools() -> list[dict[str, Any]]:
        return [
            {
                "type": "function",
                "function": {
                    "name": "search_text_products",
                    "description": "Use for text-only product recommendation queries.",
                    "parameters": {
                        "type": "object",
                        "properties": {
                            "query": {
                                "type": "string",
                                "description": "User shopping request in natural language.",
                            }
                        },
                        "required": ["query"],
                    },
                },
            },
            {
                "type": "function",
                "function": {
                    "name": "search_image_products",
                    "description": "Use when user provides an image and asks for visual similarity search.",
                    "parameters": {
                        "type": "object",
                        "properties": {
                            "note": {
                                "type": "string",
                                "description": "Optional short note about visual search.",
                            }
                        },
                    },
                },
            },
            {
                "type": "function",
                "function": {
                    "name": "search_hybrid_products",
                    "description": "Use when user gives both text preference and an image.",
                    "parameters": {
                        "type": "object",
                        "properties": {
                            "query": {
                                "type": "string",
                                "description": "User's text preference to combine with image signal.",
                            }
                        },
                        "required": ["query"],
                    },
                },
            },
        ]

    @staticmethod
    def _safe_json_loads(raw: str | None) -> dict[str, Any]:
        if not raw:
            return {}
        try:
            parsed = json.loads(raw)
            if isinstance(parsed, dict):
                return parsed
            return {}
        except json.JSONDecodeError:
            return {}

    @staticmethod
    def _product_for_tool(product: ProductResponse) -> dict[str, Any]:
        return {
            "id": product.id,
            "name": product.name,
            "category": product.category,
            "price": product.price,
            "description": product.description,
            "reason": product.reason,
        }
