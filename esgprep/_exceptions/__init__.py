# -*- coding: utf-8 -*-

"""
.. module:: esgprep._exceptions.__init__.py
   :platform: Unix
   :synopsis: esgprep exceptions initializer.

.. moduleauthor:: Guillaume Levavasseur <glipsl@ipsl.fr>

"""
from hashlib import algorithms_available as checksum_types


class KeyNotFound(Exception):
    """
    Raised when a class key is not found.

    """

    def __init__(self, key, keys=None):
        self.msg = "Key not found"
        self.msg += f"\n<key: '{key}'>"
        if keys:
            self.msg += f"\n<found keys: '{', '.join(keys)}'>"
        super(self.__class__, self).__init__(self.msg)


class InvalidChecksumType(Exception):
    """
    Raised when checksum type in unknown.

    """

    def __init__(self, client):
        self.msg = "Checksum type not supported or invalid."
        self.msg += f"\n<checksum type: '{client}'>"
        self.msg += f"\n<allowed algorithms: '{checksum_types}'>"
        super(self.__class__, self).__init__(self.msg)


class ChecksumFail(Exception):
    """
    Raised when a checksum fails.

    """

    def __init__(self, path, checksum_type=None):
        self.msg = "Checksum failed"
        if checksum_type:
            self.msg += f"\n<checksum type: '{checksum_type}'>"
        self.msg += f"\n<file: '{path}'>"
        super(self.__class__, self).__init__(self.msg)


class NoFileFound(Exception):
    """
    Raised when no file found.

    """

    def __init__(self, paths):
        self.msg = "No file found"
        for path in paths:
            self.msg += f"\n<directory: {path}>"
        super(self.__class__, self).__init__(self.msg)


class DuplicatedDataset(Exception):
    """
    Raised if a dataset already exists with submitted version.

    """

    def __init__(self, path, version):
        self.msg = "Dataset already exists"
        self.msg += f"\n<path: '{path}'>"
        self.msg += f"\n<version: '{version}'>"
        super(self.__class__, self).__init__(self.msg)


class OlderUpgrade(Exception):
    """
    Raised if a dataset already exists with submitted version.

    """

    def __init__(self, version, latest):
        self.msg = "Upgrade version is older than latest version"
        self.msg += f"\n<upgrade version: '{version}'>"
        self.msg += f"\n<latest  version: '{latest}'>"
        super(self.__class__, self).__init__(self.msg)


class DuplicatedFile(Exception):
    """
    Raised if a NetCDF file already exists into submitted dataset version.

    """

    def __init__(self, latest, upgrade):
        self.msg = "Latest dataset version already includes NetCDF file"
        self.msg += f"\n<latest  file: '{latest}'>"
        self.msg += f"\n<upgrade file: '{upgrade}'>"
        super(self.__class__, self).__init__(self.msg)


class UnchangedTrackingID(Exception):
    """
    Raised if a NetCDF file already has the tracking ID of submitted file to upgrade.

    """

    def __init__(self, latest, latest_id, upgrade, upgrade_id):
        self.msg = "Latest file version has the same tracking ID/PID, which has to be unique."
        self.msg += f"\n<latest  file: '{latest_id} - {latest}'>"
        self.msg += f"\n<upgrade file: '{upgrade_id} - {upgrade}'>"
        super(self.__class__, self).__init__(self.msg)


class NoVersionPattern(Exception):
    """
    Raised if no version facet found in the destination format.

    """

    def __init__(self, regex, patterns):
        self.msg = "No version pattern found."
        self.msg += f"\n<format: '{regex}'>"
        self.msg += f"\n<available patterns: '{patterns}'>"
        super(self.__class__, self).__init__(self.msg)


class InconsistentDRSPath(Exception):
    """
    Raised when DRS path doesn't start with the project ID.

    """

    def __init__(self, project, path):
        self.msg = "DRS path must start with the project name (case-insensitive)."
        self.msg += f"\n<project: '{project}'>"
        self.msg += f"\n<path: '{path}'>"
        super(self.__class__, self).__init__(self.msg)


class NoProjectCodeFound(Exception):
    """
    Raised when no project code found or extract from DRS path or file.

    """

    def __init__(self, val):
        self.msg = "Unable to find/extract project code."
        self.msg += f"\n<keys: '{val}'>"
        self.msg += "\n"
        self.msg += "\nTo see available projects, run: esgvoc status"
        super(self.__class__, self).__init__(self.msg)


class MissingCVdata(Exception):
    """
    Raised when CV data is missing for an authority/project.

    """

    def __init__(self, authority, project):
        self.msg = "Unable to find/load CV -- Please use \"esgfetchcv\"."
        self.msg += f"\n<authority: '{authority}'>"
        self.msg += f"\n<project: '{project}'>"
        super(self.__class__, self).__init__(self.msg)
