from pathlib import Path
import re


class TestFolder:
    def __init__(self, folder: Path):
        self.folder = folder
        self.list_dir_base = list(self.folder.glob("*"))
        self.list_version = None
        self.contains_at_least_the_3_folders()

    def exists(self):
        return self.folder.exists()

    def contains_at_least_the_3_folders(self):  # files/d**** ; v***** and latest
        list_dir_base = list(self.folder.glob("*"))
        latest = 'latest' in [dir.name for dir in self.list_dir_base]
        files = 'files' in [dir.name for dir in self.list_dir_base]
        self.list_version = [re.search('\\d{8}', folder).group() for folder in [dir.name for dir in self.list_dir_base]
                             if re.search('\\d{8}', folder) is not None]
        return len(self.list_version) > 0 or files or latest

    def is_there_same_number_of_files_in_d_and_v(self): # ODO ... ça passerra pas en cas de mise à jour partielle !
        files_dir = Path.joinpath(self.folder, "files")
        list_dversion_in_files = list(files_dir.glob("*"))  # each of d******* in files folder
        return len(self.list_version) == len(list_dversion_in_files)

    def is_there_symlink_between_v_and_d(self):
        for ver in self.list_version:
            ver_dir = Path.joinpath(self.folder, "v" + ver)
            list_files_in_version = list(ver_dir.glob("*.*"))
            for f in list_files_in_version:
                pointed_file = f.resolve()
                if not pointed_file.exists():
                    return False
        return True

    def is_there_symlink_between_latest_and_latest_version(self):
        sorted_version_list = sorted(self.list_version, key=lambda x: int(x))
        last_version = sorted_version_list[-1]
        last_version_path = Path.joinpath(self.folder, "v" + last_version)
        latest_path = Path.joinpath(self.folder, "latest")

        return latest_path.exists() and last_version_path.exists() and latest_path.is_symlink() and last_version_path == latest_path.resolve()

    def test(self):
        print("-----------------------------")
        print("--- TESTING : ", self.folder, " -------")

        assert self.exists()
        print("--- Exist                                                    -------")
        assert self.contains_at_least_the_3_folders()
        print("--- HAS files,latest, and at least one version folder        -------")

        assert self.is_there_same_number_of_files_in_d_and_v()
        print("--- HAS same number of files/d******** and v********         -------")

        assert self.is_there_symlink_between_v_and_d()
        print("--- HAS symlink between files/d********/* and v********/*    -------")

        assert self.is_there_symlink_between_latest_and_latest_version()
        print("--- HAS symlink between latest and the latest v********      -------")

        print("--- EVERYTHING FINE ")