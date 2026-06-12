"""Provider routing with fallback and logging."""

import logging
from typing import Optional

from sqlalchemy.orm import Session

from core.models import ProviderLog
from providers import get_all_providers
from providers.base import BaseAIProvider, GenerationResult, ProviderError

logger = logging.getLogger(__name__)


class ProviderRouter:
    MODES = ("manual", "auto", "fallback", "budget", "quality")

    AUTO_ORDER = ("openai", "anthropic", "mock")
    QUALITY_ORDER = ("anthropic", "openai", "mock")

    def __init__(self, session: Session | None = None):
        self.session = session
        self.providers = get_all_providers()

    def get_provider(self, name: str) -> BaseAIProvider | None:
        return self.providers.get(name)

    def is_provider_available(self, name: str) -> bool:
        provider = self.get_provider(name)
        return provider is not None and provider.is_available()

    def resolve_provider(
        self,
        mode: str = "auto",
        selected_provider: str | None = None,
    ) -> BaseAIProvider:
        mode = (mode or "auto").lower()
        if mode not in self.MODES:
            mode = "auto"

        if mode == "budget":
            if selected_provider and selected_provider != "mock":
                provider = self.get_provider(selected_provider)
                if provider and provider.is_available():
                    logger.info("Budget mode: using manually selected provider %s", selected_provider)
                    return provider
            logger.info("Budget mode: using mock provider")
            return self.providers["mock"]

        if mode == "quality":
            provider = self._first_available(self.QUALITY_ORDER)
            logger.info("Quality mode: resolved to %s", provider.name)
            return provider

        if mode == "auto":
            provider = self._first_available(self.AUTO_ORDER)
            logger.info("Auto mode: resolved to %s", provider.name)
            return provider

        if mode == "manual":
            if selected_provider:
                provider = self.get_provider(selected_provider)
                if provider and provider.is_available():
                    logger.info("Manual mode: using %s", selected_provider)
                    return provider
            provider = self._first_available(self.AUTO_ORDER)
            logger.info("Manual mode fallback: resolved to %s", provider.name)
            return provider

        if mode == "fallback":
            candidates: list[str] = []
            if selected_provider:
                candidates.append(selected_provider)
            for name in self.AUTO_ORDER:
                if name not in candidates:
                    candidates.append(name)
            provider = self._first_available(candidates)
            logger.info("Fallback mode: resolved to %s", provider.name)
            return provider

        return self.providers["mock"]

    def _first_available(self, names: tuple[str, ...] | list[str]) -> BaseAIProvider:
        for name in names:
            provider = self.get_provider(name)
            if provider and provider.is_available():
                return provider
        return self.providers["mock"]

    def generate(
        self,
        prompt: str,
        system_prompt: str | None = None,
        mode: str = "auto",
        selected_provider: str | None = None,
        task_type: str = "generate",
        **kwargs,
    ) -> GenerationResult:
        mode = (mode or "auto").lower()
        chain = self._build_fallback_chain(mode, selected_provider)
        last_error: str | None = None

        for provider_name in chain:
            provider = self.get_provider(provider_name)
            if not provider or not provider.is_available():
                continue
            try:
                result = provider.generate(prompt, system_prompt, **kwargs)
                self._log_provider(provider.name, result.model, task_type, True, result.latency_ms)
                logger.info("Generation succeeded with provider=%s model=%s", provider.name, result.model)
                return result
            except ProviderError as exc:
                last_error = exc.message
                self._log_provider(
                    provider.name,
                    provider.model_name,
                    task_type,
                    False,
                    None,
                    exc.message,
                )
                logger.warning("Provider %s failed: %s", provider.name, exc.message)
            except Exception as exc:
                last_error = type(exc).__name__
                self._log_provider(
                    provider.name,
                    provider.model_name,
                    task_type,
                    False,
                    None,
                    last_error,
                )
                logger.warning("Provider %s unexpected error: %s", provider.name, last_error)

        mock = self.providers["mock"]
        result = mock.generate(prompt, system_prompt, **kwargs)
        self._log_provider(mock.name, mock.model_name, task_type, True, result.latency_ms, last_error)
        logger.info("All providers failed or unavailable; using mock")
        return result

    def _build_fallback_chain(
        self,
        mode: str,
        selected_provider: str | None,
    ) -> list[str]:
        if mode == "budget":
            if selected_provider and selected_provider != "mock":
                return [selected_provider, "mock"]
            return ["mock"]

        if mode == "quality":
            return list(self.QUALITY_ORDER)

        if mode == "auto":
            return list(self.AUTO_ORDER)

        if mode == "manual":
            chain = []
            if selected_provider:
                chain.append(selected_provider)
            for name in self.AUTO_ORDER:
                if name not in chain:
                    chain.append(name)
            return chain

        if mode == "fallback":
            chain = []
            if selected_provider:
                chain.append(selected_provider)
            for name in self.AUTO_ORDER:
                if name not in chain:
                    chain.append(name)
            return chain

        return list(self.AUTO_ORDER)

    def _log_provider(
        self,
        provider: str,
        model: str | None,
        task_type: str,
        success: bool,
        latency_ms: int | None,
        error_message: str | None = None,
    ) -> None:
        if not self.session:
            return
        try:
            log = ProviderLog(
                provider=provider,
                model=model,
                task_type=task_type,
                success=success,
                latency_ms=latency_ms,
                error_message=error_message,
            )
            self.session.add(log)
            self.session.commit()
        except Exception as exc:
            logger.warning("Failed to log provider usage: %s", type(exc).__name__)
            if self.session:
                self.session.rollback()

    def get_availability_status(self) -> dict[str, bool]:
        return {
            name: provider.is_available()
            for name, provider in self.providers.items()
        }
