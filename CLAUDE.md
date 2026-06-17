# bhs-awesome

Tools for extracting, analyzing, and formatting AP Computer Science A (CSA) and
AP Computer Science Principles (CSP) curriculum content from PreTeXt XML files
and the College Board Course and Exam Description (CED) PDFs.

## Tech Stack

- Python 3.13, lxml, pypdf
- Package manager: `uv` (run scripts with `uv run <script>.py`)
- XML processing throughout; JSON configs for formatting rules
- `make` + `xsltproc` to render CED XML to HTML

## Project Structure

- `*.py` — Processing scripts (see below)
- `.xml-formats/` — JSON configs for `format_xml.py` (`ptx.json`, `quiz.json`, `mcqs.json`)
- `csa/` — AP CSA CED artifacts: PDF, `ced-2025-hierarchy.md`, `ced.xml`, `ced.html`, `mcqs.quiz`, and `learning-objectives/` (handwriting scans, OCR text, and `objectives.tsv`)
- `csp/` — AP CSP CED artifacts: PDF, `ced-hierarchy.md`, `ced.xml`, `ced.html`, and `sample.xml` (target schema)
- `ib/` — IB Computer Science guide: `ib-cs-guide-2025.pdf` and the extracted `ib-hierarchy.md` and `ib-hours.tsv`
- `decks/` — Flashcard `.deck` files (XML)
- `reports/` — Generated analysis reports (e.g., the book comparison)
- `lesson-planning/` — Lesson-planning system: `schema.sql` (canonical), `db.db` (live working copy, gitignored), `export/` (git-diffable TSV snapshots), and `app.py` + `templates/` (Flask web app). See `plans/lesson-planning.md`
- `bhsawesome/`, `csawesome/` — Local PreTeXt source trees extracted by `just-pretext.sh` (gitignored)
- `repos/` — Cloned source book git repos (gitignored)
- `plans/` — Implementation plans

## Key Scripts

| Script                  | Purpose                                                                                                                                                                                                   |
|-------------------------|-----------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------|
| `format_xml.py`         | XML formatter driven by `.xml-formats/*.json` configs. Supports inline/code/block/one-line/compact elements, compound code blocks, conditional rules, external formatters. Use `-i` for in-place editing. |
| `extract_key.py`        | Extracts JSON answer key from `.quiz` files (handles both multiple-choice and true/false questions)                                                                                                       |
| `extract_activities.py` | Extracts activities from a PreTeXt root file, groups by type into per-type `.ptx` files                                                                                                                  |
| `activity_report.py`    | Analyzes activity element structures and generates statistics. Options: `-d`/`--deep`, `-p`/`--prune`, `--ignore`, `-t`/`--tree`                                                                         |
| `compare_activities.py` | Compares activities between two PreTeXt root files; writes `a/`, `b/`, and `paired.tsv` to an output dir. Options: `--similarity jaccard\|jaccard-weighted\|lcs`, `-s`/`--shingle-size`                 |
| `filter_pairs.py`       | Filters a `compare_activities` output dir by threshold; writes `a/` and `b/` with unmatched activities annotated with `pair=` and `similarity=` attributes. Option: `-t`/`--threshold` (default 0.95)   |
| `hierarchy.py`             | Shared hierarchy-markdown parser used by `build_hierarchy_xml.py` and `build_hierarchy_db.py`. `parse_sections` auto-detects the flavor (CSA/CSP/IB/book) from the first heading and returns a flat list of nodes with verbatim ids and separate `head`/`body`; consumers apply their own id transforms. Exposes `LEVEL_TAGS` (per-level tags per flavor) |
| `build_hierarchy_xml.py`   | Converts a hierarchy markdown file to XML (auto-detects CSA, CSP, IB, or book flavor from the first heading). Root is `<ced>` for CSA/CSP, `<syllabus>` for IB, and `<book>` for book                     |
| `build_hierarchy_db.py`    | Loads a hierarchy markdown file (CSA/CSP CED, IB syllabus, or `extract_book_hierarchy.py` book output, auto-detected) into a SQLite table: one row per node, an id column per level (ancestors filled, deeper levels NULL), plus the node's raw markdown text |
| `load_nodes.py`            | Normalizes a hierarchy markdown file into the lesson-planning `nodes` table (course, node_id, parent_id, level, is_leaf, ordinal, text) — one uniform, course-scoped table across CSA/CSP/IB so the app's gap/coverage queries are flavor-agnostic. `--course` overrides the detected flavor |
| `import_objectives.py`     | Seeds the lesson-planning `objectives`/`course_objectives`/`coverage` tables from a learning-objectives TSV (each row's `ek` becomes a coverage edge); course-scoped, and warns on coverage node_ids absent from `nodes`. Supersedes `load_objectives.py`'s single-table mapping |
| `export_planning.py`       | Dumps the lesson-planning database's planning tables to sorted, git-diffable `<table>.tsv` snapshots (the DB is the live working copy; the TSVs are the committed state). The `nodes` table is excluded — it is regenerated from the hierarchy markdown |
| `extract_book_hierarchy.py`| Extracts the chapter/section/subsection hierarchy from a PreTeXt book (following `.ptx` includes) as a numbered markdown hierarchy (`# Chapter N:`, `## N.M`, `### N.M.K`)                              |
| `extract_ib_hierarchy.py`  | Extracts the IB Computer Science guide's five-level syllabus hierarchy (theme/topic/subtopic/learning-statement/content) from the guide PDF into a markdown hierarchy (`# Theme X:`, `## A1`, `### A1.1`, `#### A1.1.1`, `##### A1.1.1.1`); content ids are synthesized |
| `extract_ib_hours.py`      | Extracts per-topic teaching hours from the IB CS guide's syllabus outline table into a TSV (`topic`, `title`, `sl`, `hl`); an HL-only topic shows 0 SL hours                                              |
| `check_deck.py`         | Checks (and with `--fix`, repairs) the structure of a `.deck` file                                                                                                                                       |
| `rename_card_tags.py`   | Renames `<front>`/`<back>` to `<question>`/`<answer>` in a deck via text substitution (preserves formatting)                                                                                             |
| `uuidize_objectives.py` | Rewrites `objectives.tsv` in place, replacing the number column with a leading UUID                                                                                                                       |
| `list_files.py`         | Lists files in a PreTeXt document tree in topological order                                                                                                                                               |
| `identify.py`           | Adds UUID attributes to XML elements matching XPath expressions                                                                                                                                           |
| `lcs.py`                | LCS-based string similarity utilities                                                                                                                                                                     |
| `jaccard.py`            | Jaccard similarity on character k-grams (set and weighted/multiset variants)                                                                                                                             |

## Syncing Source Books

`just-pretext.sh <repo> <dest>` pulls a book's git repo and copies its PreTeXt
source tree (the files reachable from `main.ptx`, per `list_files.py`) into
`<dest>` (e.g. `bhsawesome/`, `csawesome/`).

## Building CED HTML

The CED pipeline is: `*/ced*hierarchy.md` → (`build_hierarchy_xml.py`) → `*/ced.xml`
→ (`make` via `ced-to-html.xsl`) → `*/ced.html`. (Only the CSA/CSP `<ced>` output
is rendered to HTML; IB XML uses a `<syllabus>` root and has no HTML stage.)

`make` renders `csa/ced.xml` and `csp/ced.xml` to `*/ced.html` with `xsltproc`;
`make clean` removes the generated HTML.

## Quiz Format

Questions in `.quiz` files use this XML structure:

```xml
<quiz>
  <title>Quiz Title</title>
  <instructions><p>...</p></instructions>

  <q>
    <title>Question Title</title>
    <question>
      <p>Question text</p>
      <code>code here</code>
    </question>
    <answers>
      <item correct="true">Correct answer</item>
      <item>Wrong answer</item>
    </answers>
  </q>
</quiz>
```

The only checked-in example is `csa/mcqs.quiz`. True/false questions use
`<answers type="tf" answer="t|f">` instead of `<item>` children.

## Deck Format

Flashcard `.deck` files are XML: a `<deck>` with a `<title>` and one or more
`<section>`s. Each section has a `<title>` and one or more `<cards>` groups; a
group starts with an `<ek>` (the essential-knowledge statement) followed by
`<card>`s. A card has a `<question>`, an `<answer>`, and three `<distractor>`s
(older decks use `<front>`/`<back>`; convert with `rename_card_tags.py`).
Validate with `check_deck.py`.

## Running Scripts

```bash
uv run format_xml.py -i csa/mcqs.quiz        # format quiz in place
uv run extract_key.py csa/mcqs.quiz          # extract answer key as JSON

# Build XML/DB artifacts from a hierarchy markdown file (CSA/CSP/IB/book)
uv run build_hierarchy_xml.py csa/ced-2025-hierarchy.md csa/ced.xml ap-csa-2025
uv run build_hierarchy_xml.py ib/ib-hierarchy.md ib/syllabus.xml ib-cs-2025
uv run build_hierarchy_db.py csa/ced-2025-hierarchy.md ced.db hierarchy
make                                         # render */ced.xml -> */ced.html

# Seed the lesson-planning database (nodes + raw objectives + coverage), then snapshot
uv run load_nodes.py csa/ced-2025-hierarchy.md lesson-planning/db.db
uv run import_objectives.py csa/learning-objectives/objectives.tsv lesson-planning/db.db
uv run export_planning.py lesson-planning/db.db lesson-planning/export/
uv run lesson-planning/app.py                # read-only coverage web app (port 5001)

# Extract the IB CS syllabus hierarchy and per-topic hours from the guide PDF
uv run extract_ib_hierarchy.py ib/ib-cs-guide-2025.pdf ib/ib-hierarchy.md
uv run extract_ib_hours.py ib/ib-cs-guide-2025.pdf ib/ib-hours.tsv

# Compare activities between two books
uv run compare_activities.py bhsawesome/main.ptx csawesome/main.ptx comparison/
uv run filter_pairs.py comparison/ filtered/ -t 0.90
```
