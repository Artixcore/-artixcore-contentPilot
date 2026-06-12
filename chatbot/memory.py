"""Conversation memory for chatbot context."""

from sqlalchemy.orm import Session

from core.chat_database import get_conversation_messages


def load_conversation_history(
    session: Session,
    conversation_id: int,
    limit: int = 20,
) -> list[dict]:
    messages = get_conversation_messages(session, conversation_id)
    if limit > 0:
        messages = messages[-limit:]

    history = []
    for msg in messages:
        if msg.sender_type == "user":
            history.append({"role": "user", "content": msg.message_text})
        elif msg.sender_type in ("bot", "human_admin"):
            text = msg.final_reply or msg.ai_generated_reply or msg.message_text
            if text:
                history.append({"role": "assistant", "content": text})
    return history


def build_input_prompt(user_message: str, history: list[dict]) -> str:
    lines = ["Conversation history:"]
    if history:
        for item in history:
            role = item.get("role", "user").capitalize()
            lines.append(f"{role}: {item.get('content', '')}")
    else:
        lines.append("(No prior messages)")
    lines.append("")
    lines.append(f"Latest user message: {user_message}")
    lines.append("")
    lines.append("Write a helpful reply as Artixcore Assistant.")
    return "\n".join(lines)
