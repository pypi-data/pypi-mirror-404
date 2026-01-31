# ────────────────────────────────────────────────────────────────────────────────────────
#   scan/__init__.py
#   ─────────────────
#
#   Scan subcommand - scan for sensitive words in git history.
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

from .run import run
from .scanner import scan_repository

__all__ = ["run", "scan_repository"]
