"""
Common utilities for DRS testing.
"""

import shutil

import netCDF4
import numpy as np

# Configuration
PROJECT_ID = "cmip6"
VERSION_STR = "v20250401"

# Valid models and variables from the Controlled Vocabulary
VALID_MODELS = ["IPSL-CM6A-LR", "IPSL-CM6A-MR1", "NESM3"]
VALID_VARIABLES = ["tas", "hur", "huss", "pr", "psl"]


def clean_directory(directory):
    """Clean a directory but don't delete the directory itself."""
    for item in directory.glob("*"):
        if item.is_file():
            item.unlink()
        elif item.is_dir():
            shutil.rmtree(item)
    print(f"Cleaned directory: {directory}")


def _create_base_netcdf_file(
    file_path, model_id, variable_id, time_range, version=1, member_id="r1i1p1f1"
):
    """
    Create a base NetCDF file with common attributes.

    Args:
        file_path: Path where the file will be created
        model_id: Model identifier (index or name from VALID_MODELS)
        variable_id: Variable identifier (index or name from VALID_VARIABLES)
        time_range: Tuple of (start, end) for time dimension
        version: Version number to use for randomization seed
        member_id: Member identifier (e.g., r1i1p1f1)

    Returns:
        Path to the created file
    """
    # Ensure we have valid model and variable IDs
    if isinstance(model_id, int) or (isinstance(model_id, str) and model_id.isdigit()):
        model_id = VALID_MODELS[int(model_id) % len(VALID_MODELS)]
    elif isinstance(model_id, str) and model_id.startswith("model"):
        model_id = VALID_MODELS[0]  # Default to first valid model
    elif model_id not in VALID_MODELS:
        model_id = VALID_MODELS[0]  # Default to first valid model

    if isinstance(variable_id, int) or (
        isinstance(variable_id, str) and variable_id.isdigit()
    ):
        variable_id = VALID_VARIABLES[int(variable_id) % len(VALID_VARIABLES)]
    elif isinstance(variable_id, str) and variable_id.startswith("var"):
        index = int(variable_id.replace("var", "0")) % len(VALID_VARIABLES)
        variable_id = VALID_VARIABLES[index]
    elif variable_id not in VALID_VARIABLES:
        variable_id = VALID_VARIABLES[0]  # Default to first valid variable

    # Create the parent directory if it doesn't exist
    file_path.parent.mkdir(exist_ok=True, parents=True)

    # Extract time range
    time_start, time_end = time_range
    time_size = time_end - time_start

    # Create NetCDF file with proper attributes
    ds = netCDF4.Dataset(file_path, "w", format="NETCDF4")

    # Add dimensions
    ds.createDimension("time", time_size)
    ds.createDimension("lat", 5)
    ds.createDimension("lon", 5)

    # Add variables
    times = ds.createVariable("time", "f8", ("time",))
    lats = ds.createVariable("lat", "f4", ("lat",))
    lons = ds.createVariable("lon", "f4", ("lon",))
    temp = ds.createVariable(
        variable_id,
        "f4",
        (
            "time",
            "lat",
            "lon",
        ),
    )

    # Add data
    times[:] = np.arange(time_start, time_end)
    lats[:] = np.arange(5)
    lons[:] = np.arange(5)

    # Use different random seed for different versions
    # Include member_id in the seed to ensure different data for different members
    seed_val = abs(hash(f"{model_id}{variable_id}")) % 1000 + version * 1000
    if member_id != "r1i1p1f1":
        # Extract realization number from member_id
        r_num = int(member_id[1]) if member_id[1].isdigit() else 1
        seed_val += r_num * 10
    np.random.seed(seed_val)
    temp[:] = np.random.rand(time_size, 5, 5)

    # Add global attributes relevant for DRS with valid values
    temp_dict = {"cmip6": "CMIP6", "cmip6plus": "CMIP6Plus", "cmip7": "CMIP7"}
    ds.project_id = temp_dict[PROJECT_ID]

    ds.mip_era = temp_dict[PROJECT_ID]
    ds.activity_id = "CMIP"  # Valid acitivity ID
    ds.institution_id = "IPSL"  # Valid institution ID
    ds.source_id = model_id  # Use the valid model ID
    ds.experiment_id = "historical"
    ds.variant_label = member_id
    ds.table_id = "day"
    ds.variable_id = variable_id  # Use the valid variable ID
    ds.grid_label = "gn"

    # Close the file
    ds.close()

    return file_path


def create_files_different_models(
    directory, count=3, time_range=(1, 10), variable_id="tas"
):
    """
    Create sample NetCDF files with different models.

    Args:
        directory: Directory to create files in
        count: Number of files to create
        time_range: Time range tuple (start, end)
        variable_id: Variable identifier

    Returns:
        List of created file paths
    """
    file_paths = []

    for i in range(count):
        model_id = VALID_MODELS[i % len(VALID_MODELS)]  # Cycle through valid models
        subfolder = directory / f"model_{model_id}"
        subfolder.mkdir(exist_ok=True, parents=True)

        filename = subfolder / f"{PROJECT_ID}_{model_id}_{variable_id}.nc"
        file_path = _create_base_netcdf_file(
            filename, model_id, variable_id, time_range
        )
        file_paths.append(file_path)

    return file_paths


def create_files_different_variables(
    directory, model_id=0, count=3, time_range=(1, 10)
):
    """
    Create sample NetCDF files with the same model but different variables.

    Args:
        directory: Directory to create files in
        model_id: Model identifier (index or name)
        count: Number of files to create
        time_range: Time range tuple (start, end)

    Returns:
        List of created file paths
    """
    file_paths = []

    # Ensure model_id is a valid model
    if isinstance(model_id, int) or (isinstance(model_id, str) and model_id.isdigit()):
        model_id = VALID_MODELS[int(model_id) % len(VALID_MODELS)]

    for i in range(min(count, len(VALID_VARIABLES))):
        variable_id = VALID_VARIABLES[i]
        # subfolder = directory / f"var_{variable_id}"
        directory.mkdir(exist_ok=True, parents=True)

        filename = directory / f"{PROJECT_ID}_{model_id}_{variable_id}.nc"
        file_path = _create_base_netcdf_file(
            filename, model_id, variable_id, time_range
        )
        file_paths.append(file_path)

    return file_paths


def create_files_different_times(directory, model_id=0, variable_id="tas", count=3):
    """
    Create sample NetCDF files with the same model and variable but different time ranges.

    Args:
        directory: Directory to create files in
        model_id: Model identifier (index or name)
        variable_id: Variable identifier
        count: Number of files to create

    Returns:
        List of created file paths
    """
    file_paths = []

    # Ensure model_id is a valid model
    if isinstance(model_id, int) or (isinstance(model_id, str) and model_id.isdigit()):
        model_id = VALID_MODELS[int(model_id) % len(VALID_MODELS)]

    # Ensure variable_id is valid
    if variable_id not in VALID_VARIABLES:
        variable_id = VALID_VARIABLES[0]

    # Define time ranges for each file
    time_ranges = [(i * 10, (i + 1) * 10) for i in range(count)]

    for i, time_range in enumerate(time_ranges):
        time_start, time_end = time_range
        subfolder = directory
        subfolder.mkdir(exist_ok=True, parents=True)

        filename = (
            subfolder
            / f"{PROJECT_ID}_{model_id}_{variable_id}_{time_start}-{time_end}.nc"
        )

        file_path = _create_base_netcdf_file(
            filename, model_id, variable_id, time_range
        )
        file_paths.append(file_path)

    return file_paths


def create_files_different_versions(
    directory, model_id=0, variable_id="tas", time_range=(1, 10), count=2
):
    """
    Create sample NetCDF files with same model, variable, time but different versions.

    Args:
        directory: Directory to create files in
        model_id: Model identifier (index or name)
        variable_id: Variable identifier
        time_range: Time range tuple (start, end)
        count: Number of versions to create

    Returns:
        List of created file paths
    """
    file_paths = []

    # Ensure model_id is a valid model
    if isinstance(model_id, int) or (isinstance(model_id, str) and model_id.isdigit()):
        model_id = VALID_MODELS[int(model_id) % len(VALID_MODELS)]

    # Ensure variable_id is valid
    if variable_id not in VALID_VARIABLES:
        variable_id = VALID_VARIABLES[0]

    for version in range(1, count + 1):
        subfolder = directory / f"version_{version}"
        subfolder.mkdir(exist_ok=True, parents=True)

        filename = subfolder / f"{PROJECT_ID}_{model_id}_{variable_id}.nc"
        file_path = _create_base_netcdf_file(
            filename, model_id, variable_id, time_range, version=version
        )
        file_paths.append(file_path)

    return file_paths


def create_files_different_members(
    directory, model_id=0, variable_id="tas", time_range=(1, 10), count=3
):
    """
    Create sample NetCDF files with same model, variable, time, version but different member IDs.

    Args:
        directory: Directory to create files in
        model_id: Model identifier (index or name)
        variable_id: Variable identifier
        time_range: Time range tuple (start, end)
        count: Number of members to create

    Returns:
        List of created file paths
    """
    file_paths = []

    # Ensure model_id is a valid model
    if isinstance(model_id, int) or (isinstance(model_id, str) and model_id.isdigit()):
        model_id = VALID_MODELS[int(model_id) % len(VALID_MODELS)]

    # Ensure variable_id is valid
    if variable_id not in VALID_VARIABLES:
        variable_id = VALID_VARIABLES[0]

    for i in range(1, count + 1):
        member_id = (
            f"r{i}i1p1f1"  # Different member IDs: r1i1p1f1, r2i1p1f1, r3i1p1f1, etc.
        )
        subfolder = directory / f"member_{member_id}"
        subfolder.mkdir(exist_ok=True, parents=True)

        filename = subfolder / f"{PROJECT_ID}_{model_id}_{variable_id}_{member_id}.nc"
        file_path = _create_base_netcdf_file(
            filename, model_id, variable_id, time_range, member_id=member_id
        )
        file_paths.append(file_path)

    return file_paths


def create_version_specific_files(directory, version_dirs, model_id=0):
    """
    Create files for testing version upgrades with specific changes.

    This function creates 3 files for a first version, then creates modified
    versions of those files for a second version, with only the middle file changing.
    Files have the same variable but different time ranges and unique filenames
    that include the time range to avoid collisions in the DRS structure.

    Args:
        directory: Base directory
        version_dirs: Dict mapping version names to directories
        model_id: Model identifier (index or name)

    Returns:
        Tuple of lists (first_version_files, second_version_files)
    """
    # Ensure model_id is a valid model
    if isinstance(model_id, int) or (isinstance(model_id, str) and model_id.isdigit()):
        model_id = VALID_MODELS[int(model_id) % len(VALID_MODELS)]

    # Create files with the same variable but different time ranges
    time_ranges = [(1, 10), (10, 20), (20, 30)]
    variable_id = VALID_VARIABLES[0]  # Use the same variable for all files

    # Create first version files
    first_version_files = []
    for i, time_range in enumerate(time_ranges):
        subfolder = version_dirs["v1"] / f"subfolder_{i}"
        subfolder.mkdir(exist_ok=True, parents=True)

        # Include time range in filename to ensure uniqueness
        time_start, time_end = time_range
        filename = (
            subfolder
            / f"{PROJECT_ID}_{model_id}_{variable_id}_time{time_start}-{time_end}.nc"
        )
        file_path = _create_base_netcdf_file(
            filename, model_id, variable_id, time_range, version=1
        )
        first_version_files.append(file_path)

    # Create second version files - same as first but with version=2 to have different data
    second_version_files = []
    for i, time_range in enumerate(time_ranges):
        subfolder = version_dirs["v2"] / f"subfolder_{i}"
        subfolder.mkdir(exist_ok=True, parents=True)

        # Include time range in filename to ensure uniqueness
        time_start, time_end = time_range
        filename = (
            subfolder
            / f"{PROJECT_ID}_{model_id}_{variable_id}_time{time_start}-{time_end}.nc"
        )
        file_path = _create_base_netcdf_file(
            filename, model_id, variable_id, time_range, version=2
        )
        second_version_files.append(file_path)

    return first_version_files, second_version_files


# Legacy function for backward compatibility
def create_sample_netcdf_files(directory, count=3, version=1, time_ranges=None):
    """
    Create sample NetCDF files with attributes for DRS structure.

    Legacy function that combines aspects of the more specific functions.

    Args:
        directory: Directory to create files in
        count: Number of files to create
        version: Version number to modify data slightly
        time_ranges: Optional list of tuples with (start, end) time ranges for each file
    """
    # List to store file paths for return
    file_paths = []

    # Default time ranges if not provided
    if time_ranges is None:
        # Create three files with distinct time ranges: 1:10, 10:20, 20:30
        time_ranges = (
            [(1, 10), (10, 20), (20, 30)]
            if count == 3
            else [(i * 10, (i + 1) * 10) for i in range(count)]
        )

    # Use valid models and variables
    model_id = VALID_MODELS[0]  # Use first valid model

    for i in range(count):
        # Create a folder structure to simulate real data organization
        subfolder = directory / f"subfolder_{i}"
        subfolder.mkdir(exist_ok=True, parents=True)

        # Create NetCDF file with DRS-relevant attributes
        variable_id = VALID_VARIABLES[i % len(VALID_VARIABLES)]
        filename = subfolder / f"{PROJECT_ID}_{model_id}_{variable_id}.nc"

        # Get time range for this file
        time_range = time_ranges[i] if i < len(time_ranges) else (i * 10, (i + 1) * 10)

        file_path = _create_base_netcdf_file(
            filename, model_id, variable_id, time_range, version=version
        )
        file_paths.append(file_path)

    return file_paths
