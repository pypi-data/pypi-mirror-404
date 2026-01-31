# ────────────────────────────────────────────────────────────────────────────────────────
#   remapper.py
#   ───────────
#
#   Core history rewriting logic for submodule remapping.
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
from ..common import GITLINK_MODE
from ..common import get_all_branches
from ..common import git
from ..common import init_repo

if TYPE_CHECKING:
    from pathlib import Path

# ────────────────────────────────────────────────────────────────────────────────────────
#   Constants
# ────────────────────────────────────────────────────────────────────────────────────────

M_SHA_PATTERN = re.compile(r"^M (\d+) ([0-9a-f]{40}) (.+)$")
M_ANY_PATTERN = re.compile(r"^M (\d+) (\S+) (.+)$")

# ────────────────────────────────────────────────────────────────────────────────────────
#   Mapping Loading
# ────────────────────────────────────────────────────────────────────────────────────────


# ────────────────────────────────────────────────────────────────────────────────────────
def load_mapping_file(filepath: Path) -> dict[str, str]:
    """
    Load commit mapping from a file.

    Format: old_sha new_sha (one per line, as output by sanitise)
    """
    mapping: dict[str, str] = {}
    with filepath.open(encoding="utf-8") as f:
        for line in f:
            line = line.strip()
            if not line:
                continue
            parts = line.split()
            if len(parts) >= 2:
                old_sha = parts[0]
                new_sha = parts[1]
                mapping[old_sha] = new_sha
    return mapping


# ────────────────────────────────────────────────────────────────────────────────────────
#   Main Remap Function
# ────────────────────────────────────────────────────────────────────────────────────────


def remap_repository(
    source_repo: Path,
    output_repo: Path,
    mapping_file: Path,
    submodule_path: str | None = None,
    url_rewrites: dict[str, str] | None = None,
    verbose: bool = False,
) -> dict[str, int]:
    """
    Remap submodule commit references in repository history.

    Returns statistics about the remapping operation.
    """
    if url_rewrites is None:
        url_rewrites = {}

    print(f"Source: {source_repo}")
    print(f"Output: {output_repo}")
    if submodule_path:
        print(f"Submodule path: {submodule_path}")
    else:
        print("Submodule path: (all matching gitlinks)")
    if url_rewrites:
        print(f"URL rewrites: {len(url_rewrites)}")
        for old_url, new_url in url_rewrites.items():
            print(f"  {old_url} -> {new_url}")

    # Load mapping
    print(f"Loading mapping from {mapping_file}...")
    mapping = load_mapping_file(mapping_file)
    print(f"Loaded {len(mapping)} commit mappings")

    # Initialise output repository
    print("Initialising output repository...")
    init_repo(output_repo)

    # Run the remapping
    print("Processing history...")
    stats = remap_history(
        source_repo, output_repo, mapping, submodule_path, url_rewrites, verbose
    )

    print("Done!")
    print(f"Processed {stats['commits']} commits")
    print(f"Remapped {stats['remapped']} gitlink references")
    if stats["unmapped"] > 0:
        print(f"Warning: {stats['unmapped']} gitlinks had no mapping (kept original)")
    if stats["gitmodules_updated"] > 0:
        print(f"Updated .gitmodules URL in {stats['gitmodules_updated']} commits")

    return stats


# ────────────────────────────────────────────────────────────────────────────────────────
def remap_history(
    source_repo: Path,
    output_repo: Path,
    mapping: dict[str, str],
    submodule_path: str | None,
    url_rewrites: dict[str, str],
    verbose: bool,
) -> dict[str, int]:
    """Process history through fast-export/fast-import, remapping gitlinks."""

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

    # Statistics
    stats = {
        "commits": 0,
        "remapped": 0,
        "unmapped": 0,
        "gitmodules_updated": 0,
    }

    # State tracking
    in_data = False
    in_blob_data = False
    data_remaining = 0
    current_blob_mark: str | None = None
    current_blob_data = b""
    blob_contents: dict[str, bytes] = {}  # mark -> content

    # Helper to write to import
    def write_import(data: bytes) -> None:
        assert import_proc.stdin is not None
        try:
            import_proc.stdin.write(data)
        except BrokenPipeError as e:
            import_proc.wait()
            stderr = import_proc.stderr.read().decode() if import_proc.stderr else ""
            raise RuntimeError(f"fast-import failed: {stderr}") from e

    # Process the stream
    while True:
        line = export_proc.stdout.readline()
        if not line:
            break

        # Handle blob data - capture content while passing through
        if in_blob_data:
            current_blob_data += line
            write_import(line)
            data_remaining -= len(line)
            if data_remaining <= 0:
                in_blob_data = False
                if current_blob_mark:
                    blob_contents[current_blob_mark] = current_blob_data
                current_blob_data = b""
            continue

        # Handle regular data blocks (commit messages, etc.)
        if in_data:
            write_import(line)
            data_remaining -= len(line)
            if data_remaining <= 0:
                in_data = False
            continue

        line_str = line.decode("utf-8", errors="replace")

        # Check for blob start
        if line_str.strip() == "blob":
            current_blob_mark = None
            current_blob_data = b""
            write_import(line)
            continue

        # Check for mark (track for blob content)
        if line_str.startswith("mark :"):
            current_blob_mark = line_str.strip().split()[1]  # e.g., ":3"
            write_import(line)
            continue

        # Check for data command
        if line_str.startswith("data "):
            data_size = int(line_str[5:].strip())
            data_remaining = data_size
            write_import(line)

            # If we're tracking a blob, capture its data
            if current_blob_mark is not None:
                in_blob_data = data_size > 0
            else:
                in_data = data_size > 0
            continue

        # Check for commit
        if line_str.startswith("commit "):
            stats["commits"] += 1
            current_blob_mark = None  # Reset blob tracking
            if stats["commits"] % 50 == 0:
                print(f"  Processing commit {stats['commits']}...", flush=True)
            write_import(line)
            continue

        # Check for file modification with SHA (gitlinks)
        m_match = M_SHA_PATTERN.match(line_str)
        if m_match:
            mode = m_match.group(1)
            sha = m_match.group(2)
            filepath = m_match.group(3)

            # Check if this is a gitlink we should remap
            if mode == GITLINK_MODE and (
                submodule_path is None or filepath == submodule_path
            ):
                if sha in mapping:
                    new_sha = mapping[sha]
                    write_import(f"M {mode} {new_sha} {filepath}\n".encode())
                    stats["remapped"] += 1
                    if verbose:
                        print(f"  Remapped: {sha[:8]} -> {new_sha[:8]}")
                else:
                    write_import(line)
                    stats["unmapped"] += 1
                    if verbose:
                        print(f"  Warning: No mapping for {sha[:8]}")
                continue

            write_import(line)
            continue

        # Check for file modification with mark (for .gitmodules)
        m_any_match = M_ANY_PATTERN.match(line_str)
        if m_any_match:
            mode = m_any_match.group(1)
            ref = m_any_match.group(2)
            filepath = m_any_match.group(3)

            # Check if this is .gitmodules - rewrite with modified content
            if filepath == ".gitmodules" and url_rewrites and ref.startswith(":"):
                if ref in blob_contents:
                    original = blob_contents[ref]
                    modified = modify_gitmodules(original, url_rewrites)
                    if modified != original:
                        stats["gitmodules_updated"] += 1
                        # Emit as inline data with modified content
                        write_import(f"M {mode} inline {filepath}\n".encode())
                        write_import(f"data {len(modified)}\n".encode())
                        write_import(modified)
                        continue
            write_import(line)
            continue

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

    # Checkout the default branch to clean up the working directory
    # fast-import leaves things in a detached HEAD state with staged files
    branches = get_all_branches(output_repo)
    if branches:
        # Prefer main, then master, then first available
        if "main" in branches:
            default_branch = "main"
        elif "master" in branches:
            default_branch = "master"
        else:
            default_branch = branches[0]
        git(output_repo, "checkout", "-f", default_branch)

    return stats


# ────────────────────────────────────────────────────────────────────────────────────────
def modify_gitmodules(content: bytes, url_rewrites: dict[str, str]) -> bytes:
    """Modify .gitmodules content to replace URLs based on url_rewrites mapping."""
    try:
        text = content.decode("utf-8")
    except UnicodeDecodeError:
        return content

    lines = text.split("\n")
    result_lines: list[str] = []

    for line in lines:
        # Replace matching URL lines
        if line.strip().startswith("url = "):
            current_url = line.strip()[6:].strip()
            if current_url in url_rewrites:
                result_lines.append(f"\turl = {url_rewrites[current_url]}")
            else:
                result_lines.append(line)
        else:
            result_lines.append(line)

    return "\n".join(result_lines).encode("utf-8")
