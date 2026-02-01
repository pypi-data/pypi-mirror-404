# ==============================================================================
# Twitter Service - Username to Numeric ID Conversion
# ==============================================================================

import re
from typing import Optional
from urllib.parse import quote

import httpx


async def get_twitter_numeric_id(username: str) -> Optional[str]:
    """
    Convert Twitter username to numeric ID using TweeterID API.
    This is needed for DM deep links.
    """
    clean_username = username.replace("@", "").strip()

    if not clean_username:
        return None

    try:
        async with httpx.AsyncClient() as client:
            response = await client.post(
                "https://tweeterid.com/ajax.php",
                headers={"Content-Type": "application/x-www-form-urlencoded"},
                content=f"input={quote(clean_username)}",
            )
            text = response.text.strip()

        # Validate it's actually a number
        if re.match(r"^\d+$", text):
            return text

        return None
    except Exception as e:
        print(f"Failed to get Twitter numeric ID: {e}")
        return None


def generate_twitter_dm_link(numeric_id: str, message: str) -> str:
    """Generate Twitter DM deep link."""
    encoded_message = quote(message)
    return f"https://x.com/messages/compose?recipient_id={numeric_id}&text={encoded_message}"


def generate_twitter_profile_link(username: str) -> str:
    """Generate Twitter profile link."""
    clean_username = username.replace("@", "").strip()
    return f"https://x.com/{clean_username}"


def extract_twitter_username(url: str) -> Optional[str]:
    """Extract username from Twitter/X URL."""
    match = re.search(r"(?:twitter|x)\.com/([^/\?]+)", url)
    if match:
        username = match.group(1)
        excluded = ["home", "explore", "notifications", "messages", "search", "settings", "i"]
        if username.lower() not in excluded:
            return username
    return None
