"""Load a hierarchy markdown file into a SQLite table.

Reads the CED hierarchy files produced for build_ced_xml.py (CSA or CSP flavor)
as well as the book hierarchy from extract_book_hierarchy.py, detecting the
flavor from the first level-1 heading. Writes one row per node in the
hierarchy. Each row has an id column for every level of the hierarchy -- the
node's own id plus its ancestors', with deeper levels left NULL -- and a text
column holding the node's text exactly as it appears in the .md file (the
heading text after the id, plus any body lines such as paragraphs, lists, and
code blocks, with surrounding blank lines trimmed).

Hierarchies may have any number of levels; columns are named after the level
tags, with hyphenated tags abbreviated to their initials:

- CSA columns:  unit, topic, lo, ek, text
- CSP columns:  bi, eu, lo, ek, text
- book columns: chapter, section, subsection, text
"""

import argparse
import re
import sqlite3
import sys

from ced_hierarchy import LEVEL_TAGS, parse_sections

# Table/column identifiers we generate must be plain SQL identifiers.
IDENT_RE = re.compile(r"^[A-Za-z_][A-Za-z0-9_]*$")


def section_text(sec):
    """Join a section's heading text and body, trimming surrounding blanks."""
    lines = ([sec["head"]] if sec["head"] else []) + sec["body"]
    while lines and not lines[0].strip():
        lines.pop(0)
    while lines and not lines[-1].strip():
        lines.pop()
    return "\n".join(lines)


def build_rows(sections, levels):
    """Return a list of (id_per_level..., text) tuples, one per section.

    `levels` is the sorted list of hierarchy levels; each row carries an id for
    every level, with the node's own level and deeper levels handled so that
    ancestors are filled in and deeper levels are NULL.
    """
    rows = []
    ids = {level: None for level in levels}
    for sec in sections:
        level = sec["level"]
        ids[level] = sec["id"]
        for deeper in levels:
            if deeper > level:
                ids[deeper] = None
        rows.append(tuple(ids[level] for level in levels) + (section_text(sec),))
    return rows


def column_names(flavor):
    """Id column name for each level, derived from the flavor's level tags.

    Hyphenated tags are abbreviated to their initials (e.g. learning-objective
    -> lo, essential-knowledge -> ek); single-word tags are used as-is.
    """
    tags = LEVEL_TAGS[flavor]

    def name(tag):
        return "".join(part[0] for part in tag.split("-")) if "-" in tag else tag

    return {level: name(tag) for level, tag in tags.items()}


def load(db_path, table, columns, rows):
    if not IDENT_RE.match(table):
        sys.exit(f"unsafe table name: {table!r}")
    id_cols = [columns[level] for level in sorted(columns)]
    col_defs = ", ".join(f'"{c}" TEXT' for c in id_cols) + ', "text" BLOB'
    placeholders = ", ".join(["?"] * (len(id_cols) + 1))
    conn = sqlite3.connect(db_path)
    try:
        conn.execute(f'DROP TABLE IF EXISTS "{table}"')
        conn.execute(f'CREATE TABLE "{table}" ({col_defs})')
        conn.executemany(f'INSERT INTO "{table}" VALUES ({placeholders})', rows)
        conn.commit()
    finally:
        conn.close()


def main():
    parser = argparse.ArgumentParser(description=__doc__.splitlines()[0])
    parser.add_argument("input", help="hierarchy markdown file")
    parser.add_argument("database", help="SQLite database file")
    parser.add_argument("table", help="table name to create and load")
    args = parser.parse_args()

    with open(args.input) as f:
        md = f.read()
    flavor, sections = parse_sections(md)
    columns = column_names(flavor)
    levels = sorted(columns)
    rows = build_rows(sections, levels)
    load(args.database, args.table, columns, rows)

    counts = {level: 0 for level in levels}
    for s in sections:
        counts[s["level"]] += 1
    print(
        f"{flavor}: loaded {len(rows)} rows into {args.table} ("
        + " ".join(f"{columns[lvl]}={counts[lvl]}" for lvl in levels)
        + ")"
    )


if __name__ == "__main__":
    main()
