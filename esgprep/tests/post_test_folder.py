import re
from pathlib import Path


class Post_Test_Folder:
    def __init__(self, folder: Path):
        self.folder = folder
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
        return self.folder.exists()

    def contains_at_least_the_3_folders(self):  # files/d**** ; v***** and latest
        latest = "latest" in [dir.name for dir in self.list_dir_base]
        files = "files" in [dir.name for dir in self.list_dir_base]
        return len(self.list_version) > 0 or files or latest

    def is_there_same_number_of_files_in_d_and_v(self, upgrade_from_latest=True):
        """
        Check that each version directory (v*) has corresponding files directory (d*).

        With upgrade_from_latest=True (default), different version directories can have
        different numbers of files, as updates may be partial.

        With upgrade_from_latest=False, there should be a 1:1 correspondence between
        versions and data directories, with the same number of files.
        """
        files_dir = Path.joinpath(self.folder, "files")
        data_dirs = list(files_dir.glob("d*"))
        version_dirs = [
            Path.joinpath(self.folder, "v" + ver) for ver in self.list_version
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

        # All checks passed
        return True

    def is_there_symlink_between_v_and_d(self):
        for ver in self.list_version:
            ver_dir = Path.joinpath(self.folder, "v" + ver)
            list_files_in_version = list(ver_dir.glob("*.*"))
            for f in list_files_in_version:
                pointed_file = f.resolve()
                if not pointed_file.exists():
                    return False
        return True

    def is_there_symlink_between_latest_and_latest_version(
        self, upgrade_from_latest=True
    ):
        """
        Check that files in latest directory point to their newest version.

        With upgrade_from_latest=True (the default), each file in latest should point
        to the newest version that contains that specific file.

        With upgrade_from_latest=False, the latest directory itself should be a symlink
        to the newest version directory (legacy behavior).
        """
        if not upgrade_from_latest:
            # Original behavior: check if latest is a symlink to the latest version directory
            sorted_version_list = sorted(self.list_version, key=lambda x: int(x))
            last_version = sorted_version_list[-1]
            last_version_path = Path.joinpath(self.folder, "v" + last_version)
            latest_path = Path.joinpath(self.folder, "latest")

            # Check if latest directory exists, is a symlink, and points to the latest version directory
            if not (
                latest_path.exists()
                and latest_path.is_symlink()
                and last_version_path.exists()
            ):
                return False

            # Check that latest is a symlink to the latest version directory
            return latest_path.resolve() == last_version_path

        # New behavior for upgrade_from_latest: check each file individually
        latest_path = Path.joinpath(self.folder, "latest")
        if not latest_path.exists():
            return False

        # Get all files in the latest directory
        latest_files = list(latest_path.glob("*.*"))
        if not latest_files:
            return False

        # Sort versions from newest to oldest
        sorted_version_list = sorted(
            self.list_version, key=lambda x: int(x), reverse=True
        )

        # Check each file in latest directory
        for latest_file in latest_files:
            if not latest_file.is_symlink():
                print(f"File {latest_file.name} in latest is not a symlink")
                return False

            # Get the target of the symlink (resolves to actual file in d* directory)
            target_path = latest_file.resolve()

            # Extract the filename
            filename = latest_file.name

            # Find the newest version that contains this file
            newest_version_with_file = None
            for version in sorted_version_list:
                version_path = Path.joinpath(self.folder, "v" + version)
                version_file = version_path / filename

                if version_file.exists():
                    newest_version_with_file = version
                    break

            if not newest_version_with_file:
                print(f"Could not find any version containing {filename}")
                return False

            # Now check if latest symlink points to the file in the newest version that has it
            # We need to check the file's version directory from its path
            file_version_pattern = r"/files/d(\d+)/"
            match = re.search(file_version_pattern, str(target_path))
            if not match:
                print(f"Could not extract version number from {target_path}")
                return False

            file_version = match.group(1)
            if file_version != newest_version_with_file:
                print(
                    f"File {filename} points to version {file_version} but newest is {newest_version_with_file}"
                )
                return False

        # All files point to their newest version
        return True

    def test(self, upgrade_from_latest=True):
        """
        Test the directory structure for DRS compliance.

        Args:
            upgrade_from_latest: Whether to use the upgrade_from_latest rules for validation.
                                When True, allows for partial updates with mixed file versions.
        """
        print("-----------------------------")
        print("--- TESTING : ", self.folder, " -------")
        print(f"--- Using upgrade_from_latest={upgrade_from_latest} mode")

        assert self.exists()
        print("--- Exist                                                    -------")
        assert self.contains_at_least_the_3_folders(), (
            "Has NOT files,latest, and at least one version folder"
        )
        print("--- HAS files,latest, and at least one version folder        -------")

        assert self.is_there_same_number_of_files_in_d_and_v(upgrade_from_latest), (
            "Has NOT valid mapping between files/d******** and v********"
        )
        print(
            "--- HAS valid mapping between files/d******** and v********         -------"
        )

        assert self.is_there_symlink_between_v_and_d(), (
            "Has NOT symlink between files/d********/* and v********/*"
        )
        print("--- HAS symlink between files/d********/* and v********/*    -------")

        assert self.is_there_symlink_between_latest_and_latest_version(
            upgrade_from_latest
        ), "HAS NOT valid symlinks between latest and appropriate version files"
        print(
            "--- HAS valid symlinks between latest and appropriate version files  -------"
        )

        print("--- EVERYTHING FINE ")
