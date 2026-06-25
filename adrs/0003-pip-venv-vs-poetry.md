# ADR 0003 — Dependency management: pip + venv vs Poetry

- **Status:** Accepted
- **Date:** 2026-06-25
- **Deciders:** Carlos Leguizamon Guillaumet
- **Related ADRs:** [0001 — Snowflake-only architecture](0001-snowflake-only-architecture.md)

## Context

ConsolidAR requires a Python dependency management approach. The project
ships ten runtime dependencies (snowflake-connector-python, snowpark, dbt-
core, dbt-snowflake, pandas, numpy, faker, requests, python-dateutil,
pyarrow) and four development dependencies (pytest, pytest-cov, ruff,
mypy). All declared in `pyproject.toml` using the PEP 621 standard format.

The Python ecosystem offers several mature options for managing this:

1. **Poetry** — a dependency-resolver + virtualenv-manager + build-tool
   wrapped in a single CLI. Default choice for new Python projects in 2024-
   2026 and what the author's other project, FinClose AI, uses successfully.

2. **pip + venv** — the standard-library approach. `python -m venv` creates
   isolated environments; `pip` resolves and installs from `requirements.txt`.
   Less ergonomic than Poetry, but zero external tooling dependency.

3. **uv** — a Rust-based resolver gaining adoption in 2025. Faster than
   both, but newer and adds another tool to learn.

The default selection for this project was Poetry, matching the author's
existing toolchain. The initial setup encountered a reproducible bug that
forced a re-evaluation.

### The Poetry 2.4.1 bug observed

When configuring this project, Poetry 2.4.1 consistently failed to resolve
dependencies, reporting:

> "The current project's supported Python range (>=3.11,<4.0) is not
> compatible with some of the required packages Python requirement"

The `pyproject.toml` clearly declared `requires-python = ">=3.10,<4.0"`
under the PEP 621 `[project]` table. The local Python interpreter was
3.10.12 and Poetry itself was running on 3.10.12 (verified via
`poetry env info`). Nothing in the project, environment, or cache
justified the `>=3.11` constraint that the resolver kept reporting.

Forensic steps taken:

- Deleted the `.venv` and reran `poetry install` — same error.
- Cleared the Poetry cache (`poetry cache clear --all`) — same error.
- Removed environment registrations (`poetry env remove --all`) — same.
- Restarted the WSL shell to drop any cached env vars — same.
- Migrated `pyproject.toml` to fully-modern PEP 621 (added `[project]`
  block, removed all `[tool.poetry.dependencies]` legacy fields) — same.
- Manually added `[tool.poetry.dependencies] python = ">=3.10,<4.0"` as a
  redundant declaration — same.

**Root cause identified by comparing to FinClose AI**, which uses Poetry
2.4.1 successfully on the same machine. FinClose declares:

```toml
requires-python = "^3.10"   # Poetry caret notation
```

ConsolidAR declared:

```toml
requires-python = ">=3.10,<4.0"   # PEP 440 standard notation
```

Both notations express the same logical range. Poetry parses the first
correctly. Poetry 2.4.1 misparses the second under PEP 621 with
`package-mode = false`, defaulting the lower bound to one minor version
above the running interpreter (i.e., 3.11 when running on 3.10). The
caret notation is a Poetry-proprietary syntax that does not appear in
PEP 440 or PEP 621.

### Why the workaround is unattractive

The workaround is to use Poetry's caret notation in `requires-python`,
which makes the file Poetry-specific and non-portable to any tool that
expects standards-conformant PEP 440. Tools like `pip-tools`, `uv`, build
backends, dependabot, and any third-party reader of the metadata would
need to special-case the caret syntax or fail to parse it.

The bug is also latent for adding new dependencies. Any future
`poetry add` operation triggers re-resolution and can resurface the
issue if Poetry version changes or other config interacts unpredictably.

## Decision

**ConsolidAR will use pip + venv for dependency management.** Poetry will
not be used. The project ships with:

- `pyproject.toml` in PEP 621 format declaring runtime and dev
  dependencies (the canonical project metadata)
- `requirements.txt` with the ten runtime dependencies and version
  ranges (the install contract)
- `requirements-dev.txt` adding pytest, ruff, mypy on top of runtime
  (the development environment contract)
- `requirements-lock.txt` produced via `pip freeze` capturing the exact
  pinned versions of all 81 transitive packages at the time of install
  (the reproducibility contract; equivalent to `poetry.lock`)

The standard reproduction flow becomes:

```bash
python3 -m venv .venv
source .venv/bin/activate
pip install -r requirements-lock.txt
```

A single command, with no external tool installation required.

## Alternatives considered

### Option 1 — Poetry with the caret-notation workaround

Rejected. The workaround moves the project from PEP 440-compliant
syntax to a Poetry-proprietary dialect for no upside, leaving a latent
fragility for future dependency additions. The same machine runs Poetry
2.4.1 successfully on FinClose AI, so this is not a Poetry-vs-anything
ideology — it is a specific bug in this specific project's
configuration that has resisted root-cause resolution within reasonable
time.

### Option 2 — Reinstall Poetry from scratch on a different Python

Considered. The hypothesis is that the Poetry installation itself
contains corrupted resolver state. Rejected because: (a) reproducing the
bug requires the same Poetry instance that breaks ConsolidAR but works
on FinClose, suggesting the bug is project-specific not installation-
specific; (b) reinstalling Poetry to fix one project would risk
breaking FinClose; (c) the time cost of debugging a transient tool bug
exceeds the time cost of switching to a simpler tool that already works.

### Option 3 — uv

Considered. uv is faster, modern, and resolves PEP 440 syntax
correctly. Rejected for this project because: (a) introducing a third
tool (different from FinClose's Poetry and the standard pip) adds
cognitive load; (b) the project is small enough that pip's resolution
performance is irrelevant; (c) pip + venv is universally understood and
requires zero learning curve for any reviewer.

### Option 4 — pip + venv (chosen)

Accepted. pip and venv are part of the Python standard library
(actually pip is bundled but maintained separately; venv is stdlib).
They have no external dependencies, no version conflicts with the
project, and no resolution bugs. The `requirements-lock.txt` provides
reproducibility equivalent to `poetry.lock`. The reproduction
instructions are universally understood.

## Consequences

### Positive

- Reproducibility is preserved via `requirements-lock.txt`. A reviewer
  cloning the repository and running three commands gets the exact
  same environment.
- The setup has zero external tool dependencies beyond Python itself.
  No `pipx install poetry`, no `curl | sh` install scripts.
- `pyproject.toml` remains PEP 621-compliant, so it is parseable by
  any modern Python tool (build backends, type checkers, linters)
  without special-casing.
- Eliminates an entire class of latent bugs from the project's
  dependency on a buggy version of Poetry.

### Negative

- No `poetry add` ergonomic flow for adding dependencies. New
  dependencies are added by editing `requirements.txt` (or
  `pyproject.toml`) and rerunning `pip install` then `pip freeze >
  requirements-lock.txt` to refresh the lock. Two-step instead of
  one-step. Acceptable.
- No automatic dependency-tree visualization. Compensated by `pip
  show <package>` and `pipdeptree` if needed.
- Slight cognitive inconsistency with FinClose AI, which uses Poetry.
  Documented in this ADR so a reviewer comparing the two projects has
  context. The cross-project consistency cost is lower than the
  in-project bug cost.

### Neutral

- The `.venv/` directory is project-local and gitignored. Each
  developer (including future-self) creates one with the standard
  three commands documented in the README.
- `requirements-lock.txt` is regenerated whenever runtime
  dependencies change. The regeneration step is captured in the
  Makefile.

## Implementation notes

The project's Makefile targets `make install` and `make install-dev`
correspond to:

```bash
pip install -r requirements-lock.txt
pip install -r requirements-dev.txt
```

The lock file is regenerated by:

```bash
pip install -r requirements.txt --upgrade
pip freeze > requirements-lock.txt
```

This must be re-run any time `requirements.txt` is updated.

## References

- [PEP 621 — Project metadata in pyproject.toml](https://peps.python.org/pep-0621/)
- [PEP 440 — Version Identification and Dependency Specification](https://peps.python.org/pep-0440/)
- Poetry issue tracker (bug not reported upstream during this debug; the
  workaround via caret notation was sufficient evidence of root cause to
  proceed)
- FinClose AI `pyproject.toml` for contrast — uses caret notation
  successfully on the same Poetry 2.4.1 installation