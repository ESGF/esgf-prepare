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
    properly place a file in the DRS structure, and includes the ability
    to generate its own DRS path based on project-specific rules.
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
    version: str = Field(..., description="Version identifier (e.g., 'v20250401')")
    
    # Processing flags
    ignored: bool = Field(False, description="Whether the file should be ignored")
    is_duplicate: bool = Field(False, description="Whether the file is a duplicate")
    
    # DRS generator instance (not part of the serialized model)
    _drs_generator = None
    _project_config = None
    _directory_spec = None
    _facet_order = None
    _required_facets = None
    
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
    
    @model_validator(mode='after')
    def initialize_generator(self) -> 'FileInput':
        """Initialize the DRS generator for this file."""
        try:
            # Only import and initialize if not already done
            if self._drs_generator is None:
                # Import the DRS generator for this project
                try:
                    import esgvoc.api as ev
                    from esgvoc.apps.drs.generator import DrsGenerator
                    
                    # Initialize generator
                    print(self.project)
                    self._drs_generator = DrsGenerator(self.project.lower())
                    
                    # Get project DRS specifications
                    self._project_config = ev.get_project(self.project.lower())
                    self._directory_spec = self._get_drs_spec_by_type('directory')
                except ImportError:
                    print(f"Warning: esgvoc package not available for project {self.project}")
                except Exception as e:
                    print(f"Error initializing DRS generator: {e}")
        except Exception as e:
            print(f"Unexpected error initializing generator: {e}")
        
        return self
    
    def _get_drs_spec_by_type(self, spec_type: str):
        """Get DRS specification for a specific type."""
        if not self._project_config:
            return None
            
        for spec in self._project_config.drs_specs:
            if spec.type.value == spec_type:
                return spec
        return None
    
    def get_facet_order(self) -> List[str]:
        """
        Get the order of facets for the directory structure based on project configuration.
        
        Returns:
            List of facet names in the correct order for the DRS structure
        """
        # Return cached value if available
        if self._facet_order is not None:
            return self._facet_order
            
        # Get from directory specification if available
        if self._directory_spec:
            self._facet_order = [part.collection_id for part in self._directory_spec.parts]
            return self._facet_order
        
        # Fallback for CMIP6 if no specification is available
        if self.project.lower() == "cmip6":
            self._facet_order = [
                "mip_era", "activity_id", "institution_id", "source_id", 
                "experiment_id", "member_id", "table_id", "variable_id", 
                "grid_label", "version"
            ]
            return self._facet_order
        
        # Generic fallback - use keys from drs_facets or a minimal set
        if self.drs_facets:
            self._facet_order = list(self.drs_facets.keys())
            if "version" not in self._facet_order:
                self._facet_order.append("version")
            return self._facet_order
            
        # Absolute minimal fallback
        self._facet_order = ["project", "version"]
        return self._facet_order
    
    def get_required_facets(self) -> Set[str]:
        """
        Get the set of required facets for the project.
        
        Returns:
            Set of facet names that are required for the DRS structure
        """
        # Return cached value if available
        if self._required_facets is not None:
            return self._required_facets
            
        # Get from directory specification if available
        if self._directory_spec:
            self._required_facets = {part.collection_id for part in self._directory_spec.parts if part.is_required}
            return self._required_facets
        
        # Fallback to all facets in facet order
        self._required_facets = set(self.get_facet_order())
        return self._required_facets
    
    def get_facet_alternatives(self, facet: str) -> List[str]:
        """
        Get alternative attribute names that could contain the facet value.
        
        Args:
            facet: Facet name to find alternatives for
            
        Returns:
            List of alternative attribute names
        """
        # Common attribute-to-facet mappings
        alternatives = {
            "project": ["project_id", "mip_era"],
            "mip_era": ["project_id", "project"],
            "activity_id": ["activity_drs", "activity"],
            "institution_id": ["institute_id", "institute", "institution"],
            "source_id": ["model_id", "model", "source"],
            "experiment_id": ["experiment", "exp_id", "exp"],
            "member_id": ["variant_label", "member", "ensemble", "realization"],
            "table_id": ["table", "cmor_table", "frequency"],
            "variable_id": ["variable", "var_id", "var"],
            "grid_label": ["grid", "grid_id"],
            "version": ["version_date", "date"]
        }
        
        # Return alternatives if available, otherwise just the facet itself
        return alternatives.get(facet, [facet])
    
    def _prepare_attributes_for_drs(self) -> Dict[str, Any]:
        """
        Prepare attributes for DRS generation by applying mappings.
            
        Returns:
            Processed attributes dictionary suitable for DRS generation
        """
        mapping_attrs = self.attributes.copy()
        
        # Apply standard mappings for common variant fields
        if "variant_label" in self.attributes and "member_id" not in mapping_attrs:
            mapping_attrs["member_id"] = self.attributes["variant_label"]
        
        if "mip_era" in self.attributes and "project" not in mapping_attrs:
            mapping_attrs["project"] = self.attributes["mip_era"]
        
        if "project_id" in self.attributes and "project" not in mapping_attrs:
            mapping_attrs["project"] = self.attributes["project_id"]
        
        # Ensure project and version are set
        mapping_attrs["project"] = self.project
        mapping_attrs["version"] = self.version
        
        # Add drs_facets (which may include overrides)
        mapping_attrs.update(self.drs_facets)
        
        return mapping_attrs
    
    def _extract_facets_from_drs(self, drs_path: str) -> Dict[str, str]:
        """
        Extract facet values from a DRS path string.
        
        Args:
            drs_path: DRS path string
            
        Returns:
            Dictionary of facet names and values
        """
        facets = {}
        
        # Get facet order for this project
        facet_order = self.get_facet_order()
        
        # Split path and extract facets according to order
        parts = drs_path.strip('/').split('/')
        
        # Match parts to facets based on position
        for i, part in enumerate(parts):
            if i < len(facet_order):
                facets[facet_order[i]] = part
        
        return facets
    
    def extract_facets_from_attributes(self, set_keys: Dict[str, str] = None) -> Dict[str, str]:
        """
        Extract facets from file attributes using project-specific rules.
        
        Args:
            set_keys: Dictionary mapping facet keys to attribute names
            
        Returns:
            Dictionary of extracted facets
        """
        set_keys = set_keys or {}
        facets = {}
        
        # Get required facets for this project
        required_facets = self.get_required_facets()
        
        # Extract facets from attributes using mappings and alternatives
        for facet in required_facets:
            # Skip if already in drs_facets
            if facet in self.drs_facets:
                facets[facet] = self.drs_facets[facet]
                continue
                
            # Check if there's a mapping in set_keys
            if set_keys and facet in set_keys:
                attr_name = set_keys[facet]
                if attr_name in self.attributes:
                    facets[facet] = self.attributes[attr_name]
                    continue
            
            # Try direct match in attributes
            if facet in self.attributes:
                facets[facet] = self.attributes[facet]
                continue
            
            # Try alternative attribute names
            for alt_name in self.get_facet_alternatives(facet):
                if alt_name in self.attributes:
                    facets[facet] = self.attributes[alt_name]
                    break
        
        # Ensure project is set
        if "project" not in facets:
            facets["project"] = self.project
        
        # Ensure version is set
        if "version" not in facets:
            facets["version"] = self.version
        
        return facets
    
    def update_facets(self, set_values: Dict[str, str] = None, set_keys: Dict[str, str] = None) -> None:
        """
        Update facets with provided values and/or extracted from attributes.
        
        Args:
            set_values: Dictionary of facet values to override detected values
            set_keys: Dictionary mapping facet keys to attribute names
        """
        # Apply set_values overrides first
        if set_values:
            self.drs_facets.update(set_values)
        
        # Extract additional facets from attributes
        extracted_facets = self.extract_facets_from_attributes(set_keys)
        
        # Update with extracted facets (but don't overwrite existing values)
        for facet, value in extracted_facets.items():
            if facet not in self.drs_facets:
                self.drs_facets[facet] = value
    
    @property
    def dataset_id(self) -> str:
        """Generate the dataset ID from the DRS facets."""
        # Try to use project-specific dataset ID generator
        try:
            if self._drs_generator and self._project_config:
                dataset_spec = self._get_drs_spec_by_type('dataset_id')
                if dataset_spec:
                    # Get the ordered facets for dataset ID
                    dataset_facets = [part.collection_id for part in dataset_spec.parts]
                    
                    # Collect values for each facet
                    parts = []
                    for facet in dataset_facets:
                        if facet in self.drs_facets:
                            parts.append(self.drs_facets[facet])
                        else:
                            parts.append(f"unknown_{facet}")
                    
                    # Use the dataset ID separator (usually '.')
                    separator = dataset_spec.separator if dataset_spec.separator else '.'
                    return separator.join(parts)
        except Exception as e:
            print(f"Error generating dataset ID from spec: {e}")
        
        # For CMIP6, use a specific format
        if self.project.lower() == "cmip6":
            # Get ordered facets for CMIP6 dataset ID (all except version)
            facets = self.get_facet_order()
            if "version" in facets:
                facets.remove("version")
                
            parts = []
            for facet in facets:
                if facet in self.drs_facets:
                    parts.append(self.drs_facets[facet])
                else:
                    parts.append(f"unknown_{facet}")
            return ".".join(parts)
        
        # For other projects, use a generic approach
        facet_values = [self.project] + [
            self.drs_facets.get(facet, f"unknown_{facet}") 
            for facet in self.get_facet_order() 
            if facet != "version"  # Exclude version
        ]
        return ".".join(facet_values)
    
    @property
    def drs_path(self) -> Optional[Path]:
        """Generate the full DRS path for this file using the appropriate method."""
        if not self.root_dir:
            return None
        
        # First try using the DRS generator if available
        if self._drs_generator:
            try:
                # Use DRS generator for path construction
                mapping_attrs = self._prepare_attributes_for_drs()
                drs_result = self._drs_generator.generate_directory_from_mapping(mapping_attrs)
                print(drs_result)
                print(mapping_attrs)
                if not drs_result.errors:
                    return self.root_dir / drs_result.generated_drs_expression / self.filename
                else:
                    print(f"DRS generation errors: {drs_result.errors}")
            except Exception as e:
                print(f"Error in DRS generation: {e}")
        
        # Fallback to manual path construction from facets
        try:
            # Build path according to project facet order
            path_parts = []
            for facet in self.get_facet_order():
                if facet in self.drs_facets:
                    path_parts.append(self.drs_facets[facet])
                else:
                    # Fill in missing required facets with placeholders
                    if facet in self.get_required_facets():
                        path_parts.append(f"unknown_{facet}")
            
            # Create destination path
            return self.root_dir.joinpath(*path_parts) / self.filename
        except Exception as e:
            print(f"Error constructing DRS path: {e}")
            return None

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
