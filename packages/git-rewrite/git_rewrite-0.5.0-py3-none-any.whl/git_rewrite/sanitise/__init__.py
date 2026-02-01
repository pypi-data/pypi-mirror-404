# ────────────────────────────────────────────────────────────────────────────────────────
#   sanitise/__init__.py
#   ─────────────────────
#
#   Sanitise subcommand - rewrite history to remove sensitive words.
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

from .config import SanitiseConfig
from .config import load_config
from .config import load_submodule_mapping
from .patterns import build_combined_pattern
from .patterns import build_replacement_func
from .patterns import replace_in_text
from .patterns import rewrite_author_line
from .rewriter import rewrite_repository
from .run import run

__all__ = [
    "run",
    "SanitiseConfig",
    "load_config",
    "load_submodule_mapping",
    "build_combined_pattern",
    "build_replacement_func",
    "replace_in_text",
    "rewrite_author_line",
    "rewrite_repository",
]
