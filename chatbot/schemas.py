"""Pydantic schemas for chatbot module."""

from pydantic import BaseModel, Field


class ChatReply(BaseModel):
    success: bool = True
    conversation_id: int
    message_id: int | None = None
    user_message_id: int | None = None
    draft_text: str = ""
    reply_status: str = "draft"
    safety_passed: bool = True
    safety_notes: str | None = None
    provider_used: str | None = None
    model_used: str | None = None
    sent: bool = False
    error: str | None = None


class IncomingMessage(BaseModel):
    platform: str
    user_platform_id: str | None = None
    user_display_name: str | None = None
    user_profile_url: str | None = None
    platform_conversation_id: str | None = None
    platform_message_id: str | None = None
    message_text: str
    conversation_id: int | None = None
    user_message_id: int | None = None


class ChannelStatus(BaseModel):
    platform: str
    configured: bool = False
    available: bool = False
    message: str = ""


class SafetyResult(BaseModel):
    passed: bool = True
    status: str = "passed"
    notes: list[str] = Field(default_factory=list)


class SimulateMessageRequest(BaseModel):
    platform: str
    user_name: str = "Test User"
    message_text: str
    provider_mode: str = "auto"
    selected_provider: str | None = None
