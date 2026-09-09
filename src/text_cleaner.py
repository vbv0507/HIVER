"""
Text cleaning module for customer support tweets.

Preserves customer tone, urgency cues, punctuation, and emojis while
removing targeted brand handle @mentions, URLs, and noisy Twitter encoding artifacts.
"""

import html
import re
import unicodedata
from typing import Optional

# Regex pattern for matching URLs
URL_PATTERN = re.compile(
    r"(?:https?://|www\.|t\.co/)[^\s]+",
    re.IGNORECASE,
)

# Regex pattern for anonymized Twitter user mentions (e.g., @115858)
ANONYMIZED_USER_MENTION_PATTERN = re.compile(r"@\d+\b")

# Regex pattern for excess whitespace
WHITESPACE_PATTERN = re.compile(r"[ \t]+")
MULTI_NEWLINE_PATTERN = re.compile(r"\n{2,}")


def clean_tweet_text(
    text: Optional[str],
    brand_handle: Optional[str] = None,
    remove_user_mentions: bool = False,
) -> str:
    """
    Clean tweet text while carefully preserving customer language and tone.

    Transformations applied:
    1. Unescape HTML entities (&amp; -> &, &lt; -> <, etc.).
    2. Normalize Unicode (NFKC) while removing zero-width/control characters.
    3. Remove URLs (http://, https://, www., t.co).
    4. Remove @mentions of the targeted brand handle (case-insensitive).
    5. Optionally remove anonymized numeric user mentions (@12345).
    6. Normalize whitespace, keeping line breaks and punctuation.
    7. PRESERVES emojis, casing (e.g., ALL CAPS frustration), and punctuation (e.g., "?!").

    Args:
        text: Raw tweet text string.
        brand_handle: Name of the brand handle to strip (e.g., 'AmazonHelp').
        remove_user_mentions: If True, also strips anonymized customer IDs (@115858).

    Returns:
        Cleaned text string.
    """
    if text is None or not isinstance(text, str):
        return ""

    # 1. Unescape HTML entities
    cleaned = html.unescape(text)

    # 2. Normalize Unicode to NFKC
    cleaned = unicodedata.normalize("NFKC", cleaned)

    # 3. Strip URLs
    cleaned = URL_PATTERN.sub("", cleaned)

    # 4. Remove brand handle @mentions
    if brand_handle:
        # Strip leading @ if provided in brand_handle
        clean_handle = brand_handle.lstrip("@")
        # Match @brand, case-insensitive, with optional following colon/comma
        brand_pattern = re.compile(rf"@{re.escape(clean_handle)}\b:?", re.IGNORECASE)
        cleaned = brand_pattern.sub("", cleaned)

    # 5. Optionally remove anonymized user mentions (@115858)
    if remove_user_mentions:
        cleaned = ANONYMIZED_USER_MENTION_PATTERN.sub("", cleaned)

    # 6. Remove non-printable control characters (exclude newline and tab)
    cleaned = "".join(
        ch for ch in cleaned
        if unicodedata.category(ch)[0] != "C" or ch in ("\n", "\t")
    )

    # 7. Normalize excess horizontal spaces
    cleaned = WHITESPACE_PATTERN.sub(" ", cleaned)
    # Collapse 3+ newlines to max 2
    cleaned = MULTI_NEWLINE_PATTERN.sub("\n\n", cleaned)

    # Strip leading/trailing whitespace
    return cleaned.strip()


def clean_text_for_brand(text: str, brand: str) -> str:
    """Convenience helper for cleaning text against a specific brand."""
    return clean_tweet_text(text, brand_handle=brand, remove_user_mentions=False)
