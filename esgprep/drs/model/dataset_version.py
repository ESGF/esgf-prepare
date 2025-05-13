"""
DatasetVersion model for DRS operations.
"""

from datetime import datetime
from pathlib import Path
from typing import List, Any

from pydantic import BaseModel, Field, field_validator


class DatasetVersion(BaseModel):
    """
    Represents a specific version of a dataset in the DRS structure.
    """
    version_id: str = Field(..., description="Version identifier (e.g., 'v20220101')")
    path: Path = Field(..., description="Path to the version directory")
    is_latest: bool = Field(False, description="Whether this is the latest version")
    files: List[Path] = Field(default_factory=list, description="Files in this version")
    creation_date: datetime = Field(default_factory=datetime.now, description="Version creation date")

    @field_validator('path', mode='before')
    @classmethod
    def validate_path(cls, v: Any) -> Path:
        """Ensure paths are absolute and normalized."""
        return Path(v).absolute().resolve()
