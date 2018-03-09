#!/usr/bin/env python
# -*- coding: utf-8 -*-

"""
    :platform: Unix
    :synopsis: Constants used in this module.

"""

# Facets ignored during checking
IGNORED_KEYS = ['root', 'project', 'filename', 'period_start', 'period_end']
# TODO: implement filename pattern checking as a facet?

# Mapfile extension during processing
WORKING_EXTENSION = '.part'

# Source type label
SOURCE_TYPE = {
    'file': 'file(s)',
    'dataset': 'dataset(s)'
}
