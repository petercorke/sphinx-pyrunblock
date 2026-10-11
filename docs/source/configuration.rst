Configuration
=============

``sphinx-pyrunblock`` is configured through a single ``conf.py`` dict,
``autorun_languages``. This page is the complete reference for it. For
options that apply to one ``runblock`` directive invocation rather than
the whole document, see :ref:`per-block options <index:Per-block options>`.

Configuration is backward compatible with the older ``sphinx-autorun`` extension, 
but the ``console`` language prefix is not supported.   ``pycon_input_encoding``
and ``pycon_output_encoding`` are not supported, but are silently ignored if present in ``conf.py``.  


The ``autorun_languages`` dict
-------------------------------

.. code-block:: python

    autorun_languages = {}
    autorun_languages["pycon_runfirst"] = "..."

The dict's keys are **not** language names in the usual sense -- ``pycon``
is really the only supported language, a historical artifact of an earlier
design that also executed a ``console`` (bash) language via a separate
subprocess. That's no longer how this extension works: blocks run in
an in-process ``code.InteractiveInterpreter``, which is what makes it
fast (no subprocess spawned per code block). Each block gets its own
namespace unless it joins a :ref:`session <index:Persistent sessions>`
with ``:session:``. Think of
``pycon`` as the key *prefix* under which each of the settings below is
namespaced, rather than a literal interpreter selection.

At Sphinx's ``builder-inited`` event, whatever you set in
``autorun_languages`` is merged on top of the extension's own defaults
(``pycon``, ``pycon_prefix_chars``, ``pycon_show_source``,
``pycon_fail_on_error``). You only need to set the keys you want to
change.

Per-language keys
------------------

``<lang>`` is prefix for the keys given below. It is also the argument to the ``runblock`` directive
(e.g. ``.. runblock:: pycon`` implies that the block will processed as the language ``"pycon"``.
The *value* itself is vestigial -- it dates from the
old subprocess-per-language design, where it was the shell command to
pipe code into. It isn't read for anything today; only the key's
presence matters.  This provides backward compatibility with the older ``sphinx-autorun`` extension, which used the value to specify the interpreter command.

``<lang>_prefix_chars``
    Number of characters to strip from the start of each prompted line
    (``>>>`` or ``...``, plus the following space) before executing it.
    Defaults to ``0`` if unset; the built-in ``pycon`` default is ``4``,
    matching the length of ``"``>>> ``"``.

``<lang>_show_source``
    If true, echo each line of source to the Sphinx build log as it runs
    (useful when debugging a block that isn't producing the output you
    expect). Defaults to ``False``.

``<lang>_fail_on_error``
    If true, a ``runblock`` whose code raises an exception (or fails to
    parse) fails the Sphinx build instead of just embedding the
    ``!! [RUNBLOCK-ERROR]`` marker in the rendered output -- see
    :ref:`index:Error reporting`. Defaults to ``False``, so existing
    docs with a runblock that deliberately demonstrates an error keep
    building. Applies to the whole block, including any
    ``<lang>_runfirst`` setup code and the ``:numpy:``/``:scipy:``/
    ``:smtb:``/``:precision:`` options layered on top of it.

``<lang>_runfirst``
    A newline-separated string of Python statements, **without prompts**,
    executed before every ``runblock:: <lang>`` block in the document, in
    that block's own namespace -- or, for blocks that use ``:session:``,
    once at the start of the session. Doesn't appear in
    the rendered output. This is the main per-project customisation
    point -- typically used to import commonly-used modules and set up
    formatting/print options once, rather than repeating it in every
    example.

A full worked example
-----------------------

This is the actual ``pycon_runfirst`` used to build this documentation
(also representative of what Peter's other toolboxes use): it silences
colour-code output from two libraries that would otherwise embed raw
ANSI escapes in the HTML, and fixes numpy's print precision so output is
stable across builds.

.. code-block:: python

    autorun_languages = {}
    autorun_languages[
        "pycon_runfirst"
    ] = """
    from spatialmath import SE3
    SE3._color = False
    import numpy as np
    np.set_printoptions(precision=4, suppress=True)
    from ansitable import ANSITable
    ANSITable._color = False
    """

Gotchas
-------

- The directive's ``:numpy:``/``:scipy:`` options (see
  :ref:`per-block options <index:Per-block options>`) layer **on top of**
  ``<lang>_runfirst`` -- they don't replace it. ``<lang>_runfirst`` always
  runs first, then any per-block imports requested via directive options.
- ``:precision: N`` calls ``np.set_printoptions``, so numpy must already
  be imported by that point -- either via ``:numpy:`` on the same
  directive, or because ``<lang>_runfirst`` already imports it.
- ``<lang>_prefix_chars`` only strips characters from lines that actually
  start with a prompt (``>>>`` or ``...``, plus the following space). A
  bare continuation line (for example, the body of a triple-quoted string
  spanning several lines) is
  left untouched, so multi-line string literals in your examples render
  correctly.
