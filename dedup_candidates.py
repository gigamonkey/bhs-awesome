"""Print candidate duplicate-objective clusters from the lesson-planning db.

A CLI over dedup.py: loads a course's active objectives and their coverage, runs
the similarity pre-filter, and prints the resulting clusters (each a group of
likely-duplicate objectives) for review. Decides nothing -- merging is a human
(or later automated semantic) step in the app.

    uv run dedup_candidates.py lesson-planning/db.db --course csa
    uv run dedup_candidates.py lesson-planning/db.db --method lcs --threshold 0.6
"""

import argparse
import sqlite3

import dedup


def load(db_path, course):
    conn = sqlite3.connect(db_path)
    conn.row_factory = sqlite3.Row
    try:
        objs = [(r["uuid"], r["text"]) for r in conn.execute(
            """SELECT o.uuid, o.text FROM objectives o
                 JOIN course_objectives co ON co.uuid = o.uuid AND co.course = ?
                WHERE o.status = 'active'""", (course,))]
        coverage = {}
        for r in conn.execute(
            "SELECT uuid, node_id FROM coverage WHERE course = ?", (course,)):
            coverage.setdefault(r["uuid"], set()).add(r["node_id"])
    finally:
        conn.close()
    return objs, coverage


def main():
    p = argparse.ArgumentParser(description=__doc__.splitlines()[0])
    p.add_argument("database")
    p.add_argument("--course", default="csa")
    p.add_argument("--method", choices=["jaccard", "lcs"], default="jaccard")
    p.add_argument("--threshold", type=float, default=dedup.THRESHOLD)
    args = p.parse_args()

    objs, coverage = load(args.database, args.course)
    text = dict(objs)
    groups, index = dedup.clusters_with_pairs(
        objs, coverage, threshold=args.threshold, method=args.method)

    dup_total = sum(len(g) for g in groups)
    print(f"{len(groups)} cluster(s) covering {dup_total} of {len(objs)} "
          f"objectives ({args.method}, threshold {args.threshold}):\n")
    for n, g in enumerate(groups, 1):
        members = sorted(g, key=lambda u: text[u])
        nodes = sorted({nd for u in members for nd in coverage.get(u, ())})
        print(f"[{n}] {len(members)} objectives  nodes: {', '.join(nodes) or '-'}")
        for u in members:
            print(f"    - {text[u]}")
        print()


if __name__ == "__main__":
    main()
