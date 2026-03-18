#!/usr/bin/env python

"""
General-purpose XML formatter.

Formats XML files with consistent indentation, text wrapping, and optional
CDATA sections for code elements. Element categories (inline, code,
preserve_whitespace, compact) are specified via a JSON config file; anything
not listed is treated as a block element.

Config JSON example:
{
  "indent": 2,
  "width": 80,
  "inline": ["em", "c", "url"],
  "code": ["code"],
  "preserve_whitespace": ["pre"],
  "compact": ["item"]
}
"""

import json
import re
from argparse import ArgumentParser
from sys import stderr, stdout
from textwrap import fill, dedent, indent

from lxml import etree
from xml.sax.saxutils import escape, quoteattr


# ── Configuration ────────────────────────────────────────────────────────────

DEFAULT_CONFIG = {
    "indent": 2,
    "width": 80,
    "inline": [],
    "code": [],
    "preserve_whitespace": [],
    "compact": [],
}

DEFAULT_NS = {"xml": "http://www.w3.org/XML/1998/namespace"}


def load_config(path):
    if path is None:
        return DEFAULT_CONFIG
    with open(path) as f:
        user = json.load(f)
    cfg = dict(DEFAULT_CONFIG)
    cfg.update(user)
    # Ensure list fields are sets for fast lookup.
    for key in ("inline", "code", "preserve_whitespace", "compact"):
        cfg[key] = set(cfg[key])
    return cfg


# ── Helpers ──────────────────────────────────────────────────────────────────

def indentation(level, cfg):
    return " " * (cfg["indent"] * level)


def open_tag(elem, ns, empty=False):
    s = f"<{namespaced(elem.tag, ns)}"
    for name, value in elem.attrib.items():
        s += f" {fmt_attr(name, value, ns)}"
    for prefix, url in elem.nsmap.items():
        if prefix not in ns:
            s += f' xmlns:{prefix}="{url}"'
    if empty:
        s += " /"
    s += ">"
    return s


def fmt_attr(name, value, ns):
    return f"{namespaced(name, ns)}={quoteattr(value)}"


def namespaced(name, ns):
    reverse = {v: k for k, v in ns.items()}
    if name.startswith("{"):
        uri, local = name[1:].split("}")
        prefix = reverse.get(uri)
        if prefix:
            return f"{prefix}:{local}"
        else:
            print(f"Unknown namespace {uri}", file=stderr)
            return name
    return name


def close_tag(elem, ns):
    return f"</{namespaced(elem.tag, ns)}>"


# ── Predicates ───────────────────────────────────────────────────────────────

def is_just_text(elem):
    return len(elem) == 0


def is_multiline(text):
    return len(text.split("\n")) > 1


def to_text(elem):
    return etree.tostring(elem, encoding="unicode", method="text")


def is_inline(elem, cfg):
    return elem.tag in cfg["inline"]


def is_code(elem, cfg):
    return elem.tag in cfg["code"]


def is_empty(elem):
    return (elem.text or "").strip() == "" and not len(elem)


def preserve_whitespace(elem, cfg):
    return elem.tag in cfg["preserve_whitespace"]


def is_compact(elem, cfg):
    return elem.tag in cfg["compact"]


def empty_text(x):
    return (x or "").strip() == ""


def singleton_child(elem):
    return len(elem) == 1 and empty_text(elem.text) and empty_text(elem[0].tail)


def wrappable(elem, cfg):
    return not preserve_whitespace(elem, cfg) and (
        is_inline(elem, cfg) or all(is_inline(e, cfg) for e in elem)
    )


# ── Dedentation utilities ───────────────────────────────────────────────────

def measure_indentation(line):
    return float("inf") if line == "" else len(line) - len(dedent(line))


def dedent_amount(text):
    return min(measure_indentation(line) for line in text.split("\n"))


def common_indentation(texts):
    return min(dedent_amount(text) for text in texts)


def dedent_by(text, amount):
    if amount is None:
        return dedent(text)
    return "\n".join(
        line[amount:] if len(line) > 0 else line for line in text.split("\n")
    )


# ── Renderers ────────────────────────────────────────────────────────────────

def render_inline(elem, ns, cfg):
    if is_empty(elem):
        return open_tag(elem, ns, empty=True)

    s = open_tag(elem, ns)

    if is_just_text(elem):
        s += escape(elem.text.strip())
    else:
        if elem.text and elem.text.strip():
            s += escape(elem.text)

    for child in elem:
        s += render_inline(child, ns | elem.nsmap, cfg)
        if child.tail:
            s += escape(child.tail)

    s += close_tag(elem, ns)
    return s


def render_code(elem, ns, level, cfg):
    """Render a code element: dedent its text and wrap in CDATA if needed."""
    indent1 = indentation(level, cfg)
    indent2 = indentation(level + 1, cfg)

    text = re.sub(
        r"^(\s*\n)*",
        "",
        dedent_by(to_text(elem), None).rstrip(),
    )
    needs_cdata = any(e in text for e in "&<>")

    content = f"\n{indent1}{open_tag(elem, ns)}\n"

    if needs_cdata:
        content += f"{indent2}<![CDATA[\n"

    content += indent(text, indent2)

    if needs_cdata:
        content += f"\n{indent2}]]>"

    content += f"\n{indent1}{close_tag(elem, ns)}\n"
    return content


def render_comment(elem, level, cfg):
    return f"{elem}{elem.tail or ''}".rstrip()


def render_block(elem, ns, level, cfg):
    tag = f"\n{indentation(level, cfg)}{open_tag(elem, ns)}"
    width = cfg["width"]

    if is_empty(elem):
        return f"\n{indentation(level, cfg)}{open_tag(elem, ns, empty=True)}"

    content = ""

    if elem.text and elem.text.strip():
        content += escape(elem.text.lstrip())

    if len(elem) > 0:
        if is_inline(elem[0], cfg):
            content = re.sub(r"\s+$", " ", content)
        else:
            content = content.rstrip()

    for child in elem:
        content += serialize_element(child, ns | elem.nsmap, level + 1, cfg)
        if child.tail and child.tail.strip():
            content += escape(child.tail)
        elif child.tail and not child.tail.strip() and is_inline(child, cfg):
            content += " "

    if wrappable(elem, cfg):
        oneline = (
            f"{tag}{re.sub(r'(?s)\\s+', ' ', content).strip()}{close_tag(elem, ns)}"
        )

        if len(oneline) - 1 <= width:  # -1 for the leading newline.
            return oneline if is_compact(elem, cfg) else f"{oneline}\n"

        if not singleton_child(elem):
            filled = fill_with_indent(content, indentation(level + 1, cfg), width)
            return f"{tag}\n{filled}\n{indentation(level, cfg)}{close_tag(elem, ns)}\n"

    return f"{tag}\n{indentation(level + 1, cfg)}{content.strip()}\n{indentation(level, cfg)}{close_tag(elem, ns)}\n"


def render_with_whitespace(elem, ns, level, cfg):
    if is_empty(elem):
        return f"\n{indentation(level, cfg)}{open_tag(elem, ns, empty=True)}"

    s = f"\n{indentation(level, cfg)}{open_tag(elem, ns)}"
    if elem.text and len(elem.text) > 0:
        s += escape(elem.text)
    for child in elem:
        s += render_child_with_whitespace(child, ns | elem.nsmap)
        if child.tail and len(child.tail) > 0:
            s += child.tail

    s = s.rstrip()
    s += f"\n{indentation(level, cfg)}"
    s += close_tag(elem, ns)
    s += "\n"
    return s


def render_child_with_whitespace(elem, ns):
    s = open_tag(elem, ns)
    if elem.text and len(elem.text) > 0:
        s += escape(elem.text)
    for child in elem:
        s += render_child_with_whitespace(child, ns | elem.nsmap)
        if child.tail and len(child.tail) > 0:
            s += child.tail
    s += close_tag(elem, ns)
    return s


# ── Text wrapping ────────────────────────────────────────────────────────────

def clean_text(s):
    return re.sub(r"\s+", " ", s.strip())


def fill_with_indent(text, i, width):
    return fill(
        clean_text(text),
        width=width,
        initial_indent=i,
        subsequent_indent=i,
        break_long_words=False,
        break_on_hyphens=False,
    )


# ── Main serializer ─────────────────────────────────────────────────────────

def serialize_element(elem, ns=DEFAULT_NS, level=0, cfg=DEFAULT_CONFIG):
    if not isinstance(elem.tag, str):
        return render_comment(elem, level, cfg)
    elif is_inline(elem, cfg):
        return render_inline(elem, ns, cfg)
    elif is_code(elem, cfg):
        return render_code(elem, ns, level, cfg)
    elif preserve_whitespace(elem, cfg):
        return render_with_whitespace(elem, ns, level, cfg)
    else:
        return render_block(elem, ns, level, cfg)


def document_elements(root):
    top_level = []
    e = root
    while e is not None:
        top_level.append(e)
        e = e.getprevious()
    top_level.reverse()
    e = root.getnext()
    while e is not None:
        top_level.append(e)
        e = e.getnext()
    return top_level


def reformat(filename, inplace, cfg):
    root = etree.parse(filename).getroot()
    f = open(filename, mode="w") if inplace else stdout
    print('<?xml version="1.0" encoding="utf-8"?>', file=f)
    for e in document_elements(root):
        print(serialize_element(e, cfg=cfg).rstrip(), file=f)
    if inplace:
        f.close()


# ── CLI ──────────────────────────────────────────────────────────────────────

if __name__ == "__main__":
    parser = ArgumentParser(
        prog="format-xml",
        description="General-purpose XML formatter with configurable element categories.",
    )

    parser.add_argument(
        "-i", "--inplace", action="store_true", help="Reformat in place"
    )
    parser.add_argument(
        "-q", "--quiet", action="store_true", help="Suppress progress output"
    )
    parser.add_argument(
        "-c", "--config", default=None, help="Path to JSON config file"
    )
    parser.add_argument("files", nargs="*", help="Files to reformat")

    args = parser.parse_args()
    cfg = load_config(args.config)

    for filename in args.files:
        if not args.quiet:
            print(f"{filename} ... ", file=stderr, end="")
        reformat(filename, args.inplace, cfg)
        if not args.quiet:
            print("ok.", file=stderr)
