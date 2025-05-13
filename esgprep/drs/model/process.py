"""
Process class for DRS operations in a multiprocessing context.
"""

import traceback
from pathlib import Path
from typing import Dict

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

        # Get version string
        version_str = destination_parent.name
        # Get the data version without the 'v' prefix (e.g., '20250401')
        data_version = version_str[1:] if version_str.startswith('v') else version_str

        # 1. Files directory
        files_dir = dataset_dir / "files"

        # Create data version folder (dXXXXXXXX) inside files folder
        data_dir = files_dir / f"d{data_version}"
        data_path = data_dir / destination_path.name

        # Add operations for files directory
        operations.append({
            "operation_type": "move",  # Just to create directory
            "source": None,
            "destination": files_dir,
            "description": "Create files directory"
        })

        # Add operation to create data version directory
        operations.append({
            "operation_type": "move",  # Just to create directory
            "source": None,
            "destination": data_dir,
            "description": f"Create d{data_version} directory inside files"
        })

        # Add operation for the actual file
        operations.append({
            "operation_type": self.mode,
            "source": source_path,
            "destination": data_path,
            "description": f"{self.mode} original file to files/d{data_version} directory"
        })

        # 2. Version directory
        operations.append({
            "operation_type": "move",  # Just to create directory
            "source": None,
            "destination": destination_parent,
            "description": "Create version directory"
        })

        operations.append({
            "operation_type": "symlink",  # Always use symlink for version -> files/dXXXXXXXX
            "source": data_path,
            "destination": destination_path,
            "description": "Create symlink from version directory to files/dXXXXXXXX directory"
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
