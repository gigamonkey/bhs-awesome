"""Extract per-area teaching hours from the IB Computer Science guide PDF.

The guide's "Syllabus outline" table lists the recommended teaching hours for
each syllabus area at standard level (SL) and higher level (HL), e.g.

    A1 Computer fundamentals 11 18
    ...
    B4 Abstract data types—HL only – 23

This writes a TSV with one row per area (header: area, title, sl, hl). An area
offered only at higher level shows "–" for SL in the table; that becomes 0 hours.
"""

import argparse
import re

from pypdf import PdfReader

# The outline table is the page carrying these two header strings.
TABLE_MARKERS = ("Syllabus component", "Teaching hours")

# An area row: id (A1..B4), title, then the SL and HL hour columns. Hours are an
# integer or an en/em dash ("–"/"-") meaning the area is not offered at SL.
AREA_ROW = re.compile(r"^([AB]\d)\s+(.+?)\s+([\d–-]+)\s+([\d–-]+)$")

# An HL-only area's title carries a trailing "—HL only" annotation; the HL-only
# status is already captured by 0 SL hours, so strip it from the title.
HL_ONLY = re.compile(r"\s*[—–-]\s*HL only$")


def hours(token):
    """Convert an hour cell to an int; a dash means the area isn't offered (0)."""
    return int(token) if token.isdigit() else 0


def find_table_page(reader):
    for page in reader.pages:
        text = page.extract_text() or ""
        if all(marker in text for marker in TABLE_MARKERS):
            return text
    raise SystemExit("could not find the syllabus outline table")


def parse_areas(text):
    rows = []
    for line in text.splitlines():
        m = AREA_ROW.match(line.strip())
        if m:
            title = HL_ONLY.sub("", m.group(2))
            rows.append((m.group(1), title, hours(m.group(3)), hours(m.group(4))))
    return rows


def main():
    parser = argparse.ArgumentParser(description=__doc__.splitlines()[0])
    parser.add_argument("input", help="IB CS guide PDF")
    parser.add_argument("output", help="hours TSV output file")
    args = parser.parse_args()

    reader = PdfReader(args.input)
    rows = parse_areas(find_table_page(reader))
    with open(args.output, "w") as f:
        f.write("area\ttitle\tsl\thl\n")
        for area, title, sl, hl in rows:
            f.write(f"{area}\t{title}\t{sl}\t{hl}\n")
    print(f"{len(rows)} areas")


if __name__ == "__main__":
    main()
