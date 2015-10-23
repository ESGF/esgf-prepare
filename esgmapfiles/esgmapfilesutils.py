#!/usr/bin/env python
"""
   :platform: Unix
   :synopsis: Useful functions to use with esg_mapfiles or check_vocab modules.

"""

# Module imports
import os
import re
import string
import logging
import ConfigParser
from datetime import datetime


def init_logging(logdir):
    """
    Initiates the logging configuration (output, message formatting). In the case of a logfile, the logfile name is unique and formatted as follows:
    name-YYYYMMDD-HHMMSS-PID.log

    :param str logdir: The relative or absolute logfile directory. If ``None`` the standard output is used.

    """
    if logdir is 'synda_logger':
        # Logger initiates by SYNDA worker
        pass
    elif logdir:
        name = 'esg_mapfiles'  # os.path.splitext(os.path.basename(os.path.abspath(__file__)))[0]
        logfile = '{0}-{1}-{2}.log'.format(name, datetime.now().strftime("%Y%m%d-%H%M%S"), os.getpid())
        if not os.path.exists(logdir):
            os.makedirs(logdir)
        logging.basicConfig(filename=os.path.join(logdir, logfile),
                            level=logging.DEBUG,
                            format='%(asctime)s %(levelname)s %(message)s',
                            datefmt='%Y/%m/%d %I:%M:%S %p')
    else:
        logging.basicConfig(level=logging.DEBUG,
                            format='%(message)s')


def check_directory(path):
    """
    Checks if the supplied directory exists. The path is normalized before without trailing slash.

    :param list paths: The path to check
    :returns: The same path if exists
    :rtype: *str*
    :raises Error: If the directory does not exist

    """
    directory = os.path.normpath(path)
    if not os.path.isdir(directory):
        raise Exception('No such directory: {0}'.format(directory))
    return directory


def config_parse(config_path):
    """
    Parses the configuration file if exists.

    :param str config_path: The absolute or relative path of the configuration file
    :returns: The configuration file parser
    :rtype: *dict*
    :raises Error: If no configuration file exists

    """
    if not os.path.isfile(config_path):
        raise Exception('Configuration file not found')
    cfg = ConfigParser.ConfigParser()
    cfg.read(config_path)
    if not cfg:
        raise Exception('Configuration file parsing failed')
    return cfg


def split_line(line, sep='|'):
    """
    Split a line into fields.

    :param str line: String line to split.
    :param str sep: Separator character.
    :returns:  A list of string fields.
    
    """
    fields = map(string.strip, line.split(sep))
    return fields


def split_record(option, sep='|'):
    """
    Split a multi-line record in a configuration file.
    
    :param str option: Option in the configuration file.
    :param str sep: Separator character.
    :returns: A list of the form [[field, field, ...], [field, field, ...]]

    """
    result = []
    for record in option.split('\n'):
        if record == '':
            continue
        fields = split_line(record, sep)
        result.append(fields)
    return result


def split_map_header(line):
    """
    Split header of a multi-line map in a configuration file.

    :param str line: Header line of multi-line map.
    :returns: 'from' and 'to' tuples representing the keys for the mapping.

    """
    header_pat = re.compile(r'map\s*\((?P<from_keys>[^(:)]*):(?P<to_keys>[^(:)]*)\)')
    result = re.match(header_pat, line)
    groupdict = result.groupdict()
    from_keys = split_line(groupdict['from_keys'], sep=',')
    to_keys = split_line(groupdict['to_keys'], sep=',')
    return from_keys, to_keys


def split_map(option, sep='|'):
    """
    Split a multi-line map in a configuration file.

    :param str option: Option in the configuration file.
    :param str sep: Separator character.
    :returns: A dictionary mapping the 'from' tuples to the 'to' tuples.
    
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
        result[from_values] = to_values

    return from_keys, to_keys, result
