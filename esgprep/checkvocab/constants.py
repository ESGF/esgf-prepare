#!/usr/bin/env python
# -*- coding: utf-8 -*-

"""
    :platform: Unix
    :synopsis: Constants used in this module.

"""

# Facets ignored during checking
IGNORED_KEYS = ['root', 'project', 'mip_era', 'filename', 'period_start', 'period_end']

# Status messages
STATUS = {0: 'ALL USED VALUES ARE PROPERLY DECLARED',
          1: 'THERE WERE UNDECLARED VALUES USED',
          2: 'NO USED VALUES FOUND',
          4: 'NO DECLARED VALUES FOUND'}

# Table width
FACET_WIDTH = 20
STATUS_WIDTH = 40
WIDTH = FACET_WIDTH + STATUS_WIDTH + 4
