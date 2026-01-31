# ────────────────────────────────────────────────────────────────────────────────────────
#   remap/run.py
#   ────────────
#
#   CLI runner for the remap subcommand.
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

import shutil
import sys
from typing import TYPE_CHECKING
from ..common import copy_remotes
from .remapper import remap_repository

if TYPE_CHECKING:
    import argparse

# ────────────────────────────────────────────────────────────────────────────────────────
#   Runner
# ────────────────────────────────────────────────────────────────────────────────────────


# ────────────────────────────────────────────────────────────────────────────────────────
def run(args: argparse.Namespace) -> int:
    """Run the remap subcommand."""
    # Validate paths
    if not args.repo.exists():
        print(f"Error: Source repository not found: {args.repo}", file=sys.stderr)
        return 1
    if not args.commit_map.exists():
        print(f"Error: Mapping file not found: {args.commit_map}", file=sys.stderr)
        return 1

    # Handle output directory
    if args.output.exists():
        if args.delete:
            print(f"Removing existing output directory: {args.output}")
            shutil.rmtree(args.output)
        else:
            print(
                f"Error: Output directory already exists: {args.output}",
                file=sys.stderr,
            )
            print("Use --delete to remove it first", file=sys.stderr)
            return 1

    # Build URL rewrite mapping
    url_rewrites: dict[str, str] = {}
    if args.url_rewrite:
        for old_url, new_url in args.url_rewrite:
            url_rewrites[old_url] = new_url

    remap_repository(
        source_repo=args.repo,
        output_repo=args.output,
        mapping_file=args.commit_map,
        submodule_path=args.submodule_path,
        url_rewrites=url_rewrites,
        verbose=args.verbose,
    )

    # Copy remotes if requested
    if args.copy_remotes:
        print("Copying remotes from source repository...")
        count = copy_remotes(args.repo, args.output, verbose=args.verbose)
        if count > 0:
            print(f"  Copied {count} remote(s)")
        else:
            print("  No remotes found in source repository")

    print(f"\nOutput repository created at: {args.output}")
    return 0
