# -*- coding: utf-8 -*-

"""
.. module:: esgprep._utils.__init__.py
   :platform: Unix
   :synopsis: esgprep utilities initializer.

.. moduleauthor:: Guillaume Levavasseur <glipsl@ipsl.fr>

"""

import pickle

from esgprep._utils.print import *


def match(pattern, string, inclusive=True):
    """
    Validates a string against a regular expression.
    Only match at the beginning of the string.
    Default is to match inclusive regex.

    """
    if inclusive:
        return True if re.search(pattern, string) else False
    else:
        return True if not re.search(pattern, string) else False


def load(path):
    """
    Loads data from a Pickle file.

    """
    with open(path, 'rb') as f:
        while True:
            try:
                yield pickle.load(f)
            except EOFError:
                break


def store(path, data):
    """
    Stores data into a Pickle file.

    """
    with open(path, 'wb') as f:
        for i in range(len(data)):
            pickle.dump(data[i], f)
