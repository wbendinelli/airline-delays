# Security Policy

`airline-delays` is a research repository (SAPIANS golden path, tier C):
ANAC's public flight records, the estimation panel and re-estimated tables of
a published article, a congestion model and a delay predictor. It has no
production service, no user accounts and no end-user data. This policy
extends the org-wide policy of
[`wbendinelli/.github`](https://github.com/wbendinelli/.github/blob/main/SECURITY.md).

## Supported versions

The latest state of `main` and the most recent publication tag receive
fixes. There is no long-term-support branch.

## Reporting a vulnerability

Do not open a public issue and do not describe the flaw in a pull request.
Report privately through one of:

- **GitHub Security Advisories** -- this repository's *Security -> Report a
  vulnerability* tab (preferred).
- **E-mail** -- wbendinelli@gmail.com -- with a description, reproduction
  steps, impact and the affected commit.

Expect a response within 72 hours. We ask for a reasonable
coordinated-disclosure window before the issue is made public; credit is
given to the reporter on request.

## Standards inherited from the golden path

- **Secrets never in git.** `gitleaks` runs in CI (`.github/workflows/security.yml`)
  over the full git history; push protection and secret scanning are enabled.
- **Least privilege.** Every workflow job declares a minimal `permissions:`
  block -- `contents: read` throughout.
- **Third-party actions pinned by commit SHA**, the tag kept as a comment,
  never `@main` or `@latest`; Dependabot proposes the bumps.

## Data provenance

The one way to get security wrong in a data repository is to redistribute
data that is not this repository's to redistribute, or data about people.

- **Every redistributed table carries its provenance.** Each row of
  `data/external/*.csv` cites its `source` and `url`, and a licence is read
  before a table is committed (`DECISIONS.md` ADR-0000). The article's
  estimation panel ships with `data/analysis/article_panel_manifest.json`,
  which records the sha256 of the source and of the files, never a path. Do
  not add a source without the same treatment.
- **The VRA carries no personal data.** Its unit is the scheduled flight leg
  -- carrier, flight number, airports, times, a justification code -- and
  nothing here joins it to a person.
- **Regenerated layers are never committed.** `data/raw/`, `data/staged/` and
  `data/derived/` are rebuilt from ANAC's public files by the documented
  commands and tracked only through their `README.md` and
  `data/raw/manifest.json` (`.gitignore`). No path outside the repository is
  hardcoded in a script.

## Dependencies

Python packages (`pyproject.toml`) and GitHub Actions (`.github/workflows/`)
are tracked by Dependabot (`.github/dependabot.yml`): github-actions weekly,
pip monthly. `uv.lock` pins the resolved set; `uv sync --locked` in CI fails
rather than silently re-resolving.
