# Plan: Remove the extracted tooling from `bhs-awesome`

## Goal

The two extractions are done. `hierarchy-extractors` now owns the
curriculum-hierarchy toolkit + CED/IB data, and `lesson-planning` owns the
course-agnostic planning app + engine. Both extraction plans deliberately left
this question open — each ends with *"after extraction, decide the fate of this
tooling in the old repo … separate cleanup, out of scope here."* **This is that
cleanup.** It deletes from `bhs-awesome` everything that now lives in one of the
two new repos, leaving a focused repo.

This is *not* another history rewrite. The extractions worked on throwaway
clones, so `bhs-awesome` was never modified — everything still exists here. This
is an ordinary `git rm` + edit cleanup on a branch, reviewable and revertible.
History is intentionally **kept** (the two new repos carry their own per-file
history; deleting the files here just stops the duplication going forward).

## Post-cleanup identity of `bhs-awesome`

What remains is a coherent unit: **AP CS curriculum *content* tooling** — quizzes,
flashcard decks, PreTeXt activity analysis, and the CSA learning-objectives
source data. No hierarchy extraction, no lesson-planning app. Third-party deps
collapse from `flask + lxml + pypdf` to **`lxml` only**.

## The closure (re-derived from the code)

Verified by import graph + data-reference grep, not by trusting the lists below:

- Every script that imports `hierarchy.py` — `build_hierarchy_xml.py`,
  `build_hierarchy_db.py`, `load_nodes.py`, `rebuild_db.py` — is a **moved**
  file. **No** remaining quiz/deck/activity/format script imports `hierarchy.py`,
  so it leaves cleanly.
- **No** remaining keeper references `csp/`, `ib/`, `csa/ced*`, or any hierarchy
  markdown/XML (grep over the keeper set: zero hits).
- Of the moved files, only `list_files.py` + `just-pretext.sh` are **dual-use**:
  the activity-comparison workflow (`compare_activities.py` over synced
  `bhsawesome/` + `csawesome/` book trees) still depends on them. They stay.
- Remaining third-party imports: `lxml` (many keepers); **`pypdf`** appears only
  in the moved `extract_ib_*`; **`flask`** only in the moved app.

## What to remove

### Moved to `hierarchy-extractors`

Scripts:

- `extract_ib_hierarchy.py`, `extract_ib_hours.py`
- `extract_book_hierarchy.py`, `extract_book_text.py`
- `hierarchy.py` (no remaining keeper imports it)
- `build_hierarchy_xml.py`, `build_hierarchy_db.py`
- `ced-to-html.xsl`, `Makefile` (the `make` → `ced.html` render path)
- `workflows/` (all — `extract-csa-ced-hierarchy.js`,
  `extract-csp-ced-hierarchy.js`, `README.md`)

Data (the CED/IB source + artifacts, now owned by `hierarchy-extractors`):

- `csa/ced-2025.pdf`, `csa/ced-2025-hierarchy.md`, `csa/ced.xml`,
  `csa/bhsawesome-outline.md`
- `csp/` (all — PDF, `ced-hierarchy.md`, `ced.xml`, `sample.xml`)
- `ib/` (all — PDF, `ib-hierarchy.md`, `ib-hours.tsv`, `syllabus.xml`)

Doc:

- `HIERARCHIES.md` (entirely the hierarchy subsystem; promoted to the new repo's
  primary doc).

### Moved to `lesson-planning`

- `lesson-planning/` (all — `app.py`, `schema.sql`, `static/`, `templates/`,
  `export/`)
- Root engine scripts: `load_nodes.py`, `import_objectives.py`,
  `export_planning.py`, `import_planning.py`, `rebuild_db.py`,
  `render_outline.py`
- `backup-db` (backs up `lesson-planning/db.db` — nothing left to back up here)

### Dead / superseded (in neither new repo)

- `load_objectives.py` — superseded by `import_objectives.py` (which itself
  moved); both extraction plans flagged it as dead. Remove.

## What to keep

**Quiz / deck / activity / format tooling (the remaining purpose):**

- `format_xml.py`, `extract_key.py`
- `extract_activities.py`, `activity_report.py`, `compare_activities.py`,
  `filter_pairs.py`, `jaccard.py`, `lcs.py`
- `check_deck.py`, `rename_card_tags.py`
- `identify.py`
- `list_files.py`, `just-pretext.sh` — **dual-use**: kept because the activity
  comparison syncs book trees with them. (Yes, they also live in
  `hierarchy-extractors`; the duplication is acceptable — both repos genuinely
  need them. Note it in `CLAUDE.md`.)

**Data / configs:**

- `.xml-formats/` (`ptx.json`, `quiz.json`, `mcqs.json` — drive `format_xml.py`)
- `decks/` (all `.deck` files)
- `reports/` (`compare-books-report.md`)
- `csa/mcqs.quiz`
- `csa/learning-objectives/` (objectives TSVs + OCR + scans) — the lesson-planning
  plan explicitly leaves the objectives *data* in `bhs-awesome`. See the caveat
  under "Decisions to confirm."
- `plans/` (the shared design record — see housekeeping below)

## Doc / config edits (not deletions)

- **`CLAUDE.md`** — trim to the remaining repo. Drop from the Key Scripts table
  every removed script (all `extract_*hierarchy`/`build_*`/`load_nodes`/
  `import_objectives`/`export_planning`/`import_planning`/`rebuild_db`/
  `render_outline`/`hierarchy`/`load_objectives` rows). Delete the "Building CED
  HTML", quiz-pipeline-to-hierarchy, and lesson-planning sections; remove the
  `csa/ced*`, `csp/`, `ib/`, `lesson-planning/` entries from Project Structure
  (keep `csa/learning-objectives`, `decks/`, `reports/`, `.xml-formats/`).
  Update the tech-stack line (drop `pypdf`/`xsltproc`/`make`/`flask`; keep
  `lxml`). Add a one-line note that `list_files.py`/`just-pretext.sh` are shared
  with `hierarchy-extractors`, and a pointer to both new repos.
- **`pyproject.toml`** — drop `flask` and `pypdf` from `dependencies`, leaving
  `lxml`. Keep `requires-python = ">=3.13"`. Then regenerate: `uv lock`.
- **`.gitignore`** — remove `/csa/ced.html` and `/csp/ced.html` (no `make` here
  anymore) and `db-backups/` (`backup-db` is gone). **Keep** `bhsawesome/`,
  `csawesome/`, `repos/`, `comparison*/`, `csa-activities/`, `filtered-*`,
  `google-java-format.jar` (all activity-comparison artifacts) and `*.zip`/`*~`/
  `__pycache__`/`.venv/`.
- **`plans/` housekeeping** — keep the tree (it's the shared design history,
  carried into both new repos too). Move the now-implemented
  `plans/extract-extractors.md` and `plans/extract-lesson-planning.md` into
  `plans/done/`, and drop *this* plan into `plans/done/` once executed.

## Decisions to confirm

1. **Remove the CED/IB data (`csa/ced*`, `csp/`, `ib/`)?** *Recommended: yes.*
   `hierarchy-extractors` is now the declared source of truth for it, and no
   remaining `bhs-awesome` tool reads it. The only consequence: the kept
   `csa/learning-objectives/objectives.tsv` carries `node_id`s that point into
   the CSA CED hierarchy, which will no longer live in this repo — those become
   references resolved *against the other repo* (exactly the cross-repo join
   `lesson-planning` already does). If you'd rather keep the CSA CED markdown
   here purely as a local reference for those node_ids, that's the only file
   worth reconsidering; everything else in `csp/`/`ib/` is unambiguously gone.
   (This is a working-tree delete; the data stays in git history and in
   `hierarchy-extractors`, so it's fully recoverable.)

2. **Keep `list_files.py`/`just-pretext.sh` here, or vendor on demand?**
   *Recommended: keep* — the activity comparison needs them and they're tiny.
   Listed under "What to keep" on that basis.

## Verification

1. **No dangling intra-repo imports.** After the deletions:
   `grep -rnE 'import (hierarchy|extract_activities|jaccard|lcs|import_planning|load_nodes)' *.py`
   — every hit must resolve to a kept module (`extract_activities`/`jaccard`/`lcs`
   are kept; `hierarchy`/`import_planning`/`load_nodes` must have **zero** hits).
2. **No dangling references to removed paths/scripts.**
   `grep -rnE 'lesson-planning|hierarchy\.py|ced-to-html|build_hierarchy|render_outline|HIERARCHIES|csp/|ib/|ced-2025|ced\.xml' . --include='*.py' --include='*.md' --include='*.toml' --include='*.sh'`
   — every remaining hit should be intentional prose (e.g. a `CLAUDE.md` pointer
   to the new repos) or inside `plans/`.
3. **Remaining tooling still runs** against its kept data:
   - `uv sync` (resolves to `lxml` only).
   - `uv run format_xml.py -i csa/mcqs.quiz` and `uv run extract_key.py csa/mcqs.quiz`.
   - `uv run check_deck.py decks/example.deck`.
   - Activity comparison (needs synced book trees first):
     `./just-pretext.sh <repo> bhsawesome` → `uv run compare_activities.py bhsawesome/main.ptx csawesome/main.ptx /tmp/cmp/`.
4. **Commit** on the current branch (yolo session — no new branch needed), one
   focused commit (or two: deletions, then doc/config trims).

## Out of scope

- The `hierarchy.py` → emitted-JSON cross-repo boundary (tracked in both new
  repos' plans). `bhs-awesome` isn't a party to it once `hierarchy.py` is gone.
- Any further reorganization of the remaining quiz/deck/activity tooling.
