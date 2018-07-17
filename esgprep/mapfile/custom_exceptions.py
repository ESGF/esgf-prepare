#!/usr/bin/env python
# -*- coding: utf-8 -*-

"""
    :platform: Unix
    :synopsis: Custom exceptions used in this module.

"""


class InconsistentDatasetID(Exception):
    """
    Raised when dataset ID doesn't start with the project ID.

    """

    def __init__(self, project, dset_id):
        self.msg = "The dataset ID must start with the project name (case-insensitive)."
        self.msg += "\n<project: '{}'>".format(project)
        self.msg += "\n<dataset ID: '{}'>".format(dset_id)
        super(self.__class__, self).__init__(self.msg)
