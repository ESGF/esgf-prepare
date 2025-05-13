"""
ESGF DRS Pydantic models for file input and output representation.

These models provide strong typing and validation for the ESGDRS processing pipeline.
Updated for Pydantic v2 using the recommended validation approach.
"""

# Re-export all models from the model directory
from esgprep.drs.model import (
    MigrationMode,
    FileInput,
    DatasetVersion,
    Dataset,
    DrsOperation,
    DrsResult
)

__all__ = [
    'MigrationMode',
    'FileInput',
    'DatasetVersion',
    'Dataset',
    'DrsOperation',
    'DrsResult'
]
