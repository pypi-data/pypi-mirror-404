# ────────────────────────────────────────────────────────────────────────────────────────
#   cli.py
#   ──────
#
#   Main CLI for git-rewrite with subcommand dispatch.
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

import sys
from pathlib import Path
from .argbuilder import ArgsParser
from .argbuilder import Namespace
from .version import VERSION_STR

# ────────────────────────────────────────────────────────────────────────────────────────
#   Descriptions
# ────────────────────────────────────────────────────────────────────────────────────────

SCAN_DESCRIPTION = """\
Scan a git repository for sensitive words without modifying anything.

This command streams through all commits and blobs using git fast-export,
searching for occurrences of words defined in your config file.
Use this to audit a repository before sanitising it.

The config file should be JSON with a "words" array:
  {"words": ["secretword", "internalname"]}

Example:
  git-rewrite scan -r ./my-repo -c dirty-words.json
  git-rewrite scan -r ./my-repo -c dirty-words.json -v  # verbose
"""

SANITISE_DESCRIPTION = """\
Rewrite git history to remove or replace sensitive words.

Creates a NEW repository with sanitised history. The original is never modified.
Uses git fast-export/fast-import for efficient streaming.

Features:
  - Replace words in file contents, commit messages, author/committer names
  - Map specific words to specific replacements (or use default "REDACTED")
  - Map author names to specific email addresses
  - Exclude specific files from the output (e.g., lock files)
  - Remap submodule commit references if you've sanitised submodules too

Config file (JSON):
  - words: list of words to find/replace
  - word_mapping: dict mapping words to replacements
  - email_mapping: dict mapping author names to emails
  - exclude_files: list of files to exclude

Example:
  git-rewrite sanitise -r ./dirty-repo -o ./clean-repo -c config.json
  git-rewrite sanitise --sample-config  # print example config
"""

FLATTEN_DESCRIPTION = """\
Flatten submodules by inlining their contents into the main repository.

Creates a NEW repository where submodule references (gitlinks) are replaced
with the actual file contents from those submodules at each commit.
Useful for merging submodule history into a monorepo.

The command will:
  1. Scan history to find all submodule paths and URLs
  2. Clone or use existing checkouts of submodule repositories
  3. Stream history, replacing gitlinks with actual file trees
  4. Write a commit mapping file (old SHA -> new SHA)

Use --scan-only to just list submodules without flattening.

Example:
  git-rewrite flatten -r ./repo-with-submodules -o ./flat-repo
  git-rewrite flatten -r ./repo --scan-only  # list submodules
"""

REMAP_DESCRIPTION = """\
Remap submodule commit references using a mapping file.

When you sanitise or rewrite a submodule repository, its commit SHAs change.
If you have a parent repository that references those submodules, the gitlink
references become invalid. This command updates those references.

The mapping file format is: old_sha new_sha (one per line)
This is the output from a previous sanitise operation.

Optionally rewrite submodule URLs in .gitmodules with --url-rewrite.

Example:
  git-rewrite remap -r ./parent -o ./remapped -m mapping.txt
  git-rewrite remap -r ./repo -o ./out -m map.txt \\
      --url-rewrite ../old-submodule.git ../new-submodule.git
"""

COMPOSE_DESCRIPTION = """\
Compose multiple commit mapping files into one.

When chaining operations (e.g., flatten -> sanitise), each produces a mapping
file. This command composes them: given A->B and B->C mappings, produces A->C.

Mapping files are processed in order, following the chain of transformations.
The format is: old_sha new_sha (one per line).

Example:
  git-rewrite compose -m flatten.txt -m sanitise.txt -o combined.txt
  git-rewrite compose -m a.txt -m b.txt -m c.txt -o final.txt
"""

# ────────────────────────────────────────────────────────────────────────────────────────
#   Argument Parsing
# ────────────────────────────────────────────────────────────────────────────────────────


# ────────────────────────────────────────────────────────────────────────────────────────
def create_parser() -> ArgsParser:
    """Create the main argument parser with subcommands."""
    parser = ArgsParser(
        prog="git-rewrite",
        description=(
            "Git history rewriting tools for sanitising, flattening, and remapping."
        ),
        version=f"git-rewrite {VERSION_STR}",
    )

    # =========== Common Options ===========

    common = parser.create_common_collection()
    common.add_argument(
        "-v",
        "--verbose",
        action="store_true",
        help="Show verbose output",
    )

    # =========== Scan Command ===========

    scan_cmd = parser.add_command(
        "scan",
        help="Scan repository for sensitive words (read-only)",
        description=SCAN_DESCRIPTION,
    )
    scan_cmd.add_argument(
        "-r",
        "--repo",
        type=Path,
        required=True,
        help="Path to the git repository",
    )
    scan_cmd.add_argument(
        "-c",
        "--config",
        type=Path,
        required=True,
        help="Path to JSON config file",
    )

    # =========== Sanitise Command ===========

    sanitise_cmd = parser.add_command(
        "sanitise",
        help="Rewrite history to remove sensitive words",
        description=SANITISE_DESCRIPTION,
    )
    sanitise_cmd.add_argument(
        "--sample-config",
        action="store_true",
        help="Print sample config and exit",
    )
    sanitise_cmd.add_argument(
        "-r",
        "--repo",
        type=Path,
        help="Path to source repository",
    )
    sanitise_cmd.add_argument(
        "-o",
        "--output",
        type=Path,
        help="Path for output repository",
    )
    sanitise_cmd.add_argument(
        "-c",
        "--config",
        type=Path,
        help="Path to JSON config file",
    )
    sanitise_cmd.add_argument(
        "--delete",
        action="store_true",
        help="Delete output directory if exists",
    )
    sanitise_cmd.add_argument(
        "-d",
        "--default",
        default="REDACTED",
        help="Default replacement word (default: REDACTED)",
    )
    sanitise_cmd.add_argument(
        "-m",
        "--commit-map",
        type=Path,
        help="Path to write commit mapping file",
    )
    sanitise_cmd.add_argument(
        "-s",
        "--submodule-map",
        type=Path,
        help="Path to submodule commit mapping file",
    )
    sanitise_cmd.add_argument(
        "--copy-remotes",
        action="store_true",
        help="Copy git remotes from source to output repository",
    )

    # =========== Flatten Command ===========

    flatten_cmd = parser.add_command(
        "flatten",
        help="Flatten submodules into main repository",
        description=FLATTEN_DESCRIPTION,
    )
    flatten_cmd.add_argument(
        "-r",
        "--repo",
        type=Path,
        required=True,
        help="Path to source repository",
    )
    flatten_cmd.add_argument(
        "-o",
        "--output",
        type=Path,
        help="Path for output repository",
    )
    flatten_cmd.add_argument(
        "-m",
        "--commit-map",
        type=Path,
        help="Path to write commit mapping file",
    )
    flatten_cmd.add_argument(
        "--delete",
        action="store_true",
        help="Delete output directory if exists",
    )
    flatten_cmd.add_argument(
        "--scan-only",
        action="store_true",
        help="Only scan and list submodules",
    )
    flatten_cmd.add_argument(
        "--copy-remotes",
        action="store_true",
        help="Copy git remotes from source to output repository",
    )

    # =========== Remap Command ===========

    remap_cmd = parser.add_command(
        "remap",
        help="Remap submodule commit references",
        description=REMAP_DESCRIPTION,
    )
    remap_cmd.add_argument(
        "-r",
        "--repo",
        type=Path,
        required=True,
        help="Path to source repository",
    )
    remap_cmd.add_argument(
        "-o",
        "--output",
        type=Path,
        required=True,
        help="Path for output repository",
    )
    remap_cmd.add_argument(
        "-m",
        "--commit-map",
        type=Path,
        required=True,
        help="Path to commit mapping file (old_sha new_sha per line)",
    )
    remap_cmd.add_argument(
        "--submodule-path",
        type=str,
        help="Specific submodule path to remap (for gitlink filtering)",
    )
    remap_cmd.add_argument(
        "--url-rewrite",
        nargs=2,
        action="append",
        metavar=("OLD_URL", "NEW_URL"),
        help="Rewrite URL in .gitmodules (can be specified multiple times)",
    )
    remap_cmd.add_argument(
        "--delete",
        action="store_true",
        help="Delete output directory if exists",
    )
    remap_cmd.add_argument(
        "--copy-remotes",
        action="store_true",
        help="Copy git remotes from source to output repository",
    )

    # =========== Compose Command ===========

    compose_cmd = parser.add_command(
        "compose",
        help="Compose multiple commit mapping files",
        description=COMPOSE_DESCRIPTION,
    )
    compose_cmd.add_argument(
        "-m",
        "--mapping",
        type=Path,
        action="append",
        dest="mappings",
        required=True,
        help="Mapping file to include (can be specified multiple times, in order)",
    )
    compose_cmd.add_argument(
        "-o",
        "--output",
        type=Path,
        required=True,
        help="Path for output mapping file",
    )

    return parser


# ────────────────────────────────────────────────────────────────────────────────────────
#   Main Entry Point
# ────────────────────────────────────────────────────────────────────────────────────────


# ────────────────────────────────────────────────────────────────────────────────────────
def main() -> int:
    """Main entry point."""
    from . import compose
    from . import flatten
    from . import remap
    from . import sanitise
    from . import scan

    parser = create_parser()
    args: Namespace = parser.parse()

    if not args.command:
        return 0  # Help was shown by ArgsParser

    commands = {
        "scan": scan.run,
        "sanitise": sanitise.run,
        "flatten": flatten.run,
        "remap": remap.run,
        "compose": compose.run,
    }

    return commands[args.command](args)


if __name__ == "__main__":
    sys.exit(main())
