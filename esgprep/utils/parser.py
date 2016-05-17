#!/usr/bin/env python
"""
   :platform: Unix
   :synopsis: Methods used to parser ESGF ini files.

"""

# Module imports
import os
import re
import string
import ConfigParser
import logging


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
    pattern = directory_format_raw.strip()
    pattern = pattern.replace('\.', '__ESCAPE_DOT__')
    pattern = pattern.replace('.', r'\.')
    pattern = pattern.replace('__ESCAPE_DOT__', r'\.')
    pattern = re.sub(re.compile(r'%\((root)\)s'), r'(?P<\1>[\w./-]+)', pattern)
    pattern = re.sub(esg_variable_pattern, r'(?P<\1>[\w.-]+)', pattern)
    return '{0}/(?P<filename>[\w.-]+\.nc)'.format(pattern)


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
    if result is None:
        raise Exception('Invalid map header: {0}'.format(header))
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
        if len(from_values) != n_from:
            raise Exception("Map entry does not match header: {0}".format(record))
    return from_keys, to_keys, result


def check_facet(facet, attributes, ctx):
    """
    Checks attribute from path. Each attribute or facet is auto-detected using the DRS pattern
    (regex) and compared to its corresponding options declared into the configuration file, if
    exists.

    :param str facet: The facet name to check with options list
    :param dict attributes: The attributes values auto-detected with DRS pattern
    :param ProcessingContext ctx: A :func:`mapfiles.main.ProcessingContext` class instance
    :raises Error: If the options list is missing
    :raises Error: If the attribute value is missing in the corresponding options list
    :raises Error: If the ensemble facet has a wrong syntax

    """
    if facet not in ['project', 'filename', 'variable', 'version']:
        if ctx.cfg.has_option(ctx.project_section, '{0}_options'.format(facet)):
            if facet == 'experiment':
                experiment_option_lines = split_line(ctx.cfg.get(ctx.project_section,
                                                     '{0}_options'.format(facet)),
                                                     sep='\n')
                if len(experiment_option_lines) > 1:
                    try:

                        options = [exp_option[1] for exp_option in map(lambda x: split_line(x),
                                                                       experiment_option_lines[1:])]
                    except:
                        msg = '"{0}_options" is misconfigured. Please follow the format '\
                            '"project | experiment | description"'.format(facet)
                        logging.warning(msg)
                        raise Exception(msg)
                else:
                    options = split_line(ctx.cfg.get(ctx.project_section,
                                                     '{0}_options'.format(facet)),
                                         sep=',')
            else:
                options = split_line(ctx.cfg.get(ctx.project_section,
                                                 '{0}_options'.format(facet)),
                                     sep=',')
            if attributes[facet] not in options:
                msg = '"{0}" is missing in "{1}_options" of the section "{2}" from '\
                      'esg.{3}.ini'.format(attributes[facet],
                                           facet,
                                           ctx.project_section,
                                           ctx.project)
                logging.warning(msg)
                raise Exception(msg)
        elif facet == 'ensemble':
            if not re.compile(r'r[\d]+i[\d]+p[\d]+').search(attributes[facet]):
                msg = 'Wrong syntax for "ensemble" facet. '\
                      'Please follow the regex "r[0-9]*i[0-9]*p[0-9]*".'
                logging.warning(msg)
                raise Exception(msg)
        else:
            msg = '"{0}_options" is missing in section "{1}" '\
                  'from esg.{2}.ini'.format(facet,
                                            ctx.project_section,
                                            ctx.project)
            logging.warning(msg)
            raise Exception(msg)


def get_facet_from_map(facet, attributes, ctx):
    """
    Get attribute value from the corresponding maptable in ``esg_<project>.ini`` and add
    to attributes dictionary.

    :param str facet: The facet name to get from maptable
    :param dict attributes: The attributes values auto-detected with DRS pattern
    :param ProcessingContext ctx: A :func:`mapfiles.main.ProcessingContext` class instance
    :returns: The updated attributes
    :rtype: *dict*
    :raises Error: If the maptable is missing
    :raises Error: If the maptable is miss-declared
    :raises Error: If the ensemble facet has a wrong syntax

    """
    map_option = '{0}_map'.format(facet)
    if ctx.cfg.has_option(ctx.project_section, map_option):
        from_keys, to_keys, value_map = split_map(ctx.cfg.get(ctx.project_section, map_option))
        if facet not in to_keys:
            msg = '{0}_map is miss-declared in esg.{1}.ini. '\
                  '"{0}" facet has to be in "destination facet"'.format(facet,
                                                                        ctx.project)
            logging.warning(msg)
            raise Exception(msg)
        from_values = tuple(attributes[key] for key in from_keys)
        to_values = value_map[from_values]
        attributes[facet] = to_values[to_keys.index(facet)]
    elif facet == 'ensemble':
        if not re.compile(r'r[\d]+i[\d]+p[\d]+').search(attributes[facet]):
            msg = 'Wrong syntax for "ensemble" facet. '\
                  'Please follow the regex "r[0-9]*i[0-9]*p[0-9]*".'
            logging.warning(msg)
            raise Exception(msg)
    else:
        msg = '{0}_map is required in esg.{1}.ini'.format(facet, ctx.project)
        logging.warning(msg)
        raise Exception(msg)
    return attributes
