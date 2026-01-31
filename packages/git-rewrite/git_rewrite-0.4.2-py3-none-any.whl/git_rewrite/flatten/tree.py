# ────────────────────────────────────────────────────────────────────────────────────────
#   tree.py
#   ───────
#
#   Tree manipulation and submodule expansion logic.
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

from pathlib import Path
from typing import TYPE_CHECKING
from ..common import GITLINK_MODE
from ..common import TREE_MODE
from ..common import get_gitmodules_at_commit
from ..common import get_tree_sha
from ..common import hash_object
from ..common import ls_tree
from ..common import mktree
from ..common import object_exists
from ..common import read_blob

if TYPE_CHECKING:
    from ..common import SubmoduleInfo
    from ..common import TreeEntry

# ────────────────────────────────────────────────────────────────────────────────────────
#   Types
# ────────────────────────────────────────────────────────────────────────────────────────

SubmoduleRepos = dict[str, Path]

# ────────────────────────────────────────────────────────────────────────────────────────
#   Tree Expansion
# ────────────────────────────────────────────────────────────────────────────────────────


def expand_tree(
    source_repo: Path,
    output_repo: Path,
    tree_sha: str,
    submodule_info: dict[str, SubmoduleInfo],
    submodule_repos: SubmoduleRepos,
    current_path: str = "",
    verbose: bool = False,
) -> str:
    """
    Recursively expand a tree, replacing submodule gitlinks with actual content.

    Args:
        source_repo: Path to the source repository
        output_repo: Path to the output repository (where we create new objects)
        tree_sha: SHA of the tree to expand
        submodule_info: Submodule configuration from .gitmodules
        submodule_repos: Mapping of submodule paths to their cloned repository paths
        current_path: Current path within the tree (for nested submodules)
        verbose: Whether to print verbose output

    Returns:
        SHA of the new expanded tree
    """
    entries = ls_tree(source_repo, tree_sha)
    new_entries: list[TreeEntry] = []

    for entry in entries:
        full_path = f"{current_path}/{entry['name']}" if current_path else entry["name"]

        if entry["mode"] == GITLINK_MODE:
            # This is a submodule - expand it
            new_entry = expand_submodule(
                output_repo=output_repo,
                submodule_path=full_path,
                submodule_commit=entry["sha"],
                submodule_info=submodule_info,
                submodule_repos=submodule_repos,
                verbose=verbose,
            )
            if new_entry:
                new_entries.append(new_entry)
            else:
                # Could not expand submodule, skip it
                if verbose:
                    print(f"  Warning: Could not expand submodule at {full_path}")

        elif entry["type"] == "tree":
            # Recurse into subdirectory
            expanded_sha = expand_tree(
                source_repo=source_repo,
                output_repo=output_repo,
                tree_sha=entry["sha"],
                submodule_info=submodule_info,
                submodule_repos=submodule_repos,
                current_path=full_path,
                verbose=verbose,
            )
            new_entries.append(
                {
                    "mode": entry["mode"],
                    "type": "tree",
                    "sha": expanded_sha,
                    "name": entry["name"],
                }
            )

        else:
            # Blob or other - copy to output repo
            copy_object(source_repo, output_repo, entry["sha"])
            new_entries.append(entry)

    return mktree(output_repo, new_entries)


# ────────────────────────────────────────────────────────────────────────────────────────
def expand_submodule(
    output_repo: Path,
    submodule_path: str,
    submodule_commit: str,
    submodule_info: dict[str, SubmoduleInfo],
    submodule_repos: SubmoduleRepos,
    verbose: bool = False,
) -> TreeEntry | None:
    """
    Expand a submodule by fetching its content at the specified commit.

    Returns a tree entry for the expanded submodule, or None if expansion fails.
    """
    if submodule_path not in submodule_repos:
        if verbose:
            print(f"  Submodule {submodule_path} not in cloned repos")
        return None

    submodule_repo = submodule_repos[submodule_path]

    # Check if the commit exists in the submodule repo
    if not object_exists(submodule_repo, submodule_commit):
        if verbose:
            print(f"  Commit {submodule_commit[:8]} not found in {submodule_path}")
        return None

    # Get the tree SHA for this commit in the submodule
    try:
        submodule_tree = get_tree_sha(submodule_repo, submodule_commit)
    except Exception:
        if verbose:
            print(f"  Could not get tree for {submodule_path}@{submodule_commit[:8]}")
        return None

    # Check if the submodule itself has submodules (nested submodules)
    nested_submodule_info = get_gitmodules_at_commit(submodule_repo, submodule_commit)

    # Get or create nested submodule repos if needed
    nested_submodule_repos: SubmoduleRepos = {}
    if nested_submodule_info:
        # For nested submodules, we need to resolve them relative to the parent submodule
        for nested_path in nested_submodule_info:
            full_nested_path = f"{submodule_path}/{nested_path}"
            if full_nested_path in submodule_repos:
                nested_submodule_repos[nested_path] = submodule_repos[full_nested_path]

    # Recursively expand the submodule's tree
    expanded_sha = expand_tree(
        source_repo=submodule_repo,
        output_repo=output_repo,
        tree_sha=submodule_tree,
        submodule_info=nested_submodule_info,
        submodule_repos=nested_submodule_repos,
        verbose=verbose,
    )

    return {
        "mode": TREE_MODE,
        "type": "tree",
        "sha": expanded_sha,
        "name": submodule_path.split("/")[-1],
    }


# ────────────────────────────────────────────────────────────────────────────────────────
def copy_object(source_repo: Path, output_repo: Path, sha: str) -> None:
    """Copy a git object from source to output repository if it doesn't exist."""
    if object_exists(output_repo, sha):
        return

    # Read object from source and write to output
    try:
        data = read_blob(source_repo, sha)
        hash_object(output_repo, data, "blob")
    except Exception:
        # Object might be a tree or commit, which we handle differently
        pass


# ────────────────────────────────────────────────────────────────────────────────────────
def copy_tree_objects(source_repo: Path, output_repo: Path, tree_sha: str) -> None:
    """Recursively copy all objects in a tree from source to output repository."""
    entries = ls_tree(source_repo, tree_sha)

    for entry in entries:
        if entry["type"] == "blob":
            copy_object(source_repo, output_repo, entry["sha"])
        elif entry["type"] == "tree":
            copy_tree_objects(source_repo, output_repo, entry["sha"])
