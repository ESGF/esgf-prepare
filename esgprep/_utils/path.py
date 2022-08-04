# -*- coding: utf-8 -*-

"""
.. module:: esgprep._utils.path.py
   :platform: Unix
   :synopsis: Path utilities.

.. moduleauthor:: Guillaume Levavasseur <glipsl@ipsl.fr>

"""

import pyessv
from esgprep._utils.print import *
from esgprep._utils.cv import *
from esgprep.constants import VERSION_PATTERN
from pyessv._exceptions import TemplateParsingError, TemplateValueError
from pathlib import Path

def get_project(path):
    """
    Extract project code from a pathlib.Path object.

    """
    # Get all scopes within the loaded authority.
    scopes = {scope.name: scope.namespace for scope in pyessv.all_scopes()}

    # Find intersection between scopes list and path parts.
    project = set(Path(str(path).lower()).parts).intersection(scopes)

    # Ensure only one project code matched.
    if len(project) == 1:

        # Returns pyessv scope object as project.
        return pyessv.load(scopes[project.pop()])

    elif len(project) == 0:
        Print.debug(f'No project code found: {path}')
        return None

    else:
        Print.debug(f'Unable to match one project code: {path}')
        return None


def project_idx(path):
    """
    Returns project index in the pathlib.Path parts.

    """
    # Instantiate index.
    idx = None

    # Get project code.
    project = get_project(path)

    if project and project.name in str(path).lower():
        # Retrieve index of the project code in the path parts.
        idx = Path(str(path).lower()).parts.index(project.name)

    return idx


def get_root(path):
    """
    Returns project root path as [:project[ from a pathlib.Path

    """
    # Instantiate DRS root.
    root = None

    # Get project index in path.
    idx = project_idx(path)

    if idx:
        # Keep path parts until project.
        root = Path(*path.parts[:idx])

    return root


def get_drs(path):
    """
    Returns the DRS part of a pathlib.Path as [project:filename[

    """
    # Instantiate DRS part.
    drs = None

    # Get project index in path.
    idx = project_idx(path)

    if idx:
        # Remove root parts.
        # Do on parent if path is a file.
        if path.is_file() or path.name[-3:]==".nc": # Lo ça ne fonctionne pas si le path correspond à un fichier qui n'est pas encore sur le disque du coup path[:-3]==".nc"
            drs = Path(*path.parent.parts[idx:])
        else:
            drs = Path(*path.parts[idx:])

    return drs


def get_drs_up(path):
    """
    Returns the dataset DRS part of a pathlib.Path as [project:version]

    """
    # Instantiate dataset DRS part.
    d_drs = None

    # Get project code.
    project = get_project(path)

    # Get DRS part of the path.
    drs = get_drs(path)

    if drs:
        # Retrieve index of the version level in the drs parts.
        idx = version_idx(project, 'directory_structure')

        # Get DRS parts until the dataset version.
        if len(drs.parts) >= (idx + 1):
            d_drs = Path(*drs.parts[:idx+1])

    return d_drs


def get_drs_down(path):
    """
    Returns the file DRS part of a pathlib.Path as ]version:filename[

    """
    # Instantiate dataset DRS part.
    f_drs = None

    # Get project code.
    project = get_project(path)

    # Get DRS part of the path.
    drs = get_drs(path)

    if drs:
        # Retrieve index of the version level in the drs parts.
        idx = version_idx(project, 'directory_structure')

        # Get DRS parts until the dataset version.
        if len(drs.parts) >= (idx + 1):
            f_drs = Path(*drs.parts[idx+1:])

    return f_drs


def get_version(path, integer=False):
    """
    Returns the version value from a pathlib.Path.
    Can return the digit part as integer.

    """
    # Instantiate dataset DRS part.
    version = None

    # Get project code.
    project = get_project(path)

    # Get DRS part of the path.
    drs = get_drs(path)

    if drs:
        # Retrieve index of the version level in the drs parts.
        idx = version_idx(project, 'directory_structure')

        # Get version level value.
        if len(drs.parts) >= (idx + 1):
            v = drs.parts[version_idx(project, 'directory_structure')]

            # Check version pattern.
            if re.match(VERSION_PATTERN, v):

                # Integer conversion.
                if integer:
                    version = int(v[1:])
                else:
                    version = v

    return version


def get_variable(path):
    """
    Returns the variable value from a pathlib.Path.

    """
    # Instantiate dataset DRS part.
    variable = None

    # Get project code.
    project = get_project(path)

    # Get DRS part of the path.
    drs = get_drs(path)

    if drs:
        variable = drs.parts[variable_idx(project, 'directory_structure')]

    return variable


def get_terms(path):
    """
    Validates the drs part of the pathlib.Path against CV and get pyessv terms.

    """
    # Instantiate terms.
    terms = dict()

    # Get project code.
    project = get_project(path)

    # Get DRS part of the path.
    drs = get_drs(path)
    #print("mDRS",drs)

    # Validate each drs items against CV.
    try:
        terms = {term.collection.name: term for term in pyessv.parse_directory(project.name, str(drs),4)}

    # Catch parsing errors.
    except (TemplateParsingError, TemplateValueError) as error:
        #print("OLAAAAAAA")
        Print.debug(f'Invalid DRS path -- {error}')

    return terms


def dataset_path(path):
    """
    Returns the dataset pathlib.Path corresponding to the dataset level of the current pathlib.Path.

    """
    # Get the version.
    version = get_version(path)
    #print("from_dataset_path",version)
    # Test current path.
    if path.name == version:
        return path

    # Iterate over the path parents.
    for parent in path.parents:

        # Verify last parent level is the version.
        if parent.name == version:
            # Return the parent Path object.
            return parent

    return None


def get_versions(path):
    """
    Returns all dataset versions labels of the current pathlib.Path.

    """
    # Instantiate versions list.
    versions = list()

    # Test current path.
    if path.exists():
        #print("COUCOU de get_version", path)
        #print("COUCOU", [version for version in sorted(path.iterdir())])
        if path.is_dir():
            versions = [version for version in sorted(path.iterdir()) if re.match(r'^v[\d]+$', version.name)]
        #if not versions:
        #    versions = [version for version in sorted(path.parent.iterdir()) if re.match(r'v[\d]', version.name)] # pourquoi iterdir (car on est déjà dans la verison) du coup iterdir nous renvoi le fichier ?

    #print("PATH exist:", versions )
    if not versions:
        #print("pas de version")
        # Get dataset path.
        dataset = dataset_path(path)
        #print("dataset", dataset)
        # Check dataset path exists.
        if dataset and dataset.exists():
            # Sort versions folders.
            versions = [version for version in sorted(dataset.parent.iterdir()) if re.match(r'^v[\d]+$', version.name)]
            #print("VERSION",versions)
    return versions


def is_latest_symlink(path):
    """
    Returns True if the dataset version of a pathlib.Path is "latest" and is a symlink.

    """
    return True if path.is_symlink() and get_version(path) == 'latest' else False


def with_latest_target(path):
    """
    Returns the pathlib.Path corresponding to the targeted version of a "latest" symlink.

    """
    # Instantiate target.
    target = None

    # Verify path has "latest" symlink.
    if is_latest_symlink(path):

        # Get project code.
        project = get_project(path)

        # Get dataset path.
        dataset = dataset_path(path)

        if dataset:
            # Get current path parts.
            target = list(path.parts)

            # Replace version part by targeted version of "latest" symlink.
            target[version_idx(project, 'directory_structure')] = dataset.resolve().name

            # Path object with new target parts.
            target = Path(*target)

    return target


def with_latest_version(path):
    """
    Returns the pathlib.Path corresponding to the latest existing version.

    """
    # Instantiate target.
    target = None

    # Get dataset version.
    version = get_version(path)

    # Get existing versions.
    versions = get_versions(path)

    if versions:
        # Replace current version item by latest existing version.
        target = list(path.parts)
        target[target.index(version)] = versions[-1].name

        # Path object with with new target parts.
        target = Path(*target)

    return target


def with_file_folder(path):
    """
    Returns the pathlib.Path corresponding to the hard file folder.

    """
    # Instantiate target.
    target = None

    # Appends DRS root parts.
    root = get_root(path)
    if root:
        target = list(root.parts)

        # Appends dataset DRS parts without the version level.
        d_drs = get_drs_up(path)
        if d_drs:
            target += d_drs.parent.parts

            # Appends "files" folder.
            target.append('files')

            # Appends files subdirectories depending on the DRS fashion.
            # CMIP5 like DRS has a file dataset part.
            a=get_drs_down(path).name
            #drsd = get_drs_down(path)
            if get_drs_down(path).name:
                # Get all drs parts.
                target.append(f'{get_variable(path)}_{ get_version(path, integer=True)}') # LoLo pour CMIP5 je crois ? variable après version
            else:
                target.append(f'd{get_version(path, integer=True)}')

            # Add filename.
            target.append(path.name)

            # Path object with new target parts.
            target = Path(*target)

    return target


def dataset_id(path):
    """
    Returns the dataset identifier string corresponding to a pathlib.Path

    """
    # Instantiate identifier.
    identifier = None

    # Get pyessv terms.
    terms = get_terms(path)
    #print("GETTERM! ",terms)
    if terms:
        # Get project code.
        project = get_project(path)

        # Build identifier.
        identifier = pyessv.build_dataset_identifier(project.name, set(terms.values()))

    return identifier
