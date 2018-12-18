#!/usr/bin/env python
# -*- coding: utf-8 -*-

"""
    :platform: Unix
    :synopsis: Constants used in this package.

"""

from datetime import datetime

# Program version
VERSION = '2.9.4'

# Date
VERSION_DATE = datetime(year=2018, month=12, day=10).strftime("%Y-%d-%m")

# Shell colors map
SHELL_COLORS = {'red': 1,
                'green': 2,
                'yellow': 3,
                'blue': 4,
                'magenta': 5,
                'cyan': 6,
                'gray': 7}

# GitHub API parameter for references
GITHUB_API_PARAMETER = '?{}={}'
