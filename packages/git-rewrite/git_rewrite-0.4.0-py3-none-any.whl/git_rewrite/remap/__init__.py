# ────────────────────────────────────────────────────────────────────────────────────────
#   remap/__init__.py
#   ──────────────────
#
#   Remap subcommand - remap submodule commit references.
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

from .remapper import remap_repository
from .run import run

__all__ = ["run", "remap_repository"]
