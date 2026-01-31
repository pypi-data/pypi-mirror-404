# ────────────────────────────────────────────────────────────────────────────────────────
#   config.py
#   ─────────
#
#   Shared configuration types and constants for git-rewrite.
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

from typing import TypedDict

# ────────────────────────────────────────────────────────────────────────────────────────
#   Constants
# ────────────────────────────────────────────────────────────────────────────────────────

GITLINK_MODE = "160000"
TREE_MODE = "040000"
BLOB_MODE = "100644"
EXEC_MODE = "100755"

# ────────────────────────────────────────────────────────────────────────────────────────
#   Types
# ────────────────────────────────────────────────────────────────────────────────────────


class SubmoduleInfo(TypedDict):
    """Information about a submodule from .gitmodules."""

    path: str
    url: str


class CommitInfo(TypedDict):
    """Information about a git commit."""

    tree: str
    parents: list[str]
    author_name: str
    author_email: str
    author_date: str
    committer_name: str
    committer_email: str
    committer_date: str
    message: str


class TreeEntry(TypedDict):
    """A single entry in a git tree."""

    mode: str
    type: str
    sha: str
    name: str
