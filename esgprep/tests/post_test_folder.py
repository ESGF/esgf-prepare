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
                if not f.is_symlink():
                    print(f"File {f.name} in {ver_dir.name} is not a symlink")
                    return False

                # Get the target path without resolving all the way to the file
                target_path = str(f.readlink())

                # Check if the symlink points to a file in the files/d* directory
                expected_prefix = f"../files/d"  # no version here cause if upgrade_from_latest d{ver} is different from v{ver}
                if not target_path.startswith(expected_prefix):
                    print(
                        f"File {f.name} in {ver_dir.name} doesn't point to {expected_prefix}, points to {target_path}"
                    )
                    return False
        return True

    def is_there_symlink_between_latest_and_latest_version(self):
        """
        Check that the latest directory is a symlink to the version with the highest number.
        """
        # Sort versions to find the newest one
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
        return latest_path.resolve() == last_version_path.absolute()

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

        assert self.is_there_symlink_between_latest_and_latest_version(), (
            "HAS NOT valid symlinks between latest and latest version diretory"
        )
        print(
            "--- HAS valid symlinks between latest and latest version directory  -------"
        )

        print("--- EVERYTHING FINE ")
