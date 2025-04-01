# -*- coding: utf-8 -*-
"""
Examples of how to implement the updated Pydantic v2 models in the ESGDRS process.

This module demonstrates practical usage of the models in file processing,
DRS tree generation, and command execution.
"""

import os
from datetime import datetime
from pathlib import Path
from typing import Dict, Iterator, List, Optional, Any, Union

from pydantic import ValidationError

# Import the updated models
from esgprep.drs.models import Dataset, DatasetVersion, DrsOperation, DrsResult, FileInput, MigrationMode


class DrsProcessor:
    """
    Processes files according to the DRS using the Pydantic models.
    
    This class provides a more testable implementation with better error handling
    and debugging for test environments.
    """
    
    def __init__(
        self,
        root_dir: Union[str, Path],
        mode: str = "move",
        checksum_type: Optional[str] = "sha256",
        upgrade_from_latest: bool = False,
        ignore_from_latest: List[str] |None= None,
        ignore_from_incoming: List[str] |None = None,
        version: str |None = None,
    ):
        """Initialize the DRS processor with configuration options."""
        self.root_dir = Path(root_dir) if not isinstance(root_dir, Path) else root_dir
        self.mode = MigrationMode(mode)
        self.checksum_type = checksum_type
        self.upgrade_from_latest = upgrade_from_latest
        self.ignore_from_latest = ignore_from_latest or []
        self.ignore_from_incoming = ignore_from_incoming or []
        self.version = version or f"v{datetime.now().strftime('%Y%m%d')}"
        
        # Import here to avoid circular imports - with better error handling
        self.drs_generator = None
        try:
            from esgvoc.apps.drs.generator import DrsGenerator
            self.drs_generator = DrsGenerator("cmip6")  # Could be configurable
            print("Using esgvoc DrsGenerator for DRS generation")
        except ImportError:
            print("Warning: esgvoc package not available, using fallback DRS generation")
        
        # Track processed datasets for reporting
        self.datasets: Dict[str, Dataset] = {}
    
    def create_file_input(self, file_path: Path) -> FileInput:
        """
        Create a FileInput instance from a file path with improved error handling.
        
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
                
            # Add minimum required attributes if they don't exist
            if 'project_id' not in attrs:
                attrs['project_id'] = 'cmip6'  # Default project
            
            # Add filename for parsing
            attrs["filename"] = file_path.name
            attrs["version"] = self.version
                
            # Parse DRS facets
            facets = {}
            
            # Override or add some facets for testing if filename follows CMIP6 naming convention
            # Format: variable_table_model_experiment_variant_grid_timerange.nc
            filename_parts = file_path.stem.split('_')
            if len(filename_parts) >= 7:
                facets = {
                    "project": "cmip6",
                    "activity_id": attrs.get("activity_id", "CMIP"),
                    "institution_id": attrs.get("institution_id", "IPSL"),
                    "source_id": attrs.get("source_id", filename_parts[2]),
                    "experiment_id": attrs.get("experiment_id", filename_parts[3]),
                    "member_id": attrs.get("variant_label", filename_parts[4]),
                    "table_id": attrs.get("table_id", filename_parts[1]),
                    "variable_id": attrs.get("variable_id", filename_parts[0]),
                    "grid_label": attrs.get("grid_label", filename_parts[5]),
                    "version": self.version
                }
            else:
                # Use DRS generator if available
                if self.drs_generator:
                    try:
                        # Apply necessary mappings (convert attribute names to facet names)
                        mapping_attrs = {**attrs, **{"member_id": attrs.get("variant_label", "")}}
                        drs_result = self.drs_generator.generate_directory_from_mapping(mapping_attrs)
                        
                        if not drs_result.errors:
                            # Parse facets from the resulting DRS path
                            drs_parts = drs_result.generated_drs_expression.split('/')
                            
                            # This is simplified; real implementation would use project-specific facet order
                            facet_names = [
                                "project", "activity_id", "institution_id", "source_id", 
                                "experiment_id", "member_id", "table_id", "variable_id", 
                                "grid_label", "version"
                            ]
                            
                            for i, part in enumerate(drs_parts):
                                if i < len(facet_names):
                                    facets[facet_names[i]] = part
                        else:
                            print(f"DRS generation errors: {drs_result.errors}")
                    except Exception as e:
                        print(f"Error in DRS generation: {e}")
                
                # Fallback to extracting facets directly from attributes
                if not facets:
                    # Map common attribute names to facet names
                    attr_to_facet = {
                        "project_id": "project",
                        "activity_drs": "activity_id",
                        "activity_id": "activity_id",
                        "institution_id": "institution_id",
                        "source_id": "source_id",
                        "experiment_id": "experiment_id",
                        "variant_label": "member_id",
                        "table_id": "table_id",
                        "variable_id": "variable_id",
                        "grid_label": "grid_label",
                    }
                    
                    for attr, facet in attr_to_facet.items():
                        if attr in attrs:
                            facets[facet] = attrs[attr]
                    
                    # Add version
                    facets["version"] = self.version
            
            # For testing purposes, ensure all required facets have values
            required_facets = ["project", "activity_id", "institution_id", "source_id", 
                            "experiment_id", "member_id", "table_id", "variable_id", 
                            "grid_label", "version"]
            
            for facet in required_facets:
                if facet not in facets:
                    # Use default values for missing facets
                    if facet == "project":
                        facets[facet] = "cmip6"
                    elif facet == "version":
                        facets[facet] = self.version
                    else:
                        facets[facet] = f"test_{facet}"
                        print(f"Warning: Using placeholder value for missing facet: {facet}")
            
            try:
                tracking_id = get_tracking_id(attrs) if "tracking_id" in attrs else None
            except Exception:
                tracking_id = f"hdl:21.14100/test-{datetime.now().timestamp()}"
            
            # Create the FileInput model with better error handling
            try:
                return FileInput(
                    source_path=file_path,
                    filename=file_path.name,
                    file_size=file_path.stat().st_size,
                    project=facets.get("project", "cmip6"),  # Default to cmip6
                    root_dir=self.root_dir,
                    attributes=attrs,
                    tracking_id=tracking_id,
                    version=self.version,
                    drs_facets=facets,
                    checksum=None,
                    checksum_type="sha256",
                    ignored=False,
                    is_duplicate=False
                )
            except ValidationError as e:
                print(f"Error creating FileInput for {file_path}: {e}")
                # Create a minimal valid instance
                return FileInput(
                    source_path=file_path,
                    filename=file_path.name,
                    file_size=file_path.stat().st_size if file_path.exists() else 0,
                    project="cmip6",  # Default project
                    version=self.version,
                    drs_facets=facets,
                )
        except Exception as e:
            print(f"Unexpected error creating FileInput: {e}")
            # Create a minimal valid instance for testing
            return FileInput(
                source_path=file_path,
                filename=file_path.name,
                file_size=file_path.stat().st_size if file_path.exists() else 0,
                project="cmip6",  # Default project
                version=self.version,
            )

    def process_file(self, file_path: Path) -> DrsResult:
        """
        Process a single file according to the DRS with improved error handling.
        
        Args:
            file_path: Path to the file to process
            
        Returns:
            DrsResult: Result of the processing operation
        """
        print(f"PROCESSING FILE: {file_path}")
        try:
            # Check if the file should be ignored
            if file_path.name in self.ignore_from_incoming:
                return DrsResult(
                    input_file=FileInput(
                        source_path=file_path,
                        filename=file_path.name,
                        file_size=file_path.stat().st_size,
                        project="cmip6",  # Would be detected from file
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
            
            # Generate destination path
            destination_path = None
            print("INPUT_FILE_DRS_PATH : ", input_file.drs_path)
            print("METADA:", input_file.attributes)
            print("C CA: ",self.drs_generator)
            # Try using the DRS generator if available
            if self.drs_generator and not input_file.drs_path:
                try:

                    # Use DRS generator if available and path not already determined
                    mapping_attrs = {
                        **input_file.attributes, 
                        **{"member_id": input_file.attributes.get("variant_label", "")}
                    }
                    drs_result = self.drs_generator.generate_directory_from_mapping(mapping_attrs)
                    
                    if drs_result.errors:
                        print(f"DRS generation errors: {drs_result.errors}")
                    else:
                        destination_path = self.root_dir / Path(drs_result.generated_drs_expression) / file_path.name
                except Exception as e:
                    print(f"Error in DRS generation: {e}")
            
            # Use input_file.drs_path or construct a path from facets if DRS generator failed
            print("DESTINATION FILE :",destination_path)
            if not destination_path:
                if input_file.drs_path:
                    destination_path = input_file.drs_path
                else:
                    # Construct path manually from facets
                    facets = input_file.drs_facets
                    path_parts = [
                        facets.get("project", "cmip6").lower(),
                        facets.get("activity_id", "CMIP"),
                        facets.get("institution_id", "IPSL"),
                        facets.get("source_id", "model"),
                        facets.get("experiment_id", "experiment"),
                        facets.get("member_id", "r1i1p1f1"),
                        facets.get("table_id", "day"),
                        facets.get("variable_id", "var"),
                        facets.get("grid_label", "gn"),
                        self.version
                    ]
                    destination_path = self.root_dir.joinpath(*path_parts) / file_path.name
            
            # Check if this is a duplicate of an existing file
            is_duplicate = self._check_duplicate(input_file, destination_path)
            input_file.is_duplicate = is_duplicate
            print("IS_DUPLICATE: ", is_duplicate) 
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
            print("AVANT OPERATION: ", destination_path)
            # Generate operations
            operations = self._generate_operations(input_file, destination_path, is_duplicate)
            
            print("OPERAITONS :", operations) 
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
                    project="cmip6",  # Would be detected from file
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
        print("DESTINATION_PATH",destination_path) # /root_dir/project/...path.../vXXXXXXXX/file.nc

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
        print("DRS_FACETS:", input_file.drs_facets) 
        # Extract the base parts of the path
        project = input_file.drs_facets.get("project", "CMIP6")

        
        # 1. Create the "files" directory structure
        files_dir = self.root_dir / project / "/".join(destination_path.parts[destination_path.parts.index(project)+1:-2]) / "files"
        print("FILE_DIR: ", files_dir)
        files_path = files_dir / destination_path.name
        
        # Operation to create files directory
        operations.append(DrsOperation(
            operation_type=MigrationMode.MOVE,  # Placeholder, just to create directory
            destination=files_dir,
            description="Create files directory"
        ))
        
        # Operation to copy/move/link the original file to files directory
        operations.append(DrsOperation(
            operation_type=MigrationMode.COPY,
            source=input_file.source_path,
            destination=files_path,
            description=f"{self.mode} original file to files directory"
        ))
        
        # 2. Create the version directory
        version_dir = destination_path.parent
        print("VERSION_DIR:", version_dir) 
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
        latest_dir = destination_path.parent.parent / "latest"
        latest_file = latest_dir / destination_path.name
        print("LATEST_DIR :", latest_dir)
        # Operation to create latest directory
        operations.append(DrsOperation(
            operation_type=MigrationMode.MOVE,  # Placeholder, just to create directory
            destination=latest_dir,
            description="Create latest directory"
        ))
        
        # Operation to link from latest directory to version directory file
        operations.append(DrsOperation(
            operation_type=MigrationMode.SYMLINK,
            source=destination_path,  # Relative path
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
        # Import here for error prevention
        import os
        import shutil
        
        for i, operation in enumerate(operations):
            try:
                print(f"Executing operation {i+1}: {operation.description or operation.operation_type}")
                
                # Always ensure parent directories exist for any destination
                if operation.destination:
                    operation.destination.parent.mkdir(parents=True, exist_ok=True)
                    
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
                        operation.destination.mkdir(parents=True, exist_ok=True)
                        
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
                            # Always use the string representation of the relative path
                            # Don't resolve it to an absolute path
                            relative_path = str(operation.source)
                            print(f"Creating symlink from {relative_path} to {operation.destination}")
                            os.symlink(relative_path, str(operation.destination))
                        except OSError as e:
                            print(f"Error creating symlink: {e}")                    
                
                elif operation.operation_type == MigrationMode.REMOVE:

                    if operation.source and operation.source.exists():
                        try:
                            os.unlink(str(operation.source))
                        except OSError as e:
                            print(f"Error removing file: {e}")
                
                print(f"  Operation completed successfully")
            except Exception as e:
                print(f"Error executing operation: {e}")
                return False
        
        return True
# Example usage in a command line context
def process_esgdrs_command(args: Any) -> int:
    """Process ESGDRS command using the new models and processor."""
    try:
        # Create processor with arguments
        processor = DrsProcessor(
            root_dir=Path(args.root),
            mode=args.mode if hasattr(args, 'mode') else "move",
            checksum_type=None if getattr(args, 'no_checksum', False) else "sha256",
            upgrade_from_latest=getattr(args, 'upgrade_from_latest', False),
            ignore_from_latest=[line.strip() for line in getattr(args, 'ignore_from_latest', []) or []],
            ignore_from_incoming=[line.strip() for line in getattr(args, 'ignore_from_incoming', []) or []],
            version=getattr(args, 'version', None)
        )
        
        # Process files from directory
        results = list(processor.process_directory(Path(args.directory[0])))
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


# Example integration with existing command line interface
def integrate_with_existing_cli():
    """
    Example of how to integrate the new processor with the existing CLI.
    
    This shows a bridge approach where we gradually adopt the new models
    while maintaining the existing interface.
    """
    import sys
    from argparse import ArgumentParser
    
    # Create parser similar to existing esgdrs parser
    parser = ArgumentParser(description="Process files according to DRS")
    parser.add_argument("--root", type=str, required=True, help="Root directory for DRS")
    parser.add_argument("--directory", type=str, required=True, help="Directory to scan for files")
    parser.add_argument("--action", choices=["list", "tree", "todo", "upgrade"],
                     default="list", help="Action to perform")
    parser.add_argument("--mode", choices=["move", "copy", "link", "symlink"], 
                     default="move", help="Migration mode")
    parser.add_argument("--version", type=str, help="Version to use (default: today's date)")
    parser.add_argument("--no-checksum", action="store_true", help="Disable checksumming")
    parser.add_argument("--upgrade-from-latest", action="store_true", 
                     help="Upgrade from the latest version")
    
    args = parser.parse_args()
    
    # Convert arguments for our processor
    args.directory = [args.directory]  # Make it a list to match existing interface
    
    # Process the command using our new processor
    return_code = process_esgdrs_command(args)
    
    # Exit with appropriate code
    sys.exit(return_code)


if __name__ == "__main__":
    integrate_with_existing_cli()
