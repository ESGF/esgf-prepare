"""
This module handles the generation of Data Reference Syntax (DRS) directory structures
for various ESGF projects by dynamically adapting to project-specific requirements.
"""

import os
from datetime import datetime
from pathlib import Path
from typing import Dict, Iterator, List, Optional, Union
from pydantic import ValidationError

# Import the updated models
from esgprep.drs.models import Dataset, DatasetVersion, DrsOperation, DrsResult, FileInput, MigrationMode

# For Process class
import traceback
from esgprep.constants import FRAMES
from esgprep.drs.constants import SPINNER_DESC
from esgprep._utils.print import Print, COLORS, TAGS
from esgprep._handlers.constants import LINK_SEPARATOR

class Process:
    """
    Process class that's compatible with the multiprocessing framework.
    
    This implementation avoids serializing any objects that can't be pickled,
    and instead creates everything needed on demand in each worker process.
    """
    
    def __init__(self, ctx):
        """
        Initialize Process with the shared context.
        
        Args:
            ctx: Shared processing context between child processes
        """
        # Store only the necessary context properties
        self.root = ctx.root
        self.project = ctx.project
        self.mode = ctx.mode
        self.checksum_type = ctx.checksum_type
        self.upgrade_from_latest = ctx.upgrade_from_latest
        self.ignore_from_latest = ctx.ignore_from_latest
        self.ignore_from_incoming = ctx.ignore_from_incoming
        self.version = ctx.version
        self.set_values = ctx.set_values
        self.set_keys = ctx.set_keys
        
        # Store multiprocessing synchronization primitives
        self.lock = ctx.lock
        self.errors = ctx.errors
        self.msg_length = ctx.msg_length
        self.progress = ctx.progress
        self.tree = ctx.tree
        
        # Store frames for progress display
        self.FRAMES = FRAMES
    
    def __call__(self, source):
        """
        Process a single source file.
        
        Args:
            source: Source file path
            
        Returns:
            Result of processing (True for success, None for failure)
        """
        try:
            # Process file directly using file processing logic
            # without creating a DrsProcessor instance
            processed_result = self._process_file(source)
            
            # Return True for success, None for failure
            return processed_result
            
        except KeyboardInterrupt:
            with self.lock:
                self.errors.value += 1
            raise
            
        except Exception:
            with self.lock:
                self.errors.value += 1
                
                # Format & print exception traceback
                exc = traceback.format_exc().splitlines()
                msg = TAGS.SKIP + COLORS.HEADER(str(source)) + '\n'
                msg += '\n'.join(exc)
                Print.exception(msg, buffer=True)
            
            return None
            
        finally:
            with self.lock:
                # Update progress
                self.progress.value += 1
                
                # Update progress display
                msg = f"\r{' ' * self.msg_length.value}"
                Print.progress(msg)
                
                msg = f"\r{COLORS.OKBLUE(SPINNER_DESC)} {self.FRAMES[self.progress.value % len(self.FRAMES)]} {source}"
                Print.progress(msg)
                
                self.msg_length.value = len(msg)
    
    def _process_file(self, source):
        """
        Process a file directly without creating a DrsProcessor instance.
        
        This method contains the core logic for processing a file while
        avoiding any objects that can't be pickled.
        
        Args:
            source: Path to the file to process
            
        Returns:
            True for success, None for failure
        """
        try:
            # Convert source to Path if it's a string
            source_path = Path(source)
            
            # Get file attributes
            from esgprep._utils.ncfile import get_ncattrs
            try:
                attrs = get_ncattrs(str(source_path))
            except Exception as e:
                Print.error(f"Error getting NetCDF attributes: {e}")
                return None
            
            # Extract facets from attributes
            facets = self._extract_facets(attrs)
            
            # Add necessary facets
            facets['project'] = self.project
            facets['version'] = self.version
            
            # Generate DRS path
            drs_path = self._generate_drs_path(source_path, facets)
            if not drs_path:
                Print.error(f"Could not determine DRS path for {source_path}")
                return None
            
            # Check if file is a duplicate
            is_duplicate = self._check_duplicate(source_path, drs_path)
            
            # Generate operations
            operations = self._generate_operations(source_path, drs_path, is_duplicate)
            
            # Update DRS tree
            self._update_tree(source_path, drs_path, is_duplicate, operations)
            
            # Print success message
            Print.success(f"DRS Path = {drs_path.parent}")
            
            # Return success
            return True
            
        except Exception as e:
            Print.error(f"Error processing file {source}: {e}")
            return None
    
    def _extract_facets(self, attrs):
        """Extract facets from file attributes."""
        # Implementation depends on project
        facets = {}
        
        # Apply set_values overrides
        if self.set_values:
            facets.update(self.set_values)
        
        # Extract from attributes using set_keys mappings
        if self.set_keys:
            for facet, attr_name in self.set_keys.items():
                if attr_name in attrs:
                    facets[facet] = attrs[attr_name]
        
        # Extract common facets based on project
        if self.project.lower() == "cmip6":
            # Try to extract CMIP6-specific facets
            for attr, facet in [
                ("mip_era", "mip_era"),
                ("activity_id", "activity_id"),
                ("institution_id", "institution_id"),
                ("source_id", "source_id"),
                ("experiment_id", "experiment_id"),
                ("variant_label", "member_id"),
                ("table_id", "table_id"),
                ("variable_id", "variable_id"),
                ("grid_label", "grid_label")
            ]:
                if attr in attrs and facet not in facets:
                    facets[facet] = attrs[attr]
        
        return facets
    
    def _generate_drs_path(self, source_path, facets):
        """Generate DRS path using facets."""
        # Implementation depends on project
        if self.project.lower() == "cmip6":
            # Generate path for CMIP6
            try:
                path_parts = [
                    facets.get("mip_era", "cmip6").lower(),
                    facets.get("activity_id", "unknown_activity"),
                    facets.get("institution_id", "unknown_institution"),
                    facets.get("source_id", "unknown_source"),
                    facets.get("experiment_id", "unknown_experiment"),
                    facets.get("member_id", "unknown_member"),
                    facets.get("table_id", "unknown_table"),
                    facets.get("variable_id", "unknown_variable"),
                    facets.get("grid_label", "unknown_grid"),
                    facets.get("version", self.version)
                ]
                
                return Path(self.root).joinpath(*path_parts) / source_path.name
            except Exception as e:
                Print.error(f"Error generating CMIP6 path: {e}")
                return None
        else:
            # Generic implementation for other projects
            # Build path including all available facets, with project and version
            # at the beginning and end respectively
            path_parts = [self.project.lower()]
            
            # Add all facets except project and version
            for key, value in facets.items():
                if key not in ['project', 'version']:
                    path_parts.append(value)
            
            # Add version at the end
            path_parts.append(facets.get('version', self.version))
            
            return Path(self.root).joinpath(*path_parts) / source_path.name
    
    def _check_duplicate(self, source_path, destination_path):
        """Check if the file is a duplicate of an existing file."""
        # If destination doesn't exist, it's not a duplicate
        if not destination_path.exists():
            return False
        
        # Check file sizes
        if source_path.stat().st_size != destination_path.stat().st_size:
            return False
        
        # Check checksums if enabled
        if self.checksum_type:
            try:
                from esgprep._utils.checksum import get_checksum
                source_checksum = get_checksum(str(source_path), self.checksum_type)
                dest_checksum = get_checksum(str(destination_path), self.checksum_type)
                return source_checksum == dest_checksum
            except Exception as e:
                Print.error(f"Error comparing checksums: {e}")
                return False
        
        # If we get here, sizes match and checksumming isn't enabled
        return True
    
    def _generate_operations(self, source_path, destination_path, is_duplicate):
        """Generate file operations for the DRS tree."""
        operations = []
        
        # If duplicate and not upgrading from latest
        if is_duplicate and not self.upgrade_from_latest:
            if self.mode == "move":
                # Add operation to remove the source file
                operations.append({
                    "operation_type": "remove",
                    "source": source_path,
                    "destination": source_path,
                    "description": "Remove duplicate source file"
                })
            return operations
        
        # Extract path components
        destination_parent = destination_path.parent  # Version directory
        dataset_dir = destination_parent.parent       # Dataset directory
        
        # 1. Files directory
        files_dir = dataset_dir / "files"
        files_path = files_dir / destination_path.name
        
        # Add operations for files directory
        operations.append({
            "operation_type": "move",  # Just to create directory
            "source": None,
            "destination": files_dir,
            "description": "Create files directory"
        })
        
        operations.append({
            "operation_type": self.mode,
            "source": source_path,
            "destination": files_path,
            "description": f"{self.mode} original file to files directory"
        })
        
        # 2. Version directory
        operations.append({
            "operation_type": "move",  # Just to create directory
            "source": None,
            "destination": destination_parent,
            "description": "Create version directory"
        })
        
        operations.append({
            "operation_type": "symlink",
            "source": files_path,
            "destination": destination_path,
            "description": "Create symlink from version directory to files directory"
        })
        
        # 3. Latest directory
        latest_dir = dataset_dir / "latest"
        latest_path = latest_dir / destination_path.name
        
        operations.append({
            "operation_type": "move",  # Just to create directory
            "source": None,
            "destination": latest_dir,
            "description": "Create latest directory"
        })
        
        operations.append({
            "operation_type": "symlink",
            "source": destination_path,
            "destination": latest_path,
            "description": "Create symlink from latest directory to version file"
        })
        
        return operations
    
    def _update_tree(self, source_path, destination_path, is_duplicate, operations):
        """Update the DRS tree with operations."""
        if not self.tree:
            return
            
        try:
            # Extract key path components
            dataset_path = destination_path.parent.parent
            version_path = destination_path.parent
            version = version_path.name
            
            # Create leaf for the file in the tree
            nodes = str(destination_path).split('/')
            label = f"{destination_path.name}{LINK_SEPARATOR}{source_path}"
            
            self.tree.create_leaf(
                nodes=nodes,
                label=label,
                src=str(source_path),
                mode=self.mode,
                force=True
            )
            
            # Record entry for list() and uniqueness checkup
            record = {
                'src': source_path,
                'dst': destination_path,
                'is_duplicate': is_duplicate
            }
            
            # Add to tree paths
            key = str(dataset_path)
            if key in self.tree.paths:
                self.tree.append_path(key, "files", record)
                # Update latest if needed
                if 'latest' not in self.tree.paths[key]:
                    self.tree.paths[key]['latest'] = 'Initial'
                # Update upgrade if needed
                if 'upgrade' not in self.tree.paths[key]:
                    self.tree.paths[key]['upgrade'] = version
            else:
                # Create new entry
                infos = {"files": [record], "latest": 'Initial', "upgrade": version}
                self.tree.add_path(key, infos)
                
        except Exception as e:
            Print.warning(f"Could not update DRS tree: {e}")
class DrsProcessor:
    """
    Processes files according to the DRS using project-specific configurations.
    
    This enhanced processor leverages the FileInput model's ability to determine
    its own DRS path, making the code more modular and cohesive.
    """
    
    def __init__(
        self,
        root_dir: Union[str, Path],
        project: str = "cmip6",
        mode: str = "move",
        checksum_type: Optional[str] = "sha256",
        upgrade_from_latest: bool = False,
        ignore_from_latest: List[str] | None = None,
        ignore_from_incoming: List[str] | None = None,
        version: str | None = None,
        set_values: Dict[str, str] | None = None,
        set_keys: Dict[str, str] | None = None,
    ):
        """
        Initialize the DRS processor with project-specific configuration.
        
        Args:
            root_dir: Base directory for the DRS structure
            project: Project identifier (e.g., 'cmip6', 'cordex')
            mode: Migration mode ('move', 'copy', 'link', 'symlink')
            checksum_type: Type of checksum to use, or None to disable checksumming
            upgrade_from_latest: Whether to base upgrades on the latest version
            ignore_from_latest: List of filenames to ignore from latest version
            ignore_from_incoming: List of filenames to ignore from incoming files
            version: Version string to use (default: current date in vYYYYMMDD format)
            set_values: Dictionary of facet values to override detected values
            set_keys: Dictionary mapping facet keys to attribute names
        """
        self.root_dir = Path(root_dir) if not isinstance(root_dir, Path) else root_dir
        self.project = project.lower()  # Normalize to lowercase
        self.mode = MigrationMode(mode)
        self.checksum_type = checksum_type
        self.upgrade_from_latest = upgrade_from_latest
        self.ignore_from_latest = ignore_from_latest or []
        self.ignore_from_incoming = ignore_from_incoming or []
        self.version = version or f"v{datetime.now().strftime('%Y%m%d')}"
        self.set_values = set_values or {}
        self.set_keys = set_keys or {}
        
        # Apply set_values override for version if provided
        if 'version' not in self.set_values:
            self.set_values['version'] = self.version
        
        # Track processed datasets for reporting
        self.datasets: Dict[str, Dataset] = {}
    
    def create_file_input(self, file_path: Path) -> FileInput:
        """
        Create a FileInput instance from a file path with project-specific processing.
        
        Args:
            file_path: Path to the source file
            
        Returns:
            FileInput model instance
        """
        # Import utilities with error handling
        try:
            from esgprep._utils.ncfile import get_ncattrs, get_tracking_id
            
            # Get file attributes
            try:
                attrs = get_ncattrs(str(file_path))
            except Exception as e:
                print(f"Warning: Error getting NetCDF attributes: {e}")
                attrs = {}  # Use empty dict if attributes can't be read
                
            # Add filename for parsing
            attrs["filename"] = file_path.name
            
            # Create the basic FileInput model with minimal information
            input_file = FileInput(
                source_path=file_path,
                filename=file_path.name,
                file_size=file_path.stat().st_size,
                project=self.project,
                root_dir=self.root_dir,
                attributes=attrs,
                version=self.version,
                ignored=file_path.name in self.ignore_from_incoming
            )
            
            # Update facets with provided values and from attributes
            input_file.update_facets(self.set_values, self.set_keys)
            
            # Try to get tracking ID
            try:
                input_file.tracking_id = get_tracking_id(attrs) if "tracking_id" in attrs else None
            except Exception:
                input_file.tracking_id = f"hdl:21.14100/test-{datetime.now().timestamp()}"
            
            return input_file
            
        except ValidationError as e:
            print(f"Error creating FileInput for {file_path}: {e}")
            # Create a minimal valid instance
            return FileInput(
                source_path=file_path,
                filename=file_path.name,
                file_size=file_path.stat().st_size if file_path.exists() else 0,
                project=self.project,
                version=self.version,
            )
        except Exception as e:
            print(f"Unexpected error creating FileInput: {e}")
            # Create a minimal valid instance for testing
            return FileInput(
                source_path=file_path,
                filename=file_path.name,
                file_size=file_path.stat().st_size if file_path.exists() else 0,
                project=self.project,
                version=self.version,
            )
    
    def process_file(self, file_path: Path) -> DrsResult:
        """
        Process a single file according to the DRS.
        
        Args:
            file_path: Path to the file to process
            
        Returns:
            DrsResult: Result of the processing operation
        """
        try:
            # Check if the file should be ignored
            if file_path.name in self.ignore_from_incoming:
                return DrsResult(
                    input_file=FileInput(
                        source_path=file_path,
                        filename=file_path.name,
                        file_size=file_path.stat().st_size,
                        project=self.project,
                        version=self.version,
                        ignored=True
                    ),
                    success=False,
                    error_message=f"File ignored: {file_path.name} in ignore_from_incoming list"
                )
            
            # Create the file input model
            input_file = self.create_file_input(file_path)
            
            # Calculate checksum if needed
            if self.checksum_type:
                try:
                    from esgprep._utils.checksum import get_checksum
                    input_file.checksum = get_checksum(str(file_path), self.checksum_type)
                    input_file.checksum_type = self.checksum_type
                except Exception as e:
                    print(f"Error calculating checksum: {e}")
            
            # Get the destination path using the FileInput's drs_path property
            destination_path = input_file.drs_path
            if not destination_path:
                return DrsResult(
                    input_file=input_file,
                    success=False,
                    error_message=f"Could not determine DRS path for {file_path}"
                )
            
            # Check if this is a duplicate of an existing file
            is_duplicate = self._check_duplicate(input_file, destination_path)
            input_file.is_duplicate = is_duplicate
            
            # Create or update dataset
            dataset_id = input_file.dataset_id
            if dataset_id not in self.datasets:
                self.datasets[dataset_id] = Dataset(
                    dataset_id=dataset_id,
                    facets=input_file.drs_facets
                )
            
            # Find or create the version
            dataset = self.datasets[dataset_id]
            version = next(
                (v for v in dataset.versions if v.version_id == self.version), 
                None
            )
            
            if not version:
                version = DatasetVersion(
                    version_id=self.version,
                    path=destination_path.parent,
                    is_latest=True  # Would be determined based on existing versions
                )
                dataset.versions.append(version)
            
            # Record the file in the version
            if destination_path not in version.files:
                version.files.append(destination_path)
            
            # Generate operations
            operations = self._generate_operations(input_file, destination_path, is_duplicate)
            
            # Create and return the result
            return DrsResult(
                input_file=input_file,
                operations=operations,
                success=True,
                dataset=dataset
            )
            
        except Exception as e:
            # Handle any exceptions with better error reporting
            print(f"Error processing file {file_path}: {e}")
            return DrsResult(
                input_file=FileInput(
                    source_path=file_path,
                    filename=file_path.name,
                    file_size=file_path.stat().st_size if file_path.exists() else 0,
                    project=self.project,
                    version=self.version,
                ),
                success=False,
                error_message=f"Error processing file: {str(e)}"
            )
    
    def process_directory(self, directory: Path) -> Iterator[DrsResult]:
        """
        Process all eligible files in a directory.
        
        Args:
            directory: Directory to scan for files
            
        Yields:
            DrsResult for each processed file
        """
        # Find all NetCDF files in the directory
        for root, _, files in os.walk(directory):
            for file in files:
                if file.endswith('.nc'):  # Would use more sophisticated filtering
                    file_path = Path(root) / file
                    yield self.process_file(file_path)
    
    def _check_duplicate(self, input_file: FileInput, destination_path: Path) -> bool:
        """
        Check if a file is a duplicate of an existing file.
        
        Args:
            input_file: File input model
            destination_path: Destination path in the DRS
            
        Returns:
            bool: True if the file is a duplicate
        """
        try:
            # Check if the file already exists
            if not destination_path.exists():
                return False
            
            # Check file size
            if destination_path.stat().st_size != input_file.file_size:
                return False
            
            # Check checksum if available
            if input_file.checksum and input_file.checksum_type:
                try:
                    from esgprep._utils.checksum import get_checksum
                    existing_checksum = get_checksum(
                        str(destination_path), 
                        input_file.checksum_type
                    )
                    return existing_checksum == input_file.checksum
                except Exception as e:
                    print(f"Error comparing checksums: {e}")
                    return False
            
            return True
        except Exception as e:
            print(f"Error checking for duplicate: {e}")
            return False
    
    def _generate_operations(
        self, 
        input_file: FileInput, 
        destination_path: Path,
        is_duplicate: bool
    ) -> List[DrsOperation]:
        """
        Generate the operations needed to place the file in the DRS structure.
        
        The DRS structure will be:
        - /root_dir/project/...path.../files/file.nc (original file)
        - /root_dir/project/...path.../vXXXXXXXX/file.nc (link to original)
        - /root_dir/project/...path.../latest/file.nc (link to latest version)
        
        Args:
            input_file: File input model
            destination_path: Destination path in the version directory
            is_duplicate: Whether the file is a duplicate
            
        Returns:
            List of operations to perform
        """
        operations = []
        
        # If the file is a duplicate and we're not upgrading from latest,
        # we may need to remove the source file but don't add it to the DRS
        if is_duplicate and not self.upgrade_from_latest:
            if self.mode == MigrationMode.MOVE:
                # Add operation to remove the duplicate source file
                operations.append(DrsOperation(
                    operation_type=MigrationMode.REMOVE,
                    source=input_file.source_path,
                    destination=input_file.source_path,
                    description="Remove duplicate source file"
                ))
            return operations
        
        # Extract path components for DRS operations
        
        # Get project name
        project = input_file.project.lower()
        
        # Path to version directory (parent of destination file)
        version_dir = destination_path.parent
        
        # Version string from facets
        version_str = input_file.drs_facets.get("version", self.version)
        
        # Compute the path to dataset directory (parent of version directory)
        dataset_dir = version_dir.parent
        
        # 1. Create the "files" directory structure
        files_dir = dataset_dir / "files"
        files_path = files_dir / destination_path.name
        
        # Operation to create files directory
        operations.append(DrsOperation(
            operation_type=MigrationMode.MOVE,  # Placeholder, just to create directory
            destination=files_dir,
            description="Create files directory"
        ))
        
        # Operation to copy the original file to files directory
        operations.append(DrsOperation(
            operation_type=MigrationMode.COPY,
            source=input_file.source_path,
            destination=files_path,
            description=f"{self.mode} original file to files directory"
        ))
        
        # 2. Create the version directory
        
        # Operation to create version directory
        operations.append(DrsOperation(
            operation_type=MigrationMode.MOVE,  # Placeholder, just to create directory
            destination=version_dir,
            description="Create version directory"
        ))
        
        # Operation to link from version directory to files directory
        operations.append(DrsOperation(
            operation_type=self.mode,
            source=files_path,   
            destination=destination_path,
            description="Create symlink from version directory to files directory"
        ))
        
        # 3. Create the "latest" symlink
        latest_dir = dataset_dir / "latest"
        latest_file = latest_dir / destination_path.name
        
        # Operation to create latest directory
        operations.append(DrsOperation(
            operation_type=MigrationMode.MOVE,  # Placeholder, just to create directory
            destination=latest_dir,
            description="Create latest directory"
        ))
        
        # Operation to link from latest directory to version directory file
        operations.append(DrsOperation(
            operation_type=MigrationMode.SYMLINK,
            source=destination_path,  # Link to the version file
            destination=latest_file,
            description="Create symlink from latest directory to version file"
        ))
        
        return operations

    def execute_operations(self, operations: List[DrsOperation]) -> bool:
        """
        Execute the given DRS operations.
        
        This method performs the actual file operations based on the
        operations generated during processing.
        
        Args:
            operations: List of operations to perform
            
        Returns:
            bool: True if all operations succeeded
        """
        # Import here for better error handling
        import os
        import shutil
        
        for i, operation in enumerate(operations):
            try:
                print(f"Executing operation {i+1}: {operation.description or operation.operation_type}")
                
                # Always ensure parent directories exist for any destination
                if operation.destination:
                    os.makedirs(operation.destination.parent, exist_ok=True)
                    
                if operation.operation_type == MigrationMode.MOVE:
                    if operation.source:
                        # Move the file
                        try:
                            # Use shutil.move for better cross-device handling
                            shutil.move(str(operation.source), str(operation.destination))
                        except OSError as e:
                            print(f"Error moving file: {e}")
                            # Fallback to copy+delete if move fails
                            shutil.copy2(str(operation.source), str(operation.destination))
                            os.unlink(str(operation.source))
                    # If no source, the operation is just to create a directory
                    elif operation.destination:
                        os.makedirs(operation.destination, exist_ok=True)
                        
                elif operation.operation_type == MigrationMode.COPY:
                    if operation.source:
                        # Copy the file
                        shutil.copy2(str(operation.source), str(operation.destination))
                    
                elif operation.operation_type == MigrationMode.LINK:
                    if operation.source:
                        # Create hard link
                        try:
                            os.link(str(operation.source), str(operation.destination))
                        except OSError as e:
                            print(f"Error creating hard link: {e}")
                            # Fall back to copy if hard link fails
                            print("Falling back to copy since hard link failed")
                            shutil.copy2(str(operation.source), str(operation.destination))
                    
                elif operation.operation_type == MigrationMode.SYMLINK:
                    if operation.source:
                        # Create symlink
                        if operation.destination.exists():
                            if operation.destination.is_symlink():
                                operation.destination.unlink()
                            else:
                                print(f"Cannot create symlink, destination exists and is not a symlink: {operation.destination}")
                                continue
                        
                        try:
                            # Get the relative path from destination to source
                            rel_path = os.path.relpath(str(operation.source), str(operation.destination.parent))
                            os.symlink(rel_path, str(operation.destination))
                        except OSError as e:
                            print(f"Error creating symlink: {e}")                    
                
                elif operation.operation_type == MigrationMode.REMOVE:
                    if operation.source and operation.source.exists():
                        try:
                            os.unlink(str(operation.source))
                        except OSError as e:
                            print(f"Error removing file: {e}")
                
                print("  Operation completed successfully")
            except Exception as e:
                print(f"Error executing operation: {e}")
                return False
        
        return True


# Helper functions for integration with existing code

def determine_migration_mode(args) -> str:
    """
    Determine the migration mode from the command-line arguments.
    
    Args:
        args: Parsed command-line arguments
        
    Returns:
        Migration mode string ('move', 'copy', 'link', 'symlink')
    """
    # Default is 'move'
    mode = 'move'
    
    # Check for explicit mode flags
    if getattr(args, 'copy', False):
        mode = 'copy'
    elif getattr(args, 'link', False):
        mode = 'link'
    elif getattr(args, 'symlink', False):
        mode = 'symlink'
    
    # If cmd is set and not 'make', use that (for 'remove', etc.)
    if hasattr(args, 'cmd') and args.cmd != 'make':
        mode = args.cmd
        
    return mode


# Function to integrate with existing esgdrs command
def process_esgdrs_command(args) -> int:
    """Process ESGDRS command using the enhanced DrsProcessor."""
    try:
        # Create processor with arguments
        processor = DrsProcessor(
            root_dir=Path(args.root),
            project=args.project,
            mode=determine_migration_mode(args),
            checksum_type=None if getattr(args, 'no_checksum', False) else "sha256",
            upgrade_from_latest=getattr(args, 'upgrade_from_latest', False),
            ignore_from_latest=[line.strip() for line in getattr(args, 'ignore_from_latest', []) or []],
            ignore_from_incoming=[line.strip() for line in getattr(args, 'ignore_from_incoming', []) or []],
            version=getattr(args, 'version', None),
            set_values=dict(args.set_value) if getattr(args, 'set_value', None) else {},
            set_keys=dict(args.set_key) if getattr(args, 'set_key', None) else {}
        )
        
        # Process files from directory
        results = []
        for directory in args.directory:
            results.extend(list(processor.process_directory(Path(directory))))
        
        # Report results
        success_count = sum(1 for r in results if r.success)
        print(f"Processed {len(results)} files: {success_count} succeeded, {len(results) - success_count} failed")
        
        # If action is 'upgrade', execute operations
        if getattr(args, 'action', '') == 'upgrade':
            operations = []
            for result in results:
                if result.success:
                    operations.extend(result.operations)
            
            success = processor.execute_operations(operations)
            if success:
                print("All operations completed successfully")
            else:
                print("Some operations failed")
                return 1
        
        # Return success if no errors
        return 0 if success_count == len(results) else 1
        
    except Exception as e:
        print(f"Error processing command: {e}")
        return 1
