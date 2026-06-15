"""Load a learning-objectives TSV into normalized SQLite tables.

Reads csa/learning-objectives/objectives.tsv (a header row followed by columns
uuid, unit, topic, lo, ek, objective) and splits it across three tables:

    objectives(uuid, objective)                    -- the objective text
    course_objectives(course, uuid)                -- which course an objective is for
    csa_objectives(uuid, unit, topic, lo, ek)      -- CSA CED mapping for an objective

The tables are shared across courses, so re-running replaces only the loaded
course's rows (the CSA objectives) rather than dropping the tables.
"""

import argparse
import csv
import sqlite3

COURSE = "csa"

SCHEMA = [
    "CREATE TABLE IF NOT EXISTS objectives(uuid TEXT, objective TEXT)",
    "CREATE TABLE IF NOT EXISTS course_objectives(course TEXT, uuid TEXT)",
    "CREATE TABLE IF NOT EXISTS csa_objectives(uuid TEXT, unit TEXT, topic TEXT, lo TEXT, ek TEXT)",
]


def read_rows(path):
    with open(path, newline="", encoding="utf-8") as f:
        return list(csv.DictReader(f, delimiter="\t"))


def load(db_path, rows):
    conn = sqlite3.connect(db_path)
    try:
        for statement in SCHEMA:
            conn.execute(statement)

        # Replace only this course's rows so multiple courses can share the db.
        old = [u for (u,) in conn.execute(
            "SELECT uuid FROM course_objectives WHERE course = ?", (COURSE,)
        )]
        conn.executemany("DELETE FROM objectives WHERE uuid = ?", [(u,) for u in old])
        conn.executemany("DELETE FROM csa_objectives WHERE uuid = ?", [(u,) for u in old])
        conn.execute("DELETE FROM course_objectives WHERE course = ?", (COURSE,))

        conn.executemany(
            "INSERT INTO objectives VALUES (?, ?)",
            [(r["uuid"], r["objective"]) for r in rows],
        )
        conn.executemany(
            "INSERT INTO course_objectives VALUES (?, ?)",
            [(COURSE, r["uuid"]) for r in rows],
        )
        conn.executemany(
            "INSERT INTO csa_objectives VALUES (?, ?, ?, ?, ?)",
            [(r["uuid"], r["unit"], r["topic"], r["lo"], r["ek"]) for r in rows],
        )
        conn.commit()
    finally:
        conn.close()


def main():
    parser = argparse.ArgumentParser(description=__doc__.splitlines()[0])
    parser.add_argument("input", help="objectives TSV file")
    parser.add_argument("database", help="SQLite database file")
    args = parser.parse_args()

    rows = read_rows(args.input)
    load(args.database, rows)
    print(f"loaded {len(rows)} objectives for course {COURSE!r} into {args.database}")


if __name__ == "__main__":
    main()
