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
CONTROLLED_ARGS = ['set_values', 'set_keys', 'mode', 'version']

# Tree context file
TREE_FILE = '/tmp/DRSTree.pkl'
