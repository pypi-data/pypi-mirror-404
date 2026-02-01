# ────────────────────────────────────────────────────────────────────────────────────────
#   flatten/run.py
#   ───────────────
#
#   CLI runner for the flatten subcommand.
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
from .rewriter import collect_submodules_from_gitmodules
from .rewriter import flatten_repository

if TYPE_CHECKING:
    import argparse

# ────────────────────────────────────────────────────────────────────────────────────────
#   Runner
# ────────────────────────────────────────────────────────────────────────────────────────


# ────────────────────────────────────────────────────────────────────────────────────────
def run(args: argparse.Namespace) -> int:
    """Run the flatten subcommand."""
    # Validate paths
    if not args.repo.exists():
        print(f"Error: Source repository not found: {args.repo}", file=sys.stderr)
        return 1

    # Scan-only mode
    if args.scan_only:
        print("Scanning for submodules...")
        submodules = collect_submodules_from_gitmodules(args.repo)
        if submodules:
            print(f"\nFound {len(submodules)} submodules:")
            for path, info in submodules.items():
                print(f"  {path} -> {info['url']}")
        else:
            print("\nNo submodules found.")
        return 0

    # Require output for non-scan mode
    if not args.output:
        print("Error: --output is required (unless using --scan-only)", file=sys.stderr)
        return 1

    # Default mapping file
    mapping_file = args.commit_map or (
        args.output.parent / f"{args.output.name}-mapping.txt"
    )

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

    flatten_repository(
        source_repo=args.repo,
        output_repo=args.output,
        mapping_file=mapping_file,
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
    print(f"Commit mapping written to: {mapping_file}")
    return 0
