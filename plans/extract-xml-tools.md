# Plan: Extract the generic XML tools into their own `uv tool`-installable repo

## Goal

Pull the two **format-agnostic** XML utilities — `format_xml.py` and
`identify.py` — out of `bhs-awesome` into a standalone git repository, packaged
so each becomes a console command you can `uv tool install` and run from
anywhere. Preserve the development history of both files.

This is a third sibling to `plans/done/extract-extractors.md` and
`plans/done/extract-lesson-planning.md`, but with two differences that shape the
whole plan:

1. **These tools are genuinely generic** — they know nothing about CSA/CSP/IB,
   PreTeXt, quizzes, or decks. `format_xml.py`'s behavior is entirely driven by a
   JSON config the caller supplies; `identify.py` just stamps `uuid` attributes
   onto XPath matches. So the new repo isn't "curriculum code that moved" — it's a
   small general-purpose toolkit. The point of extracting them is *reuse*: a
   `uv tool install` away in any project.

2. **`bhs-awesome` still depends on `format_xml.py`** (it formats `csa/mcqs.quiz`
   and `.ptx` files via `.xml-formats/*.json`). Unlike the prior two extractions
   — which moved code the old repo no longer needed — this one extracts a tool
   the old repo keeps using. So the old repo must switch to *consuming* the
   installed tool, and `format_xml` must be genericized so it doesn't bake in
   `bhs-awesome`'s config directory. See "Genericize" and "Coordinating with
   bhs-awesome."

## What the tools are (verified from the code)

Both are single files, importing only the **stdlib + `lxml`** — no intra-repo
imports, no third-party deps beyond `lxml`:

- **`format_xml.py`** — a configurable XML pretty-printer. Element categories
  (`inline`, `code`, `preserve_whitespace`, `one_line`, `compact`),
  `compound_code` blocks, conditional `rules`, and external `formatters` are all
  read from a JSON config (`-c`). With no config it treats everything as a block
  element. The `extend-format-xml.md` design doc states the principle outright:
  *"without hardcoding anything specific to PreTeXt or any other XML format."*
- **`identify.py`** — adds a `uuid` attribute to every element matching an XPath
  (`identify '//q' file.xml`), warning on malformed existing uuids. Fully generic
  already; **zero** coupling.

### The one coupling to break

`format_xml.py`'s `__main__` block computes
`script_dir = dirname(abspath(__file__))` and auto-loads
`{script_dir}/.xml-formats/{ext}.json` when no `-c` is given — i.e. it reaches
for `bhs-awesome`'s `.xml-formats/` directory *relative to where the script
lives*. Installed as a `uv tool`, the script lives in site-packages and that
directory won't be there. This magic-directory lookup is the only thing in either
file that isn't generic, and the genericization removes it (replacing it with an
explicit, caller-supplied config directory — see "Genericize").

`identify.py` needs no changes to be generic.

## Making them `uv tool`-installable

`uv tool install` (and `uvx`) install a project's **console scripts** onto PATH.
That needs three things the current scripts lack:

1. **A callable entry point**, not just an `if __name__ == "__main__"` block.
   Refactor each module's `__main__` body into `def main(argv=None):` and keep a
   thin `if __name__ == "__main__": main()` for `python format_xml.py` use.
2. **A `[project.scripts]` table** mapping command names to those functions.
3. **A build backend** so the project is a real installable wheel (use
   `hatchling`).

Target `pyproject.toml` (Phase-2 package layout shown; Phase 1 uses top-level
modules — see "Two phases"):

```toml
[project]
name = "xml-tools"
version = "0.1.0"
description = "Generic, config-driven XML formatter and an XPath uuid-stamper."
requires-python = ">=3.10"
dependencies = ["lxml>=6.0.2"]

[project.scripts]
xml-format   = "xml_tools.format_xml:main"
xml-identify = "xml_tools.identify:main"

[build-system]
requires = ["hatchling"]
build-backend = "hatchling.build"
```

Then:

- `uv tool install .` (from a checkout) or
  `uv tool install git+https://github.com/<user>/xml-tools` puts `xml-format` and
  `xml-identify` in `~/.local/bin`.
- `uvx --from xml-tools xml-format ...` runs without a persistent install.
- `uv tool install --editable .` during development.

**Command names (decided).** The installed commands are **`xml-format`** and
**`xml-identify`** — the `xml-` prefix keeps them grouped and steers clear of the
ImageMagick `identify` collision. (The *Python module* names stay
`format_xml` / `identify`; only the installed command names matter here.)

## Keep / exclude

### Keep — the two tools

- `format_xml.py`
- `identify.py`

### Keep — the one relevant design doc

- `plans/done/extend-format-xml.md` — the design history of `format_xml`'s
  feature set, and itself written around the "no format-specific hardcoding"
  principle. It's the only plan in `bhs-awesome` about either tool. Carry it
  (trim any incidental PreTeXt/`google-java-format` references to generic
  examples). **Do not** carry the rest of `plans/` — unlike the prior two
  extractions (which split *one* project and wanted its whole design record on
  both sides), this repo is a different kind of artifact; the curriculum/
  lesson-planning plans are pure noise here.

### Exclude — everything else

Most importantly the **`.xml-formats/` configs** (`ptx.json`, `quiz.json`,
`mcqs.json`). They're `bhs-awesome`-specific schema knowledge (PreTeXt, the quiz
format), not generic tooling — they stay in `bhs-awesome` and are passed to the
formatter via `--config`/`--config-dir`. Optionally ship a **small synthetic**
example config + sample XML under `examples/` in the new repo (a made-up schema,
not the real PreTeXt/quiz configs) so the README and smoke test have something
concrete and the config format is documented.

## Genericize — search the working tree instead of the install location

Today `format_xml.py` auto-loads `{script_dir}/.xml-formats/{ext}.json` — keyed
off where the *script* lives, which is meaningless once it's installed in
site-packages. Replace that with a search rooted at the **current working
directory**, plus two explicit escape hatches. Resolution order, highest first:

1. **`--config-file FILE`** — use exactly this JSON config, regardless of the
   input's extension. (This is the existing `-c/--config` flag, renamed; keep
   `-c` as an alias.)
2. **`--config-dir DIR`** — look up `{DIR}/{ext}.json` by the input file's
   extension, in **that directory only** (no walking). Escape hatch for when the
   config dir isn't named `.xml-formats` or isn't an ancestor of the CWD.
3. **Default: walk up from the CWD** looking for a `.xml-formats/` directory that
   contains a matching `{ext}.json` — check `./.xml-formats/{ext}.json`, then each
   parent's, stopping at the filesystem root. First hit wins. (Same discovery
   model as git finding `.git`, or a linter finding its rc file.)
4. **Nothing found → `DEFAULT_CONFIG`** (everything is a block element). No magic,
   no error.

Drop the `script_dir`/`os.path.abspath(__file__)` lines entirely. The upward
search is what lets `bhs-awesome` keep its exact workflow with **no flags**:
running `xml-format -i csa/mcqs.quiz` from anywhere in the repo discovers the
repo's `.xml-formats/mcqs.json` by walking up to the repo root — the same
convenience as today, but rooted in the *project* the user is working in rather
than the tool's install path.

Implementation notes for the executor: the lookup uses the input file's
extension, so it runs **per input file** (already the case). Resolve the walk
from `Path.cwd()` (not from the input file's directory) so a single invocation
over files in different subtrees uses one consistent config root — though
consider whether rooting at each input file's parent is more intuitive; pick one
and document it. A `--no-config` flag (force `DEFAULT_CONFIG`, skip discovery) is
a cheap nicety but optional.

`identify.py` needs no genericization.

## Two phases

Mirror the lesson-planning extraction: extract in the current (flat) shape and
get it installable, then reorganize into a package — each step small and
reviewable.

- **Phase 1** — `filter-repo` the two files (+ the one plan) at their root paths,
  add standalone scaffolding, refactor `__main__ → main()`, genericize
  `format_xml`, and make it installable as **top-level modules** (no package move
  yet). Verify `uv tool install .` yields working `xml-format` / `xml-identify`.
- **Phase 2** — move the modules into `src/xml_tools/` and switch the entry points
  to `xml_tools.format_xml:main` / `xml_tools.identify:main`. Pure reorg.

## Phase 1 — extract, genericize, make installable (flat shape)

### 1. Prep the source

Commit everything (so a clone sees it). This cleanup branch already removed the
unrelated tooling, but the extraction clones from `bhs-awesome`'s default branch —
make sure `format_xml.py`, `identify.py`, and `plans/done/extend-format-xml.md`
are committed on whatever branch you clone.

### 2. Fresh clone

```bash
git clone /Users/peter/hacks/bhs-awesome xml-tools
cd xml-tools
```

### 3. Write the keep-list and rewrite

```bash
cat > /tmp/keep.txt <<'EOF'
format_xml.py
identify.py
plans/done/extend-format-xml.md
EOF

git filter-repo --paths-from-file /tmp/keep.txt --prune-empty always
```

Notes:

- History is shallow for both files (~2 commits each) — `filter-repo` is still
  worth it for consistency and honest provenance, but don't expect a deep log.
- `filter-repo` drops `origin` on purpose; add a new remote at publish time.
- Verify: `git log --oneline -- format_xml.py` shows real commits, and
  `git log --all --oneline -- csa/ lesson-planning/ '*.quiz'` is empty.

### 4. Refactor to `main()` + genericize

- **`format_xml.py`**: wrap the `__main__` body in `def main(argv=None):`
  (`parser.parse_args(argv)`), keep `if __name__ == "__main__": main()`. Apply the
  "Genericize" changes (drop the `script_dir`/`.xml-formats` magic; rename
  `-c/--config` → `--config-file` keeping `-c`; add `--config-dir`; add the
  CWD-rooted upward `.xml-formats/{ext}.json` search as the default).
- **`identify.py`**: wrap the `__main__` body in `def main(argv=None):`; keep the
  thin guard. No other changes.

### 5. Scaffold the standalone project (flat)

- **`pyproject.toml`** — as above, but Phase-1 entry points reference the
  top-level modules and tell hatchling to ship them:

  ```toml
  [project.scripts]
  xml-format   = "format_xml:main"
  xml-identify = "identify:main"

  [tool.hatch.build.targets.wheel]
  include = ["format_xml.py", "identify.py"]
  ```

  `dependencies = ["lxml>=6.0.2"]`; `requires-python` per the decision below.
  Generate the lock: `uv lock`.
- **`.gitignore`** — minimal: `__pycache__`, `.venv/`, `dist/`,
  `.claude/settings.local.json`.
- **`.python-version`** — carry or set to match `requires-python`.
- **`README.md`** — new. What each tool does, install
  (`uv tool install git+…`), and a worked
  `xml-format --config-file examples/<x>.json examples/sample.xml` /
  `xml-identify '//foo' file.xml` example. Document the JSON config keys (lift the
  docstring's config example) and the config resolution order
  (`--config-file` > `--config-dir` > CWD-rooted `.xml-formats/{ext}.json` search
  > block default).
- **`examples/`** (optional but recommended) — a tiny synthetic config + sample
  XML, per "Keep."
- **`CLAUDE.md`** (optional) — a few lines: two generic tools, `lxml`-only,
  installable via `uv tool`.

### 6. Smoke-test installability

```bash
uv lock && uv sync

# Run in place:
uv run xml-format examples/sample.xml                          # no config found -> block layout
uv run xml-format --config-file examples/sample.json examples/sample.xml
uv run xml-identify '//item' examples/sample.xml

# Discovery: from a dir whose tree contains .xml-formats/<ext>.json, no flags:
( cd examples && uv run xml-format sample.xml )                # finds examples/.xml-formats/ if present

# Install as a uv tool and run from PATH:
uv tool install .
xml-format --help && xml-identify --help
uv tool uninstall xml-tools                   # clean up the smoke test
```

Success: both commands install onto PATH and run; `xml-format` honors
`--config-file` and `--config-dir`, discovers `.xml-formats/{ext}.json` by walking
up from the CWD, and falls back to block layout when nothing is found; nothing
references `.xml-formats/` by an install-relative path.

### 7. Publish

```bash
gh repo create <name> --public --source=. --remote=origin
git push -u origin main
```

(Per the user's global notes, the user pushes; in a yolo container you likely
lack push access — stop at the verified local repo and hand off.) These tools are
generic and carry no copyrighted data, so **public** is reasonable from the start
(contrast the extractors repo). If published to PyPI later, wire up the npm-style
Trusted-Publisher equivalent (PyPI Trusted Publishing via GitHub Actions OIDC) —
out of scope here.

## Phase 2 — package layout

After Phase 1 verifies, reorganize into a conventional package (better for an
installed tool: avoids two top-level modules colliding in site-packages):

1. `mkdir -p src/xml_tools && git mv format_xml.py src/xml_tools/ &&
   git mv identify.py src/xml_tools/ && touch src/xml_tools/__init__.py`.
2. Switch `[project.scripts]` to `xml_tools.format_xml:main` /
   `xml_tools.identify:main`; drop the `[tool.hatch.build.targets.wheel] include`
   (hatchling auto-detects `src/xml_tools`).
3. Re-run the step-6 smoke test against the package layout.

## Coordinating with `bhs-awesome` (separate follow-up)

Like the prior extractions, the old-repo cleanup is **its own change**, but it's
more involved here because `bhs-awesome` *uses* `format_xml`. Once the new repo
exists:

- Remove `bhs-awesome`'s `format_xml.py` and `identify.py`.
- Consume the tool instead — either `uv tool install`'d on the dev machine, or
  added as a dev dependency (e.g. `uv add --dev "xml-tools @ git+https://…"`).
- Invocations barely change: `xml-format -i csa/mcqs.quiz` (from anywhere in the
  repo) discovers `.xml-formats/mcqs.json` by the CWD-rooted upward search, just
  as the old script-dir lookup did — **no new flags needed**. Replace
  `uv run format_xml.py` with `xml-format` in `CLAUDE.md`'s "Running Scripts".
- `.xml-formats/` **stays** in `bhs-awesome` — it's the config the tool discovers
  and consumes.

Track this as a follow-up cleanup plan in `bhs-awesome` (the analog of
`plans/done/cleanup-after-extraction.md`); don't fold it into this extraction.

## Decisions to confirm

- **Command names (decided):** `xml-format` and `xml-identify`. Repo slug still
  open (e.g. `xml-tools`).
- **Config-search root (minor):** walk up from `Path.cwd()` vs. from each input
  file's parent directory. Pick one during implementation and document it (see
  "Genericize"). Recommended: CWD-rooted, for consistent behavior across inputs.
- **`requires-python`.** Neither file uses anything past ~3.10 (dict-union on
  `nsmap`, f-strings). Relaxing from `bhs-awesome`'s `>=3.13` to **`>=3.10`**
  widens the install base for a generic tool — recommended, but confirm.
- **Visibility / PyPI.** Public from the start (recommended; no data, generic
  code). Whether to also publish to PyPI (and set up Trusted Publishing) is a
  later, separate step.
- **Ship `examples/`?** Recommended — a synthetic config + sample XML doubles as
  format documentation and the smoke-test fixture.

## Loose ends

- The `formatters` config feature shells out to external commands (the
  `bhs-awesome` config used `google-java-format.jar`). That's a generic mechanism
  — keep it; just don't ship the jar or reference it outside an example.
- `format_xml`'s auto-config-by-extension is a genuinely handy feature; the
  `--config-dir` redesign preserves it generically rather than dropping it.
- No `uv.lock` is carried from `bhs-awesome` — regenerate fresh (the dep set is
  just `lxml`).
