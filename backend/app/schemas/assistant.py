from __future__ import annotations

from enum import Enum

from pydantic import BaseModel, Field

from app.schemas.product import ProductResponse


class Intent(str, Enum):
    GENERAL_CHAT = "general_chat"
    TEXT_RECOMMENDATION = "text_recommendation"
    IMAGE_SEARCH = "image_search"
    HYBRID_SEARCH = "hybrid_search"
    CART_UPDATE = "cart_update"


class CartActionType(str, Enum):
    ADD = "add"
    REMOVE = "remove"
    CLEAR = "clear"


class CartAction(BaseModel):
    action: CartActionType
    product_ids: list[str] = Field(default_factory=list)
    note: str | None = None


class AssistantResponse(BaseModel):
    response_text: str = Field(..., description="Assistant response shown to user")
    intent: Intent
    products: list[ProductResponse] = Field(default_factory=list)
    cart_actions: list[CartAction] = Field(default_factory=list)
