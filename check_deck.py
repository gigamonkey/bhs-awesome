#!/usr/bin/env python3
"""Check/fix the structure of a .deck file.

Usage:
    python3 check_deck.py [--fix] <deck-file>

Checks:
    1. File parses as XML (after stripping any stray </content>/</invoke> tags).
    2. Root is <deck> with a <title> and one or more <section>s.
    3. Each <section> has a <title> and one or more <cards> groups.
    4. Each <cards> group starts with an <ek> followed by one or more <card>s.
    5. Each <card> has exactly one <question>, one <answer>, and three <distractor>s,
       in that order.

With --fix, the script rewrites the file with stray tags removed (if any were
found and the rest of the structure is valid).
"""

import argparse
import re
import sys
from pathlib import Path

from lxml import etree


STRAY_TAG_RE = re.compile(r"^\s*</(content|invoke)>\s*\n", re.MULTILINE)


def strip_stray_tags(text: str) -> tuple[str, int]:
    """Remove stray </content> and </invoke> lines. Return (new_text, count)."""
    new_text, count = STRAY_TAG_RE.subn("", text)
    return new_text, count


def check_card(card: etree._Element, path: str) -> list[str]:
    errors: list[str] = []
    children = [c for c in card if isinstance(c.tag, str)]  # skip comments
    tags = [c.tag for c in children]
    expected = ["question", "answer", "distractor", "distractor", "distractor"]
    if tags != expected:
        errors.append(
            f"{path}: expected children {expected}, got {tags}"
        )
    return errors


def check_cards_group(cards: etree._Element, path: str) -> list[str]:
    errors: list[str] = []
    children = [c for c in cards if isinstance(c.tag, str)]
    if not children:
        errors.append(f"{path}: empty <cards> group")
        return errors
    if children[0].tag != "ek":
        errors.append(f"{path}: first child should be <ek>, got <{children[0].tag}>")
    for i, child in enumerate(children[1:], start=1):
        if child.tag != "card":
            errors.append(
                f"{path}/child[{i}]: expected <card>, got <{child.tag}>"
            )
            continue
        errors.extend(check_card(child, f"{path}/card[{i}]"))
    return errors


def check_section(section: etree._Element, path: str) -> list[str]:
    errors: list[str] = []
    children = [c for c in section if isinstance(c.tag, str)]
    if not children or children[0].tag != "title":
        errors.append(f"{path}: missing <title>")
    cards_groups = [c for c in children if c.tag == "cards"]
    if not cards_groups:
        errors.append(f"{path}: no <cards> groups")
    for i, cards in enumerate(cards_groups):
        errors.extend(check_cards_group(cards, f"{path}/cards[{i}]"))
    other = [c for c in children if c.tag not in ("title", "cards")]
    for c in other:
        errors.append(f"{path}: unexpected child <{c.tag}>")
    return errors


def check_deck(root: etree._Element) -> list[str]:
    errors: list[str] = []
    if root.tag != "deck":
        errors.append(f"root: expected <deck>, got <{root.tag}>")
        return errors
    children = [c for c in root if isinstance(c.tag, str)]
    if not children or children[0].tag != "title":
        errors.append("deck: missing <title>")
    sections = [c for c in children if c.tag == "section"]
    if not sections:
        errors.append("deck: no <section>s")
    for i, section in enumerate(sections):
        errors.extend(check_section(section, f"deck/section[{i}]"))
    other = [c for c in children if c.tag not in ("title", "section")]
    for c in other:
        errors.append(f"deck: unexpected child <{c.tag}>")
    return errors


def main(argv: list[str]) -> int:
    ap = argparse.ArgumentParser()
    ap.add_argument("deck_file", type=Path)
    ap.add_argument("--fix", action="store_true", help="rewrite file with stray tags stripped")
    args = ap.parse_args(argv[1:])

    original = args.deck_file.read_text()
    cleaned, stray_count = strip_stray_tags(original)
    if stray_count:
        print(f"Stripped {stray_count} stray </content>/</invoke> line(s)")

    try:
        root = etree.fromstring(cleaned.encode("utf-8"))
    except etree.XMLSyntaxError as e:
        print(f"XML parse error: {e}", file=sys.stderr)
        return 1

    errors = check_deck(root)
    if errors:
        print(f"Found {len(errors)} structural issue(s):")
        for e in errors[:50]:
            print(f"  {e}")
        if len(errors) > 50:
            print(f"  ... and {len(errors) - 50} more")
        return 1

    # Report summary
    sections = root.findall("section")
    cards = root.findall(".//card")
    distractors = root.findall(".//distractor")
    print(
        f"OK: {len(sections)} sections, {len(cards)} cards, "
        f"{len(distractors)} distractors"
    )

    if args.fix and stray_count:
        args.deck_file.write_text(cleaned)
        print(f"Wrote cleaned file: {args.deck_file}")
    elif stray_count:
        print("(Re-run with --fix to rewrite the file without the stray tags.)")

    return 0


if __name__ == "__main__":
    sys.exit(main(sys.argv))
