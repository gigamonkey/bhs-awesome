"""Convert a curriculum hierarchy markdown file to XML.

Handles four hierarchy flavors, detected from the first level-1 heading. The
document root is <ced> for the College Board flavors, <syllabus> for IB, and
<book> for the PreTeXt book flavor; its xml:id is given as a required argument.

CSP (e.g., csp/ced-hierarchy.md; schema from csp/sample.xml):
- # Big Idea N: TITLE (CODE)  ->  <big-idea xml:id="CODE"><title>TITLE</title>...
- ## ID TEXT                  ->  <essential-understanding xml:id="ID"><text>TEXT</text>...
- ### ID TEXT                 ->  <learning-objective xml:id="ID"><text>TEXT</text>...
- #### ID TEXT                ->  <essential-knowledge xml:id="ID"><text>TEXT</text>...

CSA (e.g., csa/ced-2025-hierarchy.md):
- # Unit N: TITLE             ->  <unit xml:id="unit-N"><title>TITLE</title>...
- ## ID TEXT                  ->  <topic xml:id="topic-ID"><text>TEXT</text>...
- ### ID TEXT                 ->  <learning-objective xml:id="lo-ID"><text>TEXT</text>...
- #### ID TEXT                ->  <essential-knowledge xml:id="ek-ID"><text>TEXT</text>...

IB (e.g., ib/ib-hierarchy.md):
- # Theme X: TITLE            ->  <theme xml:id="X"><title>TITLE</title>...
- ## ID TEXT                  ->  <topic xml:id="ID"><text>TEXT</text>...
- ### ID TEXT                 ->  <subtopic xml:id="ID"><text>TEXT</text>...
- #### ID TEXT                ->  <learning-statement xml:id="ID"><text>TEXT</text>...
- ##### ID TEXT               ->  <content xml:id="ID"><text>TEXT</text>...

book (e.g., extract_book_hierarchy.py output):
- # Chapter N: TITLE          ->  <chapter xml:id="chapter-N"><title>TITLE</title>...
- ## ID TEXT                  ->  <section xml:id="section-ID"><text>TEXT</text>...
- ### ID TEXT                 ->  <subsection xml:id="subsection-ID"><text>TEXT</text>...

CSA codes (e.g., 1.1.A.1) and book numbers (e.g., 1.1.1) start with a digit,
which is not a valid xml:id (NCName), so they get a level prefix like the unit-N
ids do. CSP and IB ids are already valid NCNames and used verbatim.

Bullet/lettered lists, code blocks, *italic*, and `code` are converted to
HTML-style markup inside <text>.
"""

import argparse
import re
import sys
import textwrap

from hierarchy import LEVEL_TAGS, parse_sections

LETTERED = re.compile(r"^([a-z])\. (.*)")
BULLET = re.compile(r"^- (.*)")

# The document root element, by flavor. The College Board flavors render through
# ced-to-html.xsl, which matches /ced; IB and book have no such pipeline.
ROOT_TAG = {"csa": "ced", "csp": "ced", "ib": "syllabus", "book": "book"}

# CSA codes (1.1.A.1) and book numbers (1.1.1) start with a digit, which is not a
# valid xml:id (NCName), so each level's id gets a per-level prefix.
ID_PREFIX = {
    "csa": {1: "unit", 2: "topic", 3: "lo", 4: "ek"},
    "book": {1: "chapter", 2: "section", 3: "subsection"},
}


def xml_id(flavor, level, raw_id):
    """Map a verbatim hierarchy id to a valid xml:id for the given flavor.

    CSP ids (Big Idea codes like "CRD-1.A") and IB ids (e.g. "A1.1.1.1") are
    already valid NCNames and used as is; CSA and book ids start with a digit, so
    they get a per-level prefix.
    """
    prefixes = ID_PREFIX.get(flavor)
    if prefixes:
        return f"{prefixes[level]}-{raw_id}"
    return raw_id


# --- Markdown body parser --------------------------------------------------

def parse_blocks(lines):
    """Parse a list of markdown lines into a list of block tuples.

    Returns blocks as (kind, content) where kind is one of:
        'p'    - paragraph,   content = inline-markdown string
        'pre'  - code block,  content = raw code string (newline-separated)
        'ul'   - unordered list, content = list of block-lists (one per <li>)
        'ol'   - lettered ordered list, content = list of block-lists
    """
    blocks = []
    i = 0
    n = len(lines)
    while i < n:
        # skip blank lines
        if not lines[i].strip():
            i += 1
            continue
        line = lines[i]
        if BULLET.match(line):
            items, i = parse_list(lines, i, kind="ul")
            blocks.append(("ul", items))
        elif LETTERED.match(line):
            items, i = parse_list(lines, i, kind="ol")
            blocks.append(("ol", items))
        elif line.startswith("    "):
            # top-level indented code block
            code, i = parse_code(lines, i)
            blocks.append(("pre", code))
        else:
            para, i = parse_paragraph(lines, i)
            blocks.append(("p", para))
    return blocks


def parse_paragraph(lines, start):
    """Collect consecutive non-blank, non-list, non-code lines into one paragraph."""
    out = []
    i = start
    while i < len(lines):
        ln = lines[i]
        if not ln.strip():
            break
        if BULLET.match(ln) or LETTERED.match(ln) or ln.startswith("    "):
            break
        out.append(ln.rstrip())
        i += 1
    return " ".join(out), i


def parse_code(lines, start):
    """Collect a code block: consecutive lines starting with 4 spaces (blanks allowed inside)."""
    out = []
    i = start
    while i < len(lines):
        ln = lines[i]
        if ln.startswith("    "):
            out.append(ln[4:])
            i += 1
        elif not ln.strip():
            # blank line could be part of code if next non-blank is also indented
            j = i + 1
            while j < len(lines) and not lines[j].strip():
                j += 1
            if j < len(lines) and lines[j].startswith("    "):
                out.append("")
                i += 1
            else:
                break
        else:
            break
    while out and not out[-1].strip():
        out.pop()
    return "\n".join(out), i


def parse_list(lines, start, kind):
    """Parse a list (`ul` or `ol`) starting at lines[start].

    Each item collects: the marker line's text, plus any subsequent lines
    indented by 4+ spaces (which form nested blocks).
    """
    marker = BULLET if kind == "ul" else LETTERED
    items = []
    i = start
    while i < len(lines):
        m = marker.match(lines[i])
        if not m:
            break
        first = m.group(1) if kind == "ul" else m.group(2)
        i += 1
        sub = []
        while i < len(lines):
            ln = lines[i]
            if not ln.strip():
                sub.append("")
                i += 1
                continue
            if ln.startswith("    "):
                sub.append(ln[4:])
                i += 1
                continue
            break
        while sub and not sub[-1].strip():
            sub.pop()
        if sub:
            item_blocks = parse_blocks([first, ""] + sub)
        else:
            item_blocks = [("p", first)]
        items.append(item_blocks)
    return items, i


# --- Inline + block rendering ----------------------------------------------

def render_inline(text):
    """Escape XML special chars, then convert `code` and *em*."""
    text = text.replace("&", "&amp;").replace("<", "&lt;").replace(">", "&gt;")
    text = re.sub(r"`([^`]+)`", r"<code>\1</code>", text)
    text = re.sub(r"\*([^*]+)\*", r"<em>\1</em>", text)
    return text


def render_blocks(blocks, base_indent):
    """Render a list of blocks to XML lines. base_indent is the indent prefix (string)."""
    out = []
    for kind, content in blocks:
        if kind == "p":
            out.append(f"{base_indent}<p>{render_inline(content)}</p>")
        elif kind == "pre":
            escaped = content.replace("&", "&amp;").replace("<", "&lt;").replace(">", "&gt;")
            out.append(f"{base_indent}<pre>{escaped}</pre>")
        elif kind in ("ul", "ol"):
            tag_open = "<ul>" if kind == "ul" else '<ol type="a">'
            tag_close = "</ul>" if kind == "ul" else "</ol>"
            out.append(f"{base_indent}{tag_open}")
            for item_blocks in content:
                # Compact a single-paragraph item to <li>text</li>
                if len(item_blocks) == 1 and item_blocks[0][0] == "p":
                    out.append(f"{base_indent}  <li>{render_inline(item_blocks[0][1])}</li>")
                else:
                    out.append(f"{base_indent}  <li>")
                    out.extend(render_blocks(item_blocks, base_indent + "    "))
                    out.append(f"{base_indent}  </li>")
            out.append(f"{base_indent}{tag_close}")
    return out


def wrap_text_paragraph(text, indent):
    """Wrap a long line at ~78 chars, indented by `indent`. Returns multi-line string."""
    wrapped = textwrap.fill(text, width=78, initial_indent=indent, subsequent_indent=indent,
                            break_long_words=False, break_on_hyphens=False)
    return wrapped


def render_text_element(title, body_blocks, indent_level):
    """Render the <text> element containing title prose + body blocks."""
    ind = "  " * indent_level
    inner_ind = "  " * (indent_level + 1)
    if not body_blocks:
        wrapped = wrap_text_paragraph(render_inline(title), inner_ind)
        return [f"{ind}<text>", wrapped, f"{ind}</text>"]
    out = [f"{ind}<text>"]
    out.append(f"{inner_ind}<p>{render_inline(title)}</p>")
    out.extend(render_blocks(body_blocks, inner_ind))
    out.append(f"{ind}</text>")
    return out


# --- Top-level builder -----------------------------------------------------

def build_xml(flavor, sections, level_tag, root_tag, root_id):
    out = [f'<{root_tag} xml:id="{root_id}">']
    # stack of (level, indent_level) so we know when to close ancestors
    stack = []
    for sec in sections:
        # close any open sections at >= this level
        while stack and stack[-1][0] >= sec["level"]:
            level, indent = stack.pop()
            out.append(f"{'  ' * indent}</{level_tag[level]}>")
        indent = sec["level"]  # 1=big-idea -> 1 indent, etc.
        ind = "  " * indent
        tag = level_tag[sec["level"]]
        out.append("")
        out.append(f'{ind}<{tag} xml:id="{xml_id(flavor, sec["level"], sec["id"])}">')
        if sec["level"] == 1:
            out.append(f'{ind}  <title>{render_inline(sec["head"])}</title>')
        else:
            body_blocks = parse_blocks(sec["body"])
            out.extend(render_text_element(sec["head"], body_blocks, indent + 1))
        stack.append((sec["level"], indent))
    while stack:
        level, indent = stack.pop()
        out.append(f"{'  ' * indent}</{level_tag[level]}>")
    out.append(f"</{root_tag}>")
    return "\n".join(out) + "\n"


def main():
    parser = argparse.ArgumentParser(description=__doc__.splitlines()[0])
    parser.add_argument("input", help="hierarchy markdown file")
    parser.add_argument("output", help="XML output file")
    parser.add_argument("root_id", help="xml:id for the root element")
    args = parser.parse_args()

    with open(args.input) as f:
        md = f.read()
    flavor, sections = parse_sections(md)
    if flavor not in ROOT_TAG:
        supported = "/".join(sorted(ROOT_TAG))
        sys.exit(f"build_hierarchy_xml only supports {supported} hierarchies, not {flavor!r}")
    level_tag = LEVEL_TAGS[flavor]
    xml = build_xml(flavor, sections, level_tag, ROOT_TAG[flavor], args.root_id)
    with open(args.output, "w") as f:
        f.write(xml)
    counts = {level: 0 for level in level_tag}
    for s in sections:
        counts[s["level"]] += 1
    print(f"{flavor}: " + " ".join(f"{level_tag[lvl]}={counts[lvl]}" for lvl in sorted(counts)))


if __name__ == "__main__":
    main()
