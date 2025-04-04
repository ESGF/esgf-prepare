"""
Modern implementation of the ESGF mapfile processor.

This module provides a clean, well-structured implementation for generating
ESGF mapfiles from dataset files.
"""

from datetime import datetime
import os
import re
from pathlib import Path
from typing import Dict, List, Optional, Union, Set, Iterator, Any

from esgprep.mapfile.models import FileInput, MapfileResult, MapfileEntry, Mapfile
from esgprep._utils.checksum import get_checksum

class MapfileProcessor:
    """
    Processes files to generate ESGF mapfiles.
    
    This modern processor handles mapfile generation with strong typing and
    better separation of concerns.
    """
    
    def __init__(
        self,
        outdir: Union[str, Path],
        project: str,
        mapfile_name: str = '{dataset_id}.v{version}.map',
        no_checksum: bool = False,
        checksum_type: str = 'sha256',
        checksums_from: Optional[Dict[str, str]] = None,
        tech_notes_url: Optional[str] = None,
        tech_notes_title: Optional[str] = None,
        latest_symlink: bool = False,
        all_versions: bool = False,
        version: Optional[str] = None,
    ):
        """
        Initialize the mapfile processor.
        
        Args:
            outdir: Directory where mapfiles will be written
            project: Project identifier (e.g., 'cmip6')
            mapfile_name: Template for mapfile names
            no_checksum: Whether to skip checksum calculation
            checksum_type: Type of checksum to use
            checksums_from: Dictionary of pre-computed checksums
            tech_notes_url: URL for technical notes
            tech_notes_title: Title for technical notes
            latest_symlink: Whether to follow 'latest' symlinks
            all_versions: Whether to include all versions
            version: Specific version to include
        """
        self.outdir = Path(outdir) if not isinstance(outdir, Path) else outdir
        self.project = project.lower()
        self.mapfile_name = mapfile_name
        self.no_checksum = no_checksum
        self.checksum_type = checksum_type if not no_checksum else None
        self.checksums_from = checksums_from or {}
        self.tech_notes_url = tech_notes_url
        self.tech_notes_title = tech_notes_title
        self.latest_symlink = latest_symlink
        self.all_versions = all_versions
        self.version = version
        
        # Cache of created mapfiles to avoid duplicate work
        self.mapfiles: Dict[str, Mapfile] = {}
        
        # Create output directory if it doesn't exist
        self.outdir.mkdir(parents=True, exist_ok=True)
    
    def create_file_input(self, file_path: Path) -> FileInput:
        """
        Create a FileInput instance from a file path.
        
        Args:
            file_path: Path to the source file
            
        Returns:
            FileInput instance with extracted metadata
        """
        try:
            # Get file stats
            file_stats = file_path.stat()
            
            # Try to get NetCDF attributes if it's a NetCDF file
            attributes = {}
            if file_path.suffix.lower() == '.nc':
                try:
                    from esgprep._utils.ncfile import get_ncattrs
                    attributes = get_ncattrs(str(file_path))
                except Exception as e:
                    print(f"Warning: Couldn't read NetCDF attributes: {e}")
            
            # Add filename to attributes for additional facet extraction
            attributes["filename"] = file_path.name
            
            # Create the FileInput object
            input_file = FileInput(
                source_path=file_path,
                filename=file_path.name,
                file_size=file_stats.st_size,
                mod_time=int(file_stats.st_mtime),
                project=self.project,
                attributes=attributes,
                version=self.version
            )
            
            # Update facets from attributes
            input_file.update_facets()
            
            # Calculate checksum if needed
            if not self.no_checksum:
                try:
                    checksum = get_checksum(str(file_path), self.checksum_type, self.checksums_from)
                    input_file.checksum = checksum
                    input_file.checksum_type = self.checksum_type
                except Exception as e:
                    print(f"Warning: Checksum calculation failed: {e}")
            
            return input_file
            
        except Exception as e:
            # Re-raise with more context
            raise ValueError(f"Failed to create FileInput for {file_path}: {e}")
    
    def process_file(self, file_path: Path) -> MapfileResult:
        """
        Process a single file and add it to the appropriate mapfile.
        
        Args:
            file_path: Path to the file to process
            
        Returns:
            MapfileResult: Result of the processing
        """
        try:
            # Create FileInput instance
            input_file = self.create_file_input(file_path)
            
            # Initialize the result
            result = MapfileResult(
                input_file=input_file,
                success=False
            )
            
            # Get dataset ID from FileInput
            dataset_id = input_file.dataset_id
            version = input_file.version
            
            # Get mapfile path
            mapfile_path = self._build_mapfile_path(dataset_id, version)
            result.mapfile_path = mapfile_path
            
            # Get or create mapfile
            mapfile = self._get_or_create_mapfile(mapfile_path)
            
            # Create mapfile entry
            entry = self._create_mapfile_entry(input_file)
            
            # Add entry to mapfile
            mapfile.add_entry(entry)
            
            # Mark as successful
            result.success = True
            
            return result
            
        except Exception as e:
            # For any unhandled exception, create a basic result with error
            return MapfileResult(
                input_file=FileInput(
                    source_path=file_path,
                    filename=file_path.name,
                    file_size=file_path.stat().st_size if file_path.exists() else 0,
                    project=self.project,
                    version=self.version
                ),
                success=False,
                error_message=str(e)
            )
    
    def process_directory(self, directory: Path) -> Iterator[MapfileResult]:
        """
        Process all eligible files in a directory.
        
        Args:
            directory: Directory to scan for files
            
        Yields:
            MapfileResult for each processed file
        """
        try:
            # Check if directory exists
            if not directory.exists() or not directory.is_dir():
                raise ValueError(f"Directory not found: {directory}")
            
            # Track visited symlinks to prevent infinite loops
            visited_symlinks: Set[Path] = set()
            
            # Walk through the directory
            for root, _, files in os.walk(directory):
                root_path = Path(root)
                
                # Process each file
                for file_name in files:
                    file_path = root_path / file_name
                    
                    # Skip if not a file
                    if not file_path.is_file():
                        continue
                    
                    # Handle symlinks
                    if file_path.is_symlink():
                        # Skip if already visited to prevent loops
                        if file_path in visited_symlinks:
                            continue
                        
                        # Record that we've seen this symlink
                        visited_symlinks.add(file_path)
                        
                        # Follow 'latest' symlinks if enabled
                        if "latest" in str(file_path) and not self.latest_symlink:
                            continue
                    
                    # Skip if doesn't match NetCDF pattern (can be customized)
                    if not file_name.endswith('.nc'):
                        continue
                    
                    # Skip if version filtering is enabled and doesn't match
                    if self.version and f"/v{self.version}" not in str(file_path) and not self.all_versions:
                        if not (self.latest_symlink and "/latest/" in str(file_path)):
                            continue
                    
                    # Process the file
                    yield self.process_file(file_path)
                    
        except Exception as e:
            # If the whole directory processing fails, yield an error result
            yield MapfileResult(
                input_file=FileInput(
                    source_path=directory,
                    file_size=0,
                    filename="",
                    project=self.project
                ),
                success=False,
                error_message=f"Failed to process directory: {e}"
            )
    
    def write_mapfiles(self) -> int:
        """
        Write all mapfiles to disk.
        
        Returns:
            int: Number of mapfiles written
        """
        count = 0
        for mapfile in self.mapfiles.values():
            try:
                mapfile.write()
                count += 1
            except Exception as e:
                print(f"Error writing mapfile {mapfile.path}: {e}")
        return count
    
    def _extract_dataset_info(self, file_path: Path) -> Optional[tuple[str, Optional[str]]]:
        """
        Extract dataset ID and version from a file path.
        
        This method is kept for backward compatibility. New code should use
        FileInput.dataset_id instead.
        
        Args:
            file_path: Path to the file
            
        Returns:
            tuple containing (dataset_id, version) or None if extraction fails
        """
        try:
            # Create a FileInput and use its dataset_id property
            input_file = self.create_file_input(file_path)
            dataset_id = input_file.dataset_id
            version = input_file.version
            
            # Extract version from the end of dataset_id if needed
            if not version and re.search(r'\.latest|\.v[0-9]*$', str(dataset_id)):
                version_part = dataset_id.split('.')[-1]
                if version_part.startswith('v'):
                    version = version_part[1:]  # Remove 'v' prefix
                    dataset_id = '.'.join(dataset_id.split('.')[:-1])
            
            return dataset_id, version
            
        except Exception as e:
            print(f"Error extracting dataset info: {e}")
            return None
    
    def _build_mapfile_path(self, dataset_id: str, version: Optional[str]) -> Path:
        """
        Build the path to the mapfile based on dataset ID and version.
        
        Args:
            dataset_id: Dataset identifier
            version: Dataset version
            
        Returns:
            Path to the mapfile
        """
        # Start with the template
        name = self.mapfile_name
        
        # Inject dataset name
        if '{dataset_id}' in name:
            name = name.replace('{dataset_id}', dataset_id)
        
        # Inject dataset version
        if '{version}' in name:
            if version:
                name = name.replace('{version}', version)
            else:
                name = name.replace('.{version}', '')
        
        # Inject date
        if '{date}' in name:
            name = name.replace('{date}', datetime.now().strftime("%Y%m%d"))
        
        # Inject job id
        if '{job_id}' in name:
            name = name.replace('{job_id}', str(os.getpid()))
        
        # Build full path
        return self.outdir / name
    
    def _get_or_create_mapfile(self, path: Path) -> Mapfile:
        """
        Get an existing mapfile or create a new one.
        
        Args:
            path: Path to the mapfile
            
        Returns:
            Mapfile object
        """
        path_str = str(path)
        if path_str not in self.mapfiles:
            # Create a new mapfile
            self.mapfiles[path_str] = Mapfile(path=path)
        
        return self.mapfiles[path_str]
    
    def _create_mapfile_entry(
        self, 
        input_file: FileInput
    ) -> MapfileEntry:
        """
        Create a mapfile entry for a file.
        
        Args:
            input_file: FileInput instance with file metadata
            
        Returns:
            MapfileEntry object
        """
        # Create the entry from the FileInput
        return MapfileEntry(
            dataset_id=input_file.dataset_id,
            version=input_file.version,
            path=input_file.source_path,
            size=input_file.file_size,
            mod_time=input_file.mod_time,
            checksum=input_file.checksum,
            checksum_type=input_file.checksum_type.upper() if input_file.checksum else None,
            tech_notes_url=self.tech_notes_url,
            tech_notes_title=self.tech_notes_title
        )
