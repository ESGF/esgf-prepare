# -*- coding: utf-8 -*-
"""
Examples of how to implement the updated Pydantic v2 models in the ESGDRS process.

This module demonstrates practical usage of the models in file processing,
DRS tree generation, and command execution.
"""

import os
from datetime import datetime
from pathlib import Path
from typing import Dict, Iterator, List, Optional, Any

from pydantic import ValidationError

# Import the updated models
from models import Dataset, DatasetVersion, DrsOperation, DrsResult, FileInput, MigrationMode


class DrsProcessor:
    """
    Processes files according to the DRS using the new Pydantic models.
    
    This class demonstrates how the new models could be integrated with
    existing code to provide a cleaner, more maintainable interface.
    """
    
    def __init__(
        self,
        root_dir: Path,
        mode: str = "move",
        checksum_type: Optional[str] = "sha256",
        upgrade_from_latest: bool = False,
        ignore_from_latest: List[str]|None = None,
        ignore_from_incoming: List[str]|None = None,
        version: str |None= None,
    ):
        """Initialize the DRS processor with configuration options."""
        self.root_dir = Path(root_dir)
        self.mode = MigrationMode(mode)
        self.checksum_type = checksum_type
        self.upgrade_from_latest = upgrade_from_latest
        self.ignore_from_latest = ignore_from_latest or []
        self.ignore_from_incoming = ignore_from_incoming or []
        self.version = version or f"v{datetime.now().strftime('%Y%m%d')}"
        
        # Import here to avoid circular imports
        try:
            from esgvoc.apps.drs.generator import DrsGenerator
            self.drs_generator = DrsGenerator("cmip6")  # Could be configurable
        except ImportError:
            print("Warning: esgvoc package not available, DRS generation will be limited")
            self.drs_generator = None
        
        # Track processed datasets for reporting
        self.datasets: Dict[str, Dataset] = {}
    
    def create_file_input(self, file_path: Path) -> FileInput:
        """
        Create a FileInput instance from a file path.
        
        This encapsulates the logic of extracting file metadata and DRS facets,
        improving code organization and reusability.
        
        Args:
            file_path: Path to the source file
            
        Returns:
            FileInput model instance
        """
        # Import utilities as needed
        from esgprep._utils.ncfile import get_ncattrs, get_tracking_id
        
        # Get file attributes
        attrs = get_ncattrs(str(file_path))
         
        # Add basic information
        attrs["filename"] = file_path.name
        attrs["version"] = self.version
        # Parse DRS facets
        facets = {}
        
        # Use DRS generator if available
        if self.drs_generator:
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
            # Fallback to extracting facets directly from attributes
            # Map common attribute names to facet names
            attr_to_facet = {
                "project_id": "project",
                "activity_drs": "activity_id",
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
        # Create the FileInput model
        try:
            return FileInput(
                source_path=file_path,
                filename=file_path.name,
                file_size=file_path.stat().st_size,
                project=facets.get("project", "cmip6"),  # Default to cmip6
                root_dir=self.root_dir,
                attributes=attrs,
                tracking_id=get_tracking_id(attrs) if "tracking_id" in attrs else None,
                version=self.version,
                drs_facets=facets,
                checksum=None,
                checksum_type= "sha256",
                ignored=False,
                is_duplicate= False

            )
        except ValidationError as e:
            # Properly handle validation errors
            print(f"Error creating FileInput for {file_path}: {e}")
            # Create a minimal valid instance
            return FileInput(
                source_path=file_path,
                filename=file_path.name,
                file_size=file_path.stat().st_size if file_path.exists() else 0,
                project="cmip6",  # Default project
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
        print("PROCESSING FILE: ", file_path)
        # Import utilities as needed
        from esgprep._utils.checksum import get_checksum
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
                input_file.checksum = get_checksum(str(file_path), self.checksum_type)
                input_file.checksum_type = self.checksum_type
            
            # Generate destination path
            if self.drs_generator and not input_file.drs_path:
                # Use DRS generator if available and path not already determined
                mapping_attrs = {
                    **input_file.attributes, 
                    **{"member_id": input_file.attributes.get("variant_label", "")}
                }
                drs_result = self.drs_generator.generate_directory_from_mapping(mapping_attrs)
                
                if drs_result.errors:
                    return DrsResult(
                        input_file=input_file,
                        success=False,
                        error_message=f"DRS generation errors: {drs_result.errors}"
                    )
                
                destination_path = self.root_dir / Path(drs_result.generated_drs_expression) / file_path.name
            else:
                # Use path from input_file
                destination_path = input_file.drs_path or (self.root_dir / file_path.name)
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
            print("BEFORE OPERATION")
            operations = self._generate_operations(input_file, destination_path, is_duplicate)
            
            # Create and return the result
            return DrsResult(
                input_file=input_file,
                operations=operations,
                success=True,
                dataset=dataset
            )
            
        except Exception as e:
            # Handle any exceptions
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
        # Find all netCDF files in the directory
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
        from esgprep._utils.checksum import get_checksum
        
        # Check if the file already exists
        if not destination_path.exists():
            return False
        
        # Check file size
        if destination_path.stat().st_size != input_file.file_size:
            return False
        
        # Check checksum if available
        if input_file.checksum and input_file.checksum_type:
            existing_checksum = get_checksum(
                str(destination_path), 
                input_file.checksum_type
            )
            return existing_checksum == input_file.checksum
        
        return False
    
    def _generate_operations(
        self, 
        input_file: FileInput, 
        destination_path: Path,
        is_duplicate: bool
    ) -> List[DrsOperation]:
        """
        Generate the operations needed to place the file in the DRS.
        
        Args:
            input_file: File input model
            destination_path: Destination path in the DRS
            is_duplicate: Whether the file is a duplicate
            
        Returns:
            List of operations to perform
        """
        operations = []
        
        # If duplicate and not upgrading from latest, no operations needed
        if is_duplicate and not self.upgrade_from_latest:
            if self.mode == MigrationMode.MOVE:
                # Add operation to remove the duplicate source file
                operations.append(DrsOperation(
                    operation_type=MigrationMode.REMOVE,
                    source=input_file.source_path,
                    destination=input_file.source_path,
                    is_duplicate=True
                ))
            return operations
        
        # Create destination directory if it doesn't exist
        operations.append(DrsOperation(
            operation_type=MigrationMode.MOVE,  # Placeholder, not actually moving a file
            destination=destination_path.parent,
            is_duplicate=is_duplicate
        ))
        
        # Add the main file operation
        operations.append(DrsOperation(
            operation_type=self.mode,
            source=input_file.source_path,
            destination=destination_path,
            is_duplicate=is_duplicate,
            tracking_id=input_file.tracking_id
        ))
        
        # Create "latest" symlink for this dataset version
        latest_path = destination_path.parent.parent / "latest"
        operations.append(DrsOperation(
            operation_type=MigrationMode.SYMLINK,
            source=Path(self.version),  # Relative path
            destination=latest_path,
            is_duplicate=is_duplicate
        ))
        
        # If upgrading from latest, copy files from latest version that aren't
        # in the incoming files and aren't in ignore_from_latest
        if self.upgrade_from_latest:
            # This would be implemented according to the existing logic
            # for upgrading from the latest version
            pass
        
        return operations
    
    def execute_operations(self, operations: List[DrsOperation]) -> bool:
        """
        Execute the given DRS operations.
        
        This would actually perform the file operations based on the
        operations generated during processing.
        
        Args:
            operations: List of operations to perform
            
        Returns:
            bool: True if all operations succeeded
        """
        # Example implementation - would be expanded in real code
        for operation in operations:
            try:
                if operation.operation_type == MigrationMode.MOVE:
                    if operation.source:
                        # Create parent directories if needed
                        operation.destination.parent.mkdir(parents=True, exist_ok=True)
                        # Move the file
                        operation.source.rename(operation.destination)
                elif operation.operation_type == MigrationMode.COPY:
                    if operation.source:
                        # Create parent directories if needed
                        operation.destination.parent.mkdir(parents=True, exist_ok=True)
                        # Copy the file
                        import shutil
                        shutil.copy2(operation.source, operation.destination)
                elif operation.operation_type == MigrationMode.LINK:
                    if operation.source:
                        # Create parent directories if needed
                        operation.destination.parent.mkdir(parents=True, exist_ok=True)
                        # Create hard link
                        os.link(operation.source, operation.destination)
                elif operation.operation_type == MigrationMode.SYMLINK:
                    if operation.source:
                        # Create parent directories if needed
                        operation.destination.parent.mkdir(parents=True, exist_ok=True)
                        # Create symlink
                        if operation.destination.exists():
                            operation.destination.unlink()
                        os.symlink(operation.source, operation.destination)
                elif operation.operation_type == MigrationMode.REMOVE:
                    if operation.source and operation.source.exists():
                        operation.source.unlink()
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
