# ────────────────────────────────────────────────────────────────────────────────────────
#   patterns.py
#   ───────────
#
#   Regex pattern building and text replacement for sanitisation.
#
#   (c) 2026 Cyber Assessment Labs — MIT License; see LICENSE in the project root.
#
#   Authors
#   ───────
#   bena (via Claude)
#
#   Version History
#   ───────────────
#   Jan 2026 - Created
# ────────────────────────────────────────────────────────────────────────────────────────

# ────────────────────────────────────────────────────────────────────────────────────────
#   Imports
# ────────────────────────────────────────────────────────────────────────────────────────

import re

# ────────────────────────────────────────────────────────────────────────────────────────
#   Functions
# ────────────────────────────────────────────────────────────────────────────────────────


# ────────────────────────────────────────────────────────────────────────────────────────
def build_combined_pattern(dirty_words: list[str]) -> re.Pattern[str]:
    """Build a single combined regex pattern for all dirty words."""
    escaped_words = [re.escape(word) for word in dirty_words]
    combined = r"\b(" + "|".join(escaped_words) + r")\b"
    return re.compile(combined, re.IGNORECASE)


# ────────────────────────────────────────────────────────────────────────────────────────
def build_replacement_func(
    dirty_words: list[str],
    word_mapping: dict[str, str],
    default_replacement: str = "REDACTED",
) -> tuple[re.Pattern[str], dict[str, str]]:
    """Build a combined regex pattern and mapping for replacements."""
    replacements: dict[str, str] = {}
    for word in dirty_words:
        lower_word = word.lower()
        if lower_word in word_mapping:
            replacements[lower_word] = word_mapping[lower_word]
        else:
            replacements[lower_word] = default_replacement

    escaped_words = [re.escape(word) for word in dirty_words]
    combined_pattern = r"\b(" + "|".join(escaped_words) + r")\b"
    pattern = re.compile(combined_pattern, re.IGNORECASE)

    return pattern, replacements


# ────────────────────────────────────────────────────────────────────────────────────────
def replace_in_text(
    text: str,
    pattern: re.Pattern[str],
    replacements: dict[str, str],
) -> str:
    """Replace all dirty words in text with their replacements."""

    def replace_match(match: re.Match[str]) -> str:
        matched_word = match.group(0)
        lower_word = matched_word.lower()
        replacement = replacements.get(lower_word, "REDACTED")

        if matched_word.isupper():
            return replacement.upper()
        elif matched_word[0].isupper() and len(matched_word) > 1:
            return replacement.capitalize()
        else:
            return replacement

    return pattern.sub(replace_match, text)


# ────────────────────────────────────────────────────────────────────────────────────────
def rewrite_author_line(
    line: str,
    pattern: re.Pattern[str],
    replacements: dict[str, str],
    email_mapping: dict[str, str],
) -> str:
    """Rewrite an author or committer line with name replacement and email lookup."""
    # Format: author Name <email> timestamp timezone
    # or: committer Name <email> timestamp timezone
    match = re.match(r"^(author|committer) (.+?) <([^>]*)> (.+)$", line)
    if not match:
        return replace_in_text(line, pattern, replacements)

    line_type = match.group(1)
    name = match.group(2)
    timestamp_tz = match.group(4)

    # Replace dirty words in the name
    new_name = replace_in_text(name, pattern, replacements)

    # Look up the email based on the new name
    name_lower = new_name.lower()
    if name_lower in email_mapping:
        new_email = email_mapping[name_lower]
    else:
        # Default to name@example.com (spaces replaced with dots)
        email_local = new_name.lower().replace(" ", ".")
        new_email = f"{email_local}@example.com"

    return f"{line_type} {new_name} <{new_email}> {timestamp_tz}"
