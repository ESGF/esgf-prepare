"""
DRS Processor for handling DRS operations with improved structure.
"""

import os
import re
import shutil
from datetime import datetime
from pathlib import Path
from typing import Dict, Iterator, List, Optional, Union
from pydantic import ValidationError

from esgprep.drs.models import Dataset, DatasetVersion, DrsOperation, DrsResult, FileInput, MigrationMode

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
        - /root_dir/project/...path.../files/dXXXXXXXX/file.nc (original file)
        - /root_dir/project/...path.../vXXXXXXXX/file.nc (link to files/dXXXXXXXX/file.nc)
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

        # Version string from facets (e.g., 'v20250401')
        version_str = input_file.drs_facets.get("version", self.version)

        # Get the data version without the 'v' prefix (e.g., '20250401')
        data_version = version_str[1:] if version_str.startswith('v') else version_str

        # Compute the path to dataset directory (parent of version directory)
        dataset_dir = version_dir.parent

        # 1. Create the "files" directory structure
        files_dir = dataset_dir / "files"

        # Create data version folder (dXXXXXXXX) inside files folder
        data_dir = files_dir / f"d{data_version}"
        data_path = data_dir / destination_path.name

        # Operation to create files directory
        operations.append(DrsOperation(
            operation_type=MigrationMode.MOVE,  # Placeholder, just to create directory
            destination=files_dir,
            description="Create files directory"
        ))

        # Operation to create data version directory inside files
        operations.append(DrsOperation(
            operation_type=MigrationMode.MOVE,  # Placeholder, just to create directory
            destination=data_dir,
            description=f"Create d{data_version} directory inside files"
        ))

        # Operation to copy/link/move the original file to the data version directory
        operations.append(DrsOperation(
            operation_type=self.mode,
            source=input_file.source_path,
            destination=data_path,
            description=f"{self.mode} original file to files/d{data_version} directory"
        ))

        # 2. Create the version directory

        # Operation to create version directory
        operations.append(DrsOperation(
            operation_type=MigrationMode.MOVE,  # Placeholder, just to create directory
            destination=version_dir,
            description="Create version directory"
        ))

        # Operation to link from version directory to files/dXXXXXXXX directory
        operations.append(DrsOperation(
            operation_type=MigrationMode.SYMLINK,  # Always use symlink here
            source=data_path,
            destination=destination_path,
            description=f"Create symlink from version directory to files/d{data_version} directory"
        ))

        # 3. Create the "latest" symlink
        latest_dir = dataset_dir / "latest"
        latest_file = latest_dir / destination_path.name

        # Find all version directories to determine which is latest
        # Existing version directories
        version_dirs = [d for d in dataset_dir.glob("v*") if d.is_dir() and re.match(r"v\d{8}", d.name)]

        # Add current version to the list if not already there
        current_version_dir_exists = False
        for d in version_dirs:
            if d.name == version_dir.name:
                current_version_dir_exists = True
                break

        if not current_version_dir_exists:
            version_dirs.append(version_dir)

        # Sort by version string (descending) - this ensures proper comparison
        version_dirs.sort(key=lambda d: d.name, reverse=True)

        # Only create/update latest symlink if this version is the latest
        if version_dirs and version_dirs[0].name == version_dir.name:
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
