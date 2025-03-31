# -*- coding: utf-8 -*-
"""
ESGF DRS Pydantic models for file input and output representation.

These models provide strong typing and validation for the ESGDRS processing pipeline.
Updated for Pydantic v2 using the recommended validation approach.
"""

from datetime import datetime
from enum import Enum
from pathlib import Path
from typing import Dict, List, Optional, Set, Union, Any, ClassVar

from pydantic import BaseModel, Field, field_validator, model_validator


class MigrationMode(str, Enum):
    """Migration modes for file operations in DRS."""
    MOVE = "move"
    COPY = "copy"
    LINK = "link"
    SYMLINK = "symlink"
    REMOVE = "remove"


class FileInput(BaseModel):
    """
    Represents a file to be processed by the ESGDRS pipeline.
    
    This model captures all input information needed to identify and
    properly place a file in the DRS structure.
    """
    # File information
    source_path: Path = Field(..., description="Original path of the input file")
    filename: str = Field(..., description="Name of the file")
    file_size: int = Field(..., description="Size of the file in bytes")
    
    # DRS location information
    project: str = Field(..., description="Project code (e.g., 'cmip6')")
    root_dir: Optional[Path] = Field(None, description="Root directory for the DRS tree")
    
    # Metadata from file
    attributes: Dict[str, Union[str, int, float, List]] = Field(
        default_factory=dict, description="NetCDF file attributes"
    )
    tracking_id: Optional[str] = Field(None, description="Tracking ID from file metadata")
    checksum: Optional[str] = Field(None, description="File checksum")
    checksum_type: Optional[str] = Field("sha256", description="Type of checksum")
    
    # DRS information
    drs_facets: Dict[str, str] = Field(default_factory=dict, description="DRS facets extracted from file")
    version: str = Field(..., description="Version identifier (e.g., 'v20220101')")
    
    # Processing flags
    ignored: bool = Field(False, description="Whether the file should be ignored")
    is_duplicate: bool = Field(False, description="Whether the file is a duplicate")
    
    # Project-specific facet ordering (could be moved to configuration)
    facet_orders: ClassVar[Dict[str, List[str]]] = {
        "cmip6": ["activity_id", "institution_id", "source_id", "experiment_id", 
                 "member_id", "table_id", "variable_id", "grid_label", "version"]
    }
    
    @field_validator('source_path', 'root_dir', mode='before')
    @classmethod
    def validate_path(cls, v: Any) -> Optional[Path]:
        """Ensure paths are absolute and normalized."""
        if v is not None:
            if isinstance(v, str):
                return Path(v).absolute().resolve()
            elif isinstance(v, Path):
                return v.absolute().resolve()
            else:
                raise ValueError(f"Expected string or Path object, got {type(v)}")
        return v
    
    @property
    def dataset_id(self) -> str:
        """Generate the dataset ID from the DRS facets."""
        facet_values = [self.project] + [
            self.drs_facets.get(facet, "unknown") 
            for facet in self.get_facet_order()
        ]
        return ".".join(facet_values)
    
    def get_facet_order(self) -> List[str]:
        """Get the order of facets for the project."""
        # Get from class-level mapping or fallback to keys
        return self.facet_orders.get(
            self.project.lower(), 
            list(self.drs_facets.keys())
        )
    
    @property
    def drs_path(self) -> Optional[Path]:
        """Generate the full DRS path for this file."""
        if not self.root_dir:
            return None
            
        # Build path components from facets in correct order
        path_components = [self.project]
        for facet in self.get_facet_order():
            if facet in self.drs_facets and facet != "version":
                path_components.append(self.drs_facets[facet])
        
        # Add version at the end
        path_components.append(self.version)
        
        # Construct final path
        return self.root_dir / Path(*path_components) / self.filename


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


class Dataset(BaseModel):
    """
    Represents a dataset with multiple versions in the DRS structure.
    """
    dataset_id: str = Field(..., description="Dataset identifier")
    versions: List[DatasetVersion] = Field(default_factory=list, description="Dataset versions")
    facets: Dict[str, str] = Field(default_factory=dict, description="DRS facets for this dataset")
    
    @property
    def latest_version(self) -> Optional[DatasetVersion]:
        """Get the latest version of the dataset."""
        if not self.versions:
            return None
        return sorted(self.versions, key=lambda v: v.version_id, reverse=True)[0]


class DrsOperation(BaseModel):
    """
    Represents an operation to be performed on the DRS tree.
    """
    operation_type: MigrationMode
    source: Optional[Path] = None
    destination: Path
    is_duplicate: bool = False
    tracking_id: Optional[str] = None
    
    @field_validator('source', 'destination', mode='before')
    @classmethod
    def validate_path(cls, v: Any) -> Optional[Path]:
        """Ensure paths are absolute and normalized."""
        if v is not None:
            return Path(v).absolute().resolve()
        return v


class DrsResult(BaseModel):
    """
    Represents the result of processing a file through the ESGDRS pipeline.
    """
    input_file: FileInput
    operations: List[DrsOperation] = Field(default_factory=list)
    success: bool = Field(False, description="Whether processing succeeded")
    error_message: Optional[str] = Field(None, description="Error message if processing failed")
    dataset: Optional[Dataset] = Field(None, description="Dataset this file belongs to")
    
    @model_validator(mode='after')
    def check_error_success_consistency(self) -> 'DrsResult':
        """Ensure that success and error_message are consistent."""
        if self.success and self.error_message:
            # Can't be successful with an error message
            self.success = False
        return self
