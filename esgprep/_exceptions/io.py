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
        self.user = user
        self.path = path
        self.msg = "Read permission required."
        self.msg += f"\n<user: '{user}'>"
        self.msg += f"\n<path: '{path}'>"
        self.msg += f"\n<permissions: '{oct(os.stat(path).st_mode)[-4:]}'>"
        super(self.__class__, self).__init__(self.msg)

    def __reduce__(self):
        return (self.__class__, (self.user, self.path))


class WriteAccessDenied(Exception):
    """
    Raised when user has not write access.

    """

    def __init__(self, user, path):
        self.user = user
        self.path = path
        self.msg = "Write permission required."
        self.msg += f"\n<user: '{user}'>"
        self.msg += f"\n<path: '{path}'>"
        self.msg += f"\n<permissions: '{oct(os.stat(path).st_mode)[-4:]}'>"
        super(self.__class__, self).__init__(self.msg)

    def __reduce__(self):
        return (self.__class__, (self.user, self.path))


class CrossMigrationDenied(Exception):
    """
    Raised when migration fails for cross-device link.

    """

    def __init__(self, src, dst, mode):
        self.msg = "Migration on cross-device disallowed."
        self.msg += f"\n<src: '{src}'>"
        self.msg += f"\n<dst: '{dst}'>"
        self.msg += f"\n<mode: '{mode}'>"
        super(self.__class__, self).__init__(self.msg)


class MigrationDenied(Exception):
    """
    Raised when migration fails in another case.

    """

    def __init__(self, src, dst, mode, reason):
        self.msg = "Migration disallowed."
        self.msg += f"\n<src: '{src}'>"
        self.msg += f"\n<dst: '{dst}'>"
        self.msg += f"\n<mode: '{mode}'>"
        self.msg += f"\n<reason: '{reason}'>"
        super(self.__class__, self).__init__(self.msg)
