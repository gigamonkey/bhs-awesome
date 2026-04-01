#!/usr/bin/env python

"""Filter a comparison directory by similarity threshold.

Reads paired.tsv and the a/ and b/ activity files from a directory produced
by compare_activities, then writes outdir/a/ and outdir/b/ containing only
the activities whose best pairing is below the threshold.

Each activity gets pair= and similarity= attributes reflecting its best match.
"""

import os
import sys
from argparse import ArgumentParser
from copy import deepcopy

from lxml import etree

from extract_activities import write_groups

DEFAULT_THRESHOLD = 0.95


def read_pairings(paired_tsv):
    """Read paired.tsv and return (pairings_a, pairings_b).

    Each is a dict of {uuid: (other_uuid, similarity)}.
    """
    pairings_a = {}
    pairings_b = {}
    with open(paired_tsv) as f:
        for line in f:
            _atype, uuid_a, uuid_b, sim = line.rstrip("\n").split("\t")
            sim = float(sim)
            if uuid_a != "-":
                pairings_a[uuid_a] = (uuid_b, sim)
            if uuid_b != "-":
                pairings_b[uuid_b] = (uuid_a, sim)
    return pairings_a, pairings_b


def read_groups(directory):
    """Read all .ptx files in directory and return a dict of type -> chapter element."""
    groups = {}
    for filename in sorted(os.listdir(directory)):
        if filename.endswith(".ptx"):
            atype = filename[:-4]
            tree = etree.parse(os.path.join(directory, filename))
            groups[atype] = tree.getroot()
    return groups


def filter_groups(groups, pairings, threshold):
    """Return a copy of groups with only activities whose pairing sim < threshold.

    Adds pair= and similarity= attributes to each kept activity.
    Omits sections and types that become empty after filtering.
    """
    filtered = {}
    for atype, chapter in groups.items():
        new_chapter = etree.Element("chapter")
        for section in chapter:
            new_section = etree.Element("section")
            for attr, val in section.attrib.items():
                new_section.set(attr, val)
            unused = []
            for child in section:
                if child.tag != "activity":
                    new_section.append(deepcopy(child))
                else:
                    uid = child.get("uuid")
                    other_uid, sim = pairings.get(uid, ("-", 0.0))
                    if sim < threshold:
                        act = deepcopy(child)
                        act.set("pair", other_uid)
                        act.set("similarity", f"{sim:.6f}")
                        unused.append(act)
            if unused:
                for act in unused:
                    new_section.append(act)
                new_chapter.append(new_section)
        if len(new_chapter):
            filtered[atype] = new_chapter
    return filtered


if __name__ == "__main__":
    parser = ArgumentParser(
        prog="filter_pairs",
        description=(
            "Filter a compare_activities output directory by similarity threshold, "
            "writing activities with no good match to outdir/a/ and outdir/b/."
        ),
    )
    parser.add_argument("indir", help="Directory produced by compare_activities")
    parser.add_argument("outdir", help="Output directory")
    parser.add_argument(
        "-t", "--threshold", type=float, default=DEFAULT_THRESHOLD,
        help=f"Similarity threshold below which activities are considered unmatched (default: {DEFAULT_THRESHOLD})",
    )

    args = parser.parse_args()

    pairings_a, pairings_b = read_pairings(os.path.join(args.indir, "paired.tsv"))

    groups_a = read_groups(os.path.join(args.indir, "a"))
    groups_b = read_groups(os.path.join(args.indir, "b"))

    unused_a = filter_groups(groups_a, pairings_a, args.threshold)
    unused_b = filter_groups(groups_b, pairings_b, args.threshold)

    write_groups(unused_a, os.path.join(args.outdir, "a"))
    write_groups(unused_b, os.path.join(args.outdir, "b"))
