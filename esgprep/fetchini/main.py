#!/usr/bin/env python
# -*- coding: utf-8 -*-

"""
    :platform: Unix
    :synopsis: Fetches ESGF configuration files from GitHub repository.

"""

import logging
import os


import requests

from constants import *
from context import ProcessingContext
from esgprep.utils.custom_exceptions import GitHubException
from esgprep.utils.misc import gh_request_content, backup, write_content, do_fetching


def run(args):
    """
    Main process that:

     * Decide to fetch or not depending on file presence/absence and command-line arguments,
     * Gets the GitHub file content from full API URL,
     * Backups old file if desired,
     * Writes response into INI file.

    :param ArgumentParser args: Parsed command-line arguments

    """
    # Instantiate processing context manager
    with ProcessingContext(args) as ctx:
        try:
            for project in ctx.targets:
                # Set full url
                url = ctx.url.format(INI_FILE.format(project))
                # Set output file full path
                outfile = os.path.join(ctx.config_dir, INI_FILE.format(project))
                # Get GitHub file content
                r = gh_request_content(url=url, auth=ctx.auth)
                sha = r.json()['sha']
                content = requests.get(r.json()['download_url'], auth=ctx.auth).text
                # Fetching True/False depending on flags and file checksum
                if do_fetching(outfile, sha, ctx.keep, ctx.overwrite):
                    # Backup old file if exists
                    backup(outfile, mode=ctx.backup_mode)
                    # Write new file
                    write_content(outfile, content)
                    logging.info('{} :: FETCHED (in {})'.format(url.ljust(LEN_URL), outfile))
                else:
                    logging.info('{} :: SKIPPED'.format(url.ljust(LEN_URL)))
        except GitHubException:
            ctx.error = True
