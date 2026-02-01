# ────────────────────────────────────────────────────────────────────────────────────────
#   rewriter.py
#   ───────────
#
#   Repository rewriting to replace dirty words using git fast-export/fast-import.
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
import sys
from pathlib import PurePath
from typing import TYPE_CHECKING
from ..common import get_all_branches
from ..common import git
from ..common import init_repo
from .patterns import build_replacement_func
from .patterns import replace_in_text
from .patterns import rewrite_author_line

if TYPE_CHECKING:
    from pathlib import Path

# ────────────────────────────────────────────────────────────────────────────────────────
#   Functions
# ────────────────────────────────────────────────────────────────────────────────────────


# ────────────────────────────────────────────────────────────────────────────────────────
def _matches_exclude_pattern(filepath: str, patterns: list[str]) -> bool:
    """
    Check if a filepath matches any of the exclude patterns.

    Uses PurePath.match() which supports glob patterns including:
    - `*` matches any characters within a path component
    - `**` matches any number of path components
    - `?` matches a single character

    Patterns are matched from the right side of the path, so:
    - `package-lock.json` matches `package-lock.json` and `src/package-lock.json`
    - `*.lock` matches any .lock file anywhere in the tree
    - `**/*.lock` is equivalent to `*.lock` (matches anywhere)
    - `node_modules/**` matches anything under any node_modules directory
    """
    path = PurePath(filepath)
    return any(path.match(pattern) for pattern in patterns)


# ────────────────────────────────────────────────────────────────────────────────────────
def rewrite_repository(
    repo_path: Path,
    output_path: Path,
    dirty_words: list[str],
    word_mapping: dict[str, str],
    default_replacement: str,
    commit_map_path: Path | None,
    exclude_patterns: list[str] | None = None,
    email_mapping: dict[str, str] | None = None,
    submodule_mapping: dict[str, str] | None = None,
    verbose: bool = False,
) -> dict[str, str]:
    """Rewrite the repository, replacing dirty words and excluding files."""
    if exclude_patterns is None:
        exclude_patterns = []
    if email_mapping is None:
        email_mapping = {}
    if submodule_mapping is None:
        submodule_mapping = {}
    pattern, replacements = build_replacement_func(
        dirty_words, word_mapping, default_replacement
    )

    print(f"Initialising output repository at {output_path}...")
    init_repo(output_path)

    print("Exporting repository history...")
    export_proc = subprocess.Popen(
        [
            "git",
            "fast-export",
            "--all",
            "--signed-tags=strip",
            "--tag-of-filtered-object=rewrite",
        ],
        cwd=repo_path,
        stdout=subprocess.PIPE,
        stderr=subprocess.PIPE,
    )

    import_proc = subprocess.Popen(
        ["git", "fast-import", "--quiet"],
        cwd=output_path,
        stdin=subprocess.PIPE,
        stdout=subprocess.PIPE,
        stderr=subprocess.PIPE,
    )

    assert export_proc.stdout is not None
    assert import_proc.stdin is not None

    commit_count = 0
    blob_count = 0
    excluded_count = 0
    submodule_count = 0
    in_data = False
    data_remaining = 0
    data_buffer = b""
    skip_data = False

    mark_to_old_commit: dict[str, str] = {}
    current_mark = ""

    print("Rewriting history...")

    for line in export_proc.stdout:
        if in_data:
            data_buffer += line
            data_remaining -= len(line)

            if data_remaining <= 0:
                in_data = False
                if skip_data:
                    skip_data = False
                    data_buffer = b""
                    continue

                try:
                    text = data_buffer.decode("utf-8")
                    new_text = replace_in_text(text, pattern, replacements)
                    new_data = new_text.encode("utf-8")
                    if new_data != data_buffer:
                        blob_count += 1
                        if verbose:
                            print("  Replaced content in blob")
                except UnicodeDecodeError:
                    new_data = data_buffer

                import_proc.stdin.write(f"data {len(new_data)}\n".encode())
                import_proc.stdin.write(new_data)
                data_buffer = b""
        elif line.startswith(b"M "):
            # File modification: M <mode> <dataref> <path>
            # dataref is either :mark, "inline", or a SHA (for submodules)
            parts = line.decode("utf-8", errors="replace").strip().split(" ", 3)
            if len(parts) >= 4:
                mode = parts[1]
                dataref = parts[2]
                filepath = parts[3]
                if exclude_patterns and _matches_exclude_pattern(
                    filepath, exclude_patterns
                ):
                    excluded_count += 1
                    if verbose:
                        print(f"  Excluding file: {filepath}")
                    if dataref == "inline":
                        skip_data = True
                    continue
                # Handle submodules (mode 160000) - remap commit SHA if mapping provided
                if mode == "160000":
                    submodule_count += 1
                    if submodule_mapping and dataref in submodule_mapping:
                        new_sha = submodule_mapping[dataref]
                        new_line = f"M {mode} {new_sha} {filepath}\n"
                        if verbose:
                            print(
                                f"  Remapped submodule {filepath}: {dataref} ->"
                                f" {new_sha}"
                            )
                        import_proc.stdin.write(new_line.encode("utf-8"))
                        continue
                    elif verbose:
                        print(f"  Submodule {filepath}: {dataref} (unchanged)")
            import_proc.stdin.write(line)
        elif line.startswith(b"D "):
            # File deletion - check if it's an excluded file
            filepath = line[2:].decode("utf-8", errors="replace").strip()
            if exclude_patterns and _matches_exclude_pattern(
                filepath, exclude_patterns
            ):
                continue
            import_proc.stdin.write(line)
        elif line.startswith(b"data "):
            size_str = line[5:].strip().decode("utf-8")
            data_remaining = int(size_str)
            in_data = True
            data_buffer = b""
        elif line.startswith(b"commit "):
            commit_count += 1
            if commit_count % 100 == 0:
                print(f"  Processed {commit_count} commits...")
            import_proc.stdin.write(line)
        elif line.startswith(b"mark :"):
            current_mark = line.decode("utf-8").strip()
            import_proc.stdin.write(line)
        elif line.startswith(b"original-oid "):
            current_original_commit = line[13:].strip().decode("utf-8")
            if current_mark:
                mark_to_old_commit[current_mark] = current_original_commit
            import_proc.stdin.write(line)
        elif line.startswith(b"author ") or line.startswith(b"committer "):
            try:
                text = line.decode("utf-8").rstrip("\n")
                new_text = rewrite_author_line(
                    text, pattern, replacements, email_mapping
                )
                import_proc.stdin.write((new_text + "\n").encode("utf-8"))
            except UnicodeDecodeError:
                import_proc.stdin.write(line)
        else:
            import_proc.stdin.write(line)

    import_proc.stdin.close()
    export_proc.wait()
    import_proc.wait()

    if export_proc.returncode != 0:
        stderr = export_proc.stderr.read().decode() if export_proc.stderr else ""
        print(f"Error during export: {stderr}", file=sys.stderr)
        sys.exit(1)

    if import_proc.returncode != 0:
        stderr = import_proc.stderr.read().decode() if import_proc.stderr else ""
        print(f"Error during import: {stderr}", file=sys.stderr)
        sys.exit(1)

    print(f"  Processed {commit_count} commits, rewrote {blob_count} blobs")
    if submodule_count > 0:
        print(f"  Processed {submodule_count} submodule entries")
    if excluded_count > 0:
        print(f"  Excluded {excluded_count} file entries")

    # Checkout the default branch to clean up the working directory
    # fast-import leaves things in a detached HEAD state with staged files
    print("Checking out working tree...")
    branches = get_all_branches(output_path)
    if branches:
        # Prefer main, then master, then first available
        if "main" in branches:
            default_branch = "main"
        elif "master" in branches:
            default_branch = "master"
        else:
            default_branch = branches[0]
        git(output_path, "checkout", "-f", default_branch)

    # Initialise submodules if any exist
    if submodule_count > 0:
        print("Copying submodule URLs from source repository...")
        # Get submodule URLs from source repo and apply to output
        result = subprocess.run(
            ["git", "config", "--get-regexp", r"submodule\..*\.url"],
            cwd=repo_path,
            capture_output=True,
            text=True,
        )
        if result.returncode == 0 and result.stdout.strip():
            for line in result.stdout.strip().split("\n"):
                parts = line.split(" ", 1)
                if len(parts) == 2:
                    config_key = parts[0]
                    url = parts[1]
                    subprocess.run(
                        ["git", "config", config_key, url],
                        cwd=output_path,
                        capture_output=True,
                    )
                    if verbose:
                        print(f"  Set {config_key} = {url}")

        print("Initialising submodules...")
        subprocess.run(
            ["git", "submodule", "update", "--init", "--recursive"],
            cwd=output_path,
            capture_output=True,
        )

        # Clean up submodule staging areas
        print("Cleaning submodule staging areas...")
        subprocess.run(
            ["git", "submodule", "foreach", "--recursive", "git reset --hard HEAD"],
            cwd=output_path,
            capture_output=True,
        )

        # Reset main repo again to clear any submodule changes from index
        subprocess.run(
            ["git", "reset", "--hard", "HEAD"],
            cwd=output_path,
            capture_output=True,
        )

    print("Building commit ID mapping...")
    commit_mapping: dict[str, str] = {}

    for mark, old_commit in mark_to_old_commit.items():
        mark_num = mark.split(":")[1] if ":" in mark else mark
        try:
            result = subprocess.run(
                ["git", "rev-parse", f":{mark_num}"],
                cwd=output_path,
                capture_output=True,
                text=True,
            )
            if result.returncode == 0:
                new_commit = result.stdout.strip()
                commit_mapping[old_commit] = new_commit
        except Exception:
            pass

    if not commit_mapping:
        old_commits_result = subprocess.run(
            ["git", "rev-list", "--all", "--reverse"],
            cwd=repo_path,
            capture_output=True,
            text=True,
        )
        old_commits = (
            old_commits_result.stdout.strip().split("\n")
            if old_commits_result.stdout
            else []
        )

        new_commits_result = subprocess.run(
            ["git", "rev-list", "--all", "--reverse"],
            cwd=output_path,
            capture_output=True,
            text=True,
        )
        new_commits = (
            new_commits_result.stdout.strip().split("\n")
            if new_commits_result.stdout
            else []
        )

        for old, new in zip(old_commits, new_commits, strict=False):
            if old and new:
                commit_mapping[old] = new

    if commit_map_path:
        print(f"Writing commit mapping to {commit_map_path}...")
        with open(commit_map_path, "w", encoding="utf-8") as f:
            for old_id, new_id in sorted(commit_mapping.items()):
                f.write(f"{old_id} {new_id}\n")

    return commit_mapping
