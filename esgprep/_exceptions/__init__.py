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
        self.msg += "\n<key: '{}'>".format(key)
        if keys:
            self.msg += "\n<found keys: '{}'>".format(', '.join(keys))
        super(self.__class__, self).__init__(self.msg)


class InvalidChecksumType(Exception):
    """
    Raised when checksum type in unknown.

    """

    def __init__(self, client):
        self.msg = "Checksum type not supported or invalid."
        self.msg += "\n<checksum type: '{}'>".format(client)
        self.msg += "\n<allowed algorithms: '{}'>".format(checksum_types)
        super(self.__class__, self).__init__(self.msg)


class ChecksumFail(Exception):
    """
    Raised when a checksum fails.

    """

    def __init__(self, path, checksum_type=None):
        self.msg = "Checksum failed"
        if checksum_type:
            self.msg += "\n<checksum type: '{}'>".format(checksum_type)
        self.msg += "\n<file: '{}'>".format(path)
        super(self.__class__, self).__init__(self.msg)


class NoFileFound(Exception):
    """
    Raised when no file found.

    """

    def __init__(self, paths):
        self.msg = "No file found"
        for path in paths:
            self.msg += "\n<directory: {}>".format(path)
        super(self.__class__, self).__init__(self.msg)


class DuplicatedDataset(Exception):
    """
    Raised if a dataset already exists with submitted version.

    """

    def __init__(self, path, version):
        self.msg = "Dataset already exists"
        self.msg += "\n<path: '{}'>".format(path)
        self.msg += "\n<version: '{}'>".format(version)
        super(self.__class__, self).__init__(self.msg)


class OlderUpgrade(Exception):
    """
    Raised if a dataset already exists with submitted version.

    """

    def __init__(self, version, latest):
        self.msg = "Upgrade version is older than latest version"
        self.msg += "\n<upgrade version: '{}'>".format(version)
        self.msg += "\n<latest  version: '{}'>".format(latest)
        super(self.__class__, self).__init__(self.msg)


class DuplicatedFile(Exception):
    """
    Raised if a NetCDF file already exists into submitted dataset version.

    """

    def __init__(self, latest, upgrade):
        self.msg = "Latest dataset version already includes NetCDF file"
        self.msg += "\n<latest  file: '{}'>".format(latest)
        self.msg += "\n<upgrade file: '{}'>".format(upgrade)
        super(self.__class__, self).__init__(self.msg)


class UnchangedTrackingID(Exception):
    """
    Raised if a NetCDF file already has the tracking ID of submitted file to upgrade.

    """

    def __init__(self, latest, latest_id, upgrade, upgrade_id):
        self.msg = "Latest file version has the same tracking ID/PID, which has to be unique."
        self.msg += "\n<latest  file: '{} - {}'>".format(latest_id, latest)
        self.msg += "\n<upgrade file: '{} - {}'>".format(upgrade_id, upgrade)
        super(self.__class__, self).__init__(self.msg)


class NoVersionPattern(Exception):
    """
    Raised if no version facet found in the destination format.

    """

    def __init__(self, regex, patterns):
        self.msg = "No version pattern found."
        self.msg += "\n<format: '{}'>".format(regex)
        self.msg += "\n<available patterns: '{}'>".format(patterns)
        super(self.__class__, self).__init__(self.msg)


class InconsistentDRSPath(Exception):
    """
    Raised when DRS path doesn't start with the project ID.

    """

    def __init__(self, project, path):
        self.msg = "DRS path must start with the project name (case-insensitive)."
        self.msg += "\n<project: '{}'>".format(project)
        self.msg += "\n<path: '{}'>".format(path)
        super(self.__class__, self).__init__(self.msg)


class NoProjectCodeFound(Exception):
    """
    Raised when no project code found or extract from DRS path or file.

    """

    def __init__(self, val):
        self.msg = "Unable to find/extract project code."
        self.msg += "\n<keys: '{}'>".format(val)
        super(self.__class__, self).__init__(self.msg)

class MissingCVdata(Exception):
    """
    Raised when CV data is missing for an authority/project.

    """

    def __init__(self, authority, project):
        self.msg = "Unable to find/load CV -- Please use \"esgfetchcv\"."
        self.msg += "\n<authority: '{}'>".format(authority)
        self.msg += "\n<project: '{}'>".format(project)
        super(self.__class__, self).__init__(self.msg)
