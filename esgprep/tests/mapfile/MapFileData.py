from dataclasses import dataclass, field


@dataclass
class FileData:
    datasetDir: str
    ncFileName: str = field(compare=False)
    ncSize: str
    modTime: str = field(compare=False)
    checksum: str
    checksumType: str


@dataclass
class MapFileData:
    list_file: list[FileData]

    def __eq__(self, other):
        for fd in self.list_file:
            if fd not in other.list_file:
                return False
        return True


def mapfiledataread(path: str) -> MapFileData or None:
    list_res = []
    try:
        with open(path) as f:
            lines = f.readlines()
    except (FileNotFoundError, ValueError) as error:
        print(error)
        print(f"File or Dir {path} not found")

    for line in lines:
        elem = [d.strip() for d in line.split("|")]
        mfd = FileData(*elem)
        list_res.append(mfd)

    return MapFileData(list_res)


def compare(path1: str, path2: str):
    mfd = mapfiledataread(path1)
    mfd2 = mapfiledataread(path2)
    if mfd is not None and mfd2 is not None:
        return mfd == mfd2
    return False
