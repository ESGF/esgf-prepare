# -*- coding: utf-8 -*-

"""
.. module:: esgprep._exceptions.io.py
   :platform: Unix
   :synopsis: esgprep IO exceptions.

.. moduleauthor:: Guillaume Levavasseur <glipsl@ipsl.fr>

"""

import os


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
