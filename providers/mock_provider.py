"""Mock AI provider for local development without API keys."""

import json
import time

from providers.base import BaseAIProvider, GenerationResult


class MockProvider(BaseAIProvider):
    name = "mock"

    def is_available(self) -> bool:
        return True

    @property
    def model_name(self) -> str:
        return "mock-v1"

    def generate(
        self,
        prompt: str,
        system_prompt: str | None = None,
        **kwargs,
    ) -> GenerationResult:
        start = time.perf_counter()
        time.sleep(0.05)
        platform = kwargs.get("platform", "facebook")
        topic = kwargs.get("topic", "software innovation")
        payload = self._build_payload(platform, topic)
        latency = int((time.perf_counter() - start) * 1000)
        return GenerationResult(
            text=json.dumps(payload, indent=2),
            provider=self.name,
            model=self.model_name,
            latency_ms=latency,
            success=True,
        )

    def _build_payload(self, platform: str, topic: str) -> dict:
        base_hashtags = ["#Artixcore", "#SaaS", "#SoftwareDevelopment", "#TechInnovation"]
        if platform == "facebook":
            return {
                "content": (
                    f"At Artixcore, we help modern businesses turn ideas into reliable software. "
                    f"Thinking about {topic}? Let's explore how the right platform can scale "
                    f"your operations without unnecessary complexity. Book a consultation with "
                    f"our team and start your software journey with confidence."
                ),
                "hashtags": base_hashtags[:5],
                "image_prompt": None,
                "quality_notes": "Mock content generated. Friendly business tone with clear CTA.",
            }
        if platform == "instagram":
            return {
                "content": (
                    f"Build smarter. Ship faster. 🚀\n\n"
                    f"{topic} starts with the right foundation — and Artixcore helps you get there.\n\n"
                    f"Ready to build your next product?"
                ),
                "hashtags": base_hashtags
                + ["#StartupLife", "#BuildInPublic", "#DigitalTransformation", "#Founders"],
                "image_prompt": (
                    f"Minimal tech workspace scene showing a founder reviewing a dashboard about "
                    f"{topic}, Artixcore brand colors, clean modern aesthetic."
                ),
                "quality_notes": "Mock content generated. Visual tone with image prompt included.",
            }
        if platform == "linkedin":
            return {
                "content": (
                    f"Most teams don't fail because of bad ideas — they fail because software "
                    f"doesn't keep up with growth.\n\n"
                    f"If you're evaluating {topic}, focus on architecture, automation, and "
                    f"long-term maintainability.\n\n"
                    f"Artixcore partners with founders and SMEs to build SaaS platforms, AI "
                    f"systems, and business software that scale.\n\n"
                    f"What's the biggest bottleneck in your product roadmap right now?"
                ),
                "hashtags": ["#Artixcore", "#B2B", "#SaaS", "#SoftwareEngineering"],
                "image_prompt": None,
                "quality_notes": "Mock content generated. Professional B2B hook with insight.",
            }
        if platform == "twitter":
            content = (
                f"Great products aren't built overnight — they're built with the right stack, "
                f"clear priorities, and a team that ships. Artixcore helps you do exactly that "
                f"for {topic}. 🚀"
            )
            if len(content) > 280:
                content = content[:277] + "..."
            return {
                "content": content,
                "hashtags": ["#Artixcore", "#BuildBetter"],
                "image_prompt": None,
                "quality_notes": "Mock content generated. Under 280 characters.",
            }
        if platform == "website_blog":
            slug = topic.lower().replace(" ", "-")[:60]
            article = {
                "seo_title": f"{topic.title()} for Modern Businesses | Artixcore",
                "meta_description": (
                    f"Learn how Artixcore helps companies approach {topic} with scalable "
                    f"software, automation, and founder-led engineering expertise."
                ),
                "slug": slug,
                "outline": [
                    "Introduction: Why this topic matters now",
                    "Common challenges for growing teams",
                    "How Artixcore approaches the solution",
                    "Practical steps to get started",
                    "CTA: Book a consultation",
                ],
                "article": (
                    f"## Introduction\n\n"
                    f"In today's competitive market, {topic} is no longer optional for "
                    f"businesses that want to scale efficiently.\n\n"
                    f"## The Challenge\n\n"
                    f"Many teams struggle with fragmented tools, manual workflows, and "
                    f"software that can't grow with them.\n\n"
                    f"## The Artixcore Approach\n\n"
                    f"Artixcore builds SaaS platforms, AI systems, and custom business software "
                    f"designed for reliability and long-term value.\n\n"
                    f"## Next Steps\n\n"
                    f"Ready to explore your options? Visit Artixcore and book a consultation "
                    f"to start your software journey."
                ),
                "cta_section": (
                    "Build your next product with Artixcore. Book a consultation today."
                ),
            }
            return {
                "content": json.dumps(article),
                "hashtags": [],
                "image_prompt": f"Hero image for blog post about {topic}, professional tech brand style.",
                "quality_notes": "Mock blog content with SEO fields embedded in content JSON.",
            }
        return {
            "content": f"Artixcore content about {topic}.",
            "hashtags": base_hashtags[:3],
            "image_prompt": None,
            "quality_notes": "Mock fallback content.",
        }
