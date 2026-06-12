"""Base publisher abstraction for social platforms."""


class BasePublisher:
    name: str = "base"

    def is_configured(self) -> bool:
        raise NotImplementedError

    def publish_text(self, content: str, **kwargs) -> dict:
        raise NotImplementedError

    def publish_image(self, content: str, image_url: str, **kwargs) -> dict:
        raise NotImplementedError

    def _result(
        self,
        success: bool,
        platform: str,
        external_post_id: str = "",
        external_post_url: str = "",
        error: str = "",
        raw_response: dict | None = None,
    ) -> dict:
        return {
            "success": success,
            "platform": platform,
            "external_post_id": external_post_id,
            "external_post_url": external_post_url,
            "error": error,
            "raw_response": raw_response or {},
        }
