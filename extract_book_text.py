"""Dump each division's full text from a PreTeXt book, keyed by dotted number.

Walks the structural xi:includes from a PreTeXt root (e.g. main.ptx) and emits a
single markdown file where every chapter/section/subsection heading carries the
same dotted hierarchical number used by extract_book_hierarchy.py, followed by
the readable text local to that division (paragraphs, list items, and code, but
*not* the text of nested divisions, which appear under their own headings).

This is a scratch helper for matching learning objectives to subsections: the
dotted ids line up with csa/bhsawesome-outline.md so an assignment of an
objective to, say, "6.3.3" can be read straight out of this dump.
"""

import argparse
import os
import sys

from lxml import etree

XINCLUDE = "{http://www.w3.org/2001/XInclude}include"
LEVELS = {"chapter": 1, "section": 2, "subsection": 3}
DIVISIONS = set(LEVELS)
INLINE_WRAP = {"c": "`", "em": "*", "term": "*", "alert": "*"}
# Elements whose rendered text we treat as its own block (newline separated).
BLOCK = {"p", "li", "title", "cell", "pre", "program", "code", "input", "output"}


def resolve(path):
    root = etree.parse(path).getroot()
    _resolve_includes(root, os.path.dirname(path))
    return root


def _resolve_includes(element, base):
    for child in list(element):
        if child.tag == XINCLUDE:
            href = child.get("href") or ""
            target = os.path.normpath(os.path.join(base, href))
            index = element.index(child)
            element.remove(child)
            if href.endswith(".ptx") and os.path.isfile(target):
                element.insert(index, resolve(target))
        elif isinstance(child.tag, str):
            _resolve_includes(child, base)


def inline_text(element):
    out = []
    if element.text:
        out.append(element.text)
    for child in element:
        if isinstance(child.tag, str):
            wrap = INLINE_WRAP.get(child.tag, "")
            out.append(f"{wrap}{inline_text(child)}{wrap}")
        if child.tail:
            out.append(child.tail)
    return "".join(out)


def title_of(division):
    title = division.find("title")
    return "(untitled)" if title is None else " ".join(inline_text(title).split())


def local_blocks(division, out):
    """Collect readable text blocks local to a division (not nested divisions)."""
    for child in division:
        if not isinstance(child.tag, str):
            continue
        if child.tag in DIVISIONS:
            continue  # rendered under its own heading
        if child.tag == "title":
            continue  # already shown in the heading
        _gather(child, out)


def _gather(element, out):
    if element.tag in ("program", "pre", "code", "input", "output"):
        text = "".join(element.itertext())
        text = text.strip("\n")
        if text.strip():
            out.append("```\n" + text + "\n```")
        return
    if element.tag in BLOCK:
        text = " ".join(inline_text(element).split())
        if text:
            out.append(text)
        return
    # Recurse into wrappers (statement, p-less containers, lists, tables, etc.)
    if element.text and element.text.strip():
        out.append(" ".join(element.text.split()))
    for child in element:
        if isinstance(child.tag, str):
            _gather(child, out)
        if child.tail and child.tail.strip():
            out.append(" ".join(child.tail.split()))


def walk(element, counters, sink):
    for child in element:
        if not isinstance(child.tag, str):
            continue
        if child.tag in DIVISIONS:
            level = LEVELS[child.tag]
            counters[level - 1] += 1
            for deeper in range(level, len(counters)):
                counters[deeper] = 0
            number = ".".join(str(counters[i]) for i in range(level))
            blocks = []
            local_blocks(child, blocks)
            sink.append((level, number, title_of(child), blocks))
            walk(child, counters, sink)
        else:
            walk(child, counters, sink)


def main():
    parser = argparse.ArgumentParser(description=__doc__.splitlines()[0])
    parser.add_argument("input", help="PreTeXt root file (e.g. main.ptx)")
    parser.add_argument("output", nargs="?", help="output markdown (default: stdout)")
    args = parser.parse_args()

    root = resolve(args.input)
    sink = []
    walk(root, [0, 0, 0], sink)

    parts = []
    for level, number, title, blocks in sink:
        if level == 1:
            parts.append(f"# Chapter {number}: {title}\n")
        else:
            parts.append(f"{'#' * level} {number} {title}\n")
        if blocks:
            parts.append("\n".join(blocks) + "\n")
    text = "\n".join(parts)

    if args.output:
        with open(args.output, "w") as f:
            f.write(text)
    else:
        sys.stdout.write(text)

    print(f"divisions={len(sink)}", file=sys.stderr)


if __name__ == "__main__":
    main()
