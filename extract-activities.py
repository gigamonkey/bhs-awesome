#!/usr/bin/env python

from copy import deepcopy
from lxml import etree
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


def extract_activities(root_file):
    chapter = etree.Element("chapter")

    for source in process_xml(root_file):
        tree = etree.parse(source)
        root = tree.getroot()
        activities = root.xpath(".//activity")

        if not activities:
            continue

        section = etree.SubElement(chapter, "section")

        # Copy xml:id from source section
        xml_id = root.get(XML_ID)
        if xml_id:
            section.set(XML_ID, xml_id)

        # Copy title element
        titles = root.xpath("title")
        if titles:
            section.append(deepcopy(titles[0]))

        for activity in activities:
            section.append(deepcopy(activity))

    return chapter


if __name__ == "__main__":
    parser = ArgumentParser(
        prog="extract-activities",
        description="Extract all activity elements from book files into a single XML document.",
    )
    parser.add_argument("root", help="Root file")

    args = parser.parse_args()

    chapter = extract_activities(args.root)
    sys.stdout.buffer.write(etree.tostring(chapter, pretty_print=True, xml_declaration=True, encoding="UTF-8"))
