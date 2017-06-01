#!/usr/bin/env python
# -*- coding: utf-8 -*-

"""
    :platform: Unix
    :synopsis: Methods used to parse ESGF ini files.

"""

import ConfigParser
import os
import re
import string
from glob import glob

from esgprep.utils.exceptions import *
from esgprep.utils.utils import DirectoryChecker


class CfgParser(ConfigParser.ConfigParser):
    """
    Custom ConfigParser class to parse ESGF .ini files from a source directory.

    """

    def __init__(self, directory, section=None):
        ConfigParser.ConfigParser.__init__(self)
        self.read_paths = list()
        self.parse(directory, section=section)

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
        Read and parse a filename or a list of filenames, and records their paths.

        """
        if isinstance(filenames, str):
            filenames = [filenames]
        for filename in filenames:
            try:
                fp = open(filename)
            except IOError:
                continue
            self._read(fp, filename)
            fp.close()
            self.read_paths.append(filename)

    def sections(self):
        """
        Returns the list of section names, including [DEFAULT]

        """
        return self._sections.keys() + ['DEFAULT']

    def parse(self, path, section):
        """
        Parses the configuration files. If no section is submitted, all INI files are read.

        :param str path: The directory path of configuration files
        :param str section: The section to parse (if not all ini files are read)
        :returns: The configuration file parser
        :rtype: *CfgParser*
        :raises Error: If no configuration file exists
        :raises Error: If the configuration file parsing fails

        """
        self.read(os.path.join(path, 'esg.ini'))
        if section:
            # If the section is not "[project:.*]", only read esg.ini
            if re.match(r'project:.*', section) and section not in self.sections():
                project = section.split('project:')[1]
                if not os.path.isfile(os.path.join(path, 'esg.{0}.ini'.format(project))):
                    raise NoConfigFile(os.path.join(path, 'esg.{0}.ini'.format(project)))
                self.read(os.path.join(path, 'esg.{0}.ini'.format(project)))
                if section not in self.sections():
                    raise NoConfigSection(section, self.read_paths)
        else:
            paths = glob(os.path.join(path, 'esg*.ini'))
            if not paths:
                raise NoConfigFile(os.path.join(path, 'esg*.ini'))
            self.read(paths)
        if not self:
            raise EmptyConfigFile(self.read_paths)

    def translate_directory_format(self, section):
        """
        Return a regular expression associated with the ``directory_format`` option
        in the configuration file. This can be passed to the Python ``re`` methods.

        :param str section: The section name to parse
        :returns: The corresponding ``re`` pattern

        """
        # Start translation
        pattern = self.get(section, 'directory_format', raw=True).strip()
        pattern = pattern.replace('\.', '__ESCAPE_DOT__')
        pattern = pattern.replace('.', r'\.')
        pattern = pattern.replace('__ESCAPE_DOT__', r'\.')
        # Translate %(root)s variable if exists but not required. Can include the project name.
        if re.compile(r'%\((root)\)s').search(pattern):
            pattern = re.sub(re.compile(r'%\((root)\)s'), r'(?P<\1>[\w./-]+)', pattern)
        # Include specific facet patterns
        for facet, facet_regex in self.get_patterns(section).items():
            pattern = re.sub(re.compile(r'%\(({0})\)s'.format(facet)), facet_regex.pattern, pattern)
        # Constraint on %(version)s number
        pattern = re.sub(re.compile(r'%\((version)\)s'), r'(?P<\1>v[\d]+|latest)', pattern)
        # Translate all patterns matching %(name)s
        pattern = re.sub(re.compile(r'%\(([^()]*)\)s'), r'(?P<\1>[\w.-]+)', pattern)
        return '{0}/(?P<filename>[\w.-]+)$'.format(pattern)

    def translate_dataset_format(self, section):
        """
        Return a regular expression associated with the ``dataset_id`` option
        in the configuration file. This can be passed to the Python ``re`` methods.

        :param str section: The section name to parse
        :returns: The corresponding ``re`` pattern

        """
        pattern = self.get(section, 'dataset_id', raw=True).strip()
        pattern = pattern.replace('\.', '__ESCAPE_DOT__')
        pattern = pattern.replace('.', r'\.')
        pattern = pattern.replace('__ESCAPE_DOT__', r'\.')
        # Include specific facet patterns
        for facet, facet_regex in self.get_patterns(section).iteritems():
            pattern = re.sub(re.compile(r'%\(({0})\)s'.format(facet)), facet_regex.pattern, pattern)
        # Constraint on %(version)s number
        pattern = re.sub(re.compile(r'%\((version)\)s'), r'(?P<\1>v[\d]+|latest)', pattern)
        # Translate all patterns matching %(name)s
        pattern = re.sub(re.compile(r'%\(([^()]*)\)s'), r'(?P<\1>[\w.-]+)', pattern)
        return pattern

    def translate_filename_format(self, section):
        """
        Return a regular expression filters associated with the ``directory_format`` option
        in the configuration file. This can be passed to the Python ``re`` methods.

        :param str section: The section name to parse
        :returns: The corresponding ``re`` pattern

        """
        # Start translation
        pattern = self.get(section, 'filename_format', raw=True).strip()
        pattern = pattern.replace('\.', '__ESCAPE_DOT__')
        pattern = pattern.replace('.', r'\.')
        pattern = pattern.replace('__ESCAPE_DOT__', r'\.')
        # Translate all patterns matching [.*] as optional pattern
        pattern = re.sub(re.compile(r'\[(.*)\]'), r'(\1)?', pattern)
        # Remove underscore from latest mandatory pattern to allow optional brackets
        pattern = re.sub(re.compile(r'%\(([^()]*)\)s\('), r'(?P<\1>[^-_]+)(', pattern)
        # Translate all patterns matching %(name)s
        return re.sub(re.compile(r'%\(([^()]*)\)s'), r'(?P<\1>[\w.-]+)', pattern)

    def get_facets(self, section, option, ignored=None):
        """
        Returns the set of facets declared into "*_format" attributes in the configuration file.
        :param str section: The section name to parse
        :param str option: The option to get facet names
        :param list ignored: The list of facets to ignored
        :returns: The collection of facets
        :rtype: *set*
        
        """
        facets = re.findall(re.compile(r'%\(([^()]*)\)s'), self.get(section, option, raw=True))
        if ignored:
            return [f for f in facets if f not in ignored]
        else:
            return facets

    def check_options(self, section, pairs):
        """
        Checks a {key: value} pairs against the corresponding options from the configuration file.

        :param str section: The section name to parse
        :param dict pairs: A dictionary of {key: value} to check
        :raises Error: If the value is missing in the corresponding options list

        """
        for key in pairs.keys():
            options, option = self.get_options(section, key)
            try:
                # get_options returned a list
                if pairs[key] not in options:
                    raise NoConfigValue(pairs[key], option, section, self.read_paths)
            except TypeError:
                # get_options returned a regex from pattern
                if not options.match(pairs[key]):
                    raise NoConfigValue(pairs[key], option, section, self.read_paths)
                else:
                    self.check_options(section, options.match(pairs[key]).groupdict())

    def get_options(self, section, option):
        """
        Returns the list of attribute options.

        :param str section: The section name to parse
        :param str option: The option to get available values
        :returns: The option values
        :rtype: *list* or *re.RegexObject*
        :raises Error: If the option is missing

        """
        if self.has_option(section, '{0}_options'.format(option)):
            option = '{0}_options'.format(option)
            return self.get_options_from_list(section, option), option
        elif self.has_option(section, '{0}_map'.format(option)):
            option = '{0}_map'.format(option)
            return self.get_options_from_map(section, option), option
        elif self.has_option(section, '{0}_pattern'.format(option)):
            option = '{0}_pattern'.format(option)
            return self.get_options_from_pattern(section, option), option
        else:
            raise NoConfigOptions(option, section, self.read_paths)

    def get_options_from_list(self, section, option):
        """
        Returns the list of option values from options list.

        :param str section: The section name to parse
        :param str option: The option to get available values
        :returns: The option values
        :rtype: *list*
        :raises Error: If the section does not exist
        :raises Error: If the option does not exist

        """
        if section not in self.sections():
            raise NoConfigSection(section, self.read_paths)
        if not self.has_option(section, option):
            raise NoConfigOption(option, section, self.read_paths)
        if option.rsplit('_options')[0] == 'experiment':
            options = self.get_options_from_table(section, option, field_id=2)
        else:
            options = split_line(self.get(section, option), sep=',')
        return options

    def get_options_from_table(self, section, option, field_id=None):
        """
        Returns the list of options from options table (i.e., <field1> | <field2> | <field3> | etc.).

        :param str section: The section name to parse
        :param str option: The option to get available values
        :param int field_id: The field number starting from 1 (if not return the tuple)
        :returns: The option values
        :rtype: *list*
        :raises Error: If the section does not exist
        :raises Error: If the option does not exist
        :raises Error: If the options table is misdeclared

        """
        if section not in self.sections():
            raise NoConfigSection(section, self.read_paths)
        if not self.has_option(section, option):
            raise NoConfigOption(option, section, self.read_paths)
        option_lines = split_line(self.get(section, option).lstrip(), sep='\n')
        if len(option_lines) == 1 and not option_lines[0]:
            return list()
        try:
            if field_id:
                options = [tuple(option)[field_id - 1] for option in map(lambda x: split_line(x), option_lines)]
            else:
                options = [tuple(option) for option in map(lambda x: split_line(x), option_lines)]
        except:
            raise MisdeclaredOption(option, section, self.read_paths, reason="Wrong syntax")
        return options

    def get_options_from_pairs(self, section, option, key):
        """
        Returns the list of option values from pairs table (i.e., <key> | <value>).

        :param str section: The section name to parse
        :param str option: The option to get available values
        :param str key: The key to get the value
        :returns: The key value
        :rtype: *str*
        :raises Error: If the section does not exist
        :raises Error: If the option does not exist
        :raises Error: If the key does not exist
        :raises Error: If the options table is misdeclared

        """
        if section not in self.sections():
            raise NoConfigSection(section, self.read_paths)
        if not self.has_option(section, option):
            raise NoConfigOption(option, section, self.read_paths)
        options_lines = split_line(self.get(section, option), sep='\n')
        try:
            options = dict((k, v) for k, v in map(lambda x: split_line(x), options_lines[1:]))
        except:
            raise MisdeclaredOption(option, section, self.read_paths, reason="Wrong syntax")
        try:
            return options[key]
        except KeyError:
            raise NoConfigKey(key, option, section, self.read_paths)

    def get_options_from_map(self, section, option, key=None):
        """
        Returns the list of option values from maptable.
        If no key submitted, the option name has to be ``<key>_map``.

        :param str section: The section name to parse
        :param str option: The option to get available values
        :param str key: The key to get the values
        :returns: The option values
        :rtype: *list*
        :raises Error: If the section does not exist
        :raises Error: If the option does not exist
        :raises Error: If the related key is not in the source/destination keys of the maptable

        """
        if section not in self.sections():
            raise NoConfigSection(section, self.read_paths)
        if not self.has_option(section, option):
            raise NoConfigOption(option, section, self.read_paths)
        if not key:
            key = option.split('_map')[0]
        from_keys, to_keys, value_map = split_map(self.get(section, option))
        if key in from_keys:
            return list(set([value[from_keys.index(key)] for value in value_map.keys()]))
        else:
            return list(set([value[to_keys.index(key)] for value in value_map.values()]))

    def get_option_from_map(self, section, option, pairs):
        """
        Returns the destination values corresponding to key values from maptable.
        The option name has to be ``<key>_map``. The key has to be in the destination keys of the maptable header.

        :param str section: The section name to parse
        :param str option: The option to get the value
        :param dict pairs: A dictionary of {from_key: value} to input the maptable
        :returns: The corresponding option value
        :rtype: *list*
        :raises Error: If the section does not exist
        :raises Error: If the option does not exist
        :raises Error: If the key values are not in the destination keys of the maptable

        """
        if section not in self.sections():
            raise NoConfigSection(section, self.read_paths)
        if not self.has_option(section, option):
            raise NoConfigOption(option, section, self.read_paths)
        from_keys, to_keys, value_map = split_map(self.get(section, option))
        key = option.split('_map')[0]
        if key not in to_keys:
            raise MisdeclaredOption(option, section, self.read_paths,
                                    reason="'{0}' has to be in 'destination key'".format(key))
        from_values = tuple(pairs[k] for k in from_keys)
        to_values = value_map[from_values]
        return to_values[to_keys.index(key)]

    def get_options_from_pattern(self, section, option):
        """
        Returns the expanded regex from ``key_pattern``.
        The option name has to be ``<attr>_pattern``.

        :param str section: The section name to parse
        :param str option: The option to get available values
        :returns: The expanded regex
        :rtype: *re.RegexObject*
        :raises Error: If the section does not exist
        :raises Error: If the option does not exist

        """
        if section not in self.sections():
            raise NoConfigSection(section, self.read_paths)
        if not self.has_option(section, option):
            raise NoConfigOption(option, section, self.read_paths)
        pattern = self.get(section, option, raw=True)
        # Translate all patterns matching %(digit)s
        pattern = re.sub(re.compile(r'%\((digit)\)s'), r'[\d]+', pattern)
        # Translate all patterns matching %(string)s
        pattern = re.sub(re.compile(r'%\((string)\)s'), r'[\w]+', pattern)
        # Translate all patterns matching %(facet)s
        pattern = re.sub(re.compile(r'%\(([^()]*)\)s'), r'(?P<\1>[\w.-]+)', pattern)
        return re.compile(pattern)

    def get_patterns(self, section):
        """
        Get all ``key_patterns`` options declared into the project section.

        :param str section: The section name to parse
        :returns: A dictionary of {option: pattern}
        :rtype: *dict*

        """
        patterns = dict()
        for option in self.options(section, defaults=False):
            if '_pattern' in option and option != 'version_pattern':
                patterns[option] = self.get_options_from_pattern(section, option)
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


def build_line(fields, sep=' | ', length=None):
    """
    Build a line from fields adding trailing and leading characters.

    :param tuple fields: Tuple of ordered fields
    :param str sep: Separator character
    :param tuple length: The fields length
    :returns: A string fields

    """
    if length:
        fields = [format(fields[i], str(length[i])) for i in range(len(fields))]
    line = sep.join(fields)
    return line


def align(fields):
    """
    Returns the maximum length among items of a list of tuples.
    :param list fields:
    :returns: The fields lengths
    :rtype: *tuple*

    """
    return tuple([max(map(len, f)) for f in zip(*fields)])


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
