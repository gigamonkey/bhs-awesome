#!/usr/bin/env python

"""Rewrite objectives.tsv, dropping the number column and prepending a UUID.

Input columns:  unit, topic, lo, ek, number, text
Output columns: uuid, unit, topic, lo, ek, text
"""

import uuid
from argparse import ArgumentParser


def main():
    parser = ArgumentParser(description=__doc__)
    parser.add_argument("file", help="objectives.tsv to rewrite in place")
    args = parser.parse_args()

    rows = []
    with open(args.file, encoding="utf-8") as f:
        for line in f:
            line = line.rstrip("\n")
            if not line:
                continue
            unit, topic, lo, ek, _number, text = line.split("\t")
            rows.append((str(uuid.uuid4()), unit, topic, lo, ek, text))

    with open(args.file, "w", encoding="utf-8") as f:
        for row in rows:
            f.write("\t".join(row) + "\n")


if __name__ == "__main__":
    main()
