# bhs-awesome

Tools for extracting, analyzing, and formatting AP Computer Science A (CSA)
curriculum content from PreTeXt XML files and the College Board CED PDF.

## Tech Stack

- Python 3.13, lxml
- Package manager: `uv` (run scripts with `uv run <script>.py`)
- XML processing throughout; JSON configs for formatting rules

## Project Structure

- `*.py` — Processing scripts (see below)
- `.xml-formats/` — JSON configs for `format_xml.py` (`ptx.json`, `quiz.json`)
- `ced/` — AP CSA Course and Exam Description artifacts: PDF, hierarchy, `mcqs.quiz`
- `bhsawesome/` — Local copy of BHSawesome2 PreTeXt source (gitignored, synced by `sync-bhsawesome.sh`)
- `csawesome/` — Local copy of CSAwesome2 PreTeXt source (gitignored, synced by `sync-csawesome.sh`)
- `markup/` — Plain-text markup output (gitignored)
- `plans/` — Implementation plans; `plans/done/` holds completed plans (don't read unless asked)

## Key Scripts

| Script                  | Purpose                                                                                                                                                                                                   |
|-------------------------|-----------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------|
| `format_xml.py`         | XML formatter driven by `.xml-formats/*.json` configs. Supports inline/code/block/one-line/compact elements, compound code blocks, conditional rules, external formatters. Use `-i` for in-place editing. |
| `extract_key.py`        | Extracts JSON answer key from `.quiz` files                                                                                                                                                               |
| `extract_activities.py` | Extracts activities from a PreTeXt root file, groups by type into per-type `.ptx` files                                                                                                                  |
| `activity_report.py`    | Analyzes activity element structures and generates statistics. Options: `-d`/`--deep`, `-p`/`--prune`, `--ignore`, `-t`/`--tree`                                                                         |
| `compare_activities.py` | Compares activities between two PreTeXt root files; writes `a/`, `b/`, and `paired.tsv` to an output dir. Options: `--similarity jaccard\|jaccard-weighted\|lcs`, `-s`/`--shingle-size`                 |
| `filter_pairs.py`       | Filters a `compare_activities` output dir by threshold; writes `a/` and `b/` with unmatched activities annotated with `pair=` and `similarity=` attributes. Option: `-t`/`--threshold` (default 0.95)   |
| `list_files.py`         | Lists files in a PreTeXt document tree in topological order                                                                                                                                               |
| `identify.py`           | Adds UUID attributes to XML elements matching XPath expressions                                                                                                                                           |
| `lcs.py`                | LCS-based string similarity utilities                                                                                                                                                                     |
| `jaccard.py`            | Jaccard similarity on character k-grams (set and weighted/multiset variants)                                                                                                                             |

## Sync Scripts

- `sync-bhsawesome.sh` — Pulls BHSawesome2 and copies the PreTeXt source tree into `bhsawesome/`
- `sync-csawesome.sh` — Pulls CSAwesome2 and rsyncs its PreTeXt source into `csawesome/`

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

The only checked-in example is `ced/mcqs.quiz`.

## Running Scripts

```bash
uv run format_xml.py -i ced/mcqs.quiz        # format quiz in place
uv run extract_key.py ced/mcqs.quiz          # extract answer key as JSON

# Compare activities between two books
uv run compare_activities.py bhsawesome/main.ptx csawesome/main.ptx comparison/
uv run filter_pairs.py comparison/ filtered/ -t 0.90
```
