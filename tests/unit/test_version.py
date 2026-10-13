"""
Unit tests for the version reported by the esgprep command-line tools.
"""

import re
from importlib.metadata import version

from esgprep import __version__
from esgprep.constants import VERSION, VERSION_DATE


def test_version_matches_package_metadata():
    """constants.VERSION must match the version declared in pyproject.toml."""
    assert VERSION == version("esgprep")


def test_version_date_is_iso_format():
    """VERSION_DATE is a fixed release date in YYYY-MM-DD format."""
    assert re.fullmatch(r"\d{4}-(0[1-9]|1[0-2])-(0[1-9]|[12]\d|3[01])", VERSION_DATE)


def test_version_string():
    """The --version string shows the version and the release date."""
    assert __version__ == f"from esgprep v{VERSION} {VERSION_DATE}"
