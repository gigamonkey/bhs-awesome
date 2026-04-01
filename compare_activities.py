#!/usr/bin/env python

"""Compare activities between two PreTeXt root files, finding identical or similar pairs.

Extracts activities from both roots into <outdir>/a/ and <outdir>/b/, assigns
stable UUIDs, then writes:

  <outdir>/paired.tsv     — type, uuid_a, uuid_b, similarity (all pairings)
  <outdir>/unused-a/      — activities from A not paired above threshold
  <outdir>/unused-b/      — activities from B not paired above threshold

Activities in the unused dirs have pair= and similarity= attributes added.
"""

import hashlib
import os
import re
import sys
import uuid
from argparse import ArgumentParser
from collections import deque
from copy import deepcopy

from lxml import etree

from jaccard import similarity as jaccard_similarity
from extract_activities import extract_activities, write_groups

# shingle size for jaccard similarity
k = 6

DEFAULT_THRESHOLD = 0.95


def assign_uuids(chapter):
    """Assign UUIDs in-place to all <activity> elements that lack one."""
    for activity in chapter.xpath(".//activity"):
        if not activity.get("uuid"):
            activity.set("uuid", str(uuid.uuid4()))


def normalize(activity):
    """Return a compact, whitespace-free XML string with the uuid attribute removed."""
    elem = deepcopy(activity)
    if "uuid" in elem.attrib:
        del elem.attrib["uuid"]
    return re.sub(r"\s+", "", etree.tostring(elem, encoding="unicode"))


def sha1(s):
    return hashlib.sha1(s.encode()).hexdigest()


def match_type(atype, acts_a, acts_b, paired_f, pairings_a, pairings_b):
    """Match activities of one type between the two sides, writing to paired_f.

    Populates pairings_a and pairings_b with {uuid: (other_uuid, sim)} for
    every activity on each side.
    """
    items_a = [(act.get("uuid"), normalize(act)) for act in acts_a]
    items_b = [(act.get("uuid"), normalize(act)) for act in acts_b]

    # --- Exact-match pass via SHA1 ---
    hash_to_b = {}
    for uid, norm in items_b:
        hash_to_b.setdefault(sha1(norm), deque()).append((uid, norm))

    unmatched_a = []
    for uid_a, norm_a in items_a:
        bucket = hash_to_b.get(sha1(norm_a))
        if bucket:
            uid_b, _ = bucket.popleft()
            paired_f.write(f"{atype}\t{uid_a}\t{uid_b}\t1.0\n")
            pairings_a[uid_a] = (uid_b, 1.0)
            pairings_b[uid_b] = (uid_a, 1.0)
        else:
            unmatched_a.append((uid_a, norm_a))

    unmatched_b = [item for q in hash_to_b.values() for item in q]

    exact = len(items_a) - len(unmatched_a)
    print(f"  {exact} exact match(es)", file=sys.stderr)

    if not unmatched_a or not unmatched_b:
        for uid_a, _ in unmatched_a:
            paired_f.write(f"{atype}\t{uid_a}\t-\t0.0\n")
            pairings_a[uid_a] = ("-", 0.0)
        for uid_b, _ in unmatched_b:
            paired_f.write(f"{atype}\t-\t{uid_b}\t0.0\n")
            pairings_b[uid_b] = ("-", 0.0)
        return

    # --- Fuzzy-match pass ---
    # Drive from whichever side is smaller to bound the work.
    a_is_smaller = len(unmatched_a) <= len(unmatched_b)
    if a_is_smaller:
        smaller, larger = unmatched_a, unmatched_b
        def make_row(uid_s, uid_l, sim): return f"{atype}\t{uid_s}\t{uid_l}\t{sim}\n"
        def record(uid_s, uid_l, sim): pairings_a[uid_s] = (uid_l, sim); pairings_b[uid_l] = (uid_s, sim)
        def record_unmatched_small(uid_s): pairings_a[uid_s] = ("-", 0.0)
        def record_unmatched_large(uid_l): pairings_b[uid_l] = ("-", 0.0)
    else:
        smaller, larger = unmatched_b, unmatched_a
        def make_row(uid_s, uid_l, sim): return f"{atype}\t{uid_l}\t{uid_s}\t{sim}\n"
        def record(uid_s, uid_l, sim): pairings_b[uid_s] = (uid_l, sim); pairings_a[uid_l] = (uid_s, sim)
        def record_unmatched_small(uid_s): pairings_b[uid_s] = ("-", 0.0)
        def record_unmatched_large(uid_l): pairings_a[uid_l] = ("-", 0.0)

    print(
        f"  {len(unmatched_a)} unmatched in A, {len(unmatched_b)} unmatched in B "
        f"— fuzzy matching ({len(smaller)} × up to {len(larger)})...",
        file=sys.stderr,
    )

    available = list(larger)  # mutable pool; entries set to None when claimed

    for i, (uid_small, norm_small) in enumerate(smaller, 1):
        best_sim = -1.0
        best_idx = None

        for idx, entry in enumerate(available):
            if entry is None:
                continue
            uid_large, norm_large = entry
            sim = jaccard_similarity(norm_small, norm_large, k)["total"]
            if sim > best_sim:
                best_sim = sim
                best_idx = idx

        if best_idx is not None:
            uid_large, _ = available[best_idx]
            available[best_idx] = None
            paired_f.write(make_row(uid_small, uid_large, f"{best_sim:.6f}"))
            record(uid_small, uid_large, best_sim)
        else:
            paired_f.write(make_row(uid_small, "-", "0.0"))
            record_unmatched_small(uid_small)

        if i % 10 == 0 or i == len(smaller):
            print(f"  {i}/{len(smaller)} matched", file=sys.stderr)

    for entry in available:
        if entry is not None:
            uid_large, _ = entry
            paired_f.write(make_row("-", uid_large, "0.0"))
            record_unmatched_large(uid_large)


def write_unused(groups, pairings, threshold, outdir):
    """Write activities not paired above threshold to outdir.

    Each activity gets pair= and similarity= attributes reflecting its best match.
    Sections with no unused activities are omitted.
    """
    filtered = {}
    for atype, chapter in groups.items():
        new_chapter = etree.Element("chapter")
        for section in chapter:
            new_section = etree.Element("section")
            for k, v in section.attrib.items():
                new_section.set(k, v)
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

    write_groups(filtered, outdir)


def compare_activities(root_a, root_b, outdir, threshold=DEFAULT_THRESHOLD):
    print("Extracting activities from root A...", file=sys.stderr)
    groups_a = extract_activities(root_a)
    print("Extracting activities from root B...", file=sys.stderr)
    groups_b = extract_activities(root_b)

    for chapter in groups_a.values():
        assign_uuids(chapter)
    for chapter in groups_b.values():
        assign_uuids(chapter)

    print(f"Writing A-side activities to {outdir}/a/ ...", file=sys.stderr)
    write_groups(groups_a, os.path.join(outdir, "a"))
    print(f"Writing B-side activities to {outdir}/b/ ...", file=sys.stderr)
    write_groups(groups_b, os.path.join(outdir, "b"))

    types_a = set(groups_a.keys())
    types_b = set(groups_b.keys())
    only_a = types_a - types_b
    only_b = types_b - types_a

    if only_a:
        print(f"Types only in A: {', '.join(sorted(only_a))}", file=sys.stderr)
    if only_b:
        print(f"Types only in B: {', '.join(sorted(only_b))}", file=sys.stderr)

    pairings_a = {}
    pairings_b = {}

    paired_path = os.path.join(outdir, "paired.tsv")

    with open(paired_path, "w", buffering=1) as paired_f:
        for atype in sorted(only_a):
            for act in groups_a[atype].xpath(".//activity"):
                uid = act.get("uuid")
                paired_f.write(f"{atype}\t{uid}\t-\t0.0\n")
                pairings_a[uid] = ("-", 0.0)
        for atype in sorted(only_b):
            for act in groups_b[atype].xpath(".//activity"):
                uid = act.get("uuid")
                paired_f.write(f"{atype}\t-\t{uid}\t0.0\n")
                pairings_b[uid] = ("-", 0.0)

        for atype in sorted(types_a & types_b):
            acts_a = groups_a[atype].xpath(".//activity")
            acts_b = groups_b[atype].xpath(".//activity")
            print(f"\nType '{atype}': {len(acts_a)} in A, {len(acts_b)} in B", file=sys.stderr)
            match_type(atype, acts_a, acts_b, paired_f, pairings_a, pairings_b)

    print(f"\nWrote {paired_path}", file=sys.stderr)

    print(f"Writing unused A-side activities to {outdir}/unused-a/ ...", file=sys.stderr)
    write_unused(groups_a, pairings_a, threshold, os.path.join(outdir, "unused-a"))
    print(f"Writing unused B-side activities to {outdir}/unused-b/ ...", file=sys.stderr)
    write_unused(groups_b, pairings_b, threshold, os.path.join(outdir, "unused-b"))


if __name__ == "__main__":
    parser = ArgumentParser(
        prog="compare_activities",
        description=(
            "Find identical or similar activities between two PreTeXt root files. "
            "Extracts activities to <outdir>/a/ and <outdir>/b/, writes paired.tsv, "
            "and writes unused-a/ and unused-b/ for activities below the threshold."
        ),
    )
    parser.add_argument("root_a", help="First root PreTeXt file")
    parser.add_argument("root_b", help="Second root PreTeXt file")
    parser.add_argument("outdir", help="Output directory")
    parser.add_argument(
        "--threshold", type=float, default=DEFAULT_THRESHOLD,
        help=f"Minimum similarity to consider an activity paired (default: {DEFAULT_THRESHOLD})",
    )

    args = parser.parse_args()

    compare_activities(args.root_a, args.root_b, args.outdir, args.threshold)
