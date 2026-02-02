"""Utility functions for the Nspec TUI."""

from __future__ import annotations

import re
import unicodedata

from nspec.statuses import (
    get_all_status_emojis,
    get_status_emoji_fallback,
    get_status_emoji_pattern,
)


def get_display_width(text: str) -> int:
    """Calculate actual terminal display width accounting for wide chars."""
    ansi_pattern = re.compile(r"\033\[[0-9;]*m")
    clean_text = ansi_pattern.sub("", text)

    width = 0
    for char in clean_text:
        if unicodedata.east_asian_width(char) in ("F", "W"):
            width += 2
        else:
            width += 1
    return width


def clean_title(title: str) -> str:
    """Remove redundant prefixes and clean title."""
    title = re.sub(r"^Spec\s+\d+[a-z]?:\s+", "", title)
    title = re.sub(r"^FR-\d+[a-z]?:\s+", "", title, flags=re.IGNORECASE)
    title = re.sub(r"^Feature Request:\s+", "", title, flags=re.IGNORECASE)
    title = re.sub(rf"[{get_all_status_emojis()}]", "", title)
    return title.strip()


def extract_emoji_and_text(status: str) -> tuple[str, str]:
    """Extract emoji and text from status string."""
    match = re.match(get_status_emoji_pattern(), status)
    if match:
        emoji = match.group(1)
        text = status[len(match.group(0)) :].strip()
        return emoji, text
    return "", status.strip()


def format_status(status: str, verbose: bool = False) -> str:
    """Format status with emoji prefix."""
    emoji, text = extract_emoji_and_text(status)

    if not emoji:
        status_clean = text.replace("in progress", "active").replace("in-progress", "active")
        fallback = get_status_emoji_fallback()
        emoji = fallback.get(status_clean.lower(), "")
        text = status_clean

    if not verbose:
        return emoji if emoji else text

    return f"{emoji} {text}" if emoji else text
