# -*- coding: utf-8 -*-

"""
.. module:: esgprep.contants.py
   :platform: Unix
   :synopsis: esgprep common constants.

.. moduleauthor:: Guillaume Levavasseur <glipsl@ipsl.fr>

"""

from datetime import datetime

# Program version
# Remember to change VERSION_DATE below when updating
VERSION = "3.0.0"

# Date
VERSION_DATE = datetime.now().strftime("%Y-%d-%m")

# Shell colors map
SHELL_COLORS = {
    "red": 1,
    "green": 2,
    "yellow": 3,
    "blue": 4,
    "magenta": 5,
    "cyan": 6,
    "gray": 7,
}

# GitHub API parameter for references
GITHUB_API_PARAMETER = "?{}={}"

# DRS version pattern
VERSION_PATTERN = r"(v\d{8})|(latest)"

# Spinner frames
FRAMES = ["[-----<]", "[----<-]", "[---<--]", "[--<---]", "[-<----]", "[<-----]"]

# Final spinner frame
FINAL_FRAME = "[<<<<<<]"
FINAL_STATUS = "Completed"
