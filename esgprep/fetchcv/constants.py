# -*- coding: utf-8 -*-

"""
    :platform: Unix
    :synopsis: Constants used in this module.

"""

# GitHub configuration
GITHUB_CONTENT_API = 'https://api.github.com/repos/ES-DOC/pyessv-archive/contents'
GITHUB_TREE_API = 'https://api.github.com/repos/ES-DOC/pyessv-archive/git/trees/{}?recursive=1'

# List of variable required by each process
PROCESS_VARS = ['outdir',
                'progress',
                'lock',
                'auth',
                'keep',
                'overwrite',
                'backup_mode',
                'nfiles',
                'error']
