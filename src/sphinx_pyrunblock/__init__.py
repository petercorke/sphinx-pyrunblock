# -*- coding: utf-8 -*-
"""
sphinx_pyrunblock
~~~~~~~~~~~~~~~~~~

Run the code and insert stdout after the code block.

Global options

Add to your ``conf.py`` file::

    autorun_languages = {}
    autorun_languages['pycon_runfirst'] = '''
    lines of code to run before that included in the runblock
    this code does not appear in the output
    use it to set up formatting, for example
    import numpy as np
    np.set_printoptions(precision=4, suppress=True)
    '''

"""

from .config import AutoRun, RunBlockError
from .directive import RunBlock

try:
    from importlib.metadata import version as _get_version

    __version__ = _get_version("sphinx-pyrunblock")
except Exception:
    __version__ = "0.0.0"

__all__ = ["setup", "RunBlock", "AutoRun", "RunBlockError", "__version__"]


def setup(app):
    """
    Add the runblock directive to Sphinx
    """
    app.add_directive("runblock", RunBlock)  # invoked by .. runblock::
    app.connect(
        "builder-inited", AutoRun.builder_init
    )  # connect event "builder-inited" to AutoRun.builder_init
    app.add_config_value(
        "autorun_languages", dict(AutoRun.DEFAULTS), "env"
    )  # declare autorun_languages, it is a dict defined in conf.py
    return {
        "version": __version__,
        "parallel_read_safe": False,
        "parallel_write_safe": True,
    }
