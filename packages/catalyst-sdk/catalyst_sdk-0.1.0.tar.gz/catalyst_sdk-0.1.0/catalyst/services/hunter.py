# ==============================================================================
# Hunter.io Service - Email Finding
# ==============================================================================

import re
from typing import Optional
from urllib.parse import urlparse

import httpx

from ..types import HunterEmailResult

_api_key: Optional[str] = None


def init_hunter(api_key: str) -> None:
    """Initialize the Hunter service with API key."""
    global _api_key
    _api_key = api_key


def _get_api_key() -> str:
    """Get the API key (raises if not initialized)."""
    if _api_key is None:
        raise RuntimeError("Hunter not initialized. Call init_hunter(api_key) first.")
    return _api_key


async def find_email(
    domain: str,
    first_name: str,
    last_name: str,
) -> Optional[HunterEmailResult]:
    """Find email using Hunter.io Email Finder API."""
    api_key = _get_api_key()

    params = {
        "domain": domain,
        "first_name": first_name,
        "last_name": last_name,
        "api_key": api_key,
    }

    try:
        print(f"[Hunter] Requesting: {domain} | {first_name} {last_name}")
        
        async with httpx.AsyncClient() as client:
            response = await client.get(
                "https://api.hunter.io/v2/email-finder",
                params=params,
            )
            data = response.json()

        if "errors" in data and data["errors"]:
            print(f"[Hunter] Error Response: {data['errors']}")
            return None

        if not data.get("data", {}).get("email"):
            print(f"[Hunter] No email found in response: {data}")
            return None

        result_data = data["data"]
        print(f"[Hunter] Found: {result_data['email']} (Score: {result_data['score']})")

        return HunterEmailResult(
            email=result_data["email"],
            score=result_data["score"],
            domain=result_data["domain"],
            first_name=result_data["first_name"],
            last_name=result_data["last_name"],
        )
    except Exception as e:
        print(f"[Hunter] Network/Fetch failed: {e}")
        return None


async def verify_email(email: str) -> Optional[dict]:
    """Verify an email address using Hunter.io."""
    api_key = _get_api_key()

    params = {
        "email": email,
        "api_key": api_key,
    }

    try:
        async with httpx.AsyncClient() as client:
            response = await client.get(
                "https://api.hunter.io/v2/email-verifier",
                params=params,
            )
            data = response.json()

        if "errors" in data:
            print(f"[Hunter] Verify error: {data['errors']}")
            return None

        return {
            "status": data.get("data", {}).get("status", "unknown"),
            "score": data.get("data", {}).get("score", 0),
        }
    except Exception as e:
        print(f"[Hunter] Verify failed: {e}")
        return None


def extract_domain(input_str: str) -> Optional[str]:
    """Extract domain from company name or profile URL."""
    try:
        parsed = urlparse(input_str)
        if parsed.netloc:
            return parsed.netloc.replace("www.", "")
    except Exception:
        pass

    # Not a URL, try to convert company name to domain
    cleaned = re.sub(r"[^a-z0-9]", "", input_str.lower()).strip()
    if cleaned:
        return f"{cleaned}.com"
    return None


def split_name(full_name: str) -> tuple[str, str]:
    """Split full name into first and last name."""
    parts = full_name.strip().split()

    if not parts:
        return "", ""

    if len(parts) == 1:
        return parts[0], ""

    return parts[0], " ".join(parts[1:])
