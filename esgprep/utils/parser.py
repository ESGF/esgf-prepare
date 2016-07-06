#!/usr/bin/env python
"""
   :platform: Unix
   :synopsis: Methods used to parser ESGF ini files.

"""

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
    :rtype: *ConfigParser*
    :raises Error: If no configuration file exists

    """
    if not os.path.isfile('{0}/esg.ini'.format(os.path.normpath(config_dir))):
        msg = '"esg.ini" file not found'
        logging.warning(msg)
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
    # Translation
    pattern = directory_format_raw.strip()
    pattern = pattern.replace('\.', '__ESCAPE_DOT__')
    pattern = pattern.replace('.', r'\.')
    pattern = pattern.replace('__ESCAPE_DOT__', r'\.')
    # Translate %(root)s variable
    pattern = re.sub(re.compile(r'%\((root)\)s'), r'(?P<\1>[\w./-]+)', pattern)
    # Constraint on %(ensemble)s variable
    pattern = re.sub(re.compile(r'%\((ensemble)\)s'), r'(?P<\1>r[\d]+i[\d]+p[\d]+)', pattern)
    # Constraint on %(version)s number
    pattern = re.sub(re.compile(r'%\((version)\)s'), r'(?P<\1>v[\d]+|latest)', pattern)
    # Translate all patterns matching %(name)s
    pattern = re.sub(re.compile(r'%\(([^()]*)\)s'), r'(?P<\1>[\w.-]+)', pattern)
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


def build_line(fields, sep=' | '):
    """
    Build a line from fields adding trailing and leading characters.

    :param tuple fields: Tuple of ordered fields
    :param str sep: Separator character
    :returns: A string fields

    """
    line = sep.join(fields)
    return line


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


def check_facet(cfg, section, attributes):
    """
    Checks a facet value against the corresponding options. Each attribute or facet is auto-detected
    using the DRS pattern (regex) and compared to its corresponding options declared into the configuration file, if
    exists.

    :param RawConfigParser cfg: The configuration file parser (as a :func:`ConfigParser.RawConfigParser` class instance)
    :param str section: The section name to parse
    :param dict attributes: A dictionary of {facet: value} to check
    :raises Error: If the attribute value is missing in the corresponding options list

    """
    for facet in attributes:
        if facet not in ['project', 'filename', 'variable', 'version']:
            options = get_facet_options(cfg, section, facet)
            if attributes[facet] not in options:
                msg = '"{0}" is missing in "{1}_options" or "{1}_map" of the section "{2}"'.format(attributes[facet],
                                                                                                   facet,
                                                                                                   section)
                logging.warning(msg)
                raise Exception(msg)
        else:
            pass


def get_facet_options(cfg, section, facet):
    """
    Returns the list of facet options.

    :param RawConfigParser cfg: The configuration file parser (as a :func:`ConfigParser.RawConfigParser` class instance)
    :param str section: The section name to parse
    :param str facet: The facet to get available values
    :return: The facet options
    :rtype: *list*
    :raises Error: If the option list or maptable is missing

    """
    if cfg.has_option(section, '{0}_options'.format(facet)):
        return get_options_from_list(cfg, section, facet)
    elif cfg.has_option(section, '{0}_map'.format(facet)):
        return get_options_from_map(cfg, section, facet)
    else:
        msg = '"{0}_options" or "{0}_map" is required in section "{1}"'.format(facet, section)
        logging.warning(msg)
        raise Exception(msg)


def get_options_from_list(cfg, section, facet):
    """
    Returns the list of facet options from options list.
    :param RawConfigParser cfg: The configuration file parser (as a :func:`ConfigParser.RawConfigParser` class instance)
    :param str section: The section name to parse
    :param str facet: The facet to get available values
    :returns: The facet options
    :rtype: *list*
    :raises Error: If the experiment list is misdeclared

    """
    option = '{0}_options'.format(facet)
    if facet == 'experiment':
        experiment_option_lines = split_line(cfg.get(section, option), sep='\n')
        if len(experiment_option_lines) > 1:
            try:
                options = [exp_option[1] for exp_option in map(lambda x: split_line(x), experiment_option_lines[1:])]
            except:
                msg = '"{0}" is misdeclared. Please follow the format ' \
                      '"project | experiment | description"'.format(option)
                logging.warning(msg)
                raise Exception(msg)
        else:
            options = split_line(cfg.get(section, option), sep=',')
    else:
        options = split_line(cfg.get(section, option), sep=',')
    return options


def get_options_from_map(cfg, section, facet):
    """
    Returns the list of facet options from maptable.
    :param RawConfigParser cfg: The configuration file parser (as a :func:`ConfigParser.RawConfigParser` class instance)
    :param str section: The section name to parse
    :param str facet: The facet to get available values
    :returns: The facet options
    :rtype: *list*
    :raises Error: If the facet key is not in the destination keys of the maptable

    """
    option = '{0}_map'.format(facet)
    from_keys, to_keys, value_map = split_map(cfg.get(section, option))
    if facet not in to_keys:
        msg = '{0} is misdeclared. {1} facet has to be in "destination facet"'.format(option, facet)
        logging.warning(msg)
        raise Exception(msg)
    to_values = set([value[to_keys.index(facet)] for value in value_map.values()])
    return list(to_values)


def get_option_from_map(cfg, section, facet, attributes):
    """
    Returns the corresponding facet option from maptable.
    :param RawConfigParser cfg: The configuration file parser (as a :func:`ConfigParser.RawConfigParser` class instance)
    :param str section: The section name to parse
    :param str facet: The facet to get the value
    :param dict attributes: A dictionary of {facet: value} to input the maptable
    :returns: The facet options
    :rtype: *list*
    :raises Error: If the facet key is not in the destination keys of the maptable

    """
    option = '{0}_map'.format(facet)
    from_keys, to_keys, value_map = split_map(cfg.get(section, option))
    if facet not in to_keys:
        msg = '{0} is misdeclared. {1} facet has to be in "destination facet"'.format(option, facet)
        logging.warning(msg)
        raise Exception(msg)
    from_values = tuple(attributes[key] for key in from_keys)
    to_values = value_map[from_values]
    return to_values[to_keys.index(facet)]


def get_project_options(cfg):
    """
    Returns the list of facet options from options list.
    :param RawConfigParser cfg: The configuration file parser (as a :func:`ConfigParser.RawConfigParser` class instance)
    :returns: The project options
    :rtype: *tuple*
    :raises Error: If the project list is misdeclared

    """
    if cfg.has_option('DEFAULT', 'project_options'):
        project_option_lines = split_line(cfg.get('DEFAULT', 'project_options'), sep='\n')
        try:
            options = [tuple(project_option) for project_option in map(lambda x: split_line(x),
                                                                       project_option_lines[1:])]
        except:
            msg = '"project_options" is misdeclared. Please follow the format "id | project | description".'
            logging.warning(msg)
            raise Exception(msg)
    else:
        options = list()
    return options
