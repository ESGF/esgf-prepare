#!/usr/bin/env python
# -*- coding: utf-8 -*-

"""
    :platform: Unix
    :synopsis: Constants used in this module.

"""

from os import link, symlink, environ
from shutil import copy2 as copy
from shutil import move

# Facets ignored during checking
IGNORED_KEYS = ['root', 'project', 'filename', 'version', 'period_start', 'period_end']

# Symbolic link separator
LINK_SEPARATOR = ' --> '

# Unix command
UNIX_COMMAND_LABEL = {'symlink': 'ln -s',
                      'link': 'ln',
                      'copy': 'cp',
                      'move': 'mv'}

UNIX_COMMAND = {'symlink': symlink,
                'link': link,
                'copy': copy,
                'move': move}

# Command-line parameter to ignore
CONTROLLED_ARGS = ['directory',
                   'set_values',
                   'set_keys',
                   'mode',
                   'version',
                   'root',
                   'upgrade_from_latest',
                   'ignore_from_latest']

# Tree context file
TREE_FILE = '/tmp/DRSTree_{}.pkl'.format(environ['USER'])
