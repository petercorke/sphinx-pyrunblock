# sphinx-pyrunblock — Agent Instructions

Part of the RVC ecosystem. **Read [rvc-ecosystem/AGENTS.md](https://github.com/petercorke/rvc-ecosystem/blob/main/AGENTS.md) first** — it defines shared conventions: repo ownership, math invariants, dependency boundaries, git/PR workflow, code standards, tech-debt tracking. This file only adds what's specific to this repo.

| | |
|---|---|
| PyPI package | `sphinx-pyrunblock` |
| Nickname | sphinx-pyrunblock |
| Owner | Peter Corke (`petercorke`) |
| Default branch | `main` |
| Contribution model | Branch → PR; direct push to `main` at Peter's discretion |

## Notes specific to this repo

- Renamed/evolved from a fork of [WhyNotHugo/sphinx-autorun](https://github.com/WhyNotHugo/sphinx-autorun)
  — the `upstream` remote still points there for reference; `origin` is this repo, fully
  Peter-owned, normal push/PR rules apply (this is *not* a third-party-owned repo despite the
  extra remote).
- Sphinx extension that executes code blocks and inlines their output — used across the
  ecosystem's docs (RTB, MVTB, bdsim, etc.) for runnable examples.
- Still has a `tech-debt.md` file at repo root — legacy practice, not a deliberate permanent
  exception. Migrating to GitHub Issues (the ecosystem standard) is on the list, not urgent.
