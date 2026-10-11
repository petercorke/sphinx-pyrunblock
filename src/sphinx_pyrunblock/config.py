"""Extension-wide configuration: the AutoRun language registry and errors."""

from sphinx.errors import SphinxError


class RunBlockError(SphinxError):
    category = "runblock error"


class AutoRun(object):
    """Registry of languages a ``runblock`` directive may target.

    Populated with defaults below, then merged with the ``autorun_languages``
    dict from ``conf.py`` on the Sphinx ``builder-inited`` event.
    """

    # default configuration parameters; never mutated, so that each build
    # starts from these rather than from whatever an earlier build in the
    # same process left behind
    DEFAULTS = {
        "pycon": "python ",  # declare pycon a valid language
        "pycon_prefix_chars": 4,
        "pycon_show_source": False,
        "pycon_fail_on_error": False,
    }

    # the configuration in effect for the current build
    config = dict(DEFAULTS)

    @classmethod
    def builder_init(cls, app):
        # executed on a Sphinx builder-inited event
        # - the defaults updated with the values from conf.py, rebuilt from
        #   scratch so one build's settings can't leak into the next
        cls.config = {**cls.DEFAULTS, **app.builder.config.autorun_languages}
