#!/usr/bin/env python3
"""Rename <front> -> <question> and <back> -> <answer> in a deck file.

Uses plain text substitution so formatting and whitespace are preserved
exactly (unlike an XML round-trip).
"""

import sys
from pathlib import Path


REPLACEMENTS = [
    ("<front>", "<question>"),
    ("</front>", "</question>"),
    ("<back>", "<answer>"),
    ("</back>", "</answer>"),
]


def rename_tags(text: str) -> str:
    for old, new in REPLACEMENTS:
        text = text.replace(old, new)
    return text


def main(argv: list[str]) -> int:
    if len(argv) != 2:
        print(f"usage: {argv[0]} <deck-file>", file=sys.stderr)
        return 2
    path = Path(argv[1])
    original = path.read_text()
    updated = rename_tags(original)
    path.write_text(updated)
    print(f"Updated {path}")
    return 0


if __name__ == "__main__":
    sys.exit(main(sys.argv))
