# ────────────────────────────────────────────────────────────────────────────────────────
#   flatten/__init__.py
#   ────────────────────
#
#   Flatten subcommand - flatten submodules into main repository.
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

from .rewriter import collect_submodules_from_gitmodules
from .rewriter import flatten_repository
from .run import run

__all__ = [
    "run",
    "flatten_repository",
    "collect_submodules_from_gitmodules",
]
