# ────────────────────────────────────────────────────────────────────────────────────────
#   rewriter.py
#   ───────────
#
#   Fast history rewriting using git fast-export/fast-import to flatten submodules.
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

import subprocess
import tempfile
from pathlib import Path
from typing import TYPE_CHECKING
from ..common import GITLINK_MODE
from ..common import SubmoduleInfo
from ..common import clone_repo
from ..common import get_all_branches
from ..common import get_all_commits
from ..common import git
from ..common import init_repo
from ..common import object_exists
from ..common import read_blob
from ..common import repo as git_repo

if TYPE_CHECKING:
    from collections.abc import Callable

# ────────────────────────────────────────────────────────────────────────────────────────
#   Main Flatten Function
# ────────────────────────────────────────────────────────────────────────────────────────


def flatten_repository(
    source_repo: Path,
    output_repo: Path,
    mapping_file: Path,
    verbose: bool = False,
) -> dict[str, str]:
    """
    Rewrite repository history using fast-export/fast-import to flatten submodules.

    Returns a mapping of old commit SHAs to new commit SHAs.
    """
    print(f"Source: {source_repo}")
    print(f"Output: {output_repo}")

    # Initialise output repository
    print("Initialising output repository...")
    init_repo(output_repo)

    # Collect submodule info
    print("Scanning for submodules...")
    all_submodules = collect_submodules_from_gitmodules(source_repo)
    print(f"Found {len(all_submodules)} unique submodule paths")

    # Clone submodule repos if needed
    submodule_repos: dict[str, Path] = {}
    if all_submodules:
        print("Cloning submodule repositories...")
        submodule_repos = clone_submodules_fast(source_repo, all_submodules, verbose)

    # Export, transform, and import
    print("Exporting and transforming history...")
    commit_map = export_transform_import(
        source_repo, output_repo, submodule_repos, verbose
    )

    # Write mapping file (text format: old_sha new_sha per line)
    print(f"Writing mapping to {mapping_file}...")
    mapping_file.parent.mkdir(parents=True, exist_ok=True)
    with open(mapping_file, "w", encoding="utf-8") as f:
        for old_sha, new_sha in sorted(commit_map.items()):
            f.write(f"{old_sha} {new_sha}\n")

    print("Done!")
    return commit_map


# ────────────────────────────────────────────────────────────────────────────────────────
def collect_submodules_from_gitmodules(source_repo: Path) -> dict[str, SubmoduleInfo]:
    """Collect submodule info by finding all commits that touched .gitmodules."""
    all_submodules: dict[str, SubmoduleInfo] = {}

    # Find all commits that modified .gitmodules (much faster than checking every commit)
    try:
        output = git(source_repo, "log", "--all", "--format=%H", "--", ".gitmodules")
        commits_with_gitmodules = [
            line.strip() for line in output.strip().split("\n") if line.strip()
        ]
    except Exception:
        commits_with_gitmodules = []

    # Also check all branch tips in case .gitmodules exists but was never modified
    refs_to_check = ["HEAD"]
    refs_to_check.extend(get_all_branches(source_repo))
    for ref in refs_to_check:
        try:
            commit = git(source_repo, "rev-parse", ref).strip()
            if commit not in commits_with_gitmodules:
                commits_with_gitmodules.append(commit)
        except Exception:
            continue

    print(f"  Checking {len(commits_with_gitmodules)} commits with .gitmodules...")

    for commit in commits_with_gitmodules:
        try:
            submodules = git_repo.get_gitmodules_at_commit(source_repo, commit)
            for path, info in submodules.items():
                if path not in all_submodules:
                    all_submodules[path] = info
                    print(f"  Found submodule: {path} -> {info['url']}")
        except Exception:
            continue

    return all_submodules


# ────────────────────────────────────────────────────────────────────────────────────────
def clone_submodules_fast(
    source_repo: Path,
    submodules: dict[str, SubmoduleInfo],
    verbose: bool,
) -> dict[str, Path]:
    """Clone submodule repositories, or use existing checkouts if available."""
    submodule_repos: dict[str, Path] = {}
    temp_dir = Path(tempfile.mkdtemp(prefix="git-rewrite-flatten-"))

    for path, info in submodules.items():
        # First, check if submodule is already checked out in source repo
        existing_path = source_repo / path
        if existing_path.exists() and (existing_path / ".git").exists():
            print(f"  Using existing checkout: {path}")
            submodule_repos[path] = existing_path
            continue

        # Also check for .git file (submodule worktree reference)
        git_file = existing_path / ".git"
        if existing_path.exists() and git_file.exists():
            print(f"  Using existing checkout: {path}")
            submodule_repos[path] = existing_path
            continue

        # Try to clone
        clone_path = temp_dir / path.replace("/", "_")
        url = info["url"]

        # Resolve relative URLs against source repo's remote
        if url.startswith("../") or url.startswith("./"):
            url = resolve_relative_url(source_repo, url)
            if verbose:
                print(f"  Resolved URL: {url}")

        if verbose:
            print(f"  Cloning {path} from {url}...")
        else:
            print(f"  Cloning {path}...")

        try:
            clone_repo(url, clone_path)
            submodule_repos[path] = clone_path
        except Exception as e:
            print(f"  Warning: Failed to clone {path}: {e}")
            print(f"    URL: {url}")
            print("    Try: git submodule update --init in the source repo first")

    return submodule_repos


# ────────────────────────────────────────────────────────────────────────────────────────
def resolve_relative_url(source_repo: Path, relative_url: str) -> str:
    """Resolve a relative submodule URL against the source repo's remote."""
    try:
        # Get the origin remote URL
        remote_url = git(source_repo, "remote", "get-url", "origin").strip()

        # Handle SSH URLs like git@host:path/to/repo.git
        if "@" in remote_url and ":" in remote_url and "://" not in remote_url:
            # SSH URL format: git@host:path/to/repo.git
            host_part, path_part = remote_url.split(":", 1)

            # Remove .git suffix for path manipulation
            if path_part.endswith(".git"):
                path_part = path_part[:-4]

            # Split path and apply relative navigation
            path_parts = path_part.split("/")

            for part in relative_url.split("/"):
                if part == "..":
                    if path_parts:
                        path_parts.pop()
                elif part != ".":
                    path_parts.append(part)

            resolved_path = "/".join(path_parts)
            return f"{host_part}:{resolved_path}"

        # Handle HTTPS URLs like https://host/path/to/repo.git
        if remote_url.endswith(".git"):
            base = remote_url[:-4]
        else:
            base = remote_url

        # Remove the last path component and apply relative path
        parts = relative_url.split("/")
        base_parts = base.rstrip("/").split("/")

        for part in parts:
            if part == "..":
                base_parts = base_parts[:-1]
            elif part != ".":
                base_parts.append(part)

        resolved = "/".join(base_parts)
        if not resolved.endswith(".git") and relative_url.endswith(".git"):
            resolved += ".git"

        return resolved
    except Exception:
        # Fall back to original URL if resolution fails
        return relative_url


# ────────────────────────────────────────────────────────────────────────────────────────
def export_transform_import(
    source_repo: Path,
    output_repo: Path,
    submodule_repos: dict[str, Path],
    verbose: bool,
) -> dict[str, str]:
    """Export from source, transform to expand submodules, import to output."""

    # Start fast-export
    export_cmd = [
        "git",
        "-C",
        str(source_repo),
        "fast-export",
        "--all",
        "--signed-tags=strip",
        "--tag-of-filtered-object=rewrite",
    ]
    export_proc = subprocess.Popen(
        export_cmd,
        stdout=subprocess.PIPE,
        stderr=subprocess.PIPE,
    )

    # Start fast-import
    import_cmd = [
        "git",
        "-C",
        str(output_repo),
        "fast-import",
        "--quiet",
    ]
    import_proc = subprocess.Popen(
        import_cmd,
        stdin=subprocess.PIPE,
        stdout=subprocess.PIPE,
        stderr=subprocess.PIPE,
    )

    assert export_proc.stdout is not None
    assert import_proc.stdin is not None

    # Track marks to commits for the mapping
    mark_to_original_commit: dict[int, str] = {}
    current_commit_sha: str | None = None
    current_mark: int | None = None
    next_mark = 1000000  # Start high to avoid conflicts
    commit_count = 0
    in_commit = False
    in_data = False
    data_remaining = 0

    # Regex patterns
    import re

    mark_pattern = re.compile(r"^mark :(\d+)$")
    commit_pattern = re.compile(r"^commit (.+)$")
    m_pattern = re.compile(r"^M (\d+) (?::(\d+)|([0-9a-f]{40})|inline) (.+)$")
    skip_next_data = False

    # Helper to write to import and check for errors
    def write_import(data: bytes) -> None:
        assert import_proc.stdin is not None
        try:
            import_proc.stdin.write(data)
        except BrokenPipeError as e:
            # fast-import died - get the error message
            import_proc.wait()
            stderr = import_proc.stderr.read().decode() if import_proc.stderr else ""
            raise RuntimeError(f"fast-import failed: {stderr}") from e

    # Process the stream
    while True:
        line = export_proc.stdout.readline()
        if not line:
            break

        # Handle data blocks (pass through unchanged, unless skipping)
        if in_data:
            if not skip_next_data:
                write_import(line)
            data_remaining -= len(line)
            if data_remaining <= 0:
                in_data = False
                skip_next_data = False
            continue

        line_str = line.decode("utf-8", errors="replace")

        # Check for data command
        if line_str.startswith("data "):
            data_size = int(line_str[5:].strip())
            data_remaining = data_size
            in_data = data_size > 0
            if not skip_next_data:
                write_import(line)
            continue

        # Check for commit
        commit_match = commit_pattern.match(line_str)
        if commit_match:
            in_commit = True
            commit_count += 1
            if commit_count % 50 == 0:
                print(f"  Processing commit {commit_count}...", flush=True)
            write_import(line)
            continue

        # Track mark to commit mapping
        mark_match = mark_pattern.match(line_str)
        if mark_match and in_commit:
            current_mark = int(mark_match.group(1))
            write_import(line)
            continue

        # Check for original-oid (gives us the original SHA)
        if line_str.startswith("original-oid "):
            current_commit_sha = line_str[13:].strip()
            if current_mark is not None:
                mark_to_original_commit[current_mark] = current_commit_sha
            write_import(line)
            continue

        # Check for file modification with gitlink (submodule)
        m_match = m_pattern.match(line_str)
        if m_match:
            mode = m_match.group(1)
            _mark_ref = m_match.group(2)
            sha_ref = m_match.group(3)
            filepath = m_match.group(4)

            # Skip .gitmodules - no longer needed after flattening
            if filepath == ".gitmodules":
                # If this is inline data, we need to skip the following data block
                if "inline" in line_str:
                    skip_next_data = True
                continue

            if mode == GITLINK_MODE:
                # This is a submodule - expand it
                submodule_sha = sha_ref  # Gitlinks always have SHA, not mark
                next_mark = expand_submodule_to_stream(
                    submodule_repos,
                    filepath,
                    submodule_sha,
                    next_mark,
                    verbose,
                    write_import,
                )
            else:
                # Regular file - pass through
                write_import(line)
            continue

        # Reset state at end of commit
        if line_str.strip() == "" and in_commit:
            in_commit = False
            current_commit_sha = None
            current_mark = None

        # Pass through everything else
        write_import(line)

    # Close streams
    import_proc.stdin.close()
    export_proc.wait()
    import_proc.wait()

    if export_proc.returncode != 0:
        stderr = export_proc.stderr.read().decode() if export_proc.stderr else ""
        raise RuntimeError(f"fast-export failed: {stderr}")

    if import_proc.returncode != 0:
        stderr = import_proc.stderr.read().decode() if import_proc.stderr else ""
        raise RuntimeError(f"fast-import failed: {stderr}")

    print(f"  Processed {commit_count} commits")

    # Checkout the default branch to clean up the working directory
    # fast-import leaves things in a detached HEAD state with staged files
    branches = get_all_branches(output_repo)
    if branches:
        default_branch = (
            "main"
            if "main" in branches
            else ("master" if "master" in branches else branches[0])
        )
        git(output_repo, "checkout", "-f", default_branch)

    # Build commit map by reading marks
    return build_commit_map(source_repo, output_repo, mark_to_original_commit)


# ────────────────────────────────────────────────────────────────────────────────────────
def expand_submodule_to_stream(
    submodule_repos: dict[str, Path],
    submodule_path: str,
    submodule_commit: str,
    next_mark: int,
    verbose: bool,
    write_fn: Callable[[bytes], None],
) -> int:
    """Expand a submodule into file entries in the fast-import stream."""
    if submodule_path not in submodule_repos:
        if verbose:
            print(f"  Warning: No repo for submodule {submodule_path}")
        return next_mark

    submodule_repo = submodule_repos[submodule_path]

    # Check if commit exists
    if not object_exists(submodule_repo, submodule_commit):
        if verbose:
            print(f"  Warning: Commit {submodule_commit[:8]} not in {submodule_path}")
        return next_mark

    # Get all files in the submodule at this commit
    try:
        files = get_files_recursive(submodule_repo, submodule_commit)
    except Exception as e:
        if verbose:
            print(f"  Warning: Could not list files in {submodule_path}: {e}")
        return next_mark

    # Add each file to the stream using inline data format
    # (can't use marks here because blobs must be defined before commits)
    for file_mode, file_sha, file_path in files:
        full_path = f"{submodule_path}/{file_path}"

        # Get file content
        try:
            content = read_blob(submodule_repo, file_sha)
        except Exception:
            continue

        # Write file entry with inline data
        write_fn(f"M {file_mode} inline {full_path}\n".encode())
        write_fn(f"data {len(content)}\n".encode())
        write_fn(content)
        write_fn(b"\n")

    return next_mark


# ────────────────────────────────────────────────────────────────────────────────────────
def get_files_recursive(repo_path: Path, commit: str) -> list[tuple[str, str, str]]:
    """Get all files in a commit recursively. Returns (mode, sha, path) tuples."""
    output = git(repo_path, "ls-tree", "-r", commit)
    files: list[tuple[str, str, str]] = []
    for line in output.strip().split("\n"):
        if not line:
            continue
        # Format: <mode> <type> <sha>\t<path>
        parts = line.split("\t", 1)
        mode_type_sha = parts[0].split()
        mode = mode_type_sha[0]
        sha = mode_type_sha[2]
        path = parts[1]
        # Skip submodules within submodules for now
        if mode != GITLINK_MODE:
            files.append((mode, sha, path))
    return files


# ────────────────────────────────────────────────────────────────────────────────────────
def build_commit_map(
    source_repo: Path,
    output_repo: Path,
    _mark_to_original: dict[int, str],
) -> dict[str, str]:
    """Build mapping from original commits to new commits."""
    # Get all commits from both repos and match by tree content or message
    # This is a simplified approach - for exact mapping we'd need to track marks better

    commit_map: dict[str, str] = {}

    # Get commits from source
    source_commits = get_all_commits(source_repo)

    # Get commits from output
    output_commits = get_all_commits(output_repo)

    # Match by position (since we preserve order)
    for src, dst in zip(source_commits, output_commits, strict=False):
        commit_map[src] = dst

    return commit_map
