from __future__ import annotations

import re

from app.schemas.assistant import Intent


class IntentRouter:
    """Small rule-based router used for the initial MVP scaffold."""

    GENERAL_CHAT_HINTS = {
        "hi",
        "hello",
        "hey",
        "thanks",
        "thank you",
        "help",
        "what can you do",
        "who are you",
        "what are you",
    }

    SHOPPING_HINTS = {
        "recommend",
        "suggest",
        "find",
        "show",
        "need",
        "looking",
        "buy",
        "purchase",
        "tshirt",
        "tshirts",
        "t-shirt",
        "hoodie",
        "hoodies",
        "sneaker",
        "sneakers",
        "shoe",
        "jacket",
        "backpack",
        "bag",
    }

    def route(self, message: str | None, has_image: bool) -> Intent:
        normalized_message = (message or "").strip().lower()
        terms = set(re.findall(r"[a-z0-9-]+", normalized_message))

        if has_image and normalized_message:
            return Intent.HYBRID_SEARCH
        if has_image:
            return Intent.IMAGE_SEARCH

        if not normalized_message:
            return Intent.GENERAL_CHAT

        if normalized_message in self.GENERAL_CHAT_HINTS:
            return Intent.GENERAL_CHAT

        if terms & self.SHOPPING_HINTS:
            return Intent.TEXT_RECOMMENDATION

        if normalized_message.endswith("?") and not terms & {"product", "catalog", "shop"}:
            return Intent.GENERAL_CHAT

        return Intent.TEXT_RECOMMENDATION
