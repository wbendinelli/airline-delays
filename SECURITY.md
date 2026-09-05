# Security Policy

`airline-delays` is a research repository (SAPIANS golden path, tier C):
public ANAC flight-delay records, a published-article replication, and a
delay predictor. It has no production service, no user accounts, and no
end-user data. This policy extends the org-wide policy of
[`wbendinelli/.github`](https://github.com/wbendinelli/.github/blob/main/SECURITY.md)
with what is specific to this repository.

## Supported versions

Pre-1.0: only the latest state of `main` receives fixes. There is no
long-term-support branch.

## Reporting a vulnerability

**Do not open a public issue** and do not describe the flaw in a pull
request. Report privately through one of:

- **GitHub Security Advisories** — this repository's *Security -> Report a
  vulnerability* tab (preferred).
- **Email** — **wbendinelli@gmail.com** — with a description, reproduction
  steps, impact, and the affected commit.

Expect a response within **72 hours**. We ask for a reasonable
coordinated-disclosure window before the issue is made public; credit is
given to the reporter on request.

## Standards inherited from the golden path

- **Secrets never in git.** `gitleaks` runs in CI (the reusable
  `security.yml`) over the full git history.
- **Least privilege.** Every job declares a minimal `permissions:` block —
  `contents: read` in every job in this repository.
- **Third-party actions pinned by commit SHA** (the tag kept as a
  comment), never `@main`/`@latest`; Dependabot proposes the bumps.
- **Push protection and secret scanning** enabled on the repository.

## What "security" means in a data-reconstruction repository

There is no application attack surface here, but there is a real way to
get this wrong: **redistributing data that is not this repository's to
redistribute.**

- **The private benchmark never enters git.** `proj18.dta`, the
  LABTAR/NECTAR laboratory bases, and `vra.dta` are read only from the
  `AIRLINE_DELAYS_PRIVATE_DIR` environment variable, outside the
  repository, and only by `replication/gabarito/` or a
  `scripts/verify*.py`. A pre-commit hook (`no-private-data`) and
  `.gitignore` both block these paths; treat a hook failure here as a real
  finding, not friction to route around. Accidentally committing one of
  these files and pushing it is the closest thing this repository has to a
  security incident — if it happens, report it the same way as a
  vulnerability (above), because the fix includes history rewriting, not
  just a follow-up commit.
- **Raw ANAC data is redistributed under a licence that was read, not
  assumed** (`DECISIONS.md` ADR-0000) — do not add a second data source to
  `data/external/` without the same treatment: a `source` and `url` per
  row, and a licence check before it is committed.
- **`AIRLINE_DELAYS_PRIVATE_DIR` is a path, not a secret**, but it points
  outside the repository on purpose — never hardcode a path to the
  private directory in a script; read the environment variable, so that a
  script leaking its own source code never leaks a path to someone else's
  laboratory data.

## Dependencies

Third-party Python packages (`pyproject.toml`) and GitHub Actions
(`.github/workflows/`) are tracked by Dependabot
(`.github/dependabot.yml`) — github-actions weekly, pip monthly.
`uv.lock` pins the fully resolved dependency set; `uv sync --locked` in CI
fails rather than silently re-resolving.
