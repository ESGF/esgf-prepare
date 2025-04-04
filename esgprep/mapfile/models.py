"""
Pydantic models for the ESGF mapfile module.

These models provide strong typing and validation for the mapfile generation pipeline.
"""

from datetime import datetime
from enum import Enum
from pathlib import Path
from typing import Dict, List, Optional, Union, Any, Set, ClassVar

from pydantic import BaseModel, Field, field_validator, model_validator

class FileInput(BaseModel):
    """
    Represents a file to be processed for mapfile generation.
    
    This model captures all input information needed to identify and properly 
    represent a file in a mapfile, including DRS facets and file metadata.
    """
    # File information
    source_path: Path = Field(..., description="Original path of the input file")
    filename: str = Field(..., description="Name of the file")
    file_size: int = Field(..., description="Size of the file in bytes")
    mod_time: Optional[int] = Field(None, description="Last modification time in Unix epoch")
    
    # Project information
    project: str = Field(..., description="Project code (e.g., 'cmip6')")
    
    # File metadata
    attributes: Dict[str, Union[str, int, float, List]] = Field(
        default_factory=dict, description="NetCDF file attributes"
    )
    tracking_id: Optional[str] = Field(None, description="Tracking ID from file metadata")
    checksum: Optional[str] = Field(None, description="File checksum")
    checksum_type: Optional[str] = Field(None, description="Type of checksum")
    
    # DRS information
    drs_facets: Dict[str, str] = Field(default_factory=dict, description="DRS facets extracted from file")
    version: Optional[str] = Field(None, description="Version identifier (e.g., 'v20250401')")
    
    # DRS generator instance (not part of the serialized model)
    _drs_generator = None
    _project_config = None
    
    @field_validator('source_path')
    @classmethod
    def validate_source_path(cls, v: Any) -> Path:
        """Ensure source_path is a Path object."""
        return Path(v) if isinstance(v, str) else v
    
    @field_validator('filename')
    @classmethod
    def validate_filename(cls, v: Any, info) -> str:
        """If filename not provided, extract from source_path."""
        if not v and 'source_path' in info.data:
            return info.data['source_path'].name
        return v
    
    @model_validator(mode='after')
    def initialize_generator(self) -> 'FileInput':
        """Initialize the DRS generator for this file."""
        try:
            # Only import and initialize if not already done
            if self._drs_generator is None:
                try:
                    import esgvoc.api as ev
                    from esgvoc.apps.drs.generator import DrsGenerator
                    
                    # Initialize generator
                    self._drs_generator = DrsGenerator(self.project.lower())
                    
                    # Get project DRS specifications
                    self._project_config = ev.get_project(self.project.lower())
                except ImportError:
                    # Fall back to simpler approach if esgvoc not available
                    pass
                except Exception as e:
                    print(f"Error initializing DRS generator: {e}")
        except Exception as e:
            print(f"Unexpected error initializing generator: {e}")
        
        return self
    
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
        extracted_facets = self._extract_facets_from_attributes(set_keys)
        
        # Update with extracted facets (but don't overwrite existing values)
        for facet, value in extracted_facets.items():
            if facet not in self.drs_facets:
                self.drs_facets[facet] = value
    
    def _extract_facets_from_attributes(self, set_keys: Dict[str, str] = None) -> Dict[str, str]:
        """
        Extract facets from file attributes.
        
        Args:
            set_keys: Dictionary mapping facet keys to attribute names
            
        Returns:
            Dictionary of extracted facets
        """
        set_keys = set_keys or {}
        facets = {}
        
        # Some common attribute mappings for CMIP6
        attribute_mappings = {
            "mip_era": ["project_id", "project", "mip_era"],
            "activity_id": ["activity_drs", "activity", "activity_id"],
            "institution_id": ["institute_id", "institute", "institution", "institution_id"],
            "source_id": ["model_id", "model", "source", "source_id"],
            "experiment_id": ["experiment", "exp_id", "exp", "experiment_id"],
            "member_id": ["variant_label", "member", "ensemble", "realization", "member_id"],
            "table_id": ["table", "cmor_table", "frequency", "table_id"],
            "variable_id": ["variable", "var_id", "var", "variable_id"],
            "grid_label": ["grid", "grid_id", "grid_label"],
            "version": ["version_date", "date", "version"]
        }
        
        # Try to extract facets from attributes
        for facet, alt_names in attribute_mappings.items():
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
            for alt_name in alt_names:
                if alt_name in self.attributes:
                    facets[facet] = self.attributes[alt_name]
                    break
        
        # Ensure project is set
        if "project" not in facets:
            facets["project"] = self.project
        
        # Ensure version is set if available
        if "version" not in facets and self.version:
            facets["version"] = self.version
        
        return facets
    
    @property
    def dataset_id(self) -> str:
        """
        Generate the dataset ID using the esgvoc DRS generator.
        
        Returns:
            Dataset ID string
        """
        # Try using esgvoc DRS generator if available
        if self._drs_generator and self._project_config:
            try:
                # Prepare attributes for DRS generation
                mapping_attrs = {**self.attributes}
                mapping_attrs.update(self.drs_facets)
                # Generate dataset ID using DRS generator
                result = self._drs_generator.generate_dataset_id_from_mapping(mapping_attrs)
             
                if not result.errors:
                    return result.generated_drs_expression
                else:
                    print(f"DRS generation errors: {result.errors}")
            except Exception as e:
                print(f"Error in dataset ID generation: {e}")
        
        # Fall back to manual generation
        try:
            # Get facets with project-specific order
            facets = []
            
            # For CMIP6, use a specific order
            if self.project.lower() == "cmip6":
                facet_order = [
                    "mip_era", "activity_id", "institution_id", "source_id", 
                    "experiment_id", "member_id", "table_id", "variable_id", "grid_label"
                ]
                
                # Build facet values list
                for facet in facet_order:
                    if facet in self.drs_facets:
                        facets.append(self.drs_facets[facet])
                    else:
                        # Try to find in attributes as fallback
                        found = False
                        for attr, value in self.attributes.items():
                            if facet.lower() == attr.lower():
                                facets.append(str(value))
                                found = True
                                break
                        
                        if not found:
                            facets.append(f"unknown_{facet}")
            else:
                # For other projects, use a generic approach
                # Start with project
                facets = [self.project]
                
                # Add all other facets in alphabetical order
                facets.extend([value for key, value in sorted(self.drs_facets.items()) 
                              if key != "project" and key != "version"])
            
            # Join with dots to form dataset ID
            return ".".join(facets)
            
        except Exception as e:
            print(f"Error building dataset ID manually: {e}")
            # Very basic fallback
            return f"{self.project}.unknown"

class MapfileResult(BaseModel):
    """Result of mapfile generation for a single file."""
    
    # File input data
    input_file: FileInput = Field(..., description="Input file information")
    
    # Mapfile information
    mapfile_path: Optional[Path] = Field(None, description="Path to the generated mapfile")
    
    # Processing metadata
    success: bool = Field(False, description="Whether processing succeeded")
    error_message: Optional[str] = Field(None, description="Error message if processing failed")
    
    # Optional attributes to include in mapfile
    attributes: Dict[str, Any] = Field(default_factory=dict, description="Optional attributes for mapfile")
    
    @field_validator('mapfile_path')
    @classmethod
    def validate_mapfile_path(cls, v: Any) -> Optional[Path]:
        """Ensure mapfile_path is a Path object."""
        if v is None:
            return None
        return Path(v) if isinstance(v, str) else v
    
    @property
    def source_path(self) -> Path:
        """Get source path from input file."""
        return self.input_file.source_path
    
    @property
    def file_size(self) -> int:
        """Get file size from input file."""
        return self.input_file.file_size
    
    @property
    def dataset_id(self) -> str:
        """Get dataset ID from input file."""
        return self.input_file.dataset_id
    
    @property
    def version(self) -> Optional[str]:
        """Get version from input file."""
        return self.input_file.version

class MapfileEntry(BaseModel):
    """Represents a single entry in a mapfile."""
    
    dataset_id: str = Field(..., description="Dataset identifier")
    version: Optional[str] = Field(None, description="Dataset version")
    path: Path = Field(..., description="Path to the file")
    size: int = Field(..., description="Size of the file in bytes")
    mod_time: Optional[int] = Field(None, description="Last modification time in UNIX epoch")
    checksum: Optional[str] = Field(None, description="File checksum")
    checksum_type: Optional[str] = Field(None, description="Type of checksum")
    tech_notes_url: Optional[str] = Field(None, description="URL for technical notes")
    tech_notes_title: Optional[str] = Field(None, description="Title of technical notes")
    
    def __str__(self) -> str:
        """Convert mapfile entry to string format for writing to file."""
        # Base entry with required fields
        entry_parts = []
        
        # Dataset ID with optional version
        if self.version:
            entry_parts.append(f"{self.dataset_id}#{self.version}")
        else:
            entry_parts.append(self.dataset_id)
        
        # Add file path and size
        entry_parts.append(str(self.path))
        entry_parts.append(str(self.size))
        
        # Add optional attributes
        for attr, value in {
            'mod_time': self.mod_time,
            'checksum': self.checksum,
            'checksum_type': self.checksum_type,
            'dataset_tech_notes': self.tech_notes_url,
            'dataset_tech_notes_title': self.tech_notes_title
        }.items():
            if value is not None:
                entry_parts.append(f"{attr}={value}")
        
        # Join with pipe separator
        return " | ".join(entry_parts)

class Mapfile(BaseModel):
    """Represents a complete mapfile with multiple entries."""
    
    path: Path = Field(..., description="Path to the mapfile")
    entries: List[MapfileEntry] = Field(default_factory=list, description="Entries in the mapfile")
    
    def add_entry(self, entry: MapfileEntry) -> None:
        """Add an entry to the mapfile."""
        self.entries.append(entry)
    
    def write(self) -> None:
        """Write the mapfile to disk."""
        # Create directory if it doesn't exist
        self.path.parent.mkdir(parents=True, exist_ok=True)
        
        # Write entries to file
        with open(self.path, 'w') as f:
            for entry in self.entries:
                f.write(str(entry) + '\n')
    
    @classmethod
    def read(cls, path: Path) -> 'Mapfile':
        """Read a mapfile from disk."""
        mapfile = cls(path=path)
        
        try:
            with open(path, 'r') as f:
                for line in f:
                    parts = [p.strip() for p in line.split('|')]
                    
                    # Parse dataset ID and version
                    dataset_part = parts[0]
                    if '#' in dataset_part:
                        dataset_id, version = dataset_part.split('#')
                    else:
                        dataset_id, version = dataset_part, None
                    
                    # Parse file path and size
                    file_path = Path(parts[1])
                    size = int(parts[2])
                    
                    # Parse optional attributes
                    attributes = {}
                    for i in range(3, len(parts)):
                        if '=' in parts[i]:
                            key, value = parts[i].split('=', 1)
                            attributes[key] = value
                    
                    # Create entry
                    entry = MapfileEntry(
                        dataset_id=dataset_id,
                        version=version,
                        path=file_path,
                        size=size,
                        mod_time=int(attributes.get('mod_time', 0)) if 'mod_time' in attributes else None,
                        checksum=attributes.get('checksum'),
                        checksum_type=attributes.get('checksum_type'),
                        tech_notes_url=attributes.get('dataset_tech_notes'),
                        tech_notes_title=attributes.get('dataset_tech_notes_title')
                    )
                    
                    mapfile.add_entry(entry)
        except Exception as e:
            raise ValueError(f"Failed to read mapfile {path}: {e}")
        
        return mapfile
