"""Small pure-function helpers used by the runblock directive."""

import re
from pathlib import Path


def shorter(path):
    """
    Reduce a path to the last two components

    :param path: path to shorten
    :type path: Path or str
    :return: shortened path
    :rtype: str
    """
    # this is horrible... but it works
    return str(Path(*Path(path).parts[-2:]))


def strip_lineno(source):
    """
    Remove a trailing ``:lineno`` from a ``path:lineno`` source string

    Only a trailing run of digits is removed, so the drive-letter colon of a
    Windows path (``C:\\docs\\index.rst:4``) is left alone.

    :param source: source location as reported by docutils
    :type source: str
    :return: the path without any line number
    :rtype: str
    """
    return re.sub(r":\d+$", "", source)


def linerange(s):
    """
    Parse line number range string into a set of integers

    :param s: string of the form "n", "start-end" or "start-"
    :type s: str
    :return: a set of integers in the specified range (inclusive)
    :rtype: set
    """
    if s is None:
        return set()

    parts = s.split("-")
    start = int(parts[0])
    if len(parts) == 1:
        # a single line number
        return {start}
    if len(parts[1]) > 0:
        end = int(parts[1])
        return set(list(range(start, end + 1)))
    else:
        # Open-ended range ("start-"): capped at 100, so a block longer than
        # that is silently truncated rather than materialising an unbounded
        # set. Known limitation, see sphinx-pyrunblock's planning notes.
        return set(list(range(start, 101)))
