# ==============================================================================
# Catalyst SDK - Type Definitions
# ==============================================================================

from enum import Enum
from typing import Optional
from pydantic import BaseModel


class Platform(str, Enum):
    LINKEDIN = "linkedin"
    TWITTER = "twitter"
    INSTAGRAM = "instagram"
    GITHUB = "github"
    PEERLIST = "peerlist"
    DRIBBBLE = "dribbble"
    BEHANCE = "behance"
    MEDIUM = "medium"
    PRODUCTHUNT = "producthunt"
    THREADS = "threads"
    BLUESKY = "bluesky"


class CatalystConfig(BaseModel):
    gemini_api_key: str
    serp_api_key: Optional[str] = None
    hunter_api_key: Optional[str] = None
    model: str = "gemma-3-27b-it"


class GeneratedDorks(BaseModel):
    linkedin: Optional[str] = None
    twitter: Optional[str] = None
    instagram: Optional[str] = None
    github: Optional[str] = None
    peerlist: Optional[str] = None
    dribbble: Optional[str] = None
    behance: Optional[str] = None
    medium: Optional[str] = None
    producthunt: Optional[str] = None
    threads: Optional[str] = None
    bluesky: Optional[str] = None


class SearchStrategy(BaseModel):
    platforms: list[Platform]
    reasoning: str


class SerpResult(BaseModel):
    title: str
    link: str
    snippet: str
    position: int


class ExtractedProfile(BaseModel):
    platform: Platform
    profile_url: str
    username: str
    full_name: str
    snippet: str


class HunterEmailResult(BaseModel):
    email: str
    score: int
    domain: str
    first_name: str
    last_name: str


class GeneratedEmail(BaseModel):
    subject: str
    body: str


class ProspectInfo(BaseModel):
    full_name: Optional[str] = None
    platform: Optional[Platform] = None
    snippet: Optional[str] = None
    email: Optional[str] = None


class PlatformConfig(BaseModel):
    name: str
    icon: str
    supports_deeplink: bool
    deeplink_template: Optional[str] = None
    profile_url_pattern: str


PLATFORM_CONFIGS: dict[Platform, PlatformConfig] = {
    Platform.LINKEDIN: PlatformConfig(
        name="LinkedIn",
        icon="linkedin",
        supports_deeplink=False,
        profile_url_pattern=r"linkedin\.com/in/([^/\?]+)",
    ),
    Platform.TWITTER: PlatformConfig(
        name="Twitter/X",
        icon="twitter",
        supports_deeplink=True,
        deeplink_template="https://x.com/messages/compose?recipient_id={numeric_id}&text={message}",
        profile_url_pattern=r"(?:twitter|x)\.com/([^/\?]+)",
    ),
    Platform.INSTAGRAM: PlatformConfig(
        name="Instagram",
        icon="instagram",
        supports_deeplink=True,
        profile_url_pattern=r"instagram\.com/([^/\?]+)",
    ),
    Platform.GITHUB: PlatformConfig(
        name="GitHub",
        icon="github",
        supports_deeplink=False,
        profile_url_pattern=r"github\.com/([^/\?]+)",
    ),
    Platform.PEERLIST: PlatformConfig(
        name="Peerlist",
        icon="peerlist",
        supports_deeplink=False,
        profile_url_pattern=r"peerlist\.io/([^/\?]+)",
    ),
    Platform.DRIBBBLE: PlatformConfig(
        name="Dribbble",
        icon="dribbble",
        supports_deeplink=False,
        profile_url_pattern=r"dribbble\.com/([^/\?]+)",
    ),
    Platform.BEHANCE: PlatformConfig(
        name="Behance",
        icon="behance",
        supports_deeplink=False,
        profile_url_pattern=r"behance\.net/([^/\?]+)",
    ),
    Platform.MEDIUM: PlatformConfig(
        name="Medium",
        icon="medium",
        supports_deeplink=False,
        profile_url_pattern=r"medium\.com/@?([^/\?]+)",
    ),
    Platform.PRODUCTHUNT: PlatformConfig(
        name="Product Hunt",
        icon="producthunt",
        supports_deeplink=False,
        profile_url_pattern=r"producthunt\.com/@([^/\?]+)",
    ),
    Platform.THREADS: PlatformConfig(
        name="Threads",
        icon="threads",
        supports_deeplink=False,
        profile_url_pattern=r"threads\.net/@([^/\?]+)",
    ),
    Platform.BLUESKY: PlatformConfig(
        name="Bluesky",
        icon="bluesky",
        supports_deeplink=False,
        profile_url_pattern=r"bsky\.app/profile/([^/\?]+)",
    ),
}
