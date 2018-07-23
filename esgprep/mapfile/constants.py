#!/usr/bin/env python
# -*- coding: utf-8 -*-

"""
    :platform: Unix
    :synopsis: Constants used in this module.

"""

# Facets ignored during checking
IGNORED_KEYS = ['root', 'filename', 'period_start', 'period_end']

# List of variable required by each process
PROCESS_VARS = ['project',
                'action',
                'source_type',
                'pattern',
                'dataset_name',
                'no_version',
                'outdir',
                'mapfile_name',
                'mapfile_drs',
                'basename',
                'no_checksum',
                'checksums_from',
                'checksum_type',
                'notes_url',
                'notes_title',
                'cfg',
                'facets',
                'progress',
                'nbsources',
                'lock']

# Mapfile extension during processing
WORKING_EXTENSION = '.part'

# Source type label
SOURCE_TYPE = {
    'file': 'file(s)',
    'dataset': 'dataset(s)'
}
