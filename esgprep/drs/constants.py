#!/usr/bin/env python
# -*- coding: utf-8 -*-

"""
    :platform: Unix
    :synopsis: Constants used in this module.

"""

# Symbolic link separator
LINK_SEPARATOR = ' --> '

# Unix command
UNIX_COMMAND = {'symlink': 'ln -s',
                'link': 'ln',
                'copy': 'cp',
                'move': 'mv'}

# Command-line parameter to ignore
IGNORED_ARGS = ['action', 'v', 'h', 'log', 'max_threads', 'log', 'no_checksum']

# Progress bar message length
LEN_MSG = 23
