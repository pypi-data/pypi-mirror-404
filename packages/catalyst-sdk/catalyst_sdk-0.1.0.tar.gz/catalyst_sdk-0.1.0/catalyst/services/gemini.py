# ==============================================================================
# Gemini AI Service - Dork Generation & Message Personalization
# ==============================================================================

import json
import re
from typing import Optional

import google.generativeai as genai

from ..types import (
    ExtractedProfile,
    GeneratedDorks,
    GeneratedEmail,
    Platform,
    ProspectInfo,
    SearchStrategy,
    SerpResult,
)

_model = None


def init_gemini(api_key: str, model_name: str = "gemma-3-27b-it") -> None:
    """Initialize the Gemini service with API key."""
    global _model
    genai.configure(api_key=api_key)
    _model = genai.GenerativeModel(model_name)


def _get_model():
    """Get the initialized model (raises if not initialized)."""
    if _model is None:
        raise RuntimeError("Gemini not initialized. Call init_gemini(api_key) first.")
    return _model


async def generate_search_strategy(query: str) -> SearchStrategy:
    """Generate intelligent search strategy based on user query."""
    model = _get_model()

    prompt = f"""Plan a search strategy to find prospects for: "{query}"

Available platforms: linkedin, twitter, instagram, github, peerlist, dribbble, behance, medium, producthunt, threads, bluesky.

Determine the SINGLE BEST platform for this specific role/persona.
- Developers/Engineers -> LinkedIn (PRIORITIZED over GitHub for employment/professional outreach)
- Open Source Contributors -> GitHub
- Designers -> Dribbble or Behance
- Founders/VCs/Tech Twitter -> Twitter(X) or Bluesky
- Corporate/Enterprise/Sales -> LinkedIn
- Creators/Influencers -> Instagram or Threads
- Writers/Bloggers -> Medium
- Product people -> Product Hunt

Return ONLY valid JSON:
{{
  "platforms": ["single_best_platform"],
  "reasoning": "Brief explanation of why this is the best platform"
}}"""

    try:
        response = model.generate_content(prompt)
        text = response.text
        json_match = re.search(r"\{[\s\S]*\}", text)

        if not json_match:
            return SearchStrategy(
                platforms=[Platform.LINKEDIN, Platform.TWITTER],
                reasoning="AI failed to plan, using defaults.",
            )

        data = json.loads(json_match.group())
        platforms = [Platform(p) for p in data.get("platforms", ["linkedin", "twitter"])]
        return SearchStrategy(
            platforms=platforms,
            reasoning=data.get("reasoning", "Default strategy"),
        )
    except Exception as e:
        print(f"Failed to generate search strategy: {e}")
        return SearchStrategy(
            platforms=[Platform.LINKEDIN, Platform.TWITTER],
            reasoning="AI error, using defaults.",
        )


async def extract_company_domain(snippet: str) -> Optional[str]:
    """Extract company domain from a user's bio or snippet using AI."""
    model = _get_model()

    prompt = f"""Extract the official company website domain from this professional bio/snippet.
    
Snippet: "{snippet}"

Rules:
- Return ONLY the domain (e.g., "google.com", "stripe.com"). 
- If the person works at a university, return the university domain (e.g., "stanford.edu").
- If no company is clearly mentioned or implied, return "null" (string).
- Do not return full URLs (no https://).
- Return a single string.

Domain:"""

    try:
        response = model.generate_content(prompt)
        text = response.text.strip().lower()

        if text == "null" or "sorry" in text or len(text) < 4:
            return None

        clean_domain = re.sub(r"https?://", "", text).rstrip("/").split()[0]
        return clean_domain
    except Exception as e:
        print(f"Failed to extract domain via AI: {e}")
        return None


async def generate_dorks(query: str, platforms: list[Platform]) -> GeneratedDorks:
    """Generate Google Dorks for finding profiles based on user query."""
    model = _get_model()

    platform_names = ", ".join([p.value for p in platforms])

    prompt = f"""You are an expert at writing Google Dorks to find people's social media profiles.

User wants to find: "{query}"
Target Platforms: {platform_names}

Generate optimized Google Dork queries for ONLY the requested platforms.
The dorks should be sophisticated and find relevant profiles.

Examples:
- LinkedIn: site:linkedin.com/in/ "query keywords"
- Twitter: site:twitter.com OR site:x.com "query keywords" -"retweet"
- Dribbble: site:dribbble.com "query keywords"
- GitHub: site:github.com "query keywords"

Return ONLY valid JSON in this exact format:
{{
  "linkedin": "site:linkedin.com/in/ ...",
  "twitter": "site:twitter.com ...",
  ... (only for requested platforms)
}}"""

    response = model.generate_content(prompt)
    text = response.text

    json_match = re.search(r"\{[\s\S]*\}", text)
    if not json_match:
        raise ValueError("Failed to parse dorks from AI response")

    data = json.loads(json_match.group())
    return GeneratedDorks(**data)


async def extract_profiles(
    serp_results: list[SerpResult],
    platform: Platform,
    target_count: int,
) -> list[ExtractedProfile]:
    """Extract profiles from SERP results."""
    model = _get_model()

    results_json = json.dumps([r.model_dump() for r in serp_results], indent=2)

    prompt = f"""Analyze these search results and extract profile information.

Platform: {platform.value}
Target count: {target_count}

Search Results:
{results_json}

Extract real profiles (not company pages, not posts, only personal profiles).
For each profile, extract:
- profile_url: the exact URL
- username: extracted from URL
- full_name: if visible in title/snippet
- snippet: the search result snippet

Return ONLY valid JSON array, no other text:
[
  {{
    "platform": "{platform.value}",
    "profile_url": "...",
    "username": "...",
    "full_name": "...",
    "snippet": "..."
  }}
]

If no valid profiles found, return empty array: []"""

    response = model.generate_content(prompt)
    text = response.text

    json_match = re.search(r"\[[\s\S]*\]", text)
    if not json_match:
        return []

    try:
        data = json.loads(json_match.group())
        return [ExtractedProfile(**item) for item in data]
    except Exception:
        return []


async def generate_personalized_message(
    user_about_me: str,
    prospect: ProspectInfo,
) -> str:
    """Generate personalized outreach message - HYPER PERSONALIZED, NON-AI SOUNDING."""
    model = _get_model()

    prompt = f"""You are writing a personal outreach message on behalf of someone. Your goal is to write something that sounds GENUINELY HUMAN - like a real person texting someone they want to connect with.

=== ABOUT THE SENDER (WHO YOU'RE WRITING FOR) ===
{user_about_me}

=== ABOUT THE RECIPIENT (WHO THEY'RE REACHING OUT TO) ===
Name: {prospect.full_name or 'Unknown'}
Platform: {prospect.platform.value if prospect.platform else 'social'}  
What we know about them from their profile: "{prospect.snippet or 'No specific details available'}"

=== YOUR TASK ===
Write a SHORT, GENUINE outreach message (2-3 sentences MAXIMUM) that a real person would actually send to start a conversation.

=== CRITICAL RULES ===

❌ NEVER use these AI-sounding phrases:
- "I came across your profile"
- "I noticed your work/profile/experience"
- "I was impressed by"
- "I'd love to connect"
- "I believe we could"
- "Your innovative work"
- "Reaching out because"

✅ DO:
- Sound like a real human texting a friend-of-a-friend
- Reference something SPECIFIC about them (extract from the snippet)
- Be casual, warm, but not overly familiar
- Explain why you're reaching out in ONE short sentence
- End with a soft, non-pushy question or CTA
- Keep it under 280 characters total

Write ONLY the message. No quotes, no "Here's the message:", just the raw message text:"""

    response = model.generate_content(prompt)
    return response.text.strip().strip("\"'")


async def generate_email(
    user_about_me: str,
    prospect: ProspectInfo,
) -> GeneratedEmail:
    """Generate email subject and body - HYPER PERSONALIZED, NON-AI SOUNDING."""
    if not prospect.email:
        raise ValueError("Prospect must have an email")

    model = _get_model()

    prompt = f"""You are writing a cold outreach email on behalf of someone. Your goal is to write something that sounds GENUINELY HUMAN - like a real person would write, not a marketing template.

=== ABOUT THE SENDER (WHO YOU'RE WRITING FOR) ===
{user_about_me}

=== ABOUT THE RECIPIENT ===
Name: {prospect.full_name or 'Unknown'}
Email: {prospect.email}
What we know about them: "{prospect.snippet or 'No specific details available'}"

=== YOUR TASK ===
Write a SHORT, GENUINE cold outreach email that feels personal and human.

=== CRITICAL RULES FOR SUBJECT LINE ===
❌ NEVER use:
- "Quick question"
- "Opportunity"  
- "Introduction"
- Anything with "synergy", "collaboration"

✅ DO:
- Be specific and intriguing
- Reference something about THEM
- Keep it under 50 characters

=== CRITICAL RULES FOR BODY ===
❌ NEVER use:
- "I hope this email finds you well"
- "I came across your profile/work"
- "I was impressed by"
- "I'm reaching out because"
- leverage, synergy, innovative, cutting-edge, stellar

✅ DO:
- Get straight to the point (no fluff intro)
- Reference something SPECIFIC about them from the snippet
- Explain your ask in 1-2 sentences
- Keep total body under 100 words
- End with a simple, non-pushy CTA
- Sound like a real person, not a sales bot

Return ONLY valid JSON:
{{
  "subject": "your subject here",
  "body": "your email body here"
}}"""

    response = model.generate_content(prompt)
    text = response.text

    json_match = re.search(r"\{[\s\S]*\}", text)
    if not json_match:
        raise ValueError("Failed to generate email")

    data = json.loads(json_match.group())
    return GeneratedEmail(**data)


async def generate_followup_email(
    original_subject: str,
    original_body: str,
    prospect: ProspectInfo,
    followup_number: int,
) -> GeneratedEmail:
    """Generate follow-up email with context from original email."""
    model = _get_model()
    is_last_attempt = followup_number == 2

    prompt = f"""You are writing a follow-up email. The original email was sent but got no reply. Write a GENUINE, NON-PUSHY follow-up.

=== ORIGINAL EMAIL THAT WAS SENT ===
Subject: {original_subject}
Body: {original_body}

=== ABOUT THE RECIPIENT ===
Name: {prospect.full_name or 'Unknown'}
What we know: "{prospect.snippet or 'No details'}"

=== CONTEXT ===
This is follow-up #{followup_number}. {'This is the FINAL attempt - make it count but stay respectful.' if is_last_attempt else 'One more follow-up will be sent if no reply.'}

=== CRITICAL RULES ===
❌ NEVER:
- Start with "Just following up" or "Wanted to bump this"
- Say "I know you're busy"
- Be guilt-trippy or passive aggressive

✅ DO:
- Keep it VERY short (2-3 sentences MAX)
- Add NEW value or angle if possible
- Be casual and human
- {'Gracefully give them an easy out' if is_last_attempt else 'Show genuine interest'}

Return ONLY valid JSON:
{{
  "subject": "your subject here",
  "body": "your follow-up body here"
}}"""

    response = model.generate_content(prompt)
    text = response.text

    json_match = re.search(r"\{[\s\S]*\}", text)
    if not json_match:
        raise ValueError("Failed to generate follow-up email")

    data = json.loads(json_match.group())
    return GeneratedEmail(**data)
