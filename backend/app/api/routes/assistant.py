from __future__ import annotations

from fastapi import APIRouter, File, Form, HTTPException, UploadFile, status

from app.schemas.assistant import AssistantResponse
from app.services.agent_service import AgentService

router = APIRouter(prefix="/assistant", tags=["assistant"])
agent_service = AgentService()


@router.post("/respond", response_model=AssistantResponse)
async def respond(
    message: str | None = Form(default=None),
    image: UploadFile | None = File(default=None),
    session_id: str | None = Form(default=None),
) -> AssistantResponse:
    print(
        "[assistant.route] incoming",
        {
            "message": (message or "")[:120],
            "has_image": image is not None,
            "session_id": session_id,
        },
    )
    has_message = bool((message or "").strip())
    if not has_message and image is None:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail="At least one of 'message' or 'image' must be provided.",
        )
    response = await agent_service.respond(message=message, image=image, session_id=session_id)
    print(
        "[assistant.route] outgoing",
        {
            "intent": response.intent.value,
            "products": len(response.products),
            "response_preview": response.response_text[:140],
        },
    )
    return response
