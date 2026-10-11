# Changelog

All notable changes to this project are documented here. Format loosely
follows [Keep a Changelog](https://keepachangelog.com/en/1.1.0/).

## [Unreleased]

### Added

- `:session: [NAME]` per-block option: blocks that share a session (the
  unnamed one, or a named one) share a namespace, so a later block sees the
  variables, functions and classes of earlier ones. This allows a narrative
  with prose between code blocks, instead of repeating earlier lines in
  every block and hiding them. Sessions are scoped to one document, the
  configured `runfirst` runs once at the start of a session, and `:linenos:`
  continues through the session.

### Fixed

- A compound statement (`for`, `class`, `def`, `if`, ...) followed directly
  by an unindented statement no longer swallows that statement as a syntax
  error. The trailing blank line is now optional; `else`/`elif`/`except`/
  `finally` clauses and statements left open by an unclosed bracket or
  string still continue as before.

## [1.1.0] - 2026-07-31

### Added

- `:no-prompt:` per-block directive option: renders a block as plain
  script-style code (no `>>>`/`...` prompts), with output shown as
  `# → ...` comment lines instead of interleaved REPL-style text.
- `<lang>_fail_on_error` config key (e.g. `pycon_fail_on_error`): when
  true, a `runblock` whose code raises (or fails to parse) fails the
  Sphinx build with a `RunBlockError` pointing at the `.rst` file:line,
  instead of only embedding the `!! [RUNBLOCK-ERROR]` marker in the
  rendered output. Defaults to `False`.

## [1.0.1] - 2026-07-29

Cleanup release -- 1.0.0 was published from a commit that still had
`rename-plan.md` (an internal one-time planning doc) tracked at repo
root, and before `test/` was renamed to `examples/` (it read as a typo
next to `tests/`). PyPI releases are immutable, so this couldn't be
fixed in place. No functional/behavioural changes from 1.0.0.

## [1.0.0] - 2026-07-29

First release under the new name. Renamed from `sphinx-autorun` (that
PyPI name belongs to an unrelated, still-maintained project by Hugo
Osvaldo Barrera). Hard fork -- heritage documented in the docs.

- `src/` layout, hatchling build backend
- real pytest suite, ruff-clean
- fixed a runfirst-duplication bug, dead console config, a stray debug
  print, and bare `>>>`/`...` prompt lines not being treated as blank
  lines (broke every for/try/if example needing a blank terminator)
- working CI (test/lint matrix + OIDC trusted-publish release workflow)
- real Sphinx docs site (quickstart, full `conf.py` reference, fork
  history)

See `docs/source/about.rst` for the full project lineage.

[Unreleased]: https://github.com/petercorke/sphinx-pyrunblock/compare/v1.1.0...HEAD
[1.1.0]: https://github.com/petercorke/sphinx-pyrunblock/compare/v1.0.1...v1.1.0
[1.0.1]: https://github.com/petercorke/sphinx-pyrunblock/compare/v1.0.0...v1.0.1
[1.0.0]: https://github.com/petercorke/sphinx-pyrunblock/releases/tag/v1.0.0
