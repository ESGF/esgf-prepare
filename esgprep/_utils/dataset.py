# -*- coding: utf-8 -*-

"""
.. module:: esgprep._utils.dataset.py
   :platform: Unix
   :synopsis: Dataset utilities.

.. moduleauthor:: Guillaume Levavasseur <glipsl@ipsl.fr>

"""

from esgprep._handlers.dataset_id import Dataset
from pyessv._exceptions import TemplateParsingError, TemplateValueError
from esgprep._utils.print import *
import pyessv


def get_project(dataset):
    """
    Extract project code from a Dataset object.

    """
    # Get all scopes within the loaded authority.
    scopes = {scope.name: scope.namespace for scope in pyessv.all_scopes()}

    # Find intersection between scopes list and first dataset item.
    project = set(dataset.parts[0]).intersection(scopes)

    # Ensure only one project code matched.
    if len(project) == 1:

        # Returns pyessv scope object as project.
        return pyessv.load(scopes[project.pop()])

    elif len(project) == 0:
        Print.debug(f'No project code found: {dataset.identifier}')
        return None
    else:
        Print.debug(f'Unable to match one project code: {dataset.identifier}')
        return None


def get_terms(dataset):
    """
    Validates the dataset identifier against CV and get pyessv terms.

    """
    # Instantiate terms.
    terms = dict()

    # Get project code.
    project = get_project(dataset)

    # Validate each drs items against CV.
    try:
        terms = {term.collection.name: term for term in pyessv.parse_dataset_identifier(project,
                                                                                        dataset.identifier)}

    # Catch template parsing in case of no ending version.
    except TemplateParsingError:

        # Add phony "latest" ending version.
        dataset = Dataset(dataset.identifier + 'latest')
        try:
            terms = {term.collection.name: term for term in pyessv.parse_dataset_identifier(project,
                                                                                            dataset.identifier)}

        except (TemplateParsingError, TemplateValueError) as error:
            Print.debug(f'Invalid dataset identifier -- {error}')

    # Catch parsing errors.
    except TemplateValueError as error:
        Print.debug(f'Invalid dataset identifier -- {error}')

    return terms


def dataset_id(dataset):
    """
    Returns the dataset identifier string corresponding to the dataset object.

    """
    # Instantiate identifier.
    identifier = None

    # Get pyessv terms.
    terms = get_terms(dataset)

    if terms:
        # Get project code.
        project = get_project(dataset)

        # Build identifier.
        identifier = pyessv.build_dataset_identifier(project.name, set(terms.values()))

    return identifier


def directory_structure(dataset):
    """
    Returns the DRS directory corresponding to the dataset object.

    """
    # Instantiate identifier.
    identifier = None

    # Get pyessv terms.
    terms = get_terms(dataset)

    if terms:
        # Get project code.
        project = get_project(dataset)

        # Build identifier.
        identifier = pyessv.build_directory_structure(project.name, set(terms.values()))

    return identifier