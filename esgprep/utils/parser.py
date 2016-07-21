#!/usr/bin/env python
"""
   :platform: Unix
   :synopsis: Methods used to parser ESGF ini files.

"""

import ConfigParser
import logging
import os
import re
import string

from constants import *


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


def translate_directory_format(cfg, project, project_section):
    """
    Return a list of regular expression filters associated with the ``directory_format`` option
    in the configuration file. This can be passed to the Python ``re`` methods.

    :param RawConfigParser cfg: The configuration file parser (as a :func:`ConfigParser.RawConfigParser` class instance)
    :param project: The project id as a DRS component
    :param str project_section: The project section name to parse
    :returns: The corresponding ``re`` pattern

    """
    # Translation
    pattern = cfg.get(project_section, 'directory_format', raw=True).strip()
    pattern = pattern.replace('\.', '__ESCAPE_DOT__')
    pattern = pattern.replace('.', r'\.')
    pattern = pattern.replace('__ESCAPE_DOT__', r'\.')
    # Build %(project)s variable if not exists or replace it by default value
    if not re.compile(r'%\((project)\)s').search(pattern):
        pattern = re.sub(project.lower(), r'(?P<project>[\\w.-]+)', pattern)
        logging.warning('%(project)s pattern added to "directory_format')
    else:
        project_default = get_default_value(cfg, project_section, 'project')
        pattern = re.sub(re.compile(r'%\((project)\)s'), project_default, pattern)
        logging.warning('%(project)s pattern replaced by default value: {0}'.format(project_default))
    # Build %(root)s variable if not exists or translate it
    if not re.compile(r'%\((root)\)s').search(pattern):
        pattern = re.sub(re.compile(r'^[\w./-]+'), r'(?P<root>[\w./-]+)/', pattern)
        logging.warning('%(root)s pattern added to "directory_format')
    else:
        pattern = re.sub(re.compile(r'%\((root)\)s'), r'(?P<\1>[\w./-]+)', pattern)
    # Include specific facet patterns
    for facet, facet_pattern in get_patterns(cfg, project_section).iteritems():
        pattern = re.sub(re.compile(r'%\(({0})\)s'.format(facet)), facet_pattern, pattern)
    # Constraint on %(version)s number
    pattern = re.sub(re.compile(r'%\((version)\)s'), r'(?P<\1>v[\d]+|latest)', pattern)
    # Translate all patterns matching %(name)s
    pattern = re.sub(re.compile(r'%\(([^()]*)\)s'), r'(?P<\1>[\w.-]+)', pattern)
    return '^{0}/(?P<filename>[\w.-]+)$'.format(pattern)


def get_patterns(cfg, section):
    """
    Get all ``facet_patterns`` attributes declared into the project section.

    :param RawConfigParser cfg: The configuration file parser (as a :func:`ConfigParser.RawConfigParser` class instance)
    :param str section: The section name to parse
    :returns: A dictionary of {facet: pattern}
    """
    patterns = dict()
    for option in cfg.options(section):
        if '_pattern' in option and option != 'version_pattern':
            facet = option.split('_')[0]
            pattern = cfg.get(section, option, raw=True)
            pattern = re.sub(re.compile(r'%\((digit)\)s'), r'[\d]+', pattern)
            pattern = re.sub(re.compile(r'%\((string)\)s'), r'[\w]+', pattern)
            patterns[facet] = '(?P<{0}>{1})'.format(facet, pattern)
    return patterns


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
        if facet not in get_patterns(cfg, section).keys() + IGNORED_FACETS:
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
    elif cfg.has_option(section, '{0}_pattern'.format(facet)):
        pass  # TODO: returns the re.compile(facet_pattern)
    else:
        msg = '"{0}_options", "{0}_map" or "{0}_pattern" is required in section "{1}"'.format(facet, section)
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
        msg = '{0} is misdeclared. {1} facet has to be in "destination facets"'.format(option, facet)
        logging.warning(msg)
        raise Exception(msg)
    return list(set([value[to_keys.index(facet)] for value in value_map.values()]))


def get_options_from_map_in_sources(cfg, section, option, facet):
    """
    Returns the list of facet options from maptable.
    :param RawConfigParser cfg: The configuration file parser (as a :func:`ConfigParser.RawConfigParser` class instance)
    :param str section: The section name to parse
    :param str option: The maptable to parse
    :param str facet: The facet to get available values
    :returns: The facet options
    :rtype: *list*
    :raises Error: If the facet key is not in the destination keys of the maptable

    """
    from_keys, to_keys, value_map = split_map(cfg.get(section, option))
    if facet not in from_keys:
        msg = '{0} is misdeclared. {1} facet has to be in "source facets"'.format(option, facet)
        logging.warning(msg)
        raise Exception(msg)
    return list(set([value[from_keys.index(facet)] for value in value_map.values()]))



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


def get_default_value(cfg, section, facet):
    """
    Returns the list of facet options from options list.
    :param RawConfigParser cfg: The configuration file parser (as a :func:`ConfigParser.RawConfigParser` class instance)
    :param str section: The section name to parse
    :param str facet: The facet to get default value
    :returns: The facet options
    :rtype: *list*
    :raises Error: If the experiment list is misdeclared

    """
    if not cfg.has_option(section, 'category_defaults'):
        msg = '"category_defaults" attribute is missing'
        logging.warning(msg)
        raise Exception(msg)
    category_default = split_line(cfg.get(section, 'category_defaults'), sep='\n')
    try:
        default_values = {k: v for (k, v) in map(lambda x: split_line(x), category_default[1:])}
    except:
        msg = '"category_defaults" is misdeclared. Please follow the format "facet | default_value"'
        logging.warning(msg)
        raise Exception(msg)
    return default_values[facet]


def get_maps(cfg, section):
    """
    Returns the list of maptables.
    :param RawConfigParser cfg: The configuration file parser (as a :func:`ConfigParser.RawConfigParser` class instance)
    :param str section: The section name to parse
    :returns: The maptables list
    :rtype: *list*
    :raises Error: If the "maps" options is missing list is misdeclared

    """
    if not cfg.has_option(section, 'maps'):
        msg = '"maps" attribute is missing'
        logging.warning(msg)
        raise Exception(msg)
    return split_line(cfg.get(section, 'maps'), sep=',')

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
