# ────────────────────────────────────────────────────────────────────────────────────────
#   run.py
#   ──────
#
#   Runner for the compose subcommand.
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
from typing import TYPE_CHECKING

if TYPE_CHECKING:
    import argparse
    from pathlib import Path

# ────────────────────────────────────────────────────────────────────────────────────────
#   Functions
# ────────────────────────────────────────────────────────────────────────────────────────


# ────────────────────────────────────────────────────────────────────────────────────────
def load_mapping(filepath: Path) -> dict[str, str]:
    """Load a commit mapping file (old_sha new_sha per line)."""
    mapping: dict[str, str] = {}
    with filepath.open(encoding="utf-8") as f:
        for line in f:
            line = line.strip()
            if not line:
                continue
            parts = line.split()
            if len(parts) >= 2:
                mapping[parts[0]] = parts[1]
    return mapping


# ────────────────────────────────────────────────────────────────────────────────────────
def compose_mappings(mappings: list[dict[str, str]]) -> dict[str, str]:
    """
    Compose multiple mappings into one.

    Given mappings [A->B, B->C, C->D], produces A->D.
    Each mapping is applied in order, following the chain.
    """
    if not mappings:
        return {}

    result = mappings[0].copy()

    for next_mapping in mappings[1:]:
        # For each key in result, follow the chain through next_mapping
        new_result: dict[str, str] = {}
        for original, intermediate in result.items():
            if intermediate in next_mapping:
                new_result[original] = next_mapping[intermediate]
            else:
                # No mapping found, keep intermediate as final
                new_result[original] = intermediate
        result = new_result

    return result


# ────────────────────────────────────────────────────────────────────────────────────────
def run(args: argparse.Namespace) -> int:
    """Run the compose subcommand."""
    # Validate input files exist
    for mapping_file in args.mappings:
        if not mapping_file.exists():
            print(f"Error: Mapping file not found: {mapping_file}", file=sys.stderr)
            return 1

    # Load all mappings
    mappings: list[dict[str, str]] = []
    for mapping_file in args.mappings:
        mapping = load_mapping(mapping_file)
        if args.verbose:
            print(f"Loaded {len(mapping)} entries from {mapping_file}")
        mappings.append(mapping)

    # Compose them
    result = compose_mappings(mappings)

    # Write output
    args.output.parent.mkdir(parents=True, exist_ok=True)
    with args.output.open("w", encoding="utf-8") as f:
        for old_sha, new_sha in sorted(result.items()):
            f.write(f"{old_sha} {new_sha}\n")

    print(f"Composed {len(args.mappings)} mappings -> {len(result)} entries")
    print(f"Output written to: {args.output}")

    return 0
