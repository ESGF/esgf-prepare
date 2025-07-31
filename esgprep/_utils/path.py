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
    # Extract versions and filter valid ones, excluding 'latest'
    versioned_paths = [
        (p, extract_version(p))
        for p in paths
        if "latest" not in str(p) and "files" not in str(p)
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
    Build dataset identifier from NetCDF file using esgvoc DrsGenerator.
    Returns the dataset identifier string for the given path.
    """
    Print.debug(f"dataset_id: Processing path: {path}")
    
    # Get project from path
    project = get_project(path)
    if not project:
        Print.debug(f"dataset_id: No project found for path: {path}")
        return None
    
    # Get terms from NetCDF file
    attrs = get_terms(path)
    if not attrs:
        Print.debug(f"dataset_id: No NetCDF attributes found for path: {path}")
        return None
    
    try:
        # Use esgvoc DrsGenerator to build dataset identifier
        from esgvoc.apps.drs.generator import DrsGenerator
        
        generator = DrsGenerator(project)
        
        # Extract relevant DRS term values from NetCDF attributes
        # For CMIP6, we need specific attributes to build the dataset ID
        drs_terms = []
        
        # Common CMIP6 DRS attributes in NetCDF files
        # Note: member_id might be stored as variant_label in some files
        drs_attrs = [
            'mip_era', 'activity_id', 'institution_id', 'source_id', 'experiment_id', 
            'member_id', 'variant_label', 'table_id', 'variable_id', 'grid_label'
        ]
        
        for attr in drs_attrs:
            if attr in attrs:
                value = attrs[attr]
                # Handle space-separated values by taking the first one
                if isinstance(value, str) and ' ' in value:
                    value = value.split()[0]
                drs_terms.append(str(value))
                Print.debug(f"dataset_id: Found {attr} = {value}")
        
        if not drs_terms:
            Print.debug(f"dataset_id: No DRS terms found in NetCDF attributes")
            return None
        
        Print.debug(f"dataset_id: Using DRS terms: {drs_terms}")
        
        # Generate dataset ID from bag of terms
        report = generator.generate_dataset_id_from_bag_of_terms(drs_terms)
        
        Print.debug(f"dataset_id: Report generated_drs_expression: {report.generated_drs_expression}")
        Print.debug(f"dataset_id: Report errors: {report.nb_errors}, warnings: {report.nb_warnings}")
        
        if report.nb_errors == 0 and report.generated_drs_expression:
            identifier = report.generated_drs_expression
            Print.debug(f"dataset_id: Generated identifier: {identifier}")
            return identifier
        else:
            Print.debug(f"dataset_id: Generation failed. Errors: {report.nb_errors}, Expression: {report.generated_drs_expression}")
            if hasattr(report, 'errors') and report.errors:
                Print.debug(f"dataset_id: Error details: {report.errors}")
            return None
        
    except Exception as e:
        Print.debug(f"dataset_id: Error generating dataset_id for {path}: {e}")
        return None
