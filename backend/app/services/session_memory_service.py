from __future__ import annotations

from collections import defaultdict, deque
from dataclasses import dataclass


@dataclass(frozen=True)
class SessionMessage:
    role: str
    content: str


class SessionMemoryService:
    """Small in-memory session memory for multi-turn context continuity."""

    def __init__(self, max_messages_per_session: int = 16) -> None:
        self.max_messages_per_session = max_messages_per_session
        self._memory: dict[str, deque[SessionMessage]] = defaultdict(
            lambda: deque(maxlen=self.max_messages_per_session)
        )

    def get_recent_messages(self, session_id: str | None) -> list[SessionMessage]:
        if not session_id:
            return []
        return list(self._memory.get(session_id, []))

    def append_turn(
        self,
        session_id: str | None,
        user_message: str | None,
        assistant_message: str,
    ) -> None:
        if not session_id:
            return

        bucket = self._memory[session_id]
        if user_message and user_message.strip():
            bucket.append(SessionMessage(role="user", content=user_message.strip()))
        bucket.append(SessionMessage(role="assistant", content=assistant_message.strip()))
