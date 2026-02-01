# ==============================================================================
# Catalyst SDK - Main Entry Point
# ==============================================================================

from typing import Optional

from .services import (
    execute_search,
    extract_profiles,
    find_email,
    generate_dorks,
    generate_email,
    generate_personalized_message,
    generate_search_strategy,
    init_gemini,
    init_hunter,
    init_serpapi,
)
from .types import (
    CatalystConfig,
    ExtractedProfile,
    GeneratedDorks,
    GeneratedEmail,
    HunterEmailResult,
    Platform,
    ProspectInfo,
    SearchStrategy,
    SerpResult,
)


def init_catalyst(config: CatalystConfig) -> None:
    """
    Initialize the Catalyst SDK with your API keys.

    Example:
        >>> from catalyst import init_catalyst, generate_dorks, execute_search
        >>>
        >>> init_catalyst(CatalystConfig(
        ...     gemini_api_key="your-gemini-api-key",
        ...     serp_api_key="your-serpapi-key",      # optional
        ...     hunter_api_key="your-hunter-api-key", # optional
        ... ))
        >>>
        >>> # Generate Google dorks for finding prospects
        >>> dorks = await generate_dorks("software engineers at Google", [Platform.LINKEDIN])
        >>> print(dorks.linkedin)  # site:linkedin.com/in/ "software engineer" "google"
    """
    if not config.gemini_api_key:
        raise ValueError("gemini_api_key is required")

    # Initialize Gemini (required)
    init_gemini(config.gemini_api_key, config.model)

    # Initialize optional services
    if config.serp_api_key:
        init_serpapi(config.serp_api_key)

    if config.hunter_api_key:
        init_hunter(config.hunter_api_key)


class Catalyst:
    """
    Catalyst class for object-oriented usage.

    Example:
        >>> from catalyst import Catalyst, CatalystConfig
        >>>
        >>> catalyst = Catalyst(CatalystConfig(
        ...     gemini_api_key="your-gemini-key",
        ...     serp_api_key="your-serpapi-key",
        ... ))
        >>>
        >>> prospects = await catalyst.find_prospects("YC founders", 5)
    """

    def __init__(self, config: CatalystConfig):
        init_catalyst(config)

    async def find_prospects(
        self,
        query: str,
        target_count: int = 5,
    ) -> list[ExtractedProfile]:
        """Full pipeline: Generate dorks -> Search -> Extract profiles."""
        # 1. Get AI-recommended platforms
        strategy = await generate_search_strategy(query)
        print(f"[Catalyst] Strategy: {strategy.reasoning}")

        # 2. Generate dorks
        dorks = await generate_dorks(query, strategy.platforms)
        platform_names = [p.value for p in strategy.platforms if getattr(dorks, p.value)]
        print(f"[Catalyst] Generated dorks for: {', '.join(platform_names)}")

        # 3. Search and extract
        all_profiles: list[ExtractedProfile] = []

        for platform in strategy.platforms:
            dork = getattr(dorks, platform.value, None)
            if not dork:
                continue

            try:
                results = await execute_search(dork, 20)
                if results:
                    profiles = await extract_profiles(results, platform, target_count)
                    all_profiles.extend(profiles)
                    print(f"[Catalyst] Found {len(profiles)} profiles on {platform.value}")

                    if len(all_profiles) >= target_count:
                        break
            except Exception as e:
                print(f"[Catalyst] Search failed for {platform.value}: {e}")

        # Deduplicate and limit
        seen_urls = set()
        unique = []
        for profile in all_profiles:
            if profile.profile_url not in seen_urls:
                seen_urls.add(profile.profile_url)
                unique.append(profile)
                if len(unique) >= target_count:
                    break

        return unique

    async def generate_message(
        self,
        about_me: str,
        prospect: ProspectInfo,
    ) -> str:
        """Generate personalized outreach message for a prospect."""
        return await generate_personalized_message(about_me, prospect)

    async def generate_email(
        self,
        about_me: str,
        prospect: ProspectInfo,
    ) -> GeneratedEmail:
        """Generate personalized email for a prospect."""
        if not prospect.email:
            raise ValueError("Prospect must have an email")
        return await generate_email(about_me, prospect)

    async def find_email(
        self,
        domain: str,
        first_name: str,
        last_name: str,
    ) -> Optional[HunterEmailResult]:
        """Find email for a prospect using Hunter.io."""
        return await find_email(domain, first_name, last_name)


# Re-export everything
__all__ = [
    # Main
    "init_catalyst",
    "Catalyst",
    # Types
    "CatalystConfig",
    "Platform",
    "GeneratedDorks",
    "SearchStrategy",
    "SerpResult",
    "ExtractedProfile",
    "HunterEmailResult",
    "GeneratedEmail",
    "ProspectInfo",
    # Services (functional API)
    "generate_search_strategy",
    "generate_dorks",
    "execute_search",
    "extract_profiles",
    "generate_personalized_message",
    "generate_email",
    "find_email",
]
