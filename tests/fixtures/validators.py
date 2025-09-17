"""
DRS structure validation utilities for testing.

This module contains utilities for validating that DRS (Data Reference Syntax)
structures are correctly built and organized according to ESGF standards.
"""

import re
from pathlib import Path


class DRSValidator:
    """Validator for DRS directory structure compliance."""

    def __init__(self, folder: Path):
        """
        Initialize validator for a DRS folder.

        Args:
            folder: Path to the DRS dataset directory to validate
        """
        self.folder = Path(folder)
        self.list_dir_base = list(self.folder.glob("*"))

        # Extract version numbers from directory names (v12345678)
        self.list_version = []
        for dir_path in self.list_dir_base:
            dir_name = dir_path.name
            match = re.search("\\d{8}", dir_name)
            if match and dir_name.startswith("v"):
                self.list_version.append(match.group())

        # Ensure we found at least one version directory
        assert len(self.list_version) > 0, (
            f"No version directories (v followed by 8 digits) found in {folder}"
        )

    def exists(self):
        """Check if the folder exists."""
        return self.folder.exists()

    def contains_required_directories(self):
        """Check if folder contains required DRS directories (files, latest, v*)."""
        dir_names = [dir.name for dir in self.list_dir_base]
        latest = "latest" in dir_names
        files = "files" in dir_names
        has_versions = len(self.list_version) > 0
        return latest and files and has_versions

    def has_valid_version_mapping(self, upgrade_from_latest=True):
        """
        Check that each version directory (v*) has corresponding files directory (d*).

        With upgrade_from_latest=True (default), different version directories can have
        different numbers of files, as updates may be partial.

        With upgrade_from_latest=False, there should be a 1:1 correspondence between
        versions and data directories, with the same number of files.

        Args:
            upgrade_from_latest: Whether to use upgrade_from_latest validation rules

        Returns:
            bool: True if mapping is valid
        """
        files_dir = self.folder / "files"
        if not files_dir.exists():
            print(f"Files directory not found: {files_dir}")
            return False

        data_dirs = list(files_dir.glob("d*"))
        version_dirs = [
            self.folder / f"v{ver}" for ver in self.list_version
        ]

        # Check that each v* directory has a corresponding d* directory
        for ver_dir in version_dirs:
            ver_name = ver_dir.name
            data_name = "d" + ver_name[1:]  # v20250401 -> d20250401

            data_dir = files_dir / data_name
            if not data_dir.exists():
                print(
                    f"No data directory '{data_name}' found for version directory '{ver_name}'"
                )
                return False

        # Check that each d* directory has a corresponding v* directory
        for data_dir in data_dirs:
            data_name = data_dir.name
            if not data_name.startswith("d") or len(data_name) < 2:
                continue

            ver_name = "v" + data_name[1:]  # d20250401 -> v20250401
            ver_dir = self.folder / ver_name
            if not ver_dir.exists():
                print(
                    f"No version directory '{ver_name}' found for data directory '{data_name}'"
                )
                return False

        if not upgrade_from_latest:
            # For non-upgrade_from_latest mode, verify equal file counts between corresponding dirs
            for ver_dir in version_dirs:
                ver_name = ver_dir.name
                data_name = "d" + ver_name[1:]
                data_dir = files_dir / data_name

                ver_files = list(ver_dir.glob("*.*"))
                data_files = list(data_dir.glob("*.*"))

                if len(ver_files) != len(data_files):
                    print(
                        f"Unequal number of files: {len(ver_files)} in {ver_name}, {len(data_files)} in {data_name}"
                    )
                    return False

        return True

    def has_valid_symlinks_to_files(self):
        """Check that version directories contain valid symlinks to files/d* directories."""
        for ver in self.list_version:
            ver_dir = self.folder / f"v{ver}"
            list_files_in_version = list(ver_dir.glob("*.*"))

            for f in list_files_in_version:
                if not f.is_symlink():
                    print(f"File {f.name} in {ver_dir.name} is not a symlink")
                    return False

                # Get the target path without resolving all the way to the file
                target_path = str(f.readlink())

                # Check if the symlink points to a file in the files/d* directory
                expected_prefix = "../files/d"  # no version here cause if upgrade_from_latest d{ver} is different from v{ver}
                if not target_path.startswith(expected_prefix):
                    print(
                        f"File {f.name} in {ver_dir.name} doesn't point to {expected_prefix}, points to {target_path}"
                    )
                    return False
        return True

    def has_valid_latest_symlink(self):
        """
        Check that the latest directory is a symlink to the version with the highest number.
        """
        # Sort versions to find the newest one
        sorted_version_list = sorted(self.list_version, key=lambda x: int(x))
        last_version = sorted_version_list[-1]
        last_version_path = self.folder / f"v{last_version}"
        latest_path = self.folder / "latest"

        # Check if latest directory exists, is a symlink, and points to the latest version directory
        if not (
            latest_path.exists()
            and latest_path.is_symlink()
            and last_version_path.exists()
        ):
            print(f"Latest symlink validation failed: exists={latest_path.exists()}, "
                  f"is_symlink={latest_path.is_symlink()}, "
                  f"target_exists={last_version_path.exists()}")
            return False

        # Check that latest is a symlink to the latest version directory
        is_correct = latest_path.resolve() == last_version_path.absolute()
        if not is_correct:
            print(f"Latest symlink points to wrong target: "
                  f"points to {latest_path.resolve()}, "
                  f"should point to {last_version_path.absolute()}")
        return is_correct

    def validate_all(self, upgrade_from_latest=True, verbose=True):
        """
        Run all DRS validation checks.

        Args:
            upgrade_from_latest: Whether to use upgrade_from_latest validation rules
            verbose: Whether to print detailed validation messages

        Returns:
            bool: True if all validations pass
        """
        if verbose:
            print("-----------------------------")
            print(f"--- VALIDATING: {self.folder} -------")
            print(f"--- Using upgrade_from_latest={upgrade_from_latest} mode")

        try:
            assert self.exists(), f"Directory does not exist: {self.folder}"
            if verbose:
                print("--- Directory exists ✓")

            assert self.contains_required_directories(), (
                "Missing required directories: files, latest, and at least one version folder"
            )
            if verbose:
                print("--- Has required directories (files, latest, v*) ✓")

            assert self.has_valid_version_mapping(upgrade_from_latest), (
                "Invalid mapping between files/d******** and v********"
            )
            if verbose:
                print("--- Has valid version mapping ✓")

            assert self.has_valid_symlinks_to_files(), (
                "Invalid symlinks between files/d********/* and v********/*"
            )
            if verbose:
                print("--- Has valid symlinks to files ✓")

            assert self.has_valid_latest_symlink(), (
                "Invalid symlink between latest and latest version directory"
            )
            if verbose:
                print("--- Has valid latest symlink ✓")

            if verbose:
                print("--- ALL VALIDATIONS PASSED ✓")
            return True

        except AssertionError as e:
            if verbose:
                print(f"--- VALIDATION FAILED: {e}")
            return False


def validate_drs_structure(folder, upgrade_from_latest=True, verbose=True):
    """
    Convenience function to validate a DRS structure.

    Args:
        folder: Path to the DRS dataset directory
        upgrade_from_latest: Whether to use upgrade_from_latest validation rules
        verbose: Whether to print validation messages

    Returns:
        bool: True if validation passes
    """
    validator = DRSValidator(folder)
    return validator.validate_all(upgrade_from_latest=upgrade_from_latest, verbose=verbose)


# Legacy compatibility - maintain the old interface
class Post_Test_Folder(DRSValidator):
    """Legacy compatibility class - use DRSValidator instead."""

    def __init__(self, folder: Path):
        super().__init__(folder)
        import warnings
        warnings.warn(
            "Post_Test_Folder is deprecated, use DRSValidator instead",
            DeprecationWarning,
            stacklevel=2
        )

    def contains_at_least_the_3_folders(self):
        """Legacy method - use contains_required_directories() instead."""
        return self.contains_required_directories()

    def is_there_same_number_of_files_in_d_and_v(self, upgrade_from_latest=True):
        """Legacy method - use has_valid_version_mapping() instead."""
        return self.has_valid_version_mapping(upgrade_from_latest)

    def is_there_symlink_between_v_and_d(self):
        """Legacy method - use has_valid_symlinks_to_files() instead."""
        return self.has_valid_symlinks_to_files()

    def is_there_symlink_between_latest_and_latest_version(self):
        """Legacy method - use has_valid_latest_symlink() instead."""
        return self.has_valid_latest_symlink()

    def test(self, upgrade_from_latest=True):
        """Legacy method - use validate_all() instead."""
        return self.validate_all(upgrade_from_latest, verbose=True)