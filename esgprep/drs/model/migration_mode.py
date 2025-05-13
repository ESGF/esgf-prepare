"""
Migration mode enum for DRS operations.
"""

from enum import Enum


class MigrationMode(str, Enum):
    """Migration modes for file operations in DRS."""
    MOVE = "move"
    COPY = "copy"
    LINK = "link"
    SYMLINK = "symlink"
    REMOVE = "remove"
