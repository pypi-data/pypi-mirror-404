# ────────────────────────────────────────────────────────────────────────────────────────
#   git-rewrite
#   ───────────
#
#   Git history rewriting tools.
#
#   Subcommands:
#   - scan: Scan for sensitive words (read-only)
#   - sanitise: Rewrite to remove sensitive words
#   - flatten: Flatten submodules into repository
#   - remap: Remap submodule commit references
#   - compose: Chain multiple commit mapping files
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
#   Version
# ────────────────────────────────────────────────────────────────────────────────────────

from .version import VERSION_STR

__version__ = VERSION_STR
__all__ = ["__version__"]
