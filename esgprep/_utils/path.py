import re
from pathlib import Path

import esgvoc.api as ev

from esgprep._utils.print import Print


def extract_version(path: Path) -> str:
    """
    Extracts the version string (vXXXXXXXX) from the given path.
    Raises a ValueError if no valid version is found.
    """
    match = re.search(r"v\d{8}", str(path))
    if match:
        return match.group(0)
    elif "latest" in str(path):
        return "latest"
    elif "files" in str(path):
        return "files"
    else:
        raise ValueError(f"Invalid version format in path: {path}")


def get_version_index(path: Path) -> int:
    """
    Returns the index position of the version part (vXXXXXXXX) in the path parts.
    """
    version = extract_version(path)
    parts = path.parts
    for i, part in enumerate(parts):
        if part == version:
            return i
    raise ValueError(f"No version found in path: {path}")


def get_version_and_subpath(path: Path) -> list[str]:
    """
    Returns a list of path parts from the version part to the end of the path.
    """
    index = get_version_index(path)
    return list(path.parts[index:])


def get_path_to_version(path: Path) -> list[str]:
    """
    Returns a list of path parts from the start part to the version of the path.
    """
    index = get_version_index(path)
    return list(path.parts[:index])


def get_ordered_version_paths(base_path: Path) -> list[Path]:
    """
    Returns a list of all paths in the base_path directory, ordered by version,
    excluding the 'latest' symlink.
    """
    if base_path.exists() is False:
        return []
    paths = list(base_path.iterdir())

    # Extract versions and filter valid ones, excluding 'latest'
    versioned_paths = [
        (p, extract_version(p))
        for p in paths
        if "latest" not in str(p) and "files" not in str(p)
    ]

    # Sort by version (numeric sorting for vXXXXXXXX)
    versioned_paths.sort(key=lambda x: int(x[1][1:]))

    return [p[0] for p in versioned_paths]


def get_project(path) -> str | None:
    """
    Extract project code from a pathlib.Path object.

    """
    # Get all scopes within the loaded authority.
    scopes = set(ev.get_all_projects())
    # Find intersection between scopes list and path parts.
    project = set(Path(str(path).lower()).parts).intersection(scopes)

    # Ensure only one project code matched.
    if len(project) == 1:
        return project.pop()

    elif len(project) == 0:
        Print.debug(f"No project code found: {path}")
        return None

    else:
        Print.debug(f"Unable to match one project code: {path}")
        return None
