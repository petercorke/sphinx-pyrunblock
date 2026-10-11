"""The ``runblock`` directive itself."""

from code import InteractiveInterpreter

from docutils import nodes
from docutils.parsers.rst import Directive, directives

from .config import AutoRun, RunBlockError
from .interpreter import runblock
from .utils import linerange, shorter, strip_lineno


def build_runfirst(base_runfirst, options):
    """
    Build the code to execute before a runblock's own content.

    ``:numpy:``/``:scipy:`` prepend their import so the language's
    configured ``runfirst`` (which may itself use numpy/scipy) can rely on
    it; ``:smtb:``/``:precision:`` append, since ``:precision:`` in
    particular depends on numpy already being imported by this point.

    :param base_runfirst: the language's configured ``<lang>_runfirst`` string
    :type base_runfirst: str
    :param options: the directive's parsed options (``self.options``)
    :type options: dict
    :return: the final runfirst code
    :rtype: str
    """
    runfirst = base_runfirst
    if "numpy" in options:
        runfirst = "import numpy as np\n" + runfirst
    if "scipy" in options:
        runfirst = "import scipy as sp\n" + runfirst
    if "smtb" in options:
        runfirst += "from spatialmath import *\n"
    if "precision" in options:
        runfirst += f"np.set_printoptions(precision={options['precision']})\n"
    return runfirst


class RunBlock(Directive):
    """
    Subclass of Directive that implements the runblock directive.

    The runblock directive is used to run a block of code and insert the
    output into the document::

        .. runblock:: ARGUMENT
            :OPTION: VALUE
            :OPTION: VALUE

            code block

    ARGUMENT is the language of the code block, e.g. pycon (Python console).
    Each language has some configuration options defined in the AutoRun class.

    """

    has_content = True  # directive has content, the lines of code
    required_arguments = 1  # one required arguent is the language
    optional_arguments = 0
    final_argument_whitespace = False

    # supported options
    #  .flag is True if present, False if not
    #  .unchanged means the option has a value
    option_spec = {
        "linenos": directives.flag,
        "include": directives.unchanged,
        "exclude": directives.unchanged,
        "numpy": directives.flag,
        "scipy": directives.flag,
        "smtb": directives.flag,
        "precision": directives.unchanged,
        "no-prompt": directives.flag,
        "session": directives.unchanged,
    }

    def run(self):
        """
        Format the code block

        This method is invoked on every invocation of the directive.

        - ``self.content`` is a list of lines of the code block, with prompts
        - ``self.arguments`` is a list of arguments to the directive
        - ``self.options`` is a dictionary of options to the directive
        """

        # get the language of the code block
        language = self.arguments[0]  # first argument of the directive

        # process configuration options
        config = AutoRun.config  # dict of configurations from defaults and conf.py

        if language not in config:
            raise RunBlockError("Unknown language %s" % language)

        # Get configuration values for the language from conf.py
        # - get the configuration values LANGUAGE_xxx
        prefix_chars = config.get(
            language + "_prefix_chars", 0
        )  # number of prompt chars to strip
        show_source = config.get(
            language + "_show_source", False
        )  # show the source code
        fail_on_error = config.get(
            language + "_fail_on_error", False
        )  # fail the build if any statement in the block raises

        # attempt to find the originating source, with robust fallback to rst file
        srcfile = shorter(self.reporter.source)

        try:
            note = self.state_machine.observers[0].__self__
            s = str(note.current_source)
            srcfile = shorter(strip_lineno(s))
        except Exception:
            # keep fallback value
            pass

        where = f"{srcfile}:{self.lineno}"

        no_prompt = "no-prompt" in self.options

        # A block with :session: shares its namespace with the other blocks
        # of that session in this document.  env.temp_data is cleared by
        # Sphinx for every document read, which scopes a session to one
        # document: output never depends on the order documents are read in.
        session = None
        if "session" in self.options:
            env = self.state.document.settings.env
            sessions = env.temp_data.setdefault("pyrunblock_sessions", {})
            key = (language, (self.options["session"] or "").strip())
            if key not in sessions:
                sessions[key] = {"console": InteractiveInterpreter(), "lines": 0}
                base_runfirst = config.get(language + "_runfirst", "")
            else:
                # the configured runfirst ran when the session began, running
                # it again would clobber the session's state
                base_runfirst = ""
            session = sessions[key]
        else:
            base_runfirst = config.get(language + "_runfirst", "")

        runfirst = build_runfirst(base_runfirst, self.options)

        include_lines = linerange(self.options.get("include", None))
        exclude_lines = linerange(self.options.get("exclude", None))

        # build the code block

        # first add the runfirst code, which comes from the configuration
        # file; it's a newline-separated string without prompts, and is
        # not shown in the output
        code = [rf.strip() for rf in runfirst.split("\n") if len(rf.strip()) > 0]

        runfirst_len = len(code)

        if no_prompt:
            # Plain code, no prompts to look for -- only trim trailing
            # whitespace. Leading whitespace is real Python indentation
            # (docutils has already removed the directive's own base
            # indentation from self.content) and must survive untouched,
            # otherwise a compound statement's body loses its indent.
            code += [line.rstrip() for line in self.content]
        else:
            # self.content is a list of lines of the code block, with
            # prompts. Only strip the prompt prefix (e.g. ">>> " or "... ")
            # from lines that actually carry a prompt; bare continuation
            # lines (e.g. the body of a triple-quoted string) must not have
            # their content characters removed.
            def _strip_line(line):
                s = line.strip()
                if s in (">>>", "..."):
                    # A bare prompt with nothing typed after it represents
                    # an empty input line (e.g. pressing Enter to close a
                    # compound statement), not literal ">>>"/"..." text.
                    return ""
                if s.startswith((">>> ", "... ")):
                    return s[prefix_chars:]
                return s

            code += [_strip_line(line) for line in self.content]

        ######## RUN THE CODE BLOCK ##########
        results = runblock(
            code,
            show_source,
            where,
            console=session["console"] if session is not None else None,
        )

        # each result is a triple: input, output, and whether it raised.
        # Failure is checked across *all* results, including the runfirst
        # setup code, since a broken runfirst is just as much a bug as a
        # broken block statement.
        if fail_on_error and any(failed for _, _, failed in results):
            raise RunBlockError(f"runblock failed executing code at {where}")

        code_out = ""
        for lineno, (inp, outp, _failed) in enumerate(
            results[runfirst_len:],
            start=1,
        ):  # for all i/o pairs after the runfirst code
            # check if the line is to be included or excluded
            if lineno in exclude_lines:
                continue
            if include_lines and lineno not in include_lines:
                continue

            if no_prompt:
                # Plain code, no REPL prompts. Output lines are rendered as
                # Python comments (rather than bare text) so the whole block
                # stays valid Python under the "python" Pygments lexer used
                # below -- an un-prefixed arrow isn't valid syntax and gets
                # highlighted as a lexer error instead of plain text.
                code_out += inp + "\n"
                if len(outp) > 0:
                    code_out += (
                        "\n".join(f"# → {line}" for line in outp.split("\n"))
                        + "\n"
                    )
            else:
                if "\n" in inp:
                    # multiline input
                    lines = inp.split("\n")
                    code_out += (
                        "\n".join(
                            [">>> " + lines[0]] + ["... " + line for line in lines[1:]]
                        )
                        + "\n"
                    )
                else:
                    code_out += ">>> " + inp + "\n"
                if len(outp) > 0:
                    code_out += outp + "\n"

        literal = nodes.literal_block(code_out, code_out)
        # :no-prompt: renders as plain code, so it needs the "python" lexer
        # rather than "pycon" -- pycon's own input/output distinction relies
        # entirely on the >>> / ... prompts this option removes.
        literal["language"] = "python" if no_prompt else language
        literal["linenos"] = "linenos" in self.options
        if session is not None:
            # line numbers count from the start of the session, over the lines
            # actually displayed (not those hidden by include/exclude/ignore)
            literal["highlight_args"] = {"linenostart": session["lines"] + 1}
            session["lines"] += code_out.count("\n")
        return [literal]
