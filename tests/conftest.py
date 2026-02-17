"""
Global pytest configuration and fixtures for the esgf-prepare test suite.
"""

import tempfile
import shutil
from pathlib import Path
import pytest
import toml

from tests.fixtures.generators import clean_directory


@pytest.fixture(scope="session", autouse=False)
def configure_esgvoc():
    """
    Configure and install esgvoc vocabularies in isolated test environment.

    This fixture:
    1. Saves the current user's esgvoc configuration
    2. Creates a temporary "esgprep_cv_test" configuration
    3. Switches to test configuration and synchronizes vocabularies
    4. Runs all tests with isolated configuration
    5. Restores original user configuration after tests complete

    This ensures tests don't interfere with user's esgvoc setup.
    """
    import esgvoc.core.service as service
    from esgvoc.core.service.configuration.setting import ServiceSettings

    # Test configuration name
    TEST_CONFIG_NAME = "esgprep_cv_test"
    original_config_name = None
    config_manager = None

    try:
        # Get config manager and save original configuration
        config_manager = service.get_config_manager()
        original_config_name = config_manager.get_active_config_name()

        print(f"\n[esgvoc] Saving current user configuration: {original_config_name}")

        # Check if test configuration already exists and is synchronized
        configs = config_manager.list_configs()
        test_config_exists = TEST_CONFIG_NAME in configs

        if test_config_exists:
            # Switch to test config and check if it's synchronized
            print(f"[esgvoc] Test configuration '{TEST_CONFIG_NAME}' already exists")
            config_manager.switch_config(TEST_CONFIG_NAME)

            # Update data_config_dir for test configuration
            config_manager.data_config_dir = config_manager.data_dir / TEST_CONFIG_NAME
            config_manager.data_config_dir.mkdir(parents=True, exist_ok=True)

            # Create fresh StateService with test configuration
            test_config = config_manager.get_config(TEST_CONFIG_NAME)
            service.current_state = service.StateService(test_config)

        else:
            # Create new test configuration
            print(f"[esgvoc] Creating test configuration: {TEST_CONFIG_NAME}")

            # Load test configuration from file
            test_config_file = Path(__file__).parent / "esgvoc_test_config.toml"

            if test_config_file.exists():
                print(f"[esgvoc] Loading test configuration from: {test_config_file}")
                test_config_data = toml.load(test_config_file)
            else:
                # Fallback to default settings if config file doesn't exist
                print(f"[esgvoc] Warning: {test_config_file} not found, using defaults")
                import copy

                test_config_data = copy.deepcopy(
                    ServiceSettings._get_default_settings()
                )

                # Ensure offline_mode is False
                test_config_data["universe"]["offline_mode"] = False
                for project in test_config_data["projects"]:
                    project["offline_mode"] = False

            # Add test configuration
            config_manager.add_config(TEST_CONFIG_NAME, test_config_data)

            # Switch to test configuration
            config_manager.switch_config(TEST_CONFIG_NAME)
            print(f"[esgvoc] Switched to test configuration: {TEST_CONFIG_NAME}")

            # Update data_config_dir for test configuration
            config_manager.data_config_dir = config_manager.data_dir / TEST_CONFIG_NAME
            config_manager.data_config_dir.mkdir(parents=True, exist_ok=True)

            # Create fresh StateService with test configuration
            test_config = config_manager.get_config(TEST_CONFIG_NAME)
            service.current_state = service.StateService(test_config)

        # Synchronize vocabularies for test configuration
        print(
            "[esgvoc] Synchronizing test vocabularies (this may take a few minutes on first run)..."
        )
        service.current_state.synchronize_all()
        print("[esgvoc] Test environment ready\n")

        # Just yield - don't pass state to tests, they use the global state
        yield

    finally:
        # Cleanup: Restore original configuration
        if config_manager and original_config_name:
            try:
                print(
                    f"\n[esgvoc] Restoring user configuration: {original_config_name}"
                )

                # Switch back to original configuration
                config_manager.switch_config(original_config_name)

                # Restore original data_config_dir
                config_manager.data_config_dir = (
                    config_manager.data_dir / original_config_name
                )
                config_manager.data_config_dir.mkdir(parents=True, exist_ok=True)

                # Recreate StateService with original configuration
                original_config = config_manager.get_config(original_config_name)
                service.current_state = service.StateService(original_config)

                print(f"[esgvoc] User configuration restored: {original_config_name}")

                # Note: We don't remove the test configuration to avoid re-downloading
                # on subsequent test runs. It's isolated in its own directory.

            except Exception as e:
                print(f"[esgvoc] Warning: Failed to restore configuration: {e}")
                import traceback

                traceback.print_exc()


@pytest.fixture
def tmp_dir():
    """Create a temporary directory for test outputs."""
    tmp_path = Path(tempfile.mkdtemp(prefix="esgf_test_"))
    yield tmp_path
    # Cleanup
    if tmp_path.exists():
        shutil.rmtree(tmp_path)


@pytest.fixture
def test_data_dir():
    """Provide the path to test data fixtures."""
    return Path(__file__).parent / "fixtures" / "sample_data"


@pytest.fixture
def real_data_dir():
    """Provide the path to real test data."""
    return Path(__file__).parent / "fixtures" / "real_data"


@pytest.fixture
def clean_tmp_dir(tmp_dir):
    """Provide a clean temporary directory that gets cleaned after each test."""
    clean_directory(tmp_dir)
    yield tmp_dir
    clean_directory(tmp_dir)


@pytest.fixture
def drs_test_structure(tmp_dir):
    """Create a basic DRS directory structure for testing."""
    drs_root = tmp_dir / "drs_root"
    incoming = tmp_dir / "incoming"

    # Create directories
    drs_root.mkdir(parents=True)
    incoming.mkdir(parents=True)

    return {"root": drs_root, "incoming": incoming, "tmp_dir": tmp_dir}


@pytest.fixture(scope="session")
def project_root():
    """Provide the project root directory."""
    return Path(__file__).parent.parent


def pytest_configure(config):
    """Configure pytest with custom markers."""
    config.addinivalue_line(
        "markers",
        "integration: marks tests as integration tests (deselect with '-m \"not integration\"')",
    )
    config.addinivalue_line("markers", "slow: marks tests as slow running")
    config.addinivalue_line("markers", "skip_this: marks tests to be skipped")
