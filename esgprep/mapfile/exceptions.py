#!/usr/bin/env python
# -*- coding: utf-8 -*-

"""
    :platform: Unix
    :synopsis: Custom exceptions used in this module.

"""


class ChecksumFail(Exception):
    """
    Raised when a checksum fails.

    """

    def __init__(self, path, checksum_type=None):
        self.msg = "Checksum failed."
        self.msg += "\n<file: '{0}'>".format(path)
        if checksum_type:
            self.msg += "\n<checksum type: '{0}'>".format(checksum_type)
        super(self.__class__, self).__init__(self.msg)
