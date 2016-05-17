#!/usr/bin/env python
"""
   :platform: Unix
   :synopsis: Useful functions to use with drslite module.

"""

import os
import re
import string
import logging
import ConfigParser
import textwrap
from argparse import HelpFormatter
from datetime import datetime


class MultilineFormatter(HelpFormatter):
    """
    Custom formatter class for argument parser to use with the Python
    `argparse <https://docs.python.org/2/library/argparse.html>`_ module.

    """
    def __init__(self, prog):
        # Overload the HelpFormatter class.
        super(MultilineFormatter, self).__init__(prog, max_help_position=60, width=100)

    def _fill_text(self, text, width, indent):
        # Rewrites the _fill_text method to support multiline description.
        text = self._whitespace_matcher.sub(' ', text).strip()
        multiline_text = ''
        paragraphs = text.split('|n|n ')
        for paragraph in paragraphs:
            lines = paragraph.split('|n ')
            for line in lines:
                formatted_line = textwrap.fill(line, width,
                                               initial_indent=indent,
                                               subsequent_indent=indent) + '\n'
                multiline_text += formatted_line
            multiline_text += '\n'
        return multiline_text

    def _split_lines(self, text, width):
        # Rewrites the _split_lines method to support multiline helps.
        text = self._whitespace_matcher.sub(' ', text).strip()
        lines = text.split('|n ')
        multiline_text = []
        for line in lines:
            multiline_text.append(textwrap.fill(line, width))
        multiline_text[-1] += '\n'
        return multiline_text


def init_logging(logdir, level='INFO'):
    """
    Initiates the logging configuration (output, message formatting).
    In the case of a logfile, the logfile name is unique and formatted as follows:
    ``name-YYYYMMDD-HHMMSS-JOBID.log``

    :param str logdir: The relative or absolute logfile directory. If ``None`` the standard output is used.
    :param str level: The log level.

    """
    __LOG_LEVELS__ = {'CRITICAL': logging.CRITICAL,
                      'ERROR': logging.ERROR,
                      'WARNING': logging.WARNING,
                      'INFO': logging.INFO,
                      'DEBUG': logging.DEBUG,
                      'NOTSET': logging.NOTSET}
    if logdir:
        logfile = 'drslite-{0}-{1}.log'.format(datetime.now().strftime("%Y%m%d-%H%M%S"),
                                                os.getpid())
        if not os.path.isdir(logdir):
            os.makedirs(logdir)
        logging.basicConfig(filename=os.path.join(logdir, logfile),
                            level=__LOG_LEVELS__[level],
                            format='%(asctime)s %(levelname)s %(message)s',
                            datefmt='%Y/%m/%d %I:%M:%S %p')
    else:
        logging.basicConfig(level=__LOG_LEVELS__[level],
                            format='%(asctime)s %(levelname)s %(message)s',
                            datefmt='%Y/%m/%d %I:%M:%S %p')


def config_parse(config_dir, project, project_section):
    """
    Parses the configuration files if exist.

    :param str config_dir: The absolute or relative path of the configuration file directory
    :param str project: The project name to target esg.<project>.ini file
    :param str project_section: The project section
    :returns: The configuration file parser
    :rtype: *dict*
    :raises Error: If no configuration file exists

    """
    if not os.path.isfile('{0}/esg.ini'.format(os.path.normpath(config_dir))):
        raise Exception('"esg.ini" file not found')
    cfg = ConfigParser.ConfigParser()
    cfg.read('{0}/esg.ini'.format(os.path.normpath(config_dir)))
    if project_section not in cfg.sections():
        if not os.path.isfile('{0}/esg.{1}.ini'.format(os.path.normpath(config_dir), project)):
            raise Exception('"esg.{0}.ini" file not found'.format(project))
        cfg.read('{0}/esg.{1}.ini'.format(os.path.normpath(config_dir), project))
    if not cfg:
        raise Exception('Configuration file parsing failed')
    return cfg


def translate_directory_format(directory_format_raw):
    """
    Return a list of regular expression filters associated with the ``directory_format`` option
    in the configuration file. This can be passed to the Python ``re`` methods.

    :param str directory_format_raw: The raw ``directory_format`` string
    :returns: The corresponding ``re`` pattern

    """
    # Pattern matching %(name)s from esg.ini
    esg_variable_pattern = re.compile(r'%\(([^()]*)\)s')
    # Translation
    pattern0 = directory_format_raw.strip()
    pattern1 = pattern0.replace('\.', '__ESCAPE_DOT__')
    pattern2 = pattern1.replace('.', r'\.')
    pattern3 = pattern2.replace('__ESCAPE_DOT__', r'\.')
    pattern4 = re.sub(re.compile(r'%\((root)\)s'), r'(?P<\1>[\w./-]+)', pattern3)
    pattern5 = re.sub(esg_variable_pattern, r'(?P<\1>[\w.-]+)', pattern4)
    return '{0}/(?P<filename>[\w.-]+\.nc)'.format(pattern5)


def split_line(line, sep='|'):
    """
    Split a line into fields removing trailing and leading characters.

    :param str line: String line to split
    :param str sep: Separator character
    :returns:  A list of string fields

    """
    fields = map(string.strip, line.split(sep))
    return fields


def split_record(option, sep='|'):
    """
    Split a multi-line record in a configuration file.

    :param str option: Option in the configuration file.
    :param str sep: Separator character.
    :returns: A list of the form [[field1A, field2A, ...], [field1B, field2B, ...]]

    """
    result = []
    for record in option.split('\n'):
        if record == '':
            continue
        fields = split_line(record, sep)
        result.append(fields)
    return result


def split_map_header(header):
    """
    Split header of a multi-line map in a configuration file.
    A map header defines the mapping between two sets of facets id.

    :param str header: Header line of multi-line map
    :returns: 'from' and 'to' tuples representing the keys for the mapping

    """
    header_pattern = re.compile(r'map\s*\((?P<from_keys>[^(:)]*):(?P<to_keys>[^(:)]*)\)')
    result = re.match(header_pattern, header).groupdict()
    from_keys = split_line(result['from_keys'], sep=',')
    to_keys = split_line(result['to_keys'], sep=',')
    return from_keys, to_keys


def split_map(option, sep='|'):
    """
    Split a multi-line map in a configuration file.

    :param str option: Option in the configuration file
    :param str sep: Separator character
    :returns: A dictionary mapping the 'from' tuples to the 'to' tuples

    """
    lines = option.split('\n')
    from_keys, to_keys = split_map_header(lines[0])
    n_from = len(from_keys)
    result = {}
    for record in lines[1:]:
        if record == '':
            continue
        fields = map(string.strip, record.split(sep))
        from_values = tuple(fields[0:n_from])
        to_values = tuple(fields[n_from:])
        if from_values not in result.keys():
            result[from_values] = to_values
        else:
            raise Exception('"{0}" maptable has duplicated lines'.format(lines[0]))
    return from_keys, to_keys, result
