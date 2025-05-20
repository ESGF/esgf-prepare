# -*- coding: utf-8 -*-

"""
.. module:: esgprep._utils.dataset.py
   :platform: Unix
   :synopsis: Dataset utilities.

.. moduleauthor:: Guillaume Levavasseur <glipsl@ipsl.fr>

"""

import esgvoc.api as ev

from esgprep._handlers.dataset_id import Dataset
from esgprep._utils.print import Print


def get_project(dataset):
    """
    Extract project code from a Dataset object.

    """
    # Get all project within the CV.
    projects = ev.get_all_projects()

    # Find intersection between scopes list and first dataset item.
    project = set(dataset.parts[0]).intersection(projects)

    # Ensure only one project code matched.
    if len(project) == 1:
        # Returns project code.
        return next(iter(project))

    elif len(project) == 0:
        Print.debug(f"No project code found: {dataset.identifier}")
        return None
    else:
        Print.debug(f"Unable to match one project code: {dataset.identifier}")
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
        terms = {
            term.collection.name: term
            for term in pyessv.parse_dataset_identifier(project, dataset.identifier)
        }

    # Catch template parsing in case of no ending version.
    except NamespaceParsingError:
        # Add phony "latest" ending version.
        dataset = Dataset(dataset.identifier + "latest")
        try:
            terms = {
                term.collection.name: term
                for term in pyessv.parse_dataset_identifier(project, dataset.identifier)
            }

        except (NamespaceParsingError, ValidationError) as error:
            Print.debug(f"Invalid dataset identifier -- {error}")

    # Catch parsing errors.
    except ValidationError as error:
        Print.debug(f"Invalid dataset identifier -- {error}")

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
