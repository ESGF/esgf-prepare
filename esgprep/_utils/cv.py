# -*- coding: utf-8 -*-

"""
.. module:: esgprep._utils.path.py
   :platform: Unix
   :synopsis: CV utilities.

.. moduleauthor:: Guillaume Levavasseur <glipsl@ipsl.fr>

"""

from fuzzywuzzy.fuzz import partial_ratio
from fuzzywuzzy.process import extractOne
from pyessv.parsing.identifiers.config import get_config
from pyessv.constants import IDENTIFIER_TYPE_DIRECTORY
def get_collections(project, parser):
    """
    Returns the list of collection for a syntax parser/template.

    """
    assert parser in project.data, 'Invalid parser.'
    cfg = get_config(project, IDENTIFIER_TYPE_DIRECTORY)
    return [spec.namespace for spec in cfg.specs if spec.typeof=="collection"]


def version_idx(project, parser):
    """
    Returns the index of the DRS version.

    """
    # Get version index from the corresponding pyessv template.
    # add 1 because pyessv template does not count project level. ODO is that changed with manifest ?
    collections = get_collections(project, parser)
    return collections.index(project.namespace+":version")+1   # Lo Change +1 to R (mais du coup ça plante pour remove : remet +1 ou pas  )


def variable_idx(project, parser):
    """
    Returns the index of the DRS variable.

    """
    # Find closest pyessv key using partial string comparison.
    key, _ = extractOne('variable', get_collections(project, parser), scorer=partial_ratio)

    # Get variable index from the corresponding pyessv template.
    return get_collections(project, parser).index(key) + 1
