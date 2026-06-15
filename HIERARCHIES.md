# Hierarchies

Several scripts in this repo deal with **curriculum hierarchies**: the nested
tree of units/topics/objectives (AP CSA, AP CSP), themes/areas/topics (IB CS),
or chapters/sections (the PreTeXt source books). This document describes the
scripts that produce, store, and transform those hierarchies, the data that
flows between them, and the database schema. The final section lists
opportunities to deduplicate and regularize the code.

## Overview

All the hierarchy tooling pivots around one intermediate format: a **numbered
markdown hierarchy** in which heading depth (`#`, `##`, `###`, …) encodes tree
depth and each heading carries an id and some text. Extractors produce this
markdown from PDFs and PreTeXt source; downstream tools load it into SQLite or
render it to XML.

```
  CED PDFs ──(workflows/extract-*-ced-hierarchy.js, LLM)──┐
                                                          ▼   ┌─► build_ced_xml.py ─► */ced.xml ─(make)─► */ced.html
  PDF / PreTeXt ──(deterministic extractors)──► hierarchy markdown ──┤
                                                              └─► build_ced_db.py  ─► SQLite (one wide table per hierarchy)

  objectives.tsv ──────────────► load_objectives.py ─► SQLite (3 normalized tables)

  IB CS guide PDF ─► extract_ib_hours.py ─► ib/ib-hours.tsv
```

The markdown format is the contract between stages. Anything that can emit it —
a deterministic extractor, an LLM extraction workflow, or a hand-edited file —
can feed anything that consumes it.

## The markdown hierarchy format

A hierarchy file is a sequence of ATX-style markdown headings. The level-1
heading both names the root node **and** signals the *flavor* of the file, which
the consumers sniff to know how many levels there are and what each level means.

| Flavor | Level 1 | Level 2 | Level 3 | Level 4 | Level 5 |
|--------|---------|---------|---------|---------|---------|
| `csa`  | `# Unit N: TITLE` | `## 1.1 …` (topic) | `### 1.1.A …` (learning objective) | `#### 1.1.A.1 …` (essential knowledge) | — |
| `csp`  | `# Big Idea N: TITLE (CODE)` | `## CRD-1 …` (essential understanding) | `### CRD-1.A …` (learning objective) | `#### CRD-1.A.1 …` (essential knowledge) | — |
| `book` | `# Chapter N: TITLE` | `## N.M …` (section) | `### N.M.K …` (subsection) | — | — |
| `ib`   | `# Theme X: TITLE` | `## A1 …` (area) | `### A1.1 …` (topic) | `#### A1.1.1 …` (objective) | `##### A1.1.1.1 …` (essential knowledge) |

For levels 2 and below, the heading text is `ID␠TEXT`: a whitespace-free id
token followed by the node's prose. The body lines beneath a heading
(paragraphs, bullet/lettered lists, indented code blocks) belong to that node
until the next heading.

The level-1 heading is special-cased per flavor:

- `csp` carries a parenthesized short code (`(CRD)`) that becomes the root id.
- `csa`/`book` derive the root id from the unit/chapter number.

## Extractors: source → markdown

### `extract_book_hierarchy.py` — PreTeXt book → `book` markdown

Starting from a PreTeXt root (e.g. `bhsawesome/main.ptx`), it parses the XML,
inlines structural `xi:include`s (only `.ptx` includes are followed, so missing
asset includes are harmless), and walks the `chapter`/`section`/`subsection`
divisions in document order. It assigns a dotted hierarchical number that resets
within each parent and renders `<c>` as `` `code` `` and `<em>`/`<term>`/`<alert>`
as `*emphasis*` in titles. Output is headings only (no body text).

```bash
uv run extract_book_hierarchy.py bhsawesome/main.ptx bhsawesome-hierarchy.md
```

### `extract_ib_hierarchy.py` — IB CS guide PDF → `ib` markdown

Reads the IB Computer Science guide PDF and emits the five-level
theme/area/topic/objective/essential-knowledge hierarchy. It auto-detects the
syllabus-content pages (the contiguous run carrying the "Syllabus content"
footer, beginning at the scope-note page), strips page furniture, and coalesces
PDF line wrapping back into logical records. Learning objectives carry
three-part ids from the PDF; essential-knowledge items are bulleted and have no
id, so their id is **synthesized** as the objective id plus a sequential number
(`A1.1.1` → `A1.1.1.1`, `A1.1.1.2`, …). Non-hierarchy material (guiding/linking
questions, teaching-hour lines, the scope preamble) is dropped.

```bash
uv run extract_ib_hierarchy.py ib/ib-cs-guide-2025.pdf ib/ib-hierarchy.md
```

### `extract_ib_hours.py` — IB CS guide PDF → TSV (related, not a hierarchy)

A sibling of the IB extractor that pulls a *flat* table rather than a tree: the
per-area recommended teaching hours from the guide's "Syllabus outline" table.
It finds the table page by its header strings and parses each `A1 … SL HL` row,
treating a dash (an HL-only area) as 0 SL hours and stripping the "—HL only"
annotation from the title. Output columns: `area`, `title`, `sl`, `hl`.

```bash
uv run extract_ib_hours.py ib/ib-cs-guide-2025.pdf ib/ib-hours.tsv
```

### CED hierarchies — `workflows/extract-*-ced-hierarchy.js`

The CSA and CSP CED markdown files (`csa/ced-2025-hierarchy.md`,
`csp/ced-hierarchy.md`) are not produced by a deterministic Python extractor.
The College Board CED PDFs lay out the "Required Course Content" in multi-column
boxes with sidebars and exclusion statements that don't parse cleanly, so these
two hierarchies were extracted by **LLM extraction workflows** — Claude Code
`Workflow` scripts that read the PDF a section at a time (CSA per topic, CSP per
big idea) and transcribe each under strict formatting rules, then assemble the
final markdown.

Those workflows live in `workflows/` (see `workflows/README.md` for how to run
them and the per-section page ranges):

- `extract-csa-ced-hierarchy.js` — one agent per topic reads `csa/ced-2025.pdf`
  → per-topic markdown, an adversarial verify agent corrects each, then an
  assemble agent stitches them under the four unit headers. (Recovered verbatim
  from the original session workflow.)

- `extract-csp-ced-hierarchy.js` — one agent per big idea reads the CSP CED PDF
  pages (as images) → per-section markdown, then an assemble agent concatenates
  them under the five Big Idea headers. (Reconstructed from the session that
  first produced the file, which used inline prompts and saved no script.)

Because these pipelines are non-deterministic, the **checked-in markdown is the
source of truth** and the workflows are the reproducible recipe for regenerating
it. The resulting files are valid `csa`/`csp` markdown and feed the two builders
below.

## Loaders: hierarchy → database

### `build_ced_db.py` — markdown → one wide SQLite table

Loads any `csa`/`csp`/`book` hierarchy markdown into a SQLite table, **one row
per node**. It auto-detects the flavor from the level-1 heading and creates one
id column per level (named after the level tags, with hyphenated tags
abbreviated to their initials) plus a `text` column.

Each row carries the node's own id and all its ancestors' ids; deeper levels are
left `NULL`. The `text` column holds the node's text exactly as it appears in
the markdown — the heading text after the id, plus any body lines, with
surrounding blank lines trimmed. Ids are kept verbatim (e.g. `1.1.A.1`), unlike
the XML builder which prefixes them.

```bash
uv run build_ced_db.py csa/ced-2025-hierarchy.md ced.db hierarchy
```

Columns by flavor:

| Flavor | Columns (in order) |
|--------|--------------------|
| `csa`  | `unit`, `topic`, `lo`, `ek`, `text` |
| `csp`  | `bi`, `eu`, `lo`, `ek`, `text` |
| `book` | `chapter`, `section`, `subsection`, `text` |

The table is dropped and recreated on each run. Example: a row for an essential
knowledge node `1.1.A.1` has `unit=1`, `topic=1.1`, `lo=1.1.A`, `ek=1.1.A.1`; a
row for its parent topic `1.1` has `unit=1`, `topic=1.1`, and `lo`/`ek` `NULL`.

> Note: `build_ced_db.py` currently handles `csa`/`csp`/`book` but **not** the
> five-level `ib` flavor (see "Deduplication and regularization" below).

### `load_objectives.py` — objectives TSV → three normalized tables

A different loader for a different source: the learning-objectives TSV
(`csa/learning-objectives/objectives.tsv`, columns `uuid`, `unit`, `topic`,
`lo`, `ek`, `objective`). Rather than one wide table, it splits the data across
three tables designed to be shared across courses:

```sql
objectives(uuid, objective)                 -- the objective text, keyed by UUID
course_objectives(course, uuid)             -- which course an objective belongs to
csa_objectives(uuid, unit, topic, lo, ek)   -- a CSA objective's CED hierarchy mapping
```

Tables are created with `IF NOT EXISTS` and re-running **replaces only the
loaded course's rows** (deleting by the UUIDs previously recorded for the course
in `course_objectives`), so several courses can coexist in one database. The
`course` is hardcoded to `"csa"`.

```bash
uv run load_objectives.py csa/learning-objectives/objectives.tsv objectives.db
```

## Dumper: hierarchy → XML

### `build_ced_xml.py` — markdown → CED XML

Renders a `csa`/`csp` hierarchy markdown file to nested CED XML (the schema in
`csp/sample.xml`). It auto-detects the flavor and maps levels to elements:

| Level | `csa` element | `csp` element |
|-------|---------------|---------------|
| 1 | `<unit>` | `<big-idea>` |
| 2 | `<topic>` | `<essential-understanding>` |
| 3 | `<learning-objective>` | `<learning-objective>` |
| 4 | `<essential-knowledge>` | `<essential-knowledge>` |

Each node becomes an element with an `xml:id`. Because CSA ids start with a
digit (`1.1.A.1`), which is not a valid `xml:id` (NCName), CSA ids get a level
prefix (`topic-`, `lo-`, `ek-`); the unit id is `unit-N`. Level-1 nodes get a
`<title>`; deeper nodes get a `<text>` element. The markdown body is parsed into
blocks — paragraphs (`<p>`), indented code (`<pre>`), bullet lists (`<ul>`),
lettered lists (`<ol type="a">`) — and inline `` `code` `` and `*em*` are
converted to `<code>`/`<em>`.

```bash
uv run build_ced_xml.py csa/ced-2025-hierarchy.md csa/ced.xml
make                                          # */ced.xml -> */ced.html via xsltproc
```

This is the first stage of the CED HTML pipeline:
`*/ced*hierarchy.md` → (`build_ced_xml.py`) → `*/ced.xml` → (`make`/`ced-to-html.xsl`) → `*/ced.html`.

## Database schema summary

Two databases with different shapes, produced by the two loaders:

**`build_ced_db.py` (wide, one table per hierarchy):** one row per node, one id
column per level (ancestors filled, deeper levels `NULL`), plus a `text` column.
Column names depend on flavor (see table above). The table is dropped and
recreated each run; the table name is a CLI argument.

**`load_objectives.py` (normalized, three tables):**

```
objectives(uuid TEXT, objective TEXT)
course_objectives(course TEXT, uuid TEXT)
csa_objectives(uuid TEXT, unit TEXT, topic TEXT, lo TEXT, ek TEXT)
```

`uuid` is the join key. `objectives` and `course_objectives` are
course-agnostic; `csa_objectives` holds the CSA CED hierarchy coordinates for
each objective. Note the same conceptual columns (`unit`, `topic`, `lo`, `ek`)
appear here as in `build_ced_db.py`'s `csa` table — the two loaders independently
model the CSA hierarchy.

## Deduplication and regularization

The hierarchy scripts grew up alongside each other and share a lot of structure
that is currently copy-pasted or only partially shared. Opportunities, roughly
in order of payoff:

1. **Unify the markdown parser.** `build_ced_xml.py` and `build_ced_db.py` each
   define `HEADING`/`BIG_IDEA`/`UNIT`, `parse_top_heading`, and `parse_sections`.
   `build_ced_db.py` already imports the regexes and `LEVEL_TAGS` from
   `build_ced_xml.py` but then *reimplements* `parse_top_heading` and
   `parse_sections` (with verbatim ids and an extra `book` flavor) instead of
   sharing one parser. Extract a single `hierarchy.py` module that parses a
   markdown file into a flat list of `(level, id, head, body)` nodes plus a
   detected flavor, and have both tools consume it. The id-prefixing for XML
   (`topic-`, `lo-`, `ek-`) can be a render-time transform rather than baked into
   parsing.

2. **One source of truth for flavors and levels.** The flavor definitions are
   spread across `LEVEL_TAGS` (two copies — base in `build_ced_xml.py`, extended
   in `build_ced_db.py`), `CSA_ID_PREFIX`, `BIG_IDEA`/`UNIT`/`CHAPTER` regexes,
   and the column-abbreviation logic. A single registry mapping each flavor to
   its level tags, its level-1 heading pattern, and its xml:id rules would let new
   hierarchies (or schema changes) be added in one place.

3. **Wire the `ib` flavor through the loaders/dumpers.** The IB hierarchy is
   extracted to markdown but cannot be loaded by `build_ced_db.py` (no `ib` entry
   in `LEVEL_TAGS`) or rendered by `build_ced_xml.py` (only handles 4 levels).
   The wide-table loader is already level-count-agnostic, so adding `ib`
   (theme/area/topic/objective/knowledge → e.g. `theme`, `area`, `topic`,
   `objective`, `ek`) is mostly a registry entry. The XML builder would need to
   generalize beyond a fixed four levels.

4. **Converge the two database models.** `build_ced_db.py` and
   `load_objectives.py` both encode the CSA `unit/topic/lo/ek` columns
   independently. Decide whether the wide per-node table and the normalized
   objectives tables should share a schema (or whether one can be derived from the
   other via a view) so the CSA hierarchy isn't modeled twice.

5. **Factor out the boilerplate.** Every script ends with the same shape: an
   `argparse` parser built from `__doc__.splitlines()[0]`, a per-level count, and
   a summary `print`. A small shared `main`/reporting helper would remove the
   repetition and keep the summary output consistent.

6. **Share the SQLite identifier guard and load helper.** `build_ced_db.py` has
   an `IDENT_RE` table-name check and a generic create/insert routine; if other
   loaders gain configurable table names they should reuse it rather than
   re-derive it.
