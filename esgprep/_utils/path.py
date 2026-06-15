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
    Returns a list of all "version directory" paths in the base_path directory, ordered by version,
    excluding the 'latest' symlink.
    """
    if base_path.exists() is False:
        return []
    paths = list(base_path.iterdir())
    # Extract versions and filter valid ones, excluding 'latest' and 'files'
    versioned_paths = [
        (p, extract_version(p))
        for p in paths
        if p.name != "latest" and p.name != "files" and p.is_dir()
    ]

    # Sort by version (numeric sorting for vXXXXXXXX)
    versioned_paths.sort(key=lambda x: int(x[1][1:]))

    return [p[0] for p in versioned_paths]


def get_ordered_file_version_paths(base_path: Path, file_name: str):
    res = []
    version_paths = get_ordered_version_paths(base_path)
    for version_path in version_paths:
        file_version_path = version_path / file_name
        if file_version_path.is_file():
            res.append(file_version_path)
    return res


def get_versions(path: Path) -> list[Path]:
    """
    Returns a list of all version directory paths for the given path, ordered by version.
    This is used to find all existing versions of a dataset.
    """
    versions = get_ordered_version_paths(path)
    if not versions:
        # If no versions found, try the parent directory
        # This handles cases where path might be inside a version directory
        if path.parent != path:  # Avoid infinite recursion at root
            versions = get_ordered_version_paths(path.parent)
    return versions


def get_drs(path: Path) -> Path:
    """
    Returns the DRS (Data Reference Syntax) part of the path.
    This returns the path up to but not including the version.
    """
    try:
        # Get the path parts up to the version
        drs_parts = get_path_to_version(path)
        return Path(*drs_parts) if drs_parts else Path()
    except ValueError:
        # If no version found, return the full path
        return path


def is_latest_symlink(path: Path) -> bool:
    """
    Check if the path contains 'latest' and is a symlink.
    """
    return path.is_symlink() and "latest" in str(path)


def with_latest_target(path: Path) -> Path:
    """
    If path is a 'latest' symlink, return the target path.
    Otherwise return the original path.
    """
    if is_latest_symlink(path):
        try:
            return path.resolve()
        except (OSError, RuntimeError):
            # Handle broken symlinks or circular references
            return path
    return path


def get_project(path) -> str | None:
    """
    Extract project code from a pathlib.Path object.

    """
    # Get all scopes within the loaded authority.
    scopes = set(ev.get_all_projects())

    if not scopes:
        Print.error(
            "No esgvoc vocabulary databases found. "
            "Please install at least one project snapshot, e.g.: esgvoc use cordex-cmip6@latest"
        )
        return None

    # Find intersection between scopes list and path parts.
    project = set(Path(str(path).lower()).parts).intersection(scopes)

    # Ensure only one project code matched.
    if len(project) == 1:
        project_id = project.pop()
        db_info = ev.get_active_database_info(project_id)
        if db_info:
            Print.debug(
                f"Using vocabulary database for '{project_id}': "
                f"version={db_info['version']}, source={db_info['source']}"
            )
        return project_id

    elif len(project) == 0:
        Print.warning(
            f"No project code found in path: {path}\n"
            f"  Installed vocabulary databases: {sorted(scopes)}\n"
            f"  None of these matched any part of the path. "
            f"Make sure the correct project snapshot is installed (e.g.: esgvoc use <project>@latest)"
        )
        return None

    else:
        Print.warning(
            f"Multiple project codes found in path: {sorted(project)} for {path}\n"
            f"  Unable to determine which project to use."
        )
        return None


def get_terms(path: Path) -> dict:
    """
    Extract DRS terms from NetCDF file global attributes.
    Returns a dictionary of DRS terms for the given path.
    """
    Print.debug(f"get_terms: Processing path: {path}")

    try:
        # Import NetCDF utilities
        from esgprep._utils.ncfile import get_ncattrs

        # Get NetCDF global attributes
        attrs = get_ncattrs(str(path))
        Print.debug(f"get_terms: NetCDF attributes: {list(attrs.keys())}")

        # Return the attributes as terms - they contain the DRS terms
        return attrs

    except Exception as e:
        Print.debug(f"get_terms: Error extracting terms from NetCDF {path}: {e}")
        return {}


def dataset_id(path: Path) -> str | None:
    """
    Build dataset identifier from DRS path structure using esgvoc DrsGenerator.
    Returns the dataset identifier string for the given path.

    Extracts terms from the directory path parts (between DRS root and version)
    and uses the DrsGenerator to build a valid dataset ID.
    """
    Print.debug(f"dataset_id: Processing path: {path}")

    # Get project from path
    project = get_project(path)
    if not project:
        Print.debug(f"dataset_id: No project found for path: {path}")
        return None

    try:
        from esgvoc.api import DrsType, get_project as get_project_specs
        from esgvoc.apps.drs.generator import DrsGenerator

        # Extract version from path
        version = extract_version(path)
        Print.debug(f"dataset_id: Found version: {version}")

        # Get path parts
        parts = list(path.parts)

        # Find version index in path
        try:
            version_idx = parts.index(version)
        except ValueError:
            Print.debug(f"dataset_id: Version {version} not found in path parts")
            return None

        # Get number of DRS directory parts (excluding version) from the spec
        # This tells us how many parts before the version belong to the DRS
        proj_specs = get_project_specs(project)
        dir_spec = proj_specs.drs_specs[DrsType.DIRECTORY]
        num_dir_parts = len([p for p in dir_spec.parts if p.is_required]) - 1  # -1 for version

        # DRS starts at: version_idx - num_dir_parts (searching backwards from version)
        drs_start_idx = version_idx - num_dir_parts
        if drs_start_idx < 0:
            Print.debug(f"dataset_id: Invalid DRS start index: {drs_start_idx}")
            return None

        # Extract DRS terms from directory parts
        drs_terms = list(parts[drs_start_idx:version_idx])

        # Add version (with and without v prefix for flexibility)
        drs_terms.append(version)
        if version.startswith('v'):
            drs_terms.append(version[1:])

        Print.debug(f"dataset_id: DRS terms from path: {drs_terms}")

        if not drs_terms:
            Print.debug("dataset_id: No DRS terms found in path")
            return None

        # Use DrsGenerator to build dataset ID from bag of terms
        generator = DrsGenerator(project)
        report = generator.generate_dataset_id_from_bag_of_terms(drs_terms)

        Print.debug(
            f"dataset_id: Report generated_drs_expression: {report.generated_drs_expression}"
        )
        Print.debug(
            f"dataset_id: Report errors: {report.nb_errors}, warnings: {report.nb_warnings}"
        )

        if report.nb_errors == 0 and report.generated_drs_expression:
            identifier = report.generated_drs_expression
            Print.debug(f"dataset_id: Generated identifier: {identifier}")
            return identifier
        else:
            Print.debug(
                f"dataset_id: Generation failed. Errors: {report.nb_errors}, Expression: {report.generated_drs_expression}"
            )
            if hasattr(report, "errors") and report.errors:
                Print.debug(f"dataset_id: Error details: {report.errors}")
            return None

    except Exception as e:
        Print.debug(f"dataset_id: Error generating dataset_id for {path}: {e}")
        return None
