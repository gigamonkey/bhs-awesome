# bhs-awesome

Tools for extracting, analyzing, and formatting AP Computer Science A (CSA) and
AP Computer Science Principles (CSP) curriculum content from PreTeXt XML files
and the College Board Course and Exam Description (CED) PDFs.

## Tech Stack

- Python 3.13, lxml
- Package manager: `uv` (run scripts with `uv run <script>.py`)
- XML processing throughout; JSON configs for formatting rules
- `make` + `xsltproc` to render CED XML to HTML

## Project Structure

- `*.py` — Processing scripts (see below)
- `.xml-formats/` — JSON configs for `format_xml.py` (`ptx.json`, `quiz.json`, `mcqs.json`)
- `csa/` — AP CSA CED artifacts: PDF, `ced-2025-hierarchy.md`, `ced.xml`, `ced.html`, `mcqs.quiz`, and `learning-objectives/` (handwriting scans, OCR text, and `objectives.tsv`)
- `csp/` — AP CSP CED artifacts: PDF, `ced-hierarchy.md`, `ced.xml`, `ced.html`, and `sample.xml` (target schema)
- `decks/` — Flashcard `.deck` files (XML)
- `reports/` — Generated analysis reports (e.g., the book comparison)
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
| `build_ced_xml.py`      | Converts a CED hierarchy markdown file to XML (auto-detects CSA or CSP flavor from the first heading)                                                                                                     |
| `build_ced_db.py`       | Loads a CED hierarchy markdown file into a SQLite table: one row per node, an id column per hierarchy level (ancestors filled, deeper levels NULL), plus the node's raw markdown text                     |
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

The CED pipeline is: `*/ced*hierarchy.md` → (`build_ced_xml.py`) → `*/ced.xml`
→ (`make` via `ced-to-html.xsl`) → `*/ced.html`.

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

# Build CED artifacts from a hierarchy markdown file
uv run build_ced_xml.py csa/ced-2025-hierarchy.md csa/ced.xml
uv run build_ced_db.py csa/ced-2025-hierarchy.md ced.db hierarchy
make                                         # render */ced.xml -> */ced.html

# Compare activities between two books
uv run compare_activities.py bhsawesome/main.ptx csawesome/main.ptx comparison/
uv run filter_pairs.py comparison/ filtered/ -t 0.90
```
