"""Publisher registry."""

from publishers.base import BasePublisher
from publishers.linkedin_publisher import LinkedInPublisher
from publishers.meta_facebook_publisher import MetaFacebookPublisher
from publishers.meta_instagram_publisher import MetaInstagramPublisher
from publishers.website_publisher import WebsitePublisher
from publishers.x_publisher import XPublisher


def get_all_publishers() -> dict[str, BasePublisher]:
    return {
        "linkedin": LinkedInPublisher(),
        "twitter": XPublisher(),
        "facebook": MetaFacebookPublisher(),
        "instagram": MetaInstagramPublisher(),
        "website_blog": WebsitePublisher(),
    }
