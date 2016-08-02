#!/usr/bin/env python
# -*- coding: utf-8 -*-

"""
   :platform: Unix
   :synopsis: Methods used to parse ESGF ini files.

"""

import ConfigParser
import logging
import os
import re
import string

from constants import *
from exceptions import *


class CfgParser(ConfigParser.ConfigParser):
    """
    Custom ConfigParser class

    """

    def __init__(self):
        ConfigParser.ConfigParser.__init__(self)
        self.read_paths = list()

    def options(self, section, defaults=True, **kwargs):
        """
        Can get options() with/without defaults.

        """
        try:
            opts = self._sections[section].copy()
        except KeyError:
            raise ConfigParser.NoSectionError(section)
        if defaults:
            opts.update(self._defaults)
        if '__name__' in opts:
            del opts['__name__']
        return opts.keys()

    def read(self, filenames):
        """
        Read and parse a filename or a list of filenames, and records there paths.
        """
        if isinstance(filenames, basestring):
            filenames = [filenames]
        for filename in filenames:
            try:
                fp = open(filename)
            except IOError:
                continue
            self._read(fp, filename)
            fp.close()
            self.read_paths.append(filename)


def config_parse(path, section):
    """
    Parses the configuration files if exist.

    :param str path: The absolute or relative path of the configuration file directory
    :param str section: The project section
    :returns: The configuration file parser
    :rtype: *ConfigParser*
    :raises Error: If no configuration file exists
    :raises Error: If the configuration file parsing fails

    """
    path = os.path.abspath(os.path.normpath(path))
    project = section.split('project:')[1]
    if not os.path.isfile('{0}/esg.ini'.format(path)):
        msg = "'esg.ini' not found in '{0}'".format(path)
        logging.warning(msg)
    cfg = CfgParser()
    cfg.read('{0}/esg.ini'.format(path))
    if section not in cfg.sections():
        if not os.path.isfile('{0}/esg.{1}.ini'.format(path, project)):
            raise NoConfigFile('{0}/esg.{1}.ini'.format(path, project))
        cfg.read('{0}/esg.{1}.ini'.format(path, project))
    if section not in cfg.sections():
        raise NoConfigSection(section, cfg.read_paths)
    if not cfg:
        raise EmptyConfigFile(cfg.read_paths)
    return cfg


def translate_directory_format(cfg, project_section):
    """
    Return a list of regular expression filters associated with the ``directory_format`` option
    in the configuration file. This can be passed to the Python ``re`` methods.

    :param RawConfigParser cfg: The configuration file parser (as a :func:`ConfigParser.RawConfigParser` class instance)
    :param str project_section: The project section name to parse
    :returns: The corresponding ``re`` pattern

    """
    # Start translation
    pattern = cfg.get(project_section, 'directory_format', raw=True).strip()
    pattern = pattern.replace('\.', '__ESCAPE_DOT__')
    pattern = pattern.replace('.', r'\.')
    pattern = pattern.replace('__ESCAPE_DOT__', r'\.')
    # Translate %(root)s variable if exists but not required. Can include the project name.
    if re.compile(r'%\((root)\)s').search(pattern):
        pattern = re.sub(re.compile(r'%\((root)\)s'), r'(?P<\1>[\w./-]+)', pattern)
    # Include specific facet patterns
    for facet, facet_regex in get_options_from_patterns(cfg, project_section).iteritems():
        pattern = re.sub(re.compile(r'%\(({0})\)s'.format(facet)), facet_regex.pattern, pattern)
    # Constraint on %(version)s number
    pattern = re.sub(re.compile(r'%\((version)\)s'), r'(?P<\1>v[\d]+|latest)', pattern)
    # Translate all patterns matching %(name)s
    pattern = re.sub(re.compile(r'%\(([^()]*)\)s'), r'(?P<\1>[\w.-]+)', pattern)
    return '{0}/(?P<filename>[\w.-]+)$'.format(pattern)


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
        raise InvalidMapHeader(header_pattern, header)
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
            raise DuplicatedMapEntry(fields)
        if len(from_values) != n_from:
            raise InvalidMapEntry(fields)
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
        if facet not in get_options_from_patterns(cfg, section).keys() + IGNORED_FACETS:
            options, option = get_facet_options(cfg, section, facet)
            if attributes[facet] not in options:
                raise NoConfigValue(attributes[facet], option, section, cfg.read_paths)
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
        return get_options_from_list(cfg, section, facet), '{0}_options'.format(facet)
    elif cfg.has_option(section, '{0}_map'.format(facet)):
        return get_options_from_map(cfg, section, facet), '{0}_map'.format(facet)
    elif cfg.has_option(section, '{0}_pattern'.format(facet)):
        return get_options_from_pattern(cfg, section, facet), '{0}_pattern'.format(facet)
    else:
        raise NoConfigOptions(facet, section, cfg.read_paths)


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
                raise MisdeclaredOption(option, section, cfg.read_paths,
                                        reason="Please follow the format: 'project | experiment | description'")
        else:
            options = split_line(cfg.get(section, option), sep=',')
    else:
        options = split_line(cfg.get(section, option), sep=',')
    return options


def get_options_from_map(cfg, section, facet, in_sources=False):
    """
    Returns the list of facet options from maptable.
    :param RawConfigParser cfg: The configuration file parser (as a :func:`ConfigParser.RawConfigParser` class instance)
    :param str section: The section name to parse
    :param str facet: The facet to get available values
    :param boolean in_sources: True if facet is in "source keys" (default is False)
    :returns: The facet options
    :rtype: *list*
    :raises Error: If the facet key is not in the source/destination keys of the maptable

    """
    option = '{0}_map'.format(facet)
    from_keys, to_keys, value_map = split_map(cfg.get(section, option))
    if in_sources:
        if facet not in from_keys:
            raise MisdeclaredOption(option, section, cfg.read_paths,
                                    reason="'{0}' has to be in 'source facets'".format(facet))
        return list(set([value[from_keys.index(facet)] for value in value_map.keys()]))
    else:
        if facet not in to_keys:
            raise MisdeclaredOption(option, section, cfg.read_paths,
                                    reason="'{0}' has to be in 'destination facets'".format(facet))
        return list(set([value[to_keys.index(facet)] for value in value_map.values()]))


def get_options_from_pattern(cfg, section, facet):
    """
    Get all ``facet_patterns`` attributes declared into the project section.

    :param RawConfigParser cfg: The configuration file parser (as a :func:`ConfigParser.RawConfigParser` class instance)
    :param str section: The section name to parse
    :param str facet: The facet to get available values
    :returns: The facet regex
    :rtype: *re.RegexObject*
    """
    option = '{0}_pattern'.format(facet)
    pattern = cfg.get(section, option, raw=True)
    pattern = re.sub(re.compile(r'%\((digit)\)s'), r'[\d]+', pattern)
    pattern = re.sub(re.compile(r'%\((string)\)s'), r'[\w]+', pattern)
    # TODO: Add the %(facet)s sub-pattern to combine several facets
    return re.compile('(?P<{0}>{1})'.format(facet, pattern))


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
        raise MisdeclaredOption(option, section, cfg.read_paths,
                                reason="'{0}' has to be in 'destination facets'".format(facet))
    from_values = tuple(attributes[key] for key in from_keys)
    to_values = value_map[from_values]
    return to_values[to_keys.index(facet)]


def get_options_from_patterns(cfg, section):
    """
    Get all ``facet_patterns`` attributes declared into the project section.

    :param RawConfigParser cfg: The configuration file parser (as a :func:`ConfigParser.RawConfigParser` class instance)
    :param str section: The section name to parse
    :returns: A dictionary of {facet: pattern}
    """
    patterns = dict()
    for option in cfg.options(section, defaults=False):
        if '_pattern' in option and option != 'version_pattern':
            facet = option.split('_')[0]
            patterns[facet] = get_options_from_pattern(cfg, section, facet)
    return patterns


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
        raise NoConfigOption('category_defaults', section, cfg.read_paths)
    category_default = split_line(cfg.get(section, 'category_defaults'), sep='\n')
    try:
        default_values = {k: v for (k, v) in map(lambda x: split_line(x), category_default[1:])}
    except:
        raise MisdeclaredOption('category_defaults', section, cfg.read_paths,
                                reason="Please follow the format: 'facet | default_value'")
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
        raise NoConfigOption('maps', section, cfg.read_paths)
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
            raise MisdeclaredOption('project_options', 'DEFAULT', cfg.read_paths,
                                    reason="Please follow the format: 'id | project | description'")
    else:
        options = list()
    return options
