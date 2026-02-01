# ────────────────────────────────────────────────────────────────────────────────────────
#   stream.py
#   ─────────
#
#   Git fast-export/fast-import streaming utilities.
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
import subprocess
from typing import TYPE_CHECKING
from . import repo as git_repo

if TYPE_CHECKING:
    from collections.abc import Callable
    from pathlib import Path

# ────────────────────────────────────────────────────────────────────────────────────────
#   Constants - Regex patterns for fast-export stream parsing
# ────────────────────────────────────────────────────────────────────────────────────────

MARK_PATTERN = re.compile(r"^mark :(\d+)$")
COMMIT_PATTERN = re.compile(r"^commit (.+)$")
FROM_PATTERN = re.compile(r"^from :(\d+)$")
MERGE_PATTERN = re.compile(r"^merge :(\d+)$")
M_PATTERN = re.compile(r"^M (\d+) (?::(\d+)|([0-9a-f]{40})) (.+)$")
D_PATTERN = re.compile(r"^D (.+)$")

# ────────────────────────────────────────────────────────────────────────────────────────
#   Stream Functions
# ────────────────────────────────────────────────────────────────────────────────────────


# ────────────────────────────────────────────────────────────────────────────────────────
def start_fast_export(repo_path: Path) -> subprocess.Popen[bytes]:
    """Start git fast-export process."""
    return subprocess.Popen(
        [
            "git",
            "-C",
            str(repo_path),
            "fast-export",
            "--all",
            "--signed-tags=strip",
            "--tag-of-filtered-object=rewrite",
        ],
        stdout=subprocess.PIPE,
        stderr=subprocess.PIPE,
    )


# ────────────────────────────────────────────────────────────────────────────────────────
def start_fast_import(repo_path: Path) -> subprocess.Popen[bytes]:
    """Start git fast-import process."""
    return subprocess.Popen(
        ["git", "-C", str(repo_path), "fast-import", "--quiet"],
        stdin=subprocess.PIPE,
        stdout=subprocess.PIPE,
        stderr=subprocess.PIPE,
    )


# ────────────────────────────────────────────────────────────────────────────────────────
def create_stream_writer(
    import_proc: subprocess.Popen[bytes],
) -> Callable[[bytes], None]:
    """Create a safe writer function for fast-import stdin."""

    def write_import(data: bytes) -> None:
        assert import_proc.stdin is not None
        try:
            import_proc.stdin.write(data)
        except BrokenPipeError as e:
            import_proc.wait()
            stderr = import_proc.stderr.read().decode() if import_proc.stderr else ""
            raise RuntimeError(f"fast-import failed: {stderr}") from e

    return write_import


# ────────────────────────────────────────────────────────────────────────────────────────
def finalise_stream(
    export_proc: subprocess.Popen[bytes],
    import_proc: subprocess.Popen[bytes],
) -> None:
    """Close streams and check for errors."""
    if import_proc.stdin:
        import_proc.stdin.close()
    export_proc.wait()
    import_proc.wait()

    if export_proc.returncode != 0:
        stderr = export_proc.stderr.read().decode() if export_proc.stderr else ""
        raise RuntimeError(f"fast-export failed: {stderr}")

    if import_proc.returncode != 0:
        stderr = import_proc.stderr.read().decode() if import_proc.stderr else ""
        raise RuntimeError(f"fast-import failed: {stderr}")


# ────────────────────────────────────────────────────────────────────────────────────────
def checkout_default_branch(repo_path: Path) -> None:
    """Checkout the default branch after fast-import."""
    branches = git_repo.get_all_branches(repo_path)
    if branches:
        if "main" in branches:
            default_branch = "main"
        elif "master" in branches:
            default_branch = "master"
        else:
            default_branch = branches[0]
        git_repo.git(repo_path, "checkout", "-f", default_branch)
