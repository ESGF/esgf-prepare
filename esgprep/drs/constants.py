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
IGNORED_KEYS = ['root', 'filename', 'version', 'period_start', 'period_end']

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
                   'no_checksum',
                   'upgrade_from_latest',
                   'ignore_from_latest',
                   'ignore_from_incoming']

# List of variable required by each process
PROCESS_VARS = ['root',
                'pattern',
                'facets',
                'set_values',
                'set_keys',
                'cfg',
                'project',
                'lock',
                'progress',
                'nbsources',
                'no_checksum',
                'checksum_type',
                'mode',
                'upgrade_from_latest',
                'ignore_from_latest',
                'ignore_from_incoming']

# Tree context file
TREE_FILE = '/tmp/DRSTree_{}.pkl'.format(environ['USER'])

# PID prefixes
PID_PREFIXES = {'cmip6': 'hdl:21.14100',
                'cordex': 'hdl:21.14103',
                'obs4mips': 'hdl:21.14102'}
