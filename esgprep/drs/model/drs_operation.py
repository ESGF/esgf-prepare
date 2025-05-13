"""
DrsOperation model for DRS operations.
"""

from pathlib import Path
from typing import Optional, Any

from pydantic import BaseModel, Field, field_validator

from esgprep.drs.model.migration_mode import MigrationMode


class DrsOperation(BaseModel):
    """
    Represents an operation to be performed on the DRS tree.
    Simplified for clarity and usability.
    """
    operation_type: MigrationMode
    source: Optional[Path] = None
    destination: Path
    description: Optional[str] = None  # Human-readable description of the operation

    @field_validator('source', 'destination', mode='before')
    @classmethod
    def validate_path(cls, v: Any) -> Optional[Path]:
        """Ensure paths are absolute and normalized."""
        if v is not None:
            return Path(v).absolute().resolve()
        return v
