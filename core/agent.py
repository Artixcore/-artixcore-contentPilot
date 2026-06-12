"""ContentPilot AI agent for post and campaign generation."""

import logging

from sqlalchemy.orm import Session

from core.database import get_brand_profile
from core.models import PLATFORMS, Campaign, Post
from core.router import ProviderRouter
from core.schemas import CampaignIdeas, GeneratedPost
from core.utils import (
    get_platform_rules,
    hashtags_to_json,
    load_prompt,
    parse_json_response,
)

logger = logging.getLogger(__name__)


class AgentValidationError(Exception):
    """User-facing validation error."""

    def __init__(self, message: str):
        super().__init__(message)
        self.message = message


class ContentPilotAgent:
    def __init__(self, session: Session):
        self.session = session
        self.router = ProviderRouter(session=session)

    def generate_post(
        self,
        platform: str,
        topic: str,
        goal: str,
        tone: str,
        language: str,
        cta: str,
        provider_mode: str = "auto",
        selected_provider: str | None = None,
    ) -> GeneratedPost:
        platform = (platform or "").strip().lower()
        topic = (topic or "").strip()

        if not topic:
            raise AgentValidationError("Topic is required. Please enter a topic for your post.")
        if platform not in PLATFORMS:
            raise AgentValidationError(
                f"Unsupported platform: {platform}. "
                f"Supported: {', '.join(PLATFORMS)}"
            )

        brand = get_brand_profile(self.session)
        if not brand:
            raise AgentValidationError(
                "Brand profile not found. Please configure brand settings first."
            )

        system_prompt = self._build_system_prompt(brand)
        user_prompt = self._build_generation_prompt(
            platform=platform,
            topic=topic,
            goal=goal,
            tone=tone or brand.tone,
            language=language or "English",
            cta=cta or brand.preferred_cta,
            brand=brand,
        )

        result = self.router.generate(
            prompt=user_prompt,
            system_prompt=system_prompt,
            mode=provider_mode,
            selected_provider=selected_provider,
            task_type="generate_post",
            platform=platform,
            topic=topic,
        )

        parsed = parse_json_response(result.text)
        if parsed:
            content = str(parsed.get("content", ""))
            hashtags = parsed.get("hashtags") or []
            if not isinstance(hashtags, list):
                hashtags = []
            hashtags = [str(h).lstrip("#") for h in hashtags]
            image_prompt = parsed.get("image_prompt")
            quality_notes = parsed.get("quality_notes")
        else:
            content = result.text
            hashtags = []
            image_prompt = None
            quality_notes = "Response was not valid JSON; raw content saved for review."

        quality_notes = self._run_quality_check(
            content=content,
            platform=platform,
            existing_notes=quality_notes,
            provider_mode=provider_mode,
            selected_provider=selected_provider,
        )

        post = Post(
            platform=platform,
            topic=topic,
            goal=goal or "",
            tone=tone or brand.tone,
            language=language or "English",
            cta=cta or brand.preferred_cta,
            content=content,
            hashtags=hashtags_to_json(hashtags),
            image_prompt=image_prompt,
            status="pending_approval",
            provider_used=result.provider,
            model_used=result.model,
            quality_notes=quality_notes,
        )
        self.session.add(post)
        self.session.commit()
        self.session.refresh(post)

        return GeneratedPost(
            content=content,
            hashtags=hashtags,
            image_prompt=image_prompt,
            quality_notes=quality_notes,
            provider_used=result.provider,
            model_used=result.model,
            post_id=post.id,
            platform=platform,
            topic=topic,
            saved=True,
        )

    def generate_campaign_ideas(self, campaign_id: int) -> CampaignIdeas:
        campaign = self.session.get(Campaign, campaign_id)
        if not campaign:
            raise AgentValidationError(f"Campaign {campaign_id} not found.")

        brand = get_brand_profile(self.session)
        system_prompt = self._build_system_prompt(brand) if brand else load_prompt("brand_voice.md")
        planner = load_prompt("campaign_planner.md")
        from core.utils import platforms_from_json

        platforms = platforms_from_json(campaign.platforms)
        user_prompt = (
            f"{planner}\n\n"
            f"Campaign Name: {campaign.name}\n"
            f"Goal: {campaign.goal}\n"
            f"Description: {campaign.description}\n"
            f"Platforms: {', '.join(platforms)}\n"
            f"Posts per week: {campaign.posts_per_week}\n"
        )

        result = self.router.generate(
            prompt=user_prompt,
            system_prompt=system_prompt,
            mode="auto",
            task_type="campaign_planner",
        )

        parsed = parse_json_response(result.text)
        ideas = []
        topics = []
        if parsed:
            ideas = parsed.get("ideas") or []
            topics = parsed.get("topics") or []
            if not isinstance(ideas, list):
                ideas = [str(ideas)]
            if not isinstance(topics, list):
                topics = [str(topics)]
            ideas = [str(i) for i in ideas]
            topics = [str(t) for t in topics]
        else:
            ideas = ["Review campaign goal and define 3 content pillars"]
            topics = [f"Content idea for {campaign.name}"]

        return CampaignIdeas(
            ideas=ideas,
            topics=topics,
            provider_used=result.provider,
            model_used=result.model,
        )

    def _build_system_prompt(self, brand) -> str:
        voice = load_prompt("brand_voice.md")
        return (
            f"{voice}\n\n"
            f"## Current Brand Profile\n\n"
            f"- Company: {brand.company_name}\n"
            f"- Page: {brand.page_name}\n"
            f"- Website: {brand.website_url}\n"
            f"- Description: {brand.description}\n"
            f"- Tone: {brand.tone}\n"
            f"- Target Audience: {brand.target_audience}\n"
            f"- Services: {brand.services}\n"
            f"- Preferred CTA: {brand.preferred_cta}\n"
            f"- Forbidden Style: {brand.forbidden_style}\n"
        )

    def _build_generation_prompt(
        self,
        platform: str,
        topic: str,
        goal: str,
        tone: str,
        language: str,
        cta: str,
        brand,
    ) -> str:
        generator = load_prompt("post_generator.md")
        rules = get_platform_rules(platform)
        return (
            f"{generator}\n\n"
            f"## Request\n\n"
            f"- Platform: {platform}\n"
            f"- Topic: {topic}\n"
            f"- Goal: {goal}\n"
            f"- Tone: {tone}\n"
            f"- Language: {language}\n"
            f"- CTA: {cta}\n"
            f"- Platform Rules: {rules}\n"
            f"- Company: {brand.company_name}\n"
            f"- Website: {brand.website_url}\n"
        )

    def _run_quality_check(
        self,
        content: str,
        platform: str,
        existing_notes: str | None,
        provider_mode: str,
        selected_provider: str | None,
    ) -> str:
        issues = []
        if not content or len(content.strip()) < 10:
            issues.append("Content is very short or empty.")
        if platform == "twitter" and len(content) > 280:
            issues.append("Twitter content exceeds 280 characters.")
        spam_words = ["guaranteed", "100% success", "get rich", "limited time only!!!"]
        lower = content.lower()
        for word in spam_words:
            if word in lower:
                issues.append(f"Potentially overpromising phrase detected: '{word}'")

        rule_notes = "; ".join(issues) if issues else "Passes basic rule-based quality check."
        combined = rule_notes
        if existing_notes:
            combined = f"{existing_notes} | {rule_notes}"

        if provider_mode == "budget" or (selected_provider == "mock"):
            return combined

        checker = load_prompt("quality_checker.md")
        check_prompt = (
            f"{checker}\n\nPlatform: {platform}\n\nContent:\n{content[:3000]}"
        )
        try:
            result = self.router.generate(
                prompt=check_prompt,
                system_prompt="You are a concise content quality reviewer for Artixcore.",
                mode="budget",
                task_type="quality_check",
            )
            if result.text and result.provider == "mock":
                return combined
            if result.text:
                return f"{combined} | Review: {result.text[:500]}"
        except Exception as exc:
            logger.warning("Quality check skipped: %s", type(exc).__name__)

        return combined
