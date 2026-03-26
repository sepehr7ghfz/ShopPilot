from __future__ import annotations

from enum import Enum

from pydantic import BaseModel, Field

from app.schemas.product import ProductResponse


class Intent(str, Enum):
    GENERAL_CHAT = "general_chat"
    TEXT_RECOMMENDATION = "text_recommendation"
    IMAGE_SEARCH = "image_search"
    HYBRID_SEARCH = "hybrid_search"


class AssistantResponse(BaseModel):
    response_text: str = Field(..., description="Assistant response shown to user")
    intent: Intent
    products: list[ProductResponse] = Field(default_factory=list)
