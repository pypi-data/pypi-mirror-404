# ────────────────────────────────────────────────────────────────────────────────────────
#   repo.py
#   ───────
#
#   Git repository operations using plumbing commands.
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

import configparser
import os
import subprocess
from typing import TYPE_CHECKING

if TYPE_CHECKING:
    from pathlib import Path
    from .config import CommitInfo
    from .config import SubmoduleInfo
    from .config import TreeEntry

# ────────────────────────────────────────────────────────────────────────────────────────
#   Git Command Execution
# ────────────────────────────────────────────────────────────────────────────────────────


def git(
    repo_path: Path,
    *args: str,
    input_data: str | None = None,
    env: dict[str, str] | None = None,
    check: bool = True,
) -> str:
    """Execute a git command in the given repository."""
    cmd = ["git", "-C", str(repo_path), *args]
    full_env = os.environ.copy()
    if env:
        full_env.update(env)
    result = subprocess.run(
        cmd,
        capture_output=True,
        text=True,
        input=input_data,
        env=full_env,
        check=check,
    )
    if check and result.returncode != 0:
        raise subprocess.CalledProcessError(
            result.returncode, cmd, result.stdout, result.stderr
        )
    return result.stdout


# ────────────────────────────────────────────────────────────────────────────────────────
def git_bytes(
    repo_path: Path,
    *args: str,
) -> bytes:
    """Execute a git command and return raw bytes."""
    cmd = ["git", "-C", str(repo_path), *args]
    result = subprocess.run(cmd, capture_output=True, check=True)
    return result.stdout


# ────────────────────────────────────────────────────────────────────────────────────────
#   Repository Operations
# ────────────────────────────────────────────────────────────────────────────────────────


def init_repo(path: Path) -> None:
    """Initialise a new git repository."""
    path.mkdir(parents=True, exist_ok=True)
    subprocess.run(["git", "init", str(path)], check=True, capture_output=True)


# ────────────────────────────────────────────────────────────────────────────────────────
def clone_repo(url: str, path: Path, bare: bool = False) -> None:
    """Clone a git repository."""
    cmd = ["git", "clone"]
    if bare:
        cmd.append("--bare")
    cmd.extend([url, str(path)])
    subprocess.run(cmd, check=True, capture_output=True)


# ────────────────────────────────────────────────────────────────────────────────────────
def get_all_branches(repo_path: Path) -> list[str]:
    """Get all branch names in the repository."""
    output = git(repo_path, "for-each-ref", "--format=%(refname:short)", "refs/heads/")
    return [line.strip() for line in output.strip().split("\n") if line.strip()]


# ────────────────────────────────────────────────────────────────────────────────────────
def get_all_tags(repo_path: Path) -> list[str]:
    """Get all tag names in the repository."""
    output = git(repo_path, "for-each-ref", "--format=%(refname:short)", "refs/tags/")
    return [line.strip() for line in output.strip().split("\n") if line.strip()]


# ────────────────────────────────────────────────────────────────────────────────────────
def get_tag_commit(repo_path: Path, tag: str) -> str:
    """Get the commit SHA that a tag points to (dereferencing annotated tags)."""
    return git(repo_path, "rev-parse", f"{tag}^{{commit}}").strip()


# ────────────────────────────────────────────────────────────────────────────────────────
def get_all_commits(repo_path: Path, branches: list[str] | None = None) -> list[str]:
    """Get all commits in topological order (parents before children)."""
    args = ["rev-list", "--topo-order", "--reverse"]
    if branches:
        args.extend(branches)
    else:
        args.append("--all")
    output = git(repo_path, *args)
    return [line.strip() for line in output.strip().split("\n") if line.strip()]


# ────────────────────────────────────────────────────────────────────────────────────────
def get_commit_info(repo_path: Path, commit_sha: str) -> CommitInfo:
    """Get detailed information about a commit."""
    # Get commit data in a parseable format
    format_str = "%T%n%P%n%an%n%ae%n%ai%n%cn%n%ce%n%ci"
    output = git(repo_path, "log", "-1", f"--format={format_str}", commit_sha)
    lines = output.strip().split("\n")

    tree = lines[0]
    parents = lines[1].split() if lines[1] else []
    author_name = lines[2]
    author_email = lines[3]
    author_date = lines[4]
    committer_name = lines[5]
    committer_email = lines[6]
    committer_date = lines[7]

    # Get commit message separately (can be multiline)
    message = git(repo_path, "log", "-1", "--format=%B", commit_sha).strip()

    return {
        "tree": tree,
        "parents": parents,
        "author_name": author_name,
        "author_email": author_email,
        "author_date": author_date,
        "committer_name": committer_name,
        "committer_email": committer_email,
        "committer_date": committer_date,
        "message": message,
    }


# ────────────────────────────────────────────────────────────────────────────────────────
def get_branch_commit(repo_path: Path, branch: str) -> str:
    """Get the commit SHA that a branch points to."""
    return git(repo_path, "rev-parse", branch).strip()


# ────────────────────────────────────────────────────────────────────────────────────────
#   Tree Operations
# ────────────────────────────────────────────────────────────────────────────────────────


def ls_tree(repo_path: Path, tree_sha: str) -> list[TreeEntry]:
    """List entries in a git tree."""
    output = git(repo_path, "ls-tree", tree_sha)
    entries: list[TreeEntry] = []
    for line in output.strip().split("\n"):
        if not line:
            continue
        # Format: <mode> <type> <sha>\t<name>
        parts = line.split("\t", 1)
        mode_type_sha = parts[0].split()
        entries.append(
            {
                "mode": mode_type_sha[0],
                "type": mode_type_sha[1],
                "sha": mode_type_sha[2],
                "name": parts[1],
            }
        )
    return entries


# ────────────────────────────────────────────────────────────────────────────────────────
def read_blob(repo_path: Path, blob_sha: str) -> bytes:
    """Read the contents of a blob."""
    return git_bytes(repo_path, "cat-file", "blob", blob_sha)


# ────────────────────────────────────────────────────────────────────────────────────────
def get_tree_sha(repo_path: Path, commit_sha: str) -> str:
    """Get the tree SHA for a commit."""
    return git(repo_path, "rev-parse", f"{commit_sha}^{{tree}}").strip()


# ────────────────────────────────────────────────────────────────────────────────────────
def mktree(repo_path: Path, entries: list[TreeEntry]) -> str:
    """Create a tree object from entries and return its SHA."""
    lines: list[str] = []
    for entry in entries:
        lines.append(f"{entry['mode']} {entry['type']} {entry['sha']}\t{entry['name']}")
    input_data = "\n".join(lines) + "\n" if lines else ""
    return git(repo_path, "mktree", input_data=input_data).strip()


# ────────────────────────────────────────────────────────────────────────────────────────
def hash_object(repo_path: Path, data: bytes, obj_type: str = "blob") -> str:
    """Hash an object and store it in the repository."""
    cmd = ["git", "-C", str(repo_path), "hash-object", "-w", "-t", obj_type, "--stdin"]
    result = subprocess.run(cmd, capture_output=True, input=data, check=True)
    return result.stdout.decode().strip()


# ────────────────────────────────────────────────────────────────────────────────────────
#   Commit Creation
# ────────────────────────────────────────────────────────────────────────────────────────


def commit_tree(
    repo_path: Path,
    tree_sha: str,
    parents: list[str],
    message: str,
    author_name: str,
    author_email: str,
    author_date: str,
    committer_name: str,
    committer_email: str,
    committer_date: str,
) -> str:
    """Create a commit object and return its SHA."""
    args = ["commit-tree", tree_sha]
    for parent in parents:
        args.extend(["-p", parent])

    env = {
        "GIT_AUTHOR_NAME": author_name,
        "GIT_AUTHOR_EMAIL": author_email,
        "GIT_AUTHOR_DATE": author_date,
        "GIT_COMMITTER_NAME": committer_name,
        "GIT_COMMITTER_EMAIL": committer_email,
        "GIT_COMMITTER_DATE": committer_date,
    }

    return git(repo_path, *args, input_data=message, env=env).strip()


# ────────────────────────────────────────────────────────────────────────────────────────
def update_ref(repo_path: Path, ref: str, commit_sha: str) -> None:
    """Update a reference to point to a commit."""
    git(repo_path, "update-ref", ref, commit_sha)


# ────────────────────────────────────────────────────────────────────────────────────────
#   Submodule Operations
# ────────────────────────────────────────────────────────────────────────────────────────


def get_gitmodules_at_commit(
    repo_path: Path, commit_sha: str
) -> dict[str, SubmoduleInfo]:
    """Parse .gitmodules file at a specific commit."""
    # Check if .gitmodules exists in this commit
    try:
        tree_sha = get_tree_sha(repo_path, commit_sha)
        entries = ls_tree(repo_path, tree_sha)
        gitmodules_entry = next(
            (e for e in entries if e["name"] == ".gitmodules"), None
        )
        if not gitmodules_entry:
            return {}
    except subprocess.CalledProcessError:
        return {}

    # Read and parse .gitmodules
    try:
        content = read_blob(repo_path, gitmodules_entry["sha"]).decode("utf-8")
    except subprocess.CalledProcessError:
        return {}

    return parse_gitmodules(content)


# ────────────────────────────────────────────────────────────────────────────────────────
def parse_gitmodules(content: str) -> dict[str, SubmoduleInfo]:
    """Parse .gitmodules content and return submodule info by path."""
    parser = configparser.ConfigParser()
    parser.read_string(content)

    submodules: dict[str, SubmoduleInfo] = {}
    for section in parser.sections():
        if section.startswith('submodule "'):
            path = parser.get(section, "path", fallback=None)
            url = parser.get(section, "url", fallback=None)
            if path and url:
                submodules[path] = {"path": path, "url": url}

    return submodules


# ────────────────────────────────────────────────────────────────────────────────────────
def object_exists(repo_path: Path, sha: str) -> bool:
    """Check if an object exists in the repository."""
    result = subprocess.run(
        ["git", "-C", str(repo_path), "cat-file", "-e", sha],
        capture_output=True,
    )
    return result.returncode == 0


# ────────────────────────────────────────────────────────────────────────────────────────
#   Remote Operations
# ────────────────────────────────────────────────────────────────────────────────────────


# ────────────────────────────────────────────────────────────────────────────────────────
def get_remotes(repo_path: Path) -> dict[str, str]:
    """Get all remotes and their URLs from a repository."""
    output = git(repo_path, "remote", "-v", check=False)
    remotes: dict[str, str] = {}
    for line in output.strip().split("\n"):
        if not line or "(push)" in line:
            # Skip empty lines and push URLs (we only need fetch URLs)
            continue
        parts = line.split()
        if len(parts) >= 2:
            name = parts[0]
            url = parts[1]
            remotes[name] = url
    return remotes


# ────────────────────────────────────────────────────────────────────────────────────────
def copy_remotes(source_repo: Path, dest_repo: Path, verbose: bool = False) -> int:
    """Copy all remotes from source repository to destination repository."""
    remotes = get_remotes(source_repo)
    count = 0
    for name, url in remotes.items():
        git(dest_repo, "remote", "add", name, url, check=False)
        count += 1
        if verbose:
            print(f"  Added remote: {name} -> {url}")
    return count
