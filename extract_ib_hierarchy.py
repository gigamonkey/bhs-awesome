"""Extract the IB Computer Science syllabus hierarchy from the guide PDF.

The IB CS guide organizes required course material into a five-level hierarchy:

- Theme              ->  # Theme A: Concepts of computer science
- Topic              ->  ## A1 Computer fundamentals
- Subtopic           ->  ### A1.1 Computer hardware and operation
- Learning statement ->  #### A1.1.1 Describe the functions ... of the main CPU components.
- Content            ->  ##### A1.1.1.1 Units: arithmetic logic unit (ALU), control unit (CU)

Learning statements carry three-part ids in the PDF; content items are bulleted
and have no id, so their id is synthesized as the learning-statement id plus a
sequential number.

Only the syllabus-content pages are read (auto-detected as the contiguous run of
pages carrying the "Syllabus content" footer, starting at the "A note on
syllabus scope and limits" page). The non-hierarchy material on those pages
(guiding questions, linking questions, teaching-hour lines, and the scope
preamble) is dropped.
"""

import argparse
import re

from pypdf import PdfReader

# Footer / running-header noise stripped from every page.
FOOTER = re.compile(r"^\d+\s*Computer science guide$")
SKIP_EXACT = {"Syllabus", "Syllabus content", "Syllabus outline"}

# Markers for the start/end of the syllabus-content section.
SCOPE_NOTE = "A note on syllabus scope and limits"
CONTENT_FOOTER = "Syllabus content"

# Record starters.
THEME = re.compile(r"^Theme ([AB]):\s*(.*)$")
# Node id: a letter, an optional stray dot (the guide has a "A.1.2.5" typo),
# then dot-separated numbers. 1 number = topic, 2 = subtopic, 3 = learning statement.
NODE_ID = re.compile(r"^([AB])\.?(\d+(?:\.\d+)*)\s+(.*)$", re.S)
BULLET = re.compile(r"^•\s*(.*)$")
# Lines that introduce non-hierarchy content; everything up to the next heading
# is skipped (their continuation lines and any following bullets).
SECTION_KW = ("Guiding question", "Linking questions", "Standard level",
              "Higher level", "A note on syllabus")

LEVEL_BY_DEPTH = {1: "topic", 2: "subtopic", 3: "learning-statement"}
HEADING_LEVEL = {
    "theme": 1,
    "topic": 2,
    "subtopic": 3,
    "learning-statement": 4,
    "content": 5,
}


def content_lines(reader):
    """Yield the footer-stripped lines of the syllabus-content pages, in order."""
    started = False
    for page in reader.pages:
        text = page.extract_text() or ""
        lines = text.splitlines()
        if not started:
            if any(line.strip() == SCOPE_NOTE for line in lines):
                started = True
            else:
                continue
        elif not any(line.strip() == CONTENT_FOOTER for line in lines):
            break  # past the last syllabus-content page
        for line in lines:
            s = line.strip()
            if s and s not in SKIP_EXACT and not FOOTER.match(s):
                yield s


def starter(line):
    """Return the record kind if `line` begins a new logical record, else None."""
    if THEME.match(line):
        return "theme"
    if BULLET.match(line):
        return "content"
    # A standalone "Note:" paragraph clarifies a learning statement but is not a
    # bulleted content item; keep it as its own item so it neither corrupts the
    # preceding bullet nor loses its text.
    if line.startswith("Note:"):
        return "content"
    if line.startswith(SECTION_KW) or line.startswith(("—", "“")):
        return "skip"
    m = NODE_ID.match(line)
    if m:
        return LEVEL_BY_DEPTH.get(m.group(2).count(".") + 1)
    return None


def coalesce(lines):
    """Join wrapped continuation lines into (kind, text) logical records."""
    records = []
    for line in lines:
        kind = starter(line)
        if kind:
            records.append([kind, line])
        elif records:
            prev = records[-1][1]
            # A trailing hyphen or slash marks a split compound (e.g. "problem-\n
            # solving", "input/\noutput") that rejoins without a space.
            sep = "" if prev.endswith(("-", "/")) else " "
            records[-1][1] = prev + sep + line
    return records


def node_id(text):
    """Return the canonical id and remaining text for an A1/A1.1/... heading."""
    m = NODE_ID.match(text)
    return m.group(1) + m.group(2), m.group(3).strip()


def build(records):
    """Render coalesced records to markdown heading lines."""
    out = []
    counts = {kind: 0 for kind in HEADING_LEVEL}
    skip_bullets = False
    statement = None
    content_n = 0
    for kind, text in records:
        if kind == "theme":
            m = THEME.match(text)
            out.append(f"# Theme {m.group(1)}: {m.group(2).strip()}")
            skip_bullets, statement = False, None
        elif kind in ("topic", "subtopic", "learning-statement"):
            ident, rest = node_id(text)
            out.append(f"{'#' * HEADING_LEVEL[kind]} {ident} {rest}")
            skip_bullets = False
            if kind == "learning-statement":
                statement, content_n = ident, 0
            else:
                statement = None
        elif kind == "content":
            if skip_bullets or statement is None:
                continue
            m = BULLET.match(text)
            body = m.group(1).strip() if m else text.strip()
            content_n += 1
            out.append(f"##### {statement}.{content_n} {body}")
        elif kind == "skip":
            skip_bullets = True
            continue
        counts[kind] += 1
    return out, counts


def main():
    parser = argparse.ArgumentParser(description=__doc__.splitlines()[0])
    parser.add_argument("input", help="IB CS guide PDF")
    parser.add_argument("output", help="hierarchy markdown output file")
    args = parser.parse_args()

    reader = PdfReader(args.input)
    records = coalesce(content_lines(reader))
    headings, counts = build(records)
    with open(args.output, "w") as f:
        f.write("\n\n".join(headings) + "\n")
    print(" ".join(f"{kind}={counts[kind]}" for kind in HEADING_LEVEL))


if __name__ == "__main__":
    main()
