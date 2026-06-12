"""Safety checks before sending chatbot replies."""

import re

from chatbot.schemas import SafetyResult
from core.chat_database import get_blocked_keywords
from core.models import ChatbotSettings

PROMPT_INJECTION_PATTERNS = [
    r"ignore\s+(all\s+)?(previous|prior)\s+instructions",
    r"disregard\s+(your\s+)?(system\s+)?prompt",
    r"reveal\s+(your\s+)?(system\s+)?prompt",
    r"show\s+(me\s+)?(your\s+)?api\s+key",
    r"act\s+as\s+(if\s+you\s+are\s+)?(dan|jailbreak)",
]

OVERPROMISE_PATTERNS = [
    r"\b100%\s+guarantee",
    r"\bguaranteed\s+delivery",
    r"\bwe\s+will\s+definitely\b",
    r"\bpromise\s+you\b",
    r"\bno\s+risk\b",
]

SENSITIVE_ADVICE_PATTERNS = [
    r"\b(legal|financial|medical)\s+advice\b",
    r"\byou\s+should\s+(sue|invest|take\s+this\s+medication)\b",
]

SECRET_PATTERNS = [
    r"sk-[a-zA-Z0-9]{10,}",
    r"sk-ant-[a-zA-Z0-9\-]{10,}",
    r"Bearer\s+[a-zA-Z0-9\-_.]+",
    r"api[_-]?key\s*[:=]\s*\S+",
]


def _match_any(text: str, patterns: list[str]) -> str | None:
    lower = text.lower()
    for pattern in patterns:
        if re.search(pattern, lower, re.IGNORECASE):
            return pattern
    return None


def run_safety_check(
    user_message: str,
    draft_reply: str,
    settings: ChatbotSettings,
) -> SafetyResult:
    notes: list[str] = []
    combined = f"{user_message}\n{draft_reply}"

    blocked = get_blocked_keywords(settings)
    for keyword in blocked:
        if keyword.lower() in combined.lower():
            notes.append(f"Blocked keyword detected: {keyword}")

    injection = _match_any(combined, PROMPT_INJECTION_PATTERNS)
    if injection:
        notes.append("Possible prompt injection detected.")

    secret = _match_any(draft_reply, SECRET_PATTERNS)
    if secret:
        notes.append("Possible secret or API key leakage in reply.")

    overpromise = _match_any(draft_reply, OVERPROMISE_PATTERNS)
    if overpromise:
        notes.append("Possible overpromising language detected.")

    sensitive = _match_any(draft_reply, SENSITIVE_ADVICE_PATTERNS)
    if sensitive:
        notes.append("Possible sensitive advice detected.")

    spam_indicators = draft_reply.count("http") > 3 or draft_reply.count("!!!") > 2
    if spam_indicators:
        notes.append("Possible spam risk in reply.")

    if not draft_reply or not draft_reply.strip():
        notes.append("Empty reply.")

    passed = len(notes) == 0
    status = "passed" if passed else "failed"
    return SafetyResult(passed=passed, status=status, notes=notes)
