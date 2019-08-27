# -*- coding: utf-8 -*-

"""
    :platform: Unix
    :synopsis: Constants used in this module.

"""

# Spinner description.
SPINNER_DESC = 'Mapfiles generation'

# List of variable required by each process
PROCESS_VARS = ['cmd',
                'project',
                'dataset_name',
                'no_version',
                'outdir',
                'mapfile_name',
                'basename',
                'no_checksum',
                'checksums_from',
                'progress',
                'msg_length',
                'checksum_type',
                'notes_url',
                'notes_title',
                'lock',
                'errors']

# Mapfile extension during processing.
WORKING_EXTENSION = '.part'

# Mapfile final extension.
MAPFILE_EXTENSION = '.map'
