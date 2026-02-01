# ────────────────────────────────────────────────────────────────────────────────────────
#   sanitise/run.py
#   ────────────────
#
#   CLI runner for the sanitise subcommand.
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
from .config import load_config
from .config import load_submodule_mapping
from .rewriter import rewrite_repository

if TYPE_CHECKING:
    import argparse

# ────────────────────────────────────────────────────────────────────────────────────────
#   Constants
# ────────────────────────────────────────────────────────────────────────────────────────

SAMPLE_CONFIG = """{
    "words": ["secretword", "internalname", "sensitiveid"],
    "word_mapping": {
        "secretword": "publicword",
        "internalname": "externalname"
    },
    "email_mapping": {
        "john smith": "jsmith@example.com",
        "jane doe": "jdoe@example.com"
    },
    "exclude_files": [
        "package-lock.json",
        "yarn.lock"
    ]
}"""

# ────────────────────────────────────────────────────────────────────────────────────────
#   Runner
# ────────────────────────────────────────────────────────────────────────────────────────


# ────────────────────────────────────────────────────────────────────────────────────────
def run(args: argparse.Namespace) -> int:
    """Run the sanitise subcommand."""
    # Print sample config if requested
    if args.sample_config:
        print(SAMPLE_CONFIG)
        return 0

    # Validate required arguments
    if not args.repo:
        print("Error: -r/--repo is required", file=sys.stderr)
        return 1
    if not args.output:
        print("Error: -o/--output is required", file=sys.stderr)
        return 1
    if not args.config:
        print("Error: -c/--config is required", file=sys.stderr)
        return 1

    # Validate paths exist
    if not args.repo.exists():
        print(f"Error: Repository not found: {args.repo}", file=sys.stderr)
        return 1
    if not args.config.exists():
        print(f"Error: Config file not found: {args.config}", file=sys.stderr)
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

    # Load config
    config = load_config(args.config)
    words = config.get("words", [])
    word_mapping = config.get("word_mapping", {})
    email_mapping = config.get("email_mapping", {})
    exclude_patterns = config.get("exclude_files", [])

    if not words:
        print("Error: No words specified in config file", file=sys.stderr)
        return 1

    # Load submodule mapping if provided
    submodule_mapping: dict[str, str] = {}
    if args.submodule_map:
        if not args.submodule_map.exists():
            print(
                f"Error: Submodule mapping file not found: {args.submodule_map}",
                file=sys.stderr,
            )
            return 1
        submodule_mapping = load_submodule_mapping(args.submodule_map)
        print(f"Loaded {len(submodule_mapping)} submodule mappings")

    print(f"Sanitising {len(words)} dirty words...")
    rewrite_repository(
        repo_path=args.repo,
        output_path=args.output,
        dirty_words=words,
        word_mapping=word_mapping,
        default_replacement=args.default,
        commit_map_path=args.commit_map,
        exclude_patterns=exclude_patterns,
        email_mapping=email_mapping,
        submodule_mapping=submodule_mapping,
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
