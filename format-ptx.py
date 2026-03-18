#!/usr/bin/env python

import subprocess
import re
from argparse import ArgumentParser
from sys import stderr, stdout
from textwrap import fill, dedent, indent
from xml.sax.saxutils import escape, quoteattr

from lxml import etree

INDENT = 2
WIDTH = 80
INLINE_TAGS = {
    "term",
    "url",
    "c",
    "h",
    "area",
    "em",
    "xref",
    "m",
    "pubtitle",
}
PRESERVE_WHITESPACE = {"cline", "pre"}
ONE_LINE = {"cline"}
COMPACT = {"cell", "idx", "premise"}
DEFAULT_NS = {"xml": "http://www.w3.org/XML/1998/namespace"}

format_code = False


def say(x):
    print(x, file=stderr)


def indentation(level):
    return " " * (INDENT * level)


def open_tag(elem, ns, empty=False):
    s = f"<{namespaced(elem.tag, ns)}"

    for name, value in elem.attrib.items():
        s += f" {attr(name, value, ns)}"

    for prefix, url in elem.nsmap.items():
        if prefix not in ns:
            s += f' xmlns:{prefix}="{url}"'

    if empty:
        s += " /"
    s += ">"
    return s


def attr(name, value, ns):
    return f"{namespaced(name, ns)}={quoteattr(value)}"


def namespaced(name, ns):
    reverseNS = {v: k for k, v in ns.items()}

    if name.startswith("{"):
        uri, local = name[1:].split("}")
        prefix = reverseNS.get(uri)
        if prefix:
            return f"{prefix}:{local}"
        else:
            print(f"Unknown namespace {uri}", file=stderr)
            return name
    return name


def close_tag(elem, ns):
    return f"</{namespaced(elem.tag, ns)}>"


def is_just_text(elem):
    return len(elem) == 0


def is_multiline(text):
    return len(text.split("\n")) > 1


def to_text(elem):
    return etree.tostring(elem, encoding="unicode", method="text")


def is_program(elem):
    return elem.tag == "program"


def is_pre_in_datafile(elem):
    return (
        elem.tag == "pre"
        and elem.getparent() is not None
        and elem.getparent().tag == "datafile"
        and not "source" in elem.attrib
    )


def is_inline(elem):
    return elem.tag in INLINE_TAGS


def is_empty(elem):
    return (elem.text or "").strip() == "" and not len(elem)


def preserve_whitespace(elem):
    return elem.tag in PRESERVE_WHITESPACE


def is_oneline(elem):
    return elem.tag in ONE_LINE


def empty_text(x):
    return (x or "").strip() == ""


def singleton_child(elem):
    return len(elem) == 1 and empty_text(elem.text) and empty_text(elem[0].tail)


def wrappable(elem):
    return not preserve_whitespace(elem) and (
        is_inline(elem) or all(is_inline(e) for e in elem)
    )


def render_inline(elem, ns):
    if is_empty(elem):
        return open_tag(elem, ns, empty=True)

    s = open_tag(elem, ns)

    if is_just_text(elem):
        s += escape(elem.text.strip())
    else:
        if elem.text and elem.text.strip():
            s += escape(elem.text)

    for child in elem:
        s += render_inline(child, ns | elem.nsmap)
        if child.tail:
            s += escape(child.tail)

    s += close_tag(elem, ns)
    return s


def render_program(elem, ns, level):
    """
    Render a <program> element. It may directly contain text which we then
    just render. If not, we need to check if there are <preamble> or <postamble>
    children. If so we need to combine the text from them and the <code> child
    and determine how much to dedent them so the relative indentation is
    preserved. For instance, if the code text is indented four spaces more than
    the preamble or the postamble, then they should be completely dedented, and
    the code should be dedented and then have the four extra spaces put back
    before we apply the main indentation. So we need to compute the common
    indentation of the text of all three elements.
    """

    if is_just_text(elem):
        # Simple <program> that directly contains code
        return render_verbatim_text(elem, ns, level)
    else:
        content = f"\n{indentation(level)}{open_tag(elem, ns)}\n"

        # Complex <program> with child elements
        code = elem.xpath("./*[self::preamble or self::code or self::postamble]")
        other = elem.xpath("./*[not(self::preamble or self::code or self::postamble)]")

        if code:
            d = common_indentation(to_text(x).rstrip() for x in code)
            for c in code:
                content += render_verbatim_text(c, ns, level + 1, d)

        if other:
            for o in other:
                content += render_verbatim_text(o, ns, level + 1)

        content += f"\n{indentation(level)}{close_tag(elem, ns)}\n"
        return content


def common_indentation(texts):
    return min(dedent_amount(text) for text in texts)


def dedent_amount(text):
    return min(measure_indentation(line) for line in text.split("\n"))


def measure_indentation(line):
    return float("inf") if line == "" else len(line) - len(dedent(line))


def dedent_by(text, amount):
    return (
        dedent(text)
        if amount is None
        else "\n".join(
            line[amount:] if len(line) > 0 else line for line in text.split("\n")
        )
    )


def render_verbatim_text(elem, ns, level, dedentation=None):
    indent1 = indentation(level)
    indent2 = indentation(level + 1)

    text = re.sub(
        r"^(\s*\n)*",
        "",
        maybe_formatted(dedent_by(to_text(elem), dedentation).rstrip()),
    )
    needs_cdata = any(e in text for e in "&<>")
    multiline = is_multiline(text)

    content = f"\n{indent1}{open_tag(elem, ns)}\n"

    if needs_cdata:
        content += f"{indent2}<![CDATA[\n"

    content += indent(text, indent2)

    if needs_cdata:
        content += f"\n{indent2}]]>"

    content += f"\n{indent1}{close_tag(elem, ns)}\n"

    return content


def maybe_formatted(text):
    if format_code:
        result = subprocess.run(
            ["java", "-jar", "google-java-format-1.25.2-all-deps.jar", "-a", "-"],
            capture_output=True,
            input=text,
            text=True,
            check=False,
        )
        if result.returncode != 0:
            print(f"Couldn't format\n{text}\n", file=stderr)

        return result.stdout if result.returncode == 0 else text
    else:
        return text


def render_comment(elem, level):
    return f"{elem}{elem.tail or ''}".rstrip()


def render_block(elem, ns, level=0):
    tag = f"\n{indentation(level)}{open_tag(elem, ns)}"

    if is_empty(elem):
        return f"\n{indentation(level)}{open_tag(elem, ns, empty=True)}"
    else:
        content = ""

        if elem.text and elem.text.strip():
            content += escape(elem.text.lstrip())

        if len(elem) > 0:
            if is_inline(elem[0]):
                content = re.sub(r"\s+$", " ", content)
            else:
                content = content.rstrip()

        for child in elem:
            content += serialize_element(child, ns | elem.nsmap, level + 1)
            if child.tail and child.tail.strip():
                content += escape(child.tail)
            elif child.tail and not child.tail.strip() and is_inline(child):
                content += " "

        if wrappable(elem):
            oneline = (
                f"{tag}{re.sub(r'(?s)\s+', ' ', content).strip()}{close_tag(elem, ns)}"
            )

            if len(oneline) - 1 <= WIDTH:  # -1 for the leading newline.
                return oneline if elem.tag in COMPACT else f"{oneline}\n"

            if not singleton_child(elem):
                filled = fill_with_indent(content, indentation(level + 1))
                return f"{tag}\n{filled}\n{indentation(level)}{close_tag(elem, ns)}\n"

        return f"{tag}\n{indentation(level + 1)}{content.strip()}\n{indentation(level)}{close_tag(elem, ns)}\n"


def clean_text(s):
    return re.sub(r"\s+", " ", s.strip())


def fill_with_indent(text, i):
    return fill(
        clean_text(text),
        width=WIDTH,
        initial_indent=i,
        subsequent_indent=i,
        break_long_words=False,
        break_on_hyphens=False,
    )


def render_with_whitespace(elem, ns, level=0):
    if is_empty(elem):
        return f"\n{indentation(level)}{open_tag(elem, ns, empty=True)}"

    s = f"\n{indentation(level)}{open_tag(elem, ns)}"
    if elem.text and len(elem.text) > 0:
        s += escape(elem.text)
    for child in elem:
        s += render_child_with_whitespace(child, ns | elem.nsmap)
        if child.tail and len(child.tail) > 0:
            s += child.tail

    s = s.rstrip()

    if not is_oneline(elem):
        s += f"\n{indentation(level)}"

    s += close_tag(elem, ns)

    if not is_oneline(elem):
        s += "\n"

    return s


def render_child_with_whitespace(elem, ns, level=0):
    s = open_tag(elem, ns)
    if elem.text and len(elem.text) > 0:
        s += escape(elem.text)
    for child in elem:
        s += render_child_with_whitespace(child, ns | elem.nsmap)
        if child.tail and len(child.tail) > 0:
            s += child.tail
    s += close_tag(elem, ns)
    return s


def serialize_element(elem, ns=DEFAULT_NS, level=0):
    if elem.tag == "program":
        render_program(elem, ns | elem.nsmap, level + 1)

    if not isinstance(elem.tag, str):
        return render_comment(elem, level)
    elif is_inline(elem):
        return render_inline(elem, ns)
    elif is_program(elem):
        return render_program(elem, ns, level)
    elif is_pre_in_datafile(elem):
        return render_verbatim_text(elem, ns, level)
    elif preserve_whitespace(elem):
        return render_with_whitespace(elem, ns, level)
    else:
        return render_block(elem, ns, level)


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


def reformat(filename, inplace):
    root = etree.parse(filename).getroot()

    f = open(filename, mode="w") if inplace else stdout

    print('<?xml version="1.0" encoding="utf-8"?>', file=f)
    for e in document_elements(root):
        print(serialize_element(e).rstrip(), file=f)


if __name__ == "__main__":
    parser = ArgumentParser(
        prog="format-ptx",
        description="Reformat PreText XML to be semi-human-digestible.",
    )

    parser.add_argument(
        "-i", "--inplace", action="store_true", help="Reformat in place"
    )
    parser.add_argument(
        "-q", "--quiet", action="store_true", help="Don't emit output about files."
    )
    parser.add_argument(
        "-f", "--format-code", action="store_true", help="Format Java code."
    )
    parser.add_argument("files", nargs="*", help="Files to reformat")

    args = parser.parse_args()

    format_code = args.format_code

    for f in args.files:
        if not args.quiet:
            print(f"{f} ... ", file=stderr, end="")
        reformat(f, args.inplace)
        if not args.quiet:
            print("ok.", file=stderr)
