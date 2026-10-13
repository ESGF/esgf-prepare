# -*- coding: utf-8 -*-

"""
.. module:: esgprep.contants.py
   :platform: Unix
   :synopsis: esgprep common constants.

.. moduleauthor:: Guillaume Levavasseur <glipsl@ipsl.fr>

"""

# Program version
# Keep in sync with "version" in pyproject.toml and update VERSION_DATE when releasing
VERSION = "3.4.0"

# Release date (YYYY-MM-DD)
VERSION_DATE = "2026-10-13"

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
