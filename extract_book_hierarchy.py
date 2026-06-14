"""Extract the chapter/section/subsection hierarchy from a PreTeXt book.

Starting from a PreTeXt root file (e.g. bhsawesome/main.ptx), follows the
structural `xi:include`s and emits a markdown hierarchy whose headings carry a
hierarchical number for each division:

    # Chapter 1: Introduction
    ## 1.1 What is programming? What is Java?
    ### 1.1.1 Telling the computer what to do

Chapters keep a `Chapter N:` label (a marker for sniffing the hierarchy style);
sections and subsections use a bare dotted number. Chapters are numbered in
document order; section and subsection numbers reset within their parent. Titles preserve `<c>` as `code` and `<em>` as *emphasis*.
Only `.ptx` includes are followed, so asset includes (e.g. Java source pulled
in for listings) are ignored and need not be present.
"""

import argparse
import os
import sys

from lxml import etree

XINCLUDE = "{http://www.w3.org/2001/XInclude}include"

# Division element -> heading level.
LEVELS = {"chapter": 1, "section": 2, "subsection": 3}

# Inline elements converted to markdown; everything else contributes its text.
INLINE_WRAP = {"c": "`", "em": "*", "term": "*", "alert": "*"}


def resolve(path):
    """Parse a PreTeXt file, inlining structural (.ptx) xi:includes in place."""
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
    """Render an element's mixed content to a markdown-ish inline string."""
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
    if title is None:
        return "(untitled)"
    return " ".join(inline_text(title).split())


def extract(root):
    """Return [(level, tag, number, title)] for each division in order.

    `number` is a dotted hierarchical number (e.g. "1", "1.1", "1.1.1") that
    resets within each parent.
    """
    counters = [0, 0, 0]
    rows = []
    for division in root.iter(*LEVELS):
        level = LEVELS[division.tag]
        counters[level - 1] += 1
        for deeper in range(level, len(counters)):
            counters[deeper] = 0
        number = ".".join(str(counters[i]) for i in range(level))
        rows.append((level, division.tag, number, title_of(division)))
    return rows


def main():
    parser = argparse.ArgumentParser(description=__doc__.splitlines()[0])
    parser.add_argument("input", help="PreTeXt root file (e.g. main.ptx)")
    parser.add_argument("output", nargs="?", help="output markdown file (default: stdout)")
    args = parser.parse_args()

    root = resolve(args.input)
    rows = extract(root)
    text = "".join(
        f"# Chapter {number}: {title}\n"
        if level == 1
        else f"{'#' * level} {number} {title}\n"
        for level, _tag, number, title in rows
    )

    if args.output:
        with open(args.output, "w") as f:
            f.write(text)
    else:
        sys.stdout.write(text)

    counts = {tag: 0 for tag in LEVELS}
    for _level, tag, _number, _title in rows:
        counts[tag] += 1
    print(" ".join(f"{tag}={n}" for tag, n in counts.items()), file=sys.stderr)


if __name__ == "__main__":
    main()
