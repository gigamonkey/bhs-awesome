# CED extraction workflows

These are **Claude Code Workflow scripts** (run via the `Workflow` tool, not
`uv run`) that extract the AP CSA and AP CSP CED hierarchies from the College
Board Course and Exam Description PDFs into the markdown files that drive the
rest of the CED pipeline (`build_ced_xml.py`, `build_ced_db.py`).

Unlike the deterministic extractors (`extract_ib_hierarchy.py`,
`extract_book_hierarchy.py`), these are **LLM extraction pipelines**: the CED
PDFs lay the "Required Course Content" out in multi-column boxes with sidebars
and exclusion statements that don't parse cleanly, so each section is read by an
agent (CSA reads pages as text; CSP reads them as images) and transcribed under
strict formatting rules. They are not deterministic — re-running can produce
small wording differences — so their *output* (`csa/ced-2025-hierarchy.md`,
`csp/ced-hierarchy.md`) is the checked-in source of truth, and these scripts are
the reproducible recipe for regenerating it.

## Provenance

- `extract-csa-ced-hierarchy.js` was **recovered** verbatim from the workflow
  that originally produced `csa/ced-2025-hierarchy.md` (it had been saved only
  under the session directory, not the repo). The PDF path, output dir, and the
  topic→page-range list were originally passed in as `args`; they are now inlined
  as defaults so the script is self-contained.

- `extract-csp-ced-hierarchy.js` was **reconstructed** from session
  `54430ae4` (2026-05-24), which produced `csp/ced-hierarchy.md` with no saved
  script — the work was driven by inline agent prompts, written to temporary
  `csp/.biN.md` files, concatenated with a bash heredoc, and the temp files
  deleted. This workflow reproduces that mechanism with the verbatim prompt rules
  and page ranges from that session.

## Running

Run from the repo root so the default relative PDF paths resolve. Invoke the
`Workflow` tool with the script path, e.g.:

```
Workflow({ scriptPath: 'workflows/extract-csa-ced-hierarchy.js' })
Workflow({ scriptPath: 'workflows/extract-csp-ced-hierarchy.js' })
```

Each workflow has an **Extract** phase (one agent per section), and an
**Assemble** phase (one agent concatenates the per-section files under their
unit / Big Idea headers and writes the final `*.md`). CSA adds a **Verify**
phase: a second, adversarial agent per topic re-reads the pages and corrects the
file before assembly.

Override any default by passing an `args` object (see the `DEFAULTS` block at the
top of each script): `pdf`, `outdir`, `output`, the per-section page-range list
(`topics` / `sections`), and the headers used for assembly (`units` / `bigIdeas`).
For example, to extract a single CSA topic:

```
Workflow({ scriptPath: 'workflows/extract-csa-ced-hierarchy.js',
           args: { topics: [{ id: '1.1', pages: '36-37' }] } })
```

## Structure and page ranges

**CSA** (`csa/ced-2025.pdf`) — one agent per *topic*; topics grouped into 4
units for assembly. Topic page ranges (e.g. `1.1` → pp. 36–37) are in the
`DEFAULTS.topics` list. Hierarchy: `# Unit N` → `## topic` → `### learning
objective` → `#### essential knowledge`.

**CSP** (`csp/ap-computer-science-principles-course-and-exam-description.pdf`) —
one agent per *Big Idea*, reading the appendix "Conceptual Framework" pages
(228–265). Big Idea 3 (AAP) is split across three agents because its page run is
long, each scoped to its enduring understanding(s):

| Section file | Big Idea | EU family | Pages |
|--------------|----------|-----------|-------|
| `bi1.md`  | 1 (CRD) | CRD-1, CRD-2 | 228–232 |
| `bi2.md`  | 2 (DAT) | all DAT | 233–237 |
| `bi3a.md` | 3 (AAP) | AAP-1 only | 238–241 |
| `bi3b.md` | 3 (AAP) | AAP-2 only | 241–248 |
| `bi3c.md` | 3 (AAP) | AAP-3, AAP-4 | 248–255 |
| `bi4.md`  | 4 (CSN) | all CSN | 256–259 |
| `bi5.md`  | 5 (IOC) | all IOC | 260–265 |

Hierarchy: `# Big Idea N` → `## enduring understanding` → `### learning
objective` → `#### essential knowledge`.

> Page ranges are tied to specific PDF editions. If you swap in a re-paginated
> PDF, update the page ranges in the script's `DEFAULTS` first.
