#!/usr/bin/env python

from collections import defaultdict
from copy import deepcopy
from lxml import etree
import os
import sys
from argparse import ArgumentParser


XML_NS = "http://www.w3.org/XML/1998/namespace"
XML_ID = f"{{{XML_NS}}}id"

XI_NAMESPACE = "http://www.w3.org/2001/XInclude"
XI_TAG = f"{{{XI_NAMESPACE}}}include"

# Elements that are "meta" rather than the primary activity type
META_TAGS = {"title", "statement", "hint", "solution" }


def process_xml(filename, base_dir=None):
    if base_dir is None:
        full_path = os.path.abspath(filename)
    else:
        full_path = os.path.join(base_dir, filename)

    parser = etree.XMLParser()
    tree = etree.parse(full_path, parser)
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


def activity_type(activity):
    """Determine the type of an activity by finding its first non-meta child element."""
    for child in activity:
        if isinstance(child.tag, str) and child.tag not in META_TAGS:
            return child.tag
    return "other"


def extract_activities(root_file):
    """Extract activities grouped by type. Returns dict of type -> chapter element."""
    groups = defaultdict(lambda: etree.Element("chapter"))

    for source in process_xml(root_file):
        tree = etree.parse(source)
        root = tree.getroot()
        activities = root.xpath(".//activity")

        if not activities:
            continue

        # Group activities from this file by type
        by_type = defaultdict(list)
        for activity in activities:
            by_type[activity_type(activity)].append(activity)

        # For each type that has activities in this file, add a section
        for atype, acts in by_type.items():
            chapter = groups[atype]
            section = etree.SubElement(chapter, "section")

            xml_id = root.get(XML_ID)
            if xml_id:
                section.set(XML_ID, xml_id)

            titles = root.xpath("title")
            if titles:
                section.append(deepcopy(titles[0]))

            for activity in acts:
                section.append(deepcopy(activity))

    return groups


if __name__ == "__main__":
    parser = ArgumentParser(
        prog="extract-activities",
        description="Extract activity elements from book files, organized by type into separate files.",
    )
    parser.add_argument("root", help="Root file")
    parser.add_argument("outdir", help="Output directory")
    parser.add_argument("--strip-xml-id", action="store_true", help="Remove all xml:id attributes from output")

    args = parser.parse_args()

    os.makedirs(args.outdir, exist_ok=True)

    groups = extract_activities(args.root)

    for atype, chapter in sorted(groups.items()):
        if args.strip_xml_id:
            for elem in chapter.iter():
                if XML_ID in elem.attrib:
                    del elem.attrib[XML_ID]

        outfile = os.path.join(args.outdir, f"{atype}.ptx")
        with open(outfile, "wb") as f:
            f.write(etree.tostring(chapter, pretty_print=True, xml_declaration=True, encoding="UTF-8"))
        count = len(chapter.xpath(".//activity"))
        print(f"{outfile}: {count} activities")
