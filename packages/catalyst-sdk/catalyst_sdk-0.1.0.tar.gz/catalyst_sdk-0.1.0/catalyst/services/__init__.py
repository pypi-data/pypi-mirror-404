# ==============================================================================
# Catalyst SDK - Services
# ==============================================================================

from .gemini import (
    extract_company_domain,
    extract_profiles,
    generate_dorks,
    generate_email,
    generate_followup_email,
    generate_personalized_message,
    generate_search_strategy,
    init_gemini,
)
from .hunter import (
    extract_domain,
    find_email,
    init_hunter,
    split_name,
    verify_email,
)
from .serpapi import (
    execute_multi_platform_search,
    execute_search,
    init_serpapi,
)
from .twitter import (
    extract_twitter_username,
    generate_twitter_dm_link,
    generate_twitter_profile_link,
    get_twitter_numeric_id,
)

__all__ = [
    # Gemini
    "init_gemini",
    "generate_search_strategy",
    "extract_company_domain",
    "generate_dorks",
    "extract_profiles",
    "generate_personalized_message",
    "generate_email",
    "generate_followup_email",
    # SerpAPI
    "init_serpapi",
    "execute_search",
    "execute_multi_platform_search",
    # Hunter
    "init_hunter",
    "find_email",
    "verify_email",
    "extract_domain",
    "split_name",
    # Twitter
    "get_twitter_numeric_id",
    "generate_twitter_dm_link",
    "generate_twitter_profile_link",
    "extract_twitter_username",
]
