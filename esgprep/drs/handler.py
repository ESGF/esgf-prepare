#!/usr/bin/env python
# -*- coding: utf-8 -*-

"""
    :platform: Unix
    :synopsis: Class to handle dataset directory for DRS management.

"""

import logging
import os
import re
from collections import OrderedDict
from datetime import datetime

from fuzzywuzzy import fuzz, process
from hurry.filesize import size
from netCDF4 import Dataset
from shutil import copy2 as copy
from shutil import move
from os import link, symlink
from treelib import Tree
from treelib.tree import DuplicatedNodeIdError

from esgprep.drs.constants import *
from esgprep.drs.exceptions import *
from esgprep.utils.constants import *
from esgprep.utils.exceptions import *


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

    def load_attributes(self, ctx):
        """
        The DRS attributes are deduced from the NetCDF global attributes or the filname using the
        the filename_format regex pattern. The project facet is added in any case with lower case if needed.
        The root facet is added by default and the dataset version is initally set to None.

         * Matches filename with corresponding project pattern to get DRS attributes values
         * Add NetCDF global attributes to DRS attributes
         * Overwrite with ctx.set_values pairs if submitted
         * attributes.keys() are facet names
         * attributes[facet] is the facet values.

        :param esgprep.drs.main.ProcessingContext ctx: The processing context
        :raises Error: If the filename does not match the ``directory_format`` pattern/regex
        :raises Error: If invalid NetCDF file

        """
        # Get attributes from NetCDF global attributes
        try:
            nc = Dataset(self.ffp)
            for attr in nc.ncattrs():
                self.attributes[attr] = nc.getncattr(attr)
            nc.close()
        except IOError:
            raise InvalidNetCDFFile(self.ffp)
        # Get attributes from filename, overwritting existing ones
        try:
            # re.search() method is required to search through the entire string.
            self.attributes.update(re.search(ctx.pattern, self.filename).groupdict())
        except:
            raise FilenameNotMatch(self.filename, ctx.pattern, ctx.project_section, ctx.cfg.read_paths)
        # Get attributes from command-line, overwritting exsiting ones
        self.attributes.update(ctx.set_values)
        # Set version to None
        self.attributes['root'] = ctx.root
        # Set version to None
        self.attributes['version'] = None
        # Only required to build proper DRS
        try:
            self.attributes['project'] = ctx.cfg.get_options_from_pairs(ctx.project_section,
                                                                        'category_defaults',
                                                                        'project')
        except:
            self.attributes['project'] = ctx.project.lower()

    def get_drs_parts(self, ctx):
        """
        Get the DRS pairs required to build the DRS path. The DRS parts are included as an OrderedDict():
        {project : 'CMIP5', product: 'output1', ...}

         * Checks each value which the facet is found in directory_format AND attributes keys,
         * Gets missing attributes from the maptables in the esg.<project>.ini,
         * Get attribute from ctx.set_keys if submitted and exists,
         * In the case of non-standard attribute, get the most similar key among attributes keys,
         * Builds the DRS path from the attributes.

        :param esgprep.drs.main.ProcessingContext ctx: The processing context
        :returns: The ordered DRS parts
        :rtype: *OrderedDict*
        :raises Error: If a facet cannot be checked

        """
        # Check each facet required by the directory_format template from esg.<project>.ini
        # Facet values to check are deduced from file glboal attributes or the filename
        # If a DRS attribute is missing regarding the directory-format template,
        # the DRS attributes are completed from esg.<project>.ini maptables, or with the most
        # similar NetCDF attribute.
        for facet in set(ctx.facets).intersection(self.attributes.keys()) - set(IGNORED_KEYS):
            ctx.cfg.check_options(ctx.project_section, {facet: self.attributes[facet]})
        for facet in set(ctx.facets).difference(self.attributes.keys()) - set(IGNORED_KEYS):
            try:
                self.attributes[facet] = ctx.cfg.get_option_from_map(ctx.project_section,
                                                                     '{0}_map'.format(facet),
                                                                     self.attributes)
            except:
                if facet in ctx.set_keys.keys():
                    try:
                        # Rename attribute key
                        self.attributes[facet] = self.attributes.pop(ctx.set_keys[facet])
                        ctx.cfg.check_options(ctx.project_section, {facet: self.attributes[facet]})
                    except KeyError:
                        raise NoNetCDFAttribute(ctx.set_keys[facet], self.ffp)
                else:
                    # Find closest NetCDF attributes in terms of partial string comparison
                    key, score = process.extractOne(facet, self.attributes.keys(), scorer=fuzz.partial_ratio)
                    if score >= 80:
                        # Rename attribute key
                        self.attributes[facet] = self.attributes.pop(key)
                        if ctx.verbose:
                            logging.warning('Consider "{0}" attribute instead of "{1}" facet'.format(key, facet))
                        ctx.cfg.check_options(ctx.project_section, {facet: self.attributes[facet]})
                    else:
                        raise NoConfigVariable(facet,
                                               ctx.cfg.get(ctx.project_section, 'directory_format', raw=True).strip(),
                                               ctx.project_section,
                                               ctx.cfg.read_paths)
        return OrderedDict(zip(ctx.facets, [self.attributes[facet] for facet in ctx.facets]))


class DRSPath(object):
    """
    Handler providing methods to deal with paths.

    """
    # Root directory to start DRS as constant
    VERSION = 'v{0}'.format(datetime.now().strftime('%Y%m%d'))

    def __init__(self, parts):
        # Retrieve the dataset directory parts
        self.d_parts = OrderedDict(parts.items()[:parts.keys().index('version')])
        # Retrieve the file directory parts
        self.f_parts = OrderedDict(parts.items()[parts.keys().index('version') + 1:])
        # Retrieve the upgrade version
        self.v_upgrade = DRSPath.VERSION
        # If the dataset path is not equivalent to the file diretcory (e.g., CMIP5 like)
        # Get the physical files version
        self.v_latest = self.get_latest_version()
        if self.path(f_part=False) != self.path():
            self.v_files = OrderedDict({'variable': '{0}_{1}'.format(self.get('variable'), self.v_upgrade[1:])})
        else:
            self.v_files = OrderedDict({'data': 'd{0}'.format(self.v_upgrade[1:])})

    def get(self, key):
        """
        Returns the attribute value corresponding to the key.
        The submitted key can refer to the DRS dataset parts of the DRS file parts.

        :param str key: The key
        :returns: The corresponding value
        :rtype: *str* or *list* or *dict* depending on the key
        :raises Error: If unknown key

        """
        if key in self.d_parts:
            return self.d_parts[key]
        elif key in self.f_parts.keys():
            return self.f_parts[key]
        else:
            raise KeyNotFound(key, self.d_parts.keys() + self.f_parts.keys())

    def items(self, d_part=True, f_part=True, version=True, file=False, latest=False, root=False):
        """
        Itemizes the facet values along the DRS path.
        Flags can be combine to obtain different behaviors.

        :param boolean d_part: True to append the dataset facets
        :param boolean f_part: True to append the file facets
        :param boolean version: True to append the version facet
        :param boolean file: True to append the folder for physical files
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
            if file:
                parts.update(OrderedDict({'version': 'files'}))
        if f_part:
            parts.update(self.f_parts)
        if file:
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
        Applies the DRS action.

        :param boolean todo_only: True to only print Unix command-lines to apply
        :raises Error: If any IO action fails

        """
        # Make directory for destination path if not exist
        print('{0} {1}'.format('mkdir -p', os.path.dirname(self.dst)))
        if not todo_only:
            try:
                os.makedirs(os.path.dirname(self.dst))
            except OSError:
                pass
        print('{0} {1} {2}'.format(UNIX_COMMAND[self.mode], self.src, self.dst))
        # Unlink symbolic link if already exists
        if self.mode == 'symlink' and os.path.exists(self.dst):
            print('{0} {1}'.format('unlink', self.dst))
            if not todo_only:
                os.unlink(self.dst)
        # Make upgrade depending on the migration mode
        if not todo_only:
            globals()[self.mode](self.src, self.dst)


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

    def get_display_lengths(self):
        """
        Gets the string lengths for comfort display.

        """
        self.d_lengths = [max([len(i) for i in self.paths.keys()]), 20, 20, 16, 16]
        self.d_lengths.append(sum(self.d_lengths) + 2)

    def create_leaf(self, nodes, leaf, src, mode):
        """
        Creates all upstream nodes to a DRS leaf.
        The :func:`esgprep.drs.handler.DRSLeaf` class is added to data leaf nodes.

        :param list nodes: The list of nodes tag to the leaf
        :param str leaf: The leaf tag
        :param str src: The source of the leaf
        :param str mode: The migration mode (e.g., 'copy', 'move', etc.)

        """
        nodes.append(leaf)
        for i in range(len(nodes)):
            node_id = os.path.join(*nodes[:i + 1])
            try:
                if i == 0:
                    self.create_node(nodes[i], node_id)
                elif i == len(nodes) - 1:
                    parent_node_id = os.path.join(*nodes[:i])
                    self.create_node(nodes[i], node_id,
                                     parent=parent_node_id,
                                     data=DRSLeaf(src=src,
                                                  dst=node_id.split(LINK_SEPARATOR)[0],
                                                  mode=mode))
                else:
                    parent_node_id = os.path.join(*nodes[:i])
                    self.create_node(nodes[i], node_id, parent=parent_node_id)
            except DuplicatedNodeIdError:
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
        print('{0}{1}->{2}{3}{4}'.format('Publication level'.center(self.d_lengths[0]),
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
            print('{0}{1}->{2}{3}{4}'.format(publication_level.ljust(self.d_lengths[0]),
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
        Upgrads the whole DRS tree.

        :param boolean todo_only: Only print Unix command-line to do

        """
        print(''.center(self.d_lengths[-1], '='))
        if todo_only:
            print('Unix command-lines (DRY-RUN)'.center(self.d_lengths[-1]))
        else:
            print('Unix command-lines'.center(self.d_lengths[-1]))
        print(''.center(self.d_lengths[-1], '-'))
        for leaf in self.leaves():
            leaf.data.upgrade(todo_only)
        print(''.center(self.d_lengths[-1], '='))
