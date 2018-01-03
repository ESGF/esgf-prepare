#!/usr/bin/env python
# -*- coding: utf-8 -*-

"""
    :platform: Unix
    :synopsis: Custom exceptions used in this module.

"""
import os


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


class ReadAccessDenied(Exception):
    """
    Raised when user has no read access.

    """

    def __init__(self, user, path):
        self.msg = "Read permission required."
        self.msg += "\n<user: '{}'>".format(user)
        self.msg += "\n<path: '{}'>".format(path)
        self.msg += "\n<permissions: '{}'>".format(oct(os.stat(path).st_mode)[-4:])
        super(self.__class__, self).__init__(self.msg)


class WriteAccessDenied(Exception):
    """
    Raised when user has not write access.

    """

    def __init__(self, user, path):
        self.msg = "Write permission required."
        self.msg += "\n<user: '{}'>".format(user)
        self.msg += "\n<path: '{}'>".format(path)
        self.msg += "\n<permissions: '{}'>".format(oct(os.stat(path).st_mode)[-4:])
        super(self.__class__, self).__init__(self.msg)


class CrossMigrationDenied(Exception):
    """
    Raised when migration fails for cross-device link.

    """

    def __init__(self, src, dst, mode):
        self.msg = "Migration on cross-device disallowed."
        self.msg += "\n<src: '{}'>".format(src)
        self.msg += "\n<dst: '{}'>".format(dst)
        self.msg += "\n<mode: '{}'>".format(mode)
        super(self.__class__, self).__init__(self.msg)


class MigrationDenied(Exception):
    """
    Raised when migration fails in another case.

    """

    def __init__(self, src, dst, mode, reason):
        self.msg = "Migration disallowed."
        self.msg += "\n<src: '{}'>".format(src)
        self.msg += "\n<dst: '{}'>".format(dst)
        self.msg += "\n<mode: '{}'>".format(mode)
        self.msg += "\n<reason: '{}'>".format(reason)
        super(self.__class__, self).__init__(self.msg)
