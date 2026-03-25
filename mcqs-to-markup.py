#!/usr/bin/env python

"""Convert MCQ XML files to markup .txt format."""

import os
import re
from argparse import ArgumentParser
from sys import stdout
from textwrap import fill

from lxml import etree


def text_content(elem):
    """Extract text content from an element, collapsing whitespace.
    Renders <c> children in backticks."""
    parts = []
    if elem.text:
        parts.append(elem.text)
    for child in elem:
        if child.tag == "c":
            inner = child.text or ""
            parts.append(f"`{inner}`")
        else:
            parts.append(text_content(child))
        if child.tail:
            parts.append(child.tail)
    return re.sub(r"\s+", " ", "".join(parts)).strip()


def has_code(elem):
    """Check if element contains a <code> child."""
    return elem.find("code") is not None


def dedented_code(code_elem):
    """Extract text from a <code> element, stripping leading/trailing blank
    lines and removing common indentation."""
    raw = etree.tostring(code_elem, method="text", encoding="unicode")
    lines = raw.split("\n")

    while lines and lines[0].strip() == "":
        lines.pop(0)
    while lines and lines[-1].strip() == "":
        lines.pop()

    if not lines:
        return ""

    indents = [len(line) - len(line.lstrip()) for line in lines if line.strip()]
    common = min(indents) if indents else 0

    return "\n".join(line[common:] for line in lines)


def indented_code(code_elem, prefix="   "):
    """Dedent a <code> element and re-indent with prefix."""
    text = dedented_code(code_elem)
    return "\n".join(prefix + line for line in text.split("\n"))


def render_question(elem):
    """Render the <question> element as markup text."""
    parts = []
    for child in elem:
        if child.tag == "p":
            parts.append(fill(text_content(child), width=78))
        elif child.tag == "code":
            parts.append(indented_code(child))
        elif child.tag == "ul":
            for li in child:
                parts.append("- " + fill(text_content(li), width=76, subsequent_indent="  "))
    return "\n\n".join(parts)


def render_item(elem):
    """Render an answer <item> as a single markup choice."""
    code = elem.find("code")
    if code is not None:
        text = dedented_code(code)
        if "\n" in text:
            return indented_code(code)
        return "`" + text + "`"
    return text_content(elem)


def quiz_title(filename):
    """Derive a title from the filename."""
    base = os.path.splitext(os.path.basename(filename))[0]
    return base.replace("-", " ").replace("_", " ").title()


def convert(filename, out):
    tree = etree.parse(filename)
    root = tree.getroot()

    title_elem = root.find("title")
    title = text_content(title_elem) if title_elem is not None else quiz_title(filename)

    print("-*- mode: markup; -*-", file=out)
    print(file=out)
    print(f"* {title}", file=out)
    print(file=out)
    print("## instructions", file=out)
    print(file=out)

    instructions = root.find("instructions")
    if instructions is not None:
        print(render_question(instructions), file=out)
        print(file=out)

    print("##.", file=out)
    print(file=out)

    for mcq in root.iter("mcq"):
        title_elem = mcq.find("title")
        title = text_content(title_elem) if title_elem is not None else "Untitled"

        print(f"** {title}", file=out)
        print(file=out)

        question = mcq.find("question")
        if question is not None:
            print(render_question(question), file=out)
            print(file=out)

        answers = mcq.find("answers")
        if answers is not None:
            kind = "mchoices" if answers.get("kind") == "multiple" else "choices"
            print(f"## {kind}", file=out)
            print(file=out)
            for item in answers.findall("item"):
                print(render_item(item), file=out)
                print(file=out)

        print("##.", file=out)
        print(file=out)


if __name__ == "__main__":
    parser = ArgumentParser(
        prog="to-markup",
        description="Convert MCQ XML files to markup .txt format.",
    )
    parser.add_argument("files", nargs="+", help="MCQ XML files to convert")

    args = parser.parse_args()

    for filename in args.files:
        convert(filename, stdout)
