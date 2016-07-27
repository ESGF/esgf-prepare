#!/usr/bin/env python
# -*- coding: utf-8 -*-

"""
.. module:: esgprep.drs.main.py
    :platform: Unix
    :synopsis: Manages the filesystem tree according to the project DRS and versioning.

.. moduleauthor:: Guillaume Levavasseur <glipsl@ipsl.jussieu.fr>

"""

import logging


def main(args):
    """
    Main process that:

     * Instantiates processing context
     * Parses the configuration files options and values,
     * Deduces facets and values from directories,
     * Compares the values of each facet between both,
     * Print or log the checking.

    :param ArgumentParser args: Parsed command-line arguments

    """
    logging.info('This tool is not available at the moment. Coming soon.')
