# ────────────────────────────────────────────────────────────────────────────────────────
#   common/__init__.py
#   ───────────────────
#
#   Common utilities for git-rewrite.
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

from .config import BLOB_MODE
from .config import EXEC_MODE
from .config import GITLINK_MODE
from .config import TREE_MODE
from .config import CommitInfo
from .config import SubmoduleInfo
from .config import TreeEntry
from .repo import clone_repo
from .repo import commit_tree
from .repo import copy_remotes
from .repo import get_all_branches
from .repo import get_all_commits
from .repo import get_all_tags
from .repo import get_branch_commit
from .repo import get_commit_info
from .repo import get_gitmodules_at_commit
from .repo import get_remotes
from .repo import get_tag_commit
from .repo import get_tree_sha
from .repo import git
from .repo import git_bytes
from .repo import hash_object
from .repo import init_repo
from .repo import ls_tree
from .repo import mktree
from .repo import object_exists
from .repo import parse_gitmodules
from .repo import read_blob
from .repo import update_ref
from .stream import COMMIT_PATTERN
from .stream import D_PATTERN
from .stream import FROM_PATTERN
from .stream import M_PATTERN
from .stream import MARK_PATTERN
from .stream import MERGE_PATTERN
from .stream import checkout_default_branch
from .stream import create_stream_writer
from .stream import finalise_stream
from .stream import start_fast_export
from .stream import start_fast_import

__all__ = [
    # config
    "GITLINK_MODE",
    "TREE_MODE",
    "BLOB_MODE",
    "EXEC_MODE",
    "SubmoduleInfo",
    "CommitInfo",
    "TreeEntry",
    # repo
    "git",
    "git_bytes",
    "init_repo",
    "clone_repo",
    "get_all_branches",
    "get_all_tags",
    "get_tag_commit",
    "get_all_commits",
    "get_commit_info",
    "get_branch_commit",
    "ls_tree",
    "read_blob",
    "get_tree_sha",
    "mktree",
    "hash_object",
    "commit_tree",
    "update_ref",
    "get_gitmodules_at_commit",
    "parse_gitmodules",
    "object_exists",
    "get_remotes",
    "copy_remotes",
    # stream
    "MARK_PATTERN",
    "COMMIT_PATTERN",
    "FROM_PATTERN",
    "MERGE_PATTERN",
    "M_PATTERN",
    "D_PATTERN",
    "start_fast_export",
    "start_fast_import",
    "create_stream_writer",
    "finalise_stream",
    "checkout_default_branch",
]
