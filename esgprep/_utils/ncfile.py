# -*- coding: utf-8 -*-

"""
.. module:: esgprep._utils.ncfile.py
   :platform: Unix
   :synopsis: netCDF utilities.

.. moduleauthor:: Guillaume Levavasseur <glipsl@ipsl.fr>

"""

from uuid import UUID

import pyessv
from esgprep._exceptions import NoProjectCodeFound
from esgprep._exceptions.netcdf import InvalidNetCDFFile
from esgprep._exceptions.netcdf import NoNetCDFAttribute
from esgprep._utils.cv import get_collections
from esgprep._utils.print import *
from esgprep.drs.constants import PID_PREFIXES
from fuzzywuzzy.fuzz import partial_ratio
from fuzzywuzzy.process import extractOne
from netCDF4 import Dataset
from pyessv._exceptions import TemplateParsingError, TemplateValueError


class ncopen(object):
    """
    Opens opens a netCDF file

    """

    def __init__(self, path, mode='r'):

        # Set file path.
        self.path = path

        # Set open mode.
        self.mode = mode

        # Instantiate netCDF object.
        self.nc = None

    def __enter__(self):
        # Load netCDF Dataset content.
        try:
            self.nc = Dataset(self.path, self.mode)

        # Catch IO error.
        except (IOError, OSError) as error:
            raise InvalidNetCDFFile(self.path, error)

        return self.nc

    def __exit__(self, *exc):

        # Close netCDF file.
        self.nc.close()


def get_ncattrs(path):
    """
    Loads netCDF global attributes from a pathlib.Path as dictionary.
    Ignores attributes with only whitespaces.

    """
    with ncopen(path) as nc:
        dic = {attr: nc.getncattr(attr) for attr in nc.ncattrs() if (str(nc.getncattr(attr)).split())}
        return dic
        #return {attr: nc.getncattr(attr)[0] for attr in nc.ncattrs() if (nc.getncattr(attr)).split()} #" Old


def get_tracking_id(attrs):
    """
    Get tracking_id/PID string from netCDF global attributes.

    """
    # Get project code.
    project = get_project(attrs)

    # Set project code from global attributes.
    key, score = extractOne('tracking_id', attrs.keys(), scorer=partial_ratio)
    if score < 80:
        raise NoNetCDFAttribute('tracking_id', values=attrs.keys())
    identifier = attrs[key].lower()

    # Verify valid value.
    assert is_valid(identifier, project.name)

    # Return value.
    return identifier


def is_valid(identifier, project):
    """
    Validates a tracking_id/PID string.

    """
    try:

        # Split PID
        prefix, uid = identifier.split('/')

        # Verify PID prefix.
        assert prefix == PID_PREFIXES[project]

    except ValueError:

        # Verify project unknown of PID prefixes in case of simple tracking ID.
        uid = identifier
        assert project not in PID_PREFIXES.keys()

    # Verify UUID format.
    assert is_uuid(uid)

    return True


def is_uuid(uuid_string, version=4):
    """
    Validates an UUID.

    """
    try:
        uid = UUID(uuid_string, version=version)
        return uid.hex == uuid_string.replace('-', '')
    except ValueError:
        return False


def get_project(attrs):
    """
    Extract project code from the file attributes.

    """
    # Get all scopes within the loaded authority.
    scopes = {scope.name: scope.namespace for scope in pyessv.all_scopes()}

    # Get attributes.
    if not isinstance(attrs, dict):
        attrs = get_ncattrs(attrs)

    # Set project code from global attributes.
    key, score = extractOne('mip_era', attrs.keys(), scorer=partial_ratio)# QUESTION ; mip_era ? ou project ?
    if score < 80:
        raise NoProjectCodeFound(attrs)
    project = attrs[key].lower()

    # Check project code against CV.
    try:
        return pyessv.load(scopes[project])

    except KeyError:
        Print.debug(f'No project code found: {attrs.keys()}')
        return None


def get_terms(input):
    """
    Validates the filename syntax a pathlib.Path against CV and get pyessv terms.

    """
    # Instantiate terms.
    terms = dict()

    # Get attributes.
    if not isinstance(input, dict):
        attrs = get_ncattrs(input)
        filename = input.name
    else:
        attrs = input
        filename = attrs['filename']

    # Get project code.
    project = get_project(attrs)

    # Validate each drs items against CV.
    try:

        # Validate filename syntax.
        terms = {term.collection.raw_name: term for term in pyessv.parse_filename(project.name, filename, 4)}

    except (TemplateParsingError, TemplateValueError) as error:
        Print.debug(f'Invalid filename syntax -- {error}')

    return terms


def get_terms_from_attrs(attrs, set_values=None, set_keys=None):
    """
    Validates global attributes against CV and complete pyessv terms.

    """
    # Instantiate terms.
    terms = get_terms(attrs)

    # Get project code.
    project = get_project(attrs)

    # Iterate over missing collections required to build the DRS path.
    myCollections = set(get_collections(project, 'directory_structure'))
    myterms = terms
    un = myCollections.difference(terms)
    #deux = terms.difference(myCollections)
    for collection in set(get_collections(project, 'directory_structure')).difference(terms):

        # Check input set values.
        if set_values and collection in set_values:

            term = set_values[collection]

        # Check input mapping between collections and netCDF attributes.
        elif set_keys and collection in set_keys:

            # Get appropriate netCDF attribute.
            try:
                # In case of space-separated list value, pick up the first item.
                term = attrs[set_keys[collection]].split()[0]
            except AttributeError:
                raise NoNetCDFAttribute(set_keys[collection], attrs.keys())
        # try to find attrs in netCDF global attributes
        elif collection in attrs.keys():
            term = attrs[collection]
        # Otherwise pick up missing collection from netCDF global attributes.
        else:
            # Find closest NetCDF attributes using partial string comparison
            key, score = extractOne(collection, attrs.keys(), scorer=partial_ratio)
            if score < 80:
                raise NoNetCDFAttribute(collection, attrs.keys())
            term = attrs[key].split()[0]

        # Build pyessv namespace.
        namespace = f'{project.namespace}:{collection}:{term}'

        # Validate & store term.
        term = pyessv.parse(namespace, strictness=4)
        terms[term.collection.name] = term

    return terms


def drs_path(attrs, set_values=None, set_keys=None):
    """
    Returns the corresponding directory structure string.

    """
    # Instantiate directory string.
    directory = None

    # Get pyessv terms.
    terms = get_terms_from_attrs(attrs, set_values, set_keys)

    if terms:
        # Get project code.
        project = get_project(attrs)

        # Build directory.
        directory = pyessv.build_directory(project.name, set(terms.values()))

    return directory
