# bhs-awesome

Tools for extracting, analyzing, and formatting AP Computer Science A (CSA)
curriculum content from PreTeXt XML files and the College Board CED PDF.

## Tech Stack

- Python 3.13, lxml
- Package manager: `uv` (run scripts with `uv run <script>.py`)
- XML processing throughout; JSON configs for formatting rules

## Project Structure

- `*.py` — Processing scripts (see below)
- `.xml-formats/` — JSON configs for `format-xml.py` (`ptx.json`, `mcqs.json`)
- `mcqs/` — Multiple-choice question files in XML (`.mcqs` extension)
- `ced/` — AP CSA Course and Exam Description artifacts (PDF, extracted hierarchy, MCQs)
- `csawesome-activities/` — Activities extracted from CSAwesome, grouped by type
- `pretext/`, `csawesome/` — Full curriculum trees (gitignored, not in repo)
- `plans/` — Implementation plans; `plans/done/` holds completed plans (don't read unless asked)
- `regen` — Shell script that formats and converts CED MCQs to markup

## Key Scripts

| Script                  | Purpose                                                                                                                                                                                                   |
|-------------------------|-----------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------|
| `format-xml.py`         | XML formatter driven by `.xml-formats/*.json` configs. Supports inline/code/block/one-line/compact elements, compound code blocks, conditional rules, external formatters. Use `-i` for in-place editing. |
| `mcqs-to-markup.py`     | Converts `.mcqs` XML to plain text markup                                                                                                                                                                 |
| `extract-key.py`        | Extracts JSON answer key from `.mcqs` files                                                                                                                                                               |
| `extract-activities.py` | Extracts activities from a PreTeXt root file, groups by type                                                                                                                                              |
| `activity-report.py`    | Analyzes activity element structures and generates statistics                                                                                                                                             |
| `list-files.py`         | Lists files in a PreTeXt document tree in topological order                                                                                                                                               |
| `identify.py`           | Adds UUID attributes to XML elements matching XPath expressions                                                                                                                                           |

## MCQ Format

Questions in `.mcqs` files use this XML structure:

```xml
<mcq>
  <title>Question Title</title>
  <question>
    <p>Question text</p>
    <code><![CDATA[code here]]></code>
  </question>
  <answers>
    <item correct="true">Correct answer</item>
    <item>Wrong answer</item>
  </answers>
</mcq>
```

## Running Scripts

```bash
uv run format-xml.py -i mcqs/ced.mcqs    # format MCQs in place
uv run mcqs-to-markup.py mcqs/ced.mcqs   # convert to text markup
uv run extract-key.py mcqs/ced.mcqs      # extract answer key as JSON
./regen                                  # format + convert CED MCQs
```
