# ────────────────────────────────────────────────────────────────────────────────────────
#   config.py
#   ─────────
#
#   Configuration loading and types for the sanitise subcommand.
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

import json
from typing import TYPE_CHECKING
from typing import TypedDict

if TYPE_CHECKING:
    from pathlib import Path

# ────────────────────────────────────────────────────────────────────────────────────────
#   Types
# ────────────────────────────────────────────────────────────────────────────────────────


# ────────────────────────────────────────────────────────────────────────────────────────
class SanitiseConfig(TypedDict, total=False):
    """Configuration for repository sanitisation."""

    words: list[str]
    word_mapping: dict[str, str]
    email_mapping: dict[str, str]
    exclude_files: list[str]


# ────────────────────────────────────────────────────────────────────────────────────────
#   Functions
# ────────────────────────────────────────────────────────────────────────────────────────


# ────────────────────────────────────────────────────────────────────────────────────────
def load_config(filepath: str | Path) -> SanitiseConfig:
    """Load sanitise configuration from a JSON file."""
    with open(filepath, encoding="utf-8") as f:
        data = json.load(f)

    config: SanitiseConfig = {}

    if "words" in data and isinstance(data["words"], list):
        config["words"] = [str(w) for w in data["words"] if w]

    if "word_mapping" in data and isinstance(data["word_mapping"], dict):
        config["word_mapping"] = {k.lower(): v for k, v in data["word_mapping"].items()}

    if "email_mapping" in data and isinstance(data["email_mapping"], dict):
        config["email_mapping"] = {
            k.lower(): v for k, v in data["email_mapping"].items()
        }

    if "exclude_files" in data and isinstance(data["exclude_files"], list):
        config["exclude_files"] = data["exclude_files"]

    return config


# ────────────────────────────────────────────────────────────────────────────────────────
def load_submodule_mapping(filepath: str | Path) -> dict[str, str]:
    """
    Load submodule commit mapping from a file.

    Format: old_sha new_sha (one per line)
    """
    mapping: dict[str, str] = {}
    with open(filepath, encoding="utf-8") as f:
        for line in f:
            line = line.strip()
            if not line:
                continue
            parts = line.split()
            if len(parts) >= 2:
                old_sha = parts[0].strip()
                new_sha = parts[1].strip()
                if old_sha and new_sha:
                    mapping[old_sha] = new_sha
    return mapping
