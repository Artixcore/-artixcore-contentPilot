"""Chat event logging helpers."""

import json

from sqlalchemy.orm import Session

from core.models import ChatEvent


def log_chat_event(
    session: Session,
    conversation_id: int,
    event_type: str,
    event_data: dict | None = None,
    message_id: int | None = None,
) -> ChatEvent:
    event = ChatEvent(
        conversation_id=conversation_id,
        message_id=message_id,
        event_type=event_type,
        event_data=json.dumps(event_data or {}, ensure_ascii=False),
    )
    session.add(event)
    session.flush()
    return event
