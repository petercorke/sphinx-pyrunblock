"""Real Sphinx builds for behaviour that's awkward to unit-test in isolation.

Drives ``sphinx.application.Sphinx`` directly rather than the
``sphinx.testing`` pytest plugin: that plugin's internal API has churned
across major Sphinx versions (e.g. ``sphinx.testing.path`` was removed in
Sphinx 7), whereas ``sphinx.application.Sphinx`` is the stable public
surface and ships with the base package already required by this project.
"""

import re
from pathlib import Path

import pytest
from sphinx.application import Sphinx
from sphinx.errors import SphinxError

ROOTS = Path(__file__).parent / "roots"


def _build(src_dir, tmp_path):
    app = Sphinx(
        srcdir=str(src_dir),
        confdir=str(src_dir),
        outdir=str(tmp_path / "build"),
        doctreedir=str(tmp_path / "doctrees"),
        buildername="html",
    )
    app.build()
    return app


def test_basic_build_succeeds_with_no_raw_traceback(tmp_path):
    app = _build(ROOTS / "test-basic", tmp_path)
    assert app.statuscode == 0

    html = (tmp_path / "build" / "index.html").read_text("utf-8")
    assert "RUNBLOCK-ERROR" not in html
    assert "Traceback" not in html


def test_include_filters_to_requested_line_only(tmp_path):
    # Pygments tokenises *input* lines into many small spans, but an output
    # line (class "go", generic-output) is left as one plain span, so it's
    # the reliable thing to check for a specific rendered value.
    _build(ROOTS / "test-basic", tmp_path)
    html = (tmp_path / "build" / "index.html").read_text("utf-8")
    assert '<span class="go">two</span>' in html
    assert '<span class="go">one</span>' not in html
    assert '<span class="go">three</span>' not in html


def test_numpy_option_available_in_block(tmp_path):
    app = _build(ROOTS / "test-basic", tmp_path)
    assert app.statuscode == 0
    html = (tmp_path / "build" / "index.html").read_text("utf-8")
    assert '<span class="go">np.int64(6)</span>' in html


def test_no_prompt_renders_plain_python_language(tmp_path):
    _build(ROOTS / "test-no-prompt", tmp_path)
    html = (tmp_path / "build" / "index.html").read_text("utf-8")
    assert "highlight-python" in html


def test_no_prompt_block_has_no_repl_prompt_spans(tmp_path):
    _build(ROOTS / "test-no-prompt", tmp_path)
    html = (tmp_path / "build" / "index.html").read_text("utf-8")
    # The first two blocks are :no-prompt:; neither should contain a
    # ">>> " prompt span (class "gp", generic-prompt) anywhere before the
    # third, plain block's own prompts start.
    no_prompt_section = html.split('highlight-pycon')[0]
    assert 'class="gp"' not in no_prompt_section


def test_no_prompt_output_rendered_as_comment(tmp_path):
    _build(ROOTS / "test-no-prompt", tmp_path)
    html = (tmp_path / "build" / "index.html").read_text("utf-8")
    assert '<span class="c1"># → 8</span>' in html


def test_no_prompt_preserves_compound_statement_indentation(tmp_path):
    # Regression: :no-prompt: content has no >>> / ... prompts to encode
    # indentation, so the directive must not destructively .strip() every
    # line -- that would flatten a for-loop's body and produce a
    # SyntaxError instead of executing it.
    app = _build(ROOTS / "test-no-prompt", tmp_path)
    assert app.statuscode == 0
    html = (tmp_path / "build" / "index.html").read_text("utf-8")
    assert "RUNBLOCK-ERROR" not in html
    assert '<span class="c1"># → 0</span>' in html
    assert '<span class="c1"># → 1</span>' in html
    assert '<span class="c1"># → 2</span>' in html


def test_plain_block_after_no_prompt_blocks_still_uses_pycon(tmp_path):
    _build(ROOTS / "test-no-prompt", tmp_path)
    html = (tmp_path / "build" / "index.html").read_text("utf-8")
    assert "highlight-pycon" in html
    assert '<span class="go">8</span>' in html


def test_error_does_not_fail_build_by_default(tmp_path):
    app = _build(ROOTS / "test-error-default", tmp_path)
    assert app.statuscode == 0
    html = (tmp_path / "build" / "index.html").read_text("utf-8")
    assert "RUNBLOCK-ERROR" in html


def test_fail_on_error_raises_runblockerror(tmp_path):
    with pytest.raises(SphinxError, match=r"runblock failed executing code"):
        _build(ROOTS / "test-fail-on-error", tmp_path)


def test_unknown_language_raises_runblockerror(tmp_path):
    src = tmp_path / "src"
    src.mkdir()
    (src / "conf.py").write_text('extensions = ["sphinx_pyrunblock"]\n')
    (src / "index.rst").write_text(
        "Test\n====\n\n.. runblock:: no_such_language\n\n   >>> 1\n"
    )

    with pytest.raises(SphinxError, match="Unknown language"):
        _build(src, tmp_path)


def test_session_carries_state_between_blocks(tmp_path):
    app = _build(ROOTS / "test-session", tmp_path)
    assert app.statuscode == 0
    html = (tmp_path / "build" / "index.html").read_text("utf-8")
    assert "RUNBLOCK-ERROR" not in html
    # x and counter were set in the first block, read in the second; counter
    # is 5 (not 0+5+0...) because runfirst ran once, at the session start
    assert '<span class="go">42</span>' in html
    assert '<span class="go">5</span>' in html


def test_session_isolation(tmp_path):
    _build(ROOTS / "test-session", tmp_path)
    index = (tmp_path / "build" / "index.html").read_text("utf-8")
    other = (tmp_path / "build" / "other.html").read_text("utf-8")
    # a named session, a block with no session, and the same unnamed
    # session in another document must each see none of the state
    assert index.count('<span class="go">False</span>') == 2
    assert '<span class="go">False</span>' in other


def test_session_linenos_continue_from_session_start(tmp_path):
    _build(ROOTS / "test-session", tmp_path)
    html = (tmp_path / "build" / "index.html").read_text("utf-8")
    numbers = [int(n) for n in re.findall(r'class="linenos">\s*(\d+)<', html)]
    # block 1 shows 2 lines (assignments print nothing), block 2 shows 4
    assert numbers == [1, 2, 3, 4, 5, 6]
