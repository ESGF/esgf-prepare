# -*- coding: utf-8 -*-

"""
.. module:: esgprep._utils.ncfile.py
   :platform: Unix
   :synopsis: netCDF utilities.

.. moduleauthor:: Guillaume Levavasseur <glipsl@ipsl.fr>

"""

from uuid import UUID

from fuzzywuzzy.fuzz import partial_ratio
from fuzzywuzzy.process import extractOne
from netCDF4 import Dataset

from esgprep._exceptions import NoProjectCodeFound
from esgprep._exceptions.netcdf import InvalidNetCDFFile, NoNetCDFAttribute
from esgprep.drs.constants import PID_PREFIXES


class ncopen(object):
    """
    Opens opens a netCDF file

    """

    def __init__(self, path: str, mode: str = "r"):
        # Set file path.
        self.path: str = path

        # Set open mode.
        self.mode: str = mode

        # Instantiate netCDF object.
        self.nc: Dataset | None = None

    def __enter__(self):
        # Load netCDF Dataset content.
        try:
            self.nc = Dataset(self.path, self.mode)  # type: ignore

        # Catch IO error.
        except (IOError, OSError) as error:
            raise InvalidNetCDFFile(self.path, error)

        return self.nc

    def __exit__(self, *exc):
        # Close netCDF file.
        assert self.nc is not None
        self.nc.close()


def get_ncattrs(path: str) -> dict:
    """
    Loads netCDF global attributes from a pathlib.Path as dictionary.
    Ignores attributes with only whitespaces.

    """
    with ncopen(path) as nc:
        dic = {
            attr: nc.getncattr(attr)
            for attr in nc.ncattrs()
            if (str(nc.getncattr(attr)).split())
        }
        return dic


def get_tracking_id(attrs: dict) -> str:
    """
    Get tracking_id/PID string from netCDF global attributes.

    """
    # Get project code.
    project = get_project(attrs)
    assert isinstance(project, str)
    # Set project code from global attributes.
    key, score = extractOne("tracking_id", attrs.keys(), scorer=partial_ratio)  # type: ignore
    if score < 80:
        raise NoNetCDFAttribute("tracking_id", values=attrs.keys())
    identifier = attrs[key].lower()

    # Verify valid value.
    assert is_valid(identifier, project)

    # Return value.
    return identifier


def is_valid(identifier: str, project: str) -> bool:
    """
    Validates a tracking_id/PID string.

    """
    try:
        # Split PID
        prefix, uid = identifier.split("/")

        # Verify PID prefix.
        assert prefix == PID_PREFIXES[project]

    except ValueError:
        # Verify project unknown of PID prefixes in case of simple tracking ID.
        uid = identifier
        assert project not in PID_PREFIXES.keys()

    # Verify UUID format.
    assert is_uuid(uid)

    return True


def is_uuid(uuid_string, version=4):
    """
    Validates an UUID.

    """
    try:
        uid = UUID(uuid_string, version=version)
        return uid.hex == uuid_string.replace("-", "")
    except ValueError:
        return False


def get_project(attrs: str | dict) -> str | None:
    """
    Extract project code from the file attributes.

    """

    # Get attributes.
    if not isinstance(attrs, dict):
        attrs = get_ncattrs(attrs)

    # Set project code from global attributes.
    key, score = extractOne("mip_era", attrs.keys(), scorer=partial_ratio)  # type: ignore
    if score < 80:
        raise NoProjectCodeFound(attrs)

    project = attrs[key].lower()

    # Return project code.
    return project
