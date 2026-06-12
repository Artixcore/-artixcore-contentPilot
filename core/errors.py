"""Application error hierarchy with user-facing fields."""

from __future__ import annotations

from typing import Any


class AppError(Exception):
    """Base application error with structured user-facing fields."""

    default_error_code = "APP_ERROR"
    default_user_action = "Please try again or contact support if the problem persists."
    retryable_default = False

    def __init__(
        self,
        message: str,
        reason: str = "",
        user_action: str = "",
        error_code: str = "",
        status: str = "error",
        original_exception: Exception | None = None,
        metadata: dict | None = None,
        retryable: bool | None = None,
    ):
        super().__init__(message)
        self.message = message
        self.reason = reason or message
        self.user_action = user_action or self.default_user_action
        self.error_code = error_code or self.default_error_code
        self.status = status
        self.original_exception = original_exception
        self.metadata = metadata or {}
        self.retryable = self.retryable_default if retryable is None else retryable

    def to_dict(self) -> dict[str, Any]:
        return {
            "success": False,
            "error_code": self.error_code,
            "message": self.message,
            "reason": self.reason,
            "user_action": self.user_action,
            "status": self.status,
            "retryable": self.retryable,
            "metadata": self.metadata,
        }


class ValidationAppError(AppError):
    default_error_code = "VALIDATION_ERROR"
    default_user_action = "Please check your input and try again."

    def __init__(self, message: str, **kwargs):
        super().__init__(message, reason=kwargs.pop("reason", message), retryable=False, **kwargs)


class ProviderUnavailableAppError(AppError):
    default_error_code = "PROVIDER_UNAVAILABLE"
    default_user_action = (
        "Please provide a valid OpenAI or Anthropic API key in Provider Settings."
    )

    def __init__(self, message: str, **kwargs):
        super().__init__(message, retryable=False, **kwargs)


class AIProviderError(AppError):
    default_error_code = "AI_PROVIDER_ERROR"
    default_user_action = "Wait a moment and try again, or switch to another AI provider."
    retryable_default = True

    def __init__(self, message: str, provider: str = "", **kwargs):
        metadata = kwargs.pop("metadata", None) or {}
        if provider:
            metadata["provider"] = provider
        super().__init__(message, metadata=metadata, **kwargs)


class DatabaseError(AppError):
    default_error_code = "DATABASE_ERROR"
    default_user_action = (
        "Please check local database file permissions or restart the app."
    )
    retryable_default = True

    def __init__(self, message: str, **kwargs):
        super().__init__(
            message,
            reason=kwargs.pop("reason", "Database operation failed."),
            **kwargs,
        )


class PublishingError(AppError):
    default_error_code = "PUBLISHING_ERROR"
    default_user_action = "Check your publishing settings and platform configuration, then retry."
    retryable_default = True

    def __init__(self, message: str, platform: str = "", **kwargs):
        metadata = kwargs.pop("metadata", None) or {}
        if platform:
            metadata["platform"] = platform
        super().__init__(message, metadata=metadata, **kwargs)


class ChatbotError(AppError):
    default_error_code = "CHATBOT_ERROR"
    default_user_action = "Review chatbot settings and try again."
    retryable_default = True


class TelegramControllerError(AppError):
    default_error_code = "TELEGRAM_ERROR"
    default_user_action = "Check Telegram bot token and admin IDs in settings."
    retryable_default = True


class ExternalAPIError(AppError):
    default_error_code = "EXTERNAL_API_ERROR"
    default_user_action = (
        "This connector is temporarily paused after repeated failures. "
        "Please wait or check configuration."
    )
    retryable_default = True

    def __init__(self, message: str, service: str = "", **kwargs):
        metadata = kwargs.pop("metadata", None) or {}
        if service:
            metadata["service"] = service
        super().__init__(message, metadata=metadata, **kwargs)


class RateLimitError(AppError):
    default_error_code = "RATE_LIMIT"
    default_user_action = "Too many requests. Please wait a moment and try again."
    retryable_default = True

    def __init__(self, message: str = "Too many requests. Please wait a moment and try again.", **kwargs):
        super().__init__(message, reason=kwargs.pop("reason", "Rate limit exceeded."), **kwargs)


class TimeoutAppError(AppError):
    default_error_code = "TIMEOUT"
    default_user_action = "The operation took too long. Please try again."
    retryable_default = True

    def __init__(self, message: str = "The operation timed out.", **kwargs):
        super().__init__(message, reason=kwargs.pop("reason", "Request timed out."), **kwargs)


class AuthenticationConfigError(AppError):
    default_error_code = "AUTH_CONFIG_ERROR"
    default_user_action = "Check your API keys and tokens in settings."
    retryable_default = False


class ExportError(AppError):
    default_error_code = "EXPORT_ERROR"
    default_user_action = "Check file permissions or try another export format."
    retryable_default = True

    def __init__(self, message: str, **kwargs):
        super().__init__(
            message,
            reason=kwargs.pop("reason", "Export operation failed."),
            **kwargs,
        )


class TrainingDataError(AppError):
    default_error_code = "TRAINING_DATA_ERROR"
    default_user_action = "Check training data settings and try again."
    retryable_default = False


class FileUploadError(AppError):
    default_error_code = "FILE_UPLOAD_ERROR"
    default_user_action = "Check the file format and size, then try uploading again."
    retryable_default = False


class UnsafeContentError(AppError):
    default_error_code = "UNSAFE_CONTENT"
    default_user_action = "Review the content and edit before sending."
    retryable_default = False

    def __init__(self, message: str, **kwargs):
        super().__init__(
            message,
            reason=kwargs.pop("reason", "Content failed safety checks."),
            **kwargs,
        )


class ConfigurationError(AppError):
    default_error_code = "CONFIGURATION_ERROR"
    default_user_action = "Review your environment configuration in .env and settings."
    retryable_default = False


class LoadLimitError(AppError):
    default_error_code = "LOAD_LIMIT"
    default_user_action = (
        "ContentPilot is handling many tasks right now. Please wait and try again shortly."
    )
    retryable_default = True

    def __init__(
        self,
        message: str = "ContentPilot is handling many tasks right now. Please wait and try again shortly.",
        **kwargs,
    ):
        super().__init__(message, reason=kwargs.pop("reason", "System is under heavy load."), **kwargs)
