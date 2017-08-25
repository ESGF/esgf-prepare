#!/usr/bin/env python
# -*- coding: utf-8 -*-

"""
    :platform: Unix
    :synopsis: Custom exceptions used in this module.

"""


class DuplicatedDataset(Exception):
    """
    Raised if a dataset already exists with submitted version.

    """

    def __init__(self, version, path):
        self.msg = "Dataset already exists"
        self.msg += "\n<version: '{}'>".format(version)
        self.msg += "\n<path: '{}'>".format(path)
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
