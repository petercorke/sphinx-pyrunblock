# Technical Debt

## `runblock` execution is not thread-safe (`parallel_read_safe: False`)

`setup()` (`src/sphinx_pyrunblock/__init__.py`) declares
`parallel_read_safe: False`, so Sphinx falls back to fully serial reading
whenever a build requests `-j`/parallel reading, and prints a warning.
Documented as expected/ignorable in `docs/source/index.rst`
("Parallel build warning").

### Why

`runsource()` (`src/sphinx_pyrunblock/interpreter.py`) captures a code
block's output by mutating process-global state for the duration of
execution: `sys.stdout`/`sys.stderr` (via `contextlib.redirect_stdout`/
`redirect_stderr`, which set plain module attributes, not thread-locals),
`sys.__stdout__`, and OS file descriptor 1 (via `os.dup2`, to catch
C-extension writes that bypass `sys.stdout`, e.g. numpy/matplotlib).
None of this is reentrant — two `runblock` directives executing
concurrently *in the same process* would race on the save/redirect/
restore sequence and corrupt each other's captured output.

In practice this is currently harmless: Sphinx's `-j` parallel reading
uses separate `multiprocessing` worker processes, each with its own fd
table and `sys.stdout`, so no actual collision occurs today. The `False`
flag is a conservative, correct declaration about the code itself, not a
reaction to an observed bug — kept in case Sphinx's parallel
implementation ever changes, or the extension is invoked from a threaded
context.

### Possible fix (sketch, not started)

Subprocess-per-block isolation (fully safe, but per-block process-spawn
overhead, discussed and rejected for now) vs. a narrower fix: wrap just
the redirect/execute/restore critical section in `runsource()` with a
module-level `threading.Lock()`, e.g.:

```python
_stdout_lock = threading.Lock()

def runsource(self, source, ...):
    ...
    with _stdout_lock:
        devnull_fd = os.open(os.devnull, os.O_WRONLY)
        ...
        os.dup2(devnull_fd, 1)
        ...
        try:
            with contextlib.redirect_stdout(stdout), contextlib.redirect_stderr(stderr):
                self.runcode(code)
        finally:
            ...
```

This serializes only actual code *execution* (milliseconds per block)
rather than Sphinx serializing entire-document *reading*, so it would be
strictly better than today's fallback if `parallel_read_safe` were ever
flipped to `True`. Concurrent runblocks would still queue rather than
truly overlap, since fd 1 is process-wide and can't be made
thread-local — there's no way around that short of subprocess isolation.
No action planned; captured here in case parallel reading becomes a
real bottleneck for some downstream toolbox's docs build.

## `runblock` never fails the Sphinx build on a runtime error — RESOLVED

Resolved 2026-07-31 on `feature/fail-on-error`: added the opt-in
`pycon_fail_on_error` config key described below, exactly as proposed.
`runsource()`/`runblock()` (`src/sphinx_pyrunblock/interpreter.py`) now
return a structured `failed: bool` alongside each result instead of the
old marker-string sniffing, and `RunBlock.run()` raises `RunBlockError`
(with the `file:line` location, matching the existing `!! [RUNBLOCK-ERROR]`
marker's location) when enabled and any statement in the block — including
`runfirst` setup code — failed. Defaults to `False`, so existing docs with
a runblock deliberately demonstrating an error keep building unchanged.
Documented in `docs/source/{index,configuration}.rst`. Downstream
toolboxes (RTB, MVTB, SMTB, bdsim, spatialgeometry) still need to opt in
via their own `conf.py` — that rollout hasn't happened yet.

### Background

`RunBlock.run()` (`src/sphinx_pyrunblock/directive.py`) calls
`runblock()` (`src/sphinx_pyrunblock/interpreter.py`), which executes
each line of a `.. runblock:: pycon` block through an
`InteractiveInterpreter`. When the executed code raises (e.g. a missing
optional dependency), `runsource()` catches it, formats a
`!! [RUNBLOCK-ERROR] ...` marker plus indented traceback, and returns
that as the directive's *output* — but `RunBlock.run()` always returns a
`literal_block` node regardless of whether the code succeeded, so Sphinx
reports the build as green either way. `RunBlockError`
(`src/sphinx_pyrunblock/config.py`) already exists as a `SphinxError`
subclass but is never actually raised anywhere.

Concrete case that motivated this: spatialgeometry
(jhavl/spatialgeometry) has an `intro.rst` `runblock` example calling
`closest_point()`, which needs the optional `coal` dependency. The
docs-build CI job only installed the `docs` extra, not `collision`, so
the block raised `ModuleNotFoundError` on every single build — and that
traceback got baked straight into the published HTML instead of failing
CI. Nobody noticed until someone actually read the live docs page
(2026-07-28). Fixed on the spatialgeometry side by installing the right
extra, but the underlying gap in sphinx-autorun — that this class of bug
is invisible to CI — remains.

### Proposed fix

Add an opt-in `conf.py` config value, e.g. `autorun_fail_on_error = True`
(or per-language, `autorun_languages['pycon_fail_on_error'] = True`),
checked in `RunBlock.run()` after collecting `results` from `runblock()`:
if any result's output starts with the `!! [RUNBLOCK-ERROR]` marker,
raise `RunBlockError` instead of returning the `literal_block`. Default
to `False` for backward compatibility, in case any existing docs have a
runblock that's deliberately demonstrating an error/traceback as
expected output.

Once added, downstream docs builds (RTB, MVTB, SMTB, bdsim,
spatialgeometry) should opt in — turns today's "silently ships a broken
example to production docs" failure mode into a normal, visible CI
failure at the PR that introduced it.

### Resolved — package identity/publishing confusion

This used to be an open question: this repo's `pyproject.toml` was at
`0.8.0` while PyPI's published `sphinx-autorun` was at `2.0.0` under a
different, unrelated author (Hugo Osvaldo Barrera / `WhyNotHugo`) — every
toolbox's `docs` extra listed `"sphinx-autorun"` unpinned, and there was
no way to be sure a fix landed here would ever reach any of them.

Resolved 2026-07-29: this project renamed to **`sphinx-pyrunblock`** and
published properly to PyPI under that name (`pip install
sphinx-pyrunblock`, `github.com/petercorke/sphinx-pyrunblock`, hard fork,
no relation to the `sphinx-autorun` PyPI project). Downstream toolboxes
still need to switch their `docs` extra and `conf.py` `extensions` entry
from `sphinx_autorun` to `sphinx_pyrunblock` — that per-toolbox rollout
(RTB, MVTB, SMTB, spatialgeometry, swift) hasn't happened yet, but the
identity/publishing ambiguity itself is gone.
