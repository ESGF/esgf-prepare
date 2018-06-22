#!/usr/bin/env python
# -*- coding: utf-8 -*-

"""
    :platform: Unix
    :synopsis: Constants used in this module.

"""

# Facets ignored during checking
IGNORED_KEYS = ['root', 'project', 'filename', 'period_start', 'period_end', 'version']

# List of variable required by each process
PROCESS_VARS = ['directory',
                'dataset_id',
                'dataset_list',
                'incoming',
                'source_values',
                'pattern',
                'set_keys',
                'facets',
                'lock',
                'progress',
                'source_type',
                'scan_data',
                'scan_errors',
                'nbsources']

# Status messages
STATUS = {0: 'ALL USED VALUES ARE PROPERLY DECLARED',
          1: 'THERE WERE UNDECLARED VALUES USED',
          2: 'NO USED VALUES FOUND',
          4: 'NO DECLARED VALUES FOUND'}

# Table width
FACET_WIDTH = 20
STATUS_WIDTH = 40
WIDTH = FACET_WIDTH + STATUS_WIDTH + 4

# Source type label
SOURCE_TYPE = {
    'file': 'file(s)',
    'dataset': 'dataset(s)'
}
