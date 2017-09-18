#!/usr/bin/env python
# -*- coding: utf-8 -*-

"""
    :platform: Unix
    :synopsis: Class to handle dataset directory for DRS management.

"""

import getpass
import logging
import re
from collections import OrderedDict

from ESGConfigParser.custom_exceptions import ExpressionNotMatch, NoConfigOptions, NoConfigOption
from fuzzywuzzy import fuzz, process
from hurry.filesize import size
from netCDF4 import Dataset
from treelib import Tree
from treelib.tree import DuplicatedNodeIdError

from constants import *
from custom_exceptions import *
from esgprep.utils.constants import *
from esgprep.utils.custom_exceptions import *


class File(object):
    """
    Handler providing methods to deal with file processing.

    """

    def __init__(self, ffp):
        # Retrieve file full path
        self.ffp = ffp
        # Retrieve filename only
        self.filename = os.path.basename(ffp)
        # File attributes as dict(): {institute: 'IPSL', project: 'CMIP5', ...}
        self.attributes = dict()
        # Retrieve file size
        self.size = os.stat(self.ffp).st_size

    def get(self, key):
        """
        Returns the attribute value corresponding to the key.
        The submitted key can refer to ``File.key`` or ``File.attributes[key]``.

        :param str key: The key
        :returns: The corresponding value
        :rtype: *str* or *list* or *dict* depending on the key
        :raises Error: If unknown key

        """
        if key in self.attributes:
            return self.attributes[key]
        elif key in self.__dict__.keys():
            return self.__dict__[key]
        else:
            raise KeyNotFound(key, self.attributes.keys() + self.__dict__.keys())

    def load_attributes(self, project, root, pattern, set_values):
        """
        Loads DRS attributes catched from a regular expression match.
        The project facet is added in any case with lower case.
        The root facet is added by default.
        The dataset version is initially set to None.
        Can be overwrite by "set_values" pairs if submitted.

        :param str project: The project name
        :param str root: The DRS tree root
        :param str pattern: The regular expression to match
        :param dict set_values: Key/value pairs of facet to set for the run
        :raises Error: If regular expression matching fails
        :raises Error: If invalid NetCDF file.

        """
        # Get attributes from NetCDF global attributes
        try:
            nc = Dataset(self.ffp)
            for attr in nc.ncattrs():
                self.attributes[attr] = nc.getncattr(attr)
            nc.close()
        except IOError:
            raise InvalidNetCDFFile(self.ffp)
        # Get attributes from filename, overwriting existing ones
        try:
            # re.search() method is required to search through the entire string.
            self.attributes.update(re.search(pattern, self.filename).groupdict())
        except:
            raise ExpressionNotMatch(self.filename, pattern)
        # Get attributes from command-line, overwriting existing ones
        self.attributes.update(set_values)
        # Set version to None
        self.attributes['root'] = root
        # Set version to None
        self.attributes['version'] = None
        # Only required to build proper DRS
        self.attributes['project'] = project

    def check_facets(self, facets, config, set_keys):
        """
        Checks each facet against the controlled vocabulary.
        If a DRS attribute is missing regarding the list of facets,
        The DRS attributes are completed from the configuration file maptables.
        In the case of non-standard attribute, it gets the most similar key among netCDF attributes names.
        Attributes can be directly mapped with "set_keys" pairs if submitted.


        :param list facets: The list of facet to check
        :param ESGConfigParser.SectionParser config: The configuration parser
        :param dict set_keys: Key/Attribute pairs to map for the run
        :raises Error: If one facet checkup fails

        """
        for facet in set(facets).intersection(self.attributes.keys()) - set(IGNORED_KEYS):
            config.check_options({facet: self.attributes[facet]})
        for facet in set(facets).difference(self.attributes.keys()) - set(IGNORED_KEYS):
            try:
                self.attributes[facet] = config.get_option_from_map('{}_map'.format(facet), self.attributes)
            except NoConfigOption:
                if facet in set_keys.keys():
                    try:
                        # Rename attribute key
                        self.attributes[facet] = self.attributes.pop(set_keys[facet])
                        config.check_options({facet: self.attributes[facet]})
                    except KeyError:
                        raise NoNetCDFAttribute(set_keys[facet], self.ffp)
                else:
                    # Find closest NetCDF attributes in terms of partial string comparison
                    key, score = process.extractOne(facet, self.attributes.keys(), scorer=fuzz.partial_ratio)
                    if score >= 80:
                        # Rename attribute key
                        self.attributes[facet] = self.attributes.pop(key)
                        logging.warning('Consider "{}" attribute instead of "{}" facet'.format(key, facet))
                        config.check_options({facet: self.attributes[facet]})
                    else:
                        raise NoConfigOptions(facet)

    def get_drs_parts(self, facets):
        """
        Gets the DRS pairs required to build the DRS path. The DRS parts are included as an OrderedDict():
        {project : 'CMIP5', product: 'output1', ...}

        :param list facets: The list of facet to check
        :returns: The ordered DRS parts
        :rtype: *OrderedDict*

        """
        return OrderedDict(zip(facets, [self.attributes[facet] for facet in facets]))


class DRSPath(object):
    """
    Handler providing methods to deal with paths.

    """
    # Default DRS tree version
    # Modified on the ProcessingContext instance
    TREE_VERSION = 'v{}'.format(datetime.now().strftime('%Y%m%d'))

    def __init__(self, parts):
        # Retrieve the dataset directory parts
        self.d_parts = OrderedDict(parts.items()[:parts.keys().index('version')])
        # Retrieve the file directory parts
        self.f_parts = OrderedDict(parts.items()[parts.keys().index('version') + 1:])
        # Retrieve the upgrade version
        self.v_upgrade = DRSPath.TREE_VERSION
        # If the dataset path is not equivalent to the file diretcory (e.g., CMIP5 like)
        # Get the physical files version
        self.v_latest = self.get_latest_version()
        if self.path(f_part=False) != self.path():
            self.v_files = OrderedDict({'variable': '{}_{}'.format(self.get('variable'), self.v_upgrade[1:])})
        else:
            self.v_files = OrderedDict({'data': 'd{}'.format(self.v_upgrade[1:])})

    def get(self, key):
        """
        Returns the attribute value corresponding to the key.
        The submitted key can refer to the DRS dataset parts of the DRS file parts.

        :param str key: The key
        :returns: The value
        :rtype: *str* or *list* or *dict* depending on the key
        :raises Error: If unknown key

        """
        if key in self.d_parts:
            return self.d_parts[key]
        elif key in self.f_parts.keys():
            return self.f_parts[key]
        else:
            raise KeyNotFound(key, self.d_parts.keys() + self.f_parts.keys())

    def items(self, d_part=True, f_part=True, version=True, file_folder=False, latest=False, root=False):
        """
        Itemizes the facet values along the DRS path.
        Flags can be combine to obtain different behaviors.

        :param boolean d_part: True to append the dataset facets
        :param boolean f_part: True to append the file facets
        :param boolean version: True to append the version facet
        :param boolean file_folder: True to append the folder for physical files
        :param boolean latest: True to switch from upgrade to latest version
        :param boolean root: True to prepend the DRS root directory
        :return: The corresponding facet values
        :rtype: *list*

        """
        parts = OrderedDict()
        if d_part:
            parts = self.d_parts.copy()
        if version:
            if latest:
                parts.update(OrderedDict({'version': self.v_latest}))
            else:
                parts.update(OrderedDict({'version': self.v_upgrade}))
            if file_folder:
                parts.update(OrderedDict({'version': 'files'}))
        if f_part:
            parts.update(self.f_parts)
        if file_folder:
            parts.update(self.v_files)
        if not root and 'root' in parts.keys():
            del parts['root']
        return parts.values()

    def path(self, **kwargs):
        """
        Convert a list of facet values into path.
        The arguments are the same as :func:`esgprep.drs.handler.DRSPath.items`

        :returns: The path
        :rtype: *str*

        """
        return os.path.join(*self.items(**kwargs))

    def get_latest_version(self):
        """
        Get the current latest dataset version if exists.

        :returns: The latest dataset version properly formatted
        :rtype: *str*
        :raises Error: If latest version exists and is the same as upgrade version

        """
        # Test if dataset path already exists
        dset_path = self.path(f_part=False, version=False, root=True)
        if os.path.isdir(dset_path):
            # Get and sort all existing dataset versions
            versions = sorted([v for v in os.listdir(dset_path) if re.compile(r'v[\d]+').search(v)])
            # Upgrade version should not already exist
            if self.v_upgrade in versions:
                raise DuplicatedDataset(self.v_upgrade, dset_path)
            # Pickup respectively previous, next and latest version
            return versions[-1]
        else:
            return None


class DRSLeaf(object):
    """
    Handler providing methods to deal with DRS file.

    """

    def __init__(self, src, dst, mode):
        # Retrieve source data path
        self.src = src
        # Get destination data path
        self.dst = dst
        # Retrieve migration mode
        self.mode = mode

    def upgrade(self, todo_only=True):
        """
        Upgrade the DRS tree.

        :param boolean todo_only: True to only print Unix command-lines to apply (i.e., as dry-run)

        """
        # Make directory for destination path if not exist
        print('{} {}'.format('mkdir -p', os.path.dirname(self.dst)))
        if not todo_only:
            try:
                os.makedirs(os.path.dirname(self.dst))
            except OSError:
                pass
        print('{} {} {}'.format(UNIX_COMMAND_LABEL[self.mode], self.src, self.dst))
        # Unlink symbolic link if already exists
        if self.mode == 'symlink' and os.path.exists(self.dst):
            print('{} {}'.format('unlink', self.dst))
            if not todo_only:
                os.unlink(self.dst)
        # Make upgrade depending on the migration mode
        if not todo_only:
            UNIX_COMMAND[self.mode](self.src, self.dst)

    def has_permissions(self, root):
        """
        Checks permissions for DRS leaf migration.
        Discards relative paths.

        :param str root: The DRS tree root
        :raises Error: If missing user privileges

        """
        # Check src access
        # Define src access depending on the migration mode
        if self.mode == 'move':
            if os.path.isabs(self.src) and not os.access(self.src, os.W_OK):
                raise WriteAccessDenied(getpass.getuser(), self.src)
        else:
            if os.path.isabs(self.src) and not os.access(self.src, os.R_OK):
                raise ReadAccessDenied(getpass.getuser(), self.src)
        # Check dst access (always write)
        # Backward the DRS is path does not exist
        dst = self.dst
        while not os.path.exists(dst) and dst != root:
            dst = os.path.split(dst)[0]
        if os.path.isabs(dst) and not os.access(dst, os.W_OK):
            raise WriteAccessDenied(getpass.getuser(), dst)


class DRSTree(Tree):
    """
    Handler providing methods to deal with DRS tree.

    """

    def __init__(self, root, version, mode):
        # Retrieve original class init
        Tree.__init__(self)
        # To records dataset and files
        self.paths = dict()
        # Retrieve the root directory to build the DRS
        self.drs_root = root
        # Retrieve the dataset version to build the DRS
        self.drs_version = version
        # Retrieve the migration mode
        self.drs_mode = mode
        # Display width
        self.d_lengths = []

    def get_display_lengths(self):
        """
        Gets the string lengths for comfort display.

        """
        self.d_lengths = []
        self.d_lengths = [max([len(i) for i in self.paths.keys()]), 20, 20, 16, 16]
        self.d_lengths.append(sum(self.d_lengths) + 2)

    def create_leaf(self, nodes, leaf, label, src, mode):
        """
        Creates all upstream nodes to a DRS leaf.
        The :func:`esgprep.drs.handler.DRSLeaf` class is added to data leaf nodes.

        :param list nodes: The list of node tags to the leaf
        :param str leaf: The leaf name
        :param str label: The leaf label
        :param str src: The source of the leaf
        :param str mode: The migration mode (e.g., 'copy', 'move', etc.)

        """
        nodes.append(leaf)
        for i in range(len(nodes)):
            node_id = os.path.join(*nodes[:i + 1])
            try:
                if i == 0:
                    self.create_node(tag=nodes[i],
                                     identifier=node_id)
                elif i == len(nodes) - 1:
                    parent_node_id = os.path.join(*nodes[:i])
                    self.create_node(tag=label,
                                     identifier=node_id,
                                     parent=parent_node_id,
                                     data=DRSLeaf(src=src,
                                                  dst=node_id.split(LINK_SEPARATOR)[0],
                                                  mode=mode))
                else:
                    parent_node_id = os.path.join(*nodes[:i])
                    self.create_node(tag=nodes[i],
                                     identifier=node_id,
                                     parent=parent_node_id)
            except DuplicatedNodeIdError:
                # Mandatory to recursively generated the tree
                pass

    def leaves(self, root=None):
        """
        Yield leaves of the whole DRS tree of a subtree.

        """
        if root is None:
            for node in self._nodes.values():
                if node.is_leaf():
                    yield node
        else:
            for node in self.expand_tree(root):
                if self[node].is_leaf():
                    yield self[node]

    def list(self):
        """
        List and summary upgrade information at the publication level.

        """
        print(''.center(self.d_lengths[-1], '='))
        print('{}{}->{}{}{}'.format('Publication level'.center(self.d_lengths[0]),
                                    'Latest version'.center(self.d_lengths[1]),
                                    'Upgrade version'.center(self.d_lengths[2]),
                                    'Files to upgrade'.rjust(self.d_lengths[3]),
                                    'Upgrade size'.rjust(self.d_lengths[4])))
        print(''.center(self.d_lengths[-1], '-'))
        for dset_path, incomings in self.paths.items():
            dset_dir, dset_version = os.path.dirname(dset_path), os.path.basename(dset_path)
            publication_level = os.path.normpath(dset_dir)
            files_number = len(incomings)
            latest_version = sorted([incoming['latest'] for incoming in incomings])[-1]
            total_size = size(sum([incoming['size'] for incoming in incomings]))
            print('{}{}->{}{}{}'.format(publication_level.ljust(self.d_lengths[0]),
                                        latest_version.center(self.d_lengths[1]),
                                        dset_version.center(self.d_lengths[2]),
                                        str(files_number).rjust(self.d_lengths[3]),
                                        total_size.rjust(self.d_lengths[4])))
        print(''.center(self.d_lengths[-1], '='))

    def tree(self):
        """
        Prints the whole DRS tree in a visual way.

        """
        print(''.center(self.d_lengths[-1], '='))
        print('Upgrade DRS Tree'.center(self.d_lengths[-1]))
        print(''.center(self.d_lengths[-1], '-'))
        self.show()
        print(''.center(self.d_lengths[-1], '='))

    def todo(self):
        """
        As a dry run :func:`esgprep.drs.handler.DRSTree.upgrade` that only prints command-line to do.

        """
        self.upgrade(todo_only=True)

    def upgrade(self, todo_only=False):
        """
        Upgrades the whole DRS tree.

        :param boolean todo_only: Only print Unix command-line to do

        """
        # Check permissions before upgrade
        if not todo_only:
            for leaf in self.leaves():
                leaf.data.has_permissions(self.drs_root)
        print(''.center(self.d_lengths[-1], '='))
        if todo_only:
            print('Unix command-lines (DRY-RUN)'.center(self.d_lengths[-1]))
        else:
            print('Unix command-lines'.center(self.d_lengths[-1]))
        print(''.center(self.d_lengths[-1], '-'))
        for leaf in self.leaves():
            leaf.data.upgrade(todo_only)
        print(''.center(self.d_lengths[-1], '='))
