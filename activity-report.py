#!/usr/bin/env python

"""Report on the different structures of activity elements in book files."""

from lxml import etree
from collections import Counter
import os
import sys
from argparse import ArgumentParser


XML_NS = "http://www.w3.org/XML/1998/namespace"
XML_ID = f"{{{XML_NS}}}id"

XI_NAMESPACE = "http://www.w3.org/2001/XInclude"
XI_TAG = f"{{{XI_NAMESPACE}}}include"


def process_xml(filename, base_dir=None):
    if base_dir is None:
        full_path = os.path.abspath(filename)
    else:
        full_path = os.path.join(base_dir, filename)

    tree = etree.parse(full_path)
    root = tree.getroot()

    return walk(root, base_dir=os.path.dirname(full_path))


def walk(elem, base_dir):
    if elem.tag == XI_TAG and elem.get("parse") != "text":
        href = elem.get("href")
        if href:
            included_path = os.path.join(base_dir, href)
            yield included_path
            yield from process_xml(href, base_dir)
    else:
        for child in elem:
            yield from walk(child, base_dir)


def signature(activity, deep=False, prune=None, ignore=None):
    """Return a hashable representation of an activity's structure.

    With deep=False, returns a tuple of direct child tag names.
    With deep=True, returns a nested tuple representing the full tree
    structure down to the leaves.
    prune is an optional set of element names to not descend into.
    ignore is an optional set of element names to omit entirely.
    """
    ignore = ignore or set()
    if deep:
        return _deep_sig(activity, prune=prune or set(), ignore=ignore)
    return tuple(c.tag for c in activity if isinstance(c.tag, str) and c.tag not in ignore)


def _deep_sig(elem, prune, ignore):
    """Recursively build a nested tuple of (tag, children...) for each element.

    When all children have the same tag, collapse them into a single
    representative child marked with ("*", ...). The representative is
    built by merging the structures of all instances.
    """
    if elem.tag in prune:
        return (elem.tag,)
    children = [
        _deep_sig(c, prune, ignore)
        for c in elem
        if isinstance(c.tag, str) and c.tag not in ignore
    ]
    if not children:
        return (elem.tag,)
    return (elem.tag, *_collapse_children(children))


def _collapse_children(children):
    """Deduplicate children by tag, merging same-tag siblings.

    Groups children by tag name, preserving first-seen order. When
    multiple children share a tag, their structures are merged into
    a single representative.
    """
    groups = {}
    order = []
    for child in children:
        tag = child[0]
        if tag not in groups:
            groups[tag] = []
            order.append(tag)
        groups[tag].append(child)
    result = []
    for tag in order:
        group = groups[tag]
        if len(group) == 1:
            result.append(group[0])
        else:
            result.append(_merge_sigs(group))
    return result


def _merge_sigs(sigs):
    """Merge multiple same-tag signatures into one representative.

    Collects the union of child structures across all instances,
    deduplicates by tag, and recursively merges where needed.
    """
    tag = sigs[0][0]
    all_children = []
    for sig in sigs:
        all_children.extend(sig[1:])
    if not all_children:
        return (tag,)
    return (tag, *_collapse_children(all_children))


def format_sig(sig, deep=False):
    """Format a signature for display."""
    if deep:
        # Skip the outer "activity" wrapper, show just its children
        children = sig[1:]
        return ", ".join(_format_deep(c) for c in children)
    return ", ".join(sig)


def _format_deep(sig):
    """Format a deep signature using {} for nesting, all on one line."""
    tag = sig[0]
    children = sig[1:]
    if not children:
        return tag
    inner = ", ".join(_format_deep(c) for c in children)
    return f"{tag}{{{inner}}}"


def _truncate_sig(sig, depth):
    """Truncate a deep signature to the given depth.

    depth=1 means just the tag name, depth=2 means tag + child tags, etc.
    depth=0 means no truncation (return as-is).
    """
    if depth == 0:
        return sig
    if depth <= 1:
        return (sig[0],)
    return (sig[0],) + tuple(_truncate_sig(c, depth - 1) for c in sig[1:])


def display_tree(items, remaining_depth, indent=0, min_trunc=2, verbose=False, examples=None):
    """Display a hierarchical tree of signatures grouped at increasing depth.

    items: list of (full_deep_sig, count)
    remaining_depth: how many display levels left (0 = unlimited)
    indent: current indentation level
    min_trunc: minimum truncation depth to try for grouping
    """
    from collections import defaultdict

    if not items:
        return

    # At the last level, show full sigs flat
    if remaining_depth == 1:
        for sig, count in sorted(items, key=lambda x: -x[1]):
            formatted = format_sig(sig, deep=True)
            line = f"{'  ' * indent}{count:4d}  {formatted}"
            if verbose and examples:
                line += f"  (e.g. {examples.get(sig, '?')})"
            print(line)
        return

    # Find the shallowest truncation depth that splits items into
    # multiple groups
    trunc = min_trunc
    while True:
        groups = defaultdict(list)
        for sig, count in items:
            key = _truncate_sig(sig, trunc)
            groups[key].append((sig, count))

        if len(groups) > 1:
            break

        # If truncation matches full sigs, we can't split further
        if all(_truncate_sig(sig, trunc) == sig for sig, _ in items):
            for sig, count in sorted(items, key=lambda x: -x[1]):
                formatted = format_sig(sig, deep=True)
                line = f"{'  ' * indent}{count:4d}  {formatted}"
                if verbose and examples:
                    line += f"  (e.g. {examples.get(sig, '?')})"
                print(line)
            return

        trunc += 1

    sorted_groups = sorted(groups.items(), key=lambda x: sum(c for _, c in x[1]), reverse=True)
    next_depth = 0 if remaining_depth == 0 else remaining_depth - 1

    for key, members in sorted_groups:
        total = sum(c for _, c in members)
        formatted = format_sig(key, deep=True)
        line = f"{'  ' * indent}{total:4d}  {formatted}"
        if verbose and examples and len(members) == 1:
            line += f"  (e.g. {examples.get(members[0][0], '?')})"
        print(line)

        if len(members) > 1:
            display_tree(members, next_depth, indent + 1, trunc + 1,
                         verbose=verbose, examples=examples)


if __name__ == "__main__":
    parser = ArgumentParser(
        prog="activity-report",
        description="Report on the different structures of activity elements.",
    )
    parser.add_argument("root", help="Root file")
    parser.add_argument(
        "-v", "--verbose", action="store_true",
        help="Show example labels for each structure",
    )
    parser.add_argument(
        "-d", "--deep", action="store_true",
        help="Use full tree structure down to leaves, not just direct children",
    )
    parser.add_argument(
        "-p", "--prune", action="append", default=[], metavar="ELEM",
        help="Don't descend into elements with this tag (can be repeated or comma-delimited)",
    )
    parser.add_argument(
        "--ignore", action="append", default=[], metavar="ELEM",
        help="Omit elements with this tag entirely (can be repeated or comma-delimited)",
    )
    parser.add_argument(
        "-t", "--tree", type=int, nargs="?", const=0, default=None, metavar="DEPTH",
        help="Hierarchical display with DEPTH levels (0 = unlimited, default). Implies --deep.",
    )

    args = parser.parse_args()

    if args.tree is not None:
        args.deep = True

    prune = set()
    for p in args.prune:
        prune.update(p.split(","))

    ignore = set()
    for i in args.ignore:
        ignore.update(i.split(","))

    signatures = Counter()
    examples = {}

    for source in process_xml(args.root):
        tree = etree.parse(source)
        for activity in tree.xpath("//activity"):
            sig = signature(activity, deep=args.deep, prune=prune, ignore=ignore)
            signatures[sig] += 1
            if sig not in examples:
                examples[sig] = activity.get("label", "?")

    total = sum(signatures.values())

    if args.tree is not None:
        items = [(sig, count) for sig, count in signatures.items()]
        print(f"{total} activities, {len(signatures)} distinct structures\n")
        display_tree(items, args.tree, verbose=args.verbose, examples=examples)
    else:
        print(f"{total} activities, {len(signatures)} distinct structures\n")

        for sig, count in signatures.most_common():
            formatted = format_sig(sig, deep=args.deep)
            line = f"{count:4d}  {formatted}"
            if args.verbose:
                line += f"  (e.g. {examples[sig]})"
            print(line)
