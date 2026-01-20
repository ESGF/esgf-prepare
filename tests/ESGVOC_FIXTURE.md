# esgvoc Configuration Fixture for Tests

## Overview

A pytest session-scoped fixture that automatically configures and installs esgvoc controlled vocabularies in an **isolated test environment**. This ensures:
- Tests have access to ESGF project vocabularies without manual setup
- User's personal esgvoc configuration is preserved and not affected
- Test configuration is completely isolated from user configuration
- After tests complete, the original user configuration is restored

## Implementation

### Location
`tests/conftest.py` - Session-scoped fixture with `autouse=True`

### How It Works

1. **Save User Configuration**: Stores the current active esgvoc configuration name
2. **Create Test Configuration**: Creates isolated `esgprep_cv_test` configuration
3. **Switch to Test Config**: Switches esgvoc to use test configuration
4. **Synchronize Vocabularies**: Downloads vocabularies (~100MB) and builds SQLite databases (first run only)
5. **Run Tests**: All tests execute with isolated test configuration
6. **Restore User Config**: After all tests, switches back to original user configuration
7. **Smart Caching**: If `esgprep_cv_test` exists and is synchronized, reuses it immediately

### Configuration Isolation

This fixture uses the same pattern as `esgvoc`'s own `test_cv` application to ensure complete isolation:

```python
# Before tests
User config: "default_test" (active) → Saved
Test config: "esgprep_cv_test" (created) → Activated

# During tests
Active config: "esgprep_cv_test"
Data directory: ~/.local/share/esgvoc/esgprep_cv_test/

# After tests
Test config: "esgprep_cv_test" (kept for next run)
User config: "default_test" → Restored as active
```

### Configuration File

The test configuration is loaded from **`tests/esgvoc_test_config.toml`**. This file allows you to:
- Match your development environment's esgvoc setup
- Use the same vocabulary branches you're working with
- Easily modify test configuration without changing code

**Example configuration:**
```toml
[[projects]]
project_name = "cmip6"
github_repo = "https://github.com/WCRP-CMIP/CMIP6_CVs"
branch = "esgvoc_dev"  # Use same branch as your dev environment
local_path = "repos/CMIP6_CVs"
db_path = "dbs/cmip6.sqlite"
offline_mode = false
```

**To modify**: Edit `tests/esgvoc_test_config.toml` to match your `esgvoc config show <your-config>` output.

### Configuration Details

The default test configuration includes:

```python
{
    "universe": {
        "github_repo": "https://github.com/WCRP-CMIP/WCRP-universe",
        "branch": "esgvoc",
        "local_path": "repos/WCRP-universe",
        "db_path": "dbs/universe.sqlite",
        "offline_mode": False,
    },
    "projects": [
        {
            "project_name": "cmip6",
            "github_repo": "https://github.com/WCRP-CMIP/CMIP6_CVs",
            "branch": "esgvoc",
            "local_path": "repos/CMIP6_CVs",
            "db_path": "dbs/cmip6.sqlite",
            "offline_mode": False,
        },
        {
            "project_name": "cmip6plus",
            "github_repo": "https://github.com/WCRP-CMIP/CMIP6Plus_CVs",
            "branch": "esgvoc",
            "local_path": "repos/CMIP6Plus_CVs",
            "db_path": "dbs/cmip6plus.sqlite",
            "offline_mode": False,
        }
    ]
}
```

## Usage

### For Test Writers

**No explicit usage required!** The fixture runs automatically before all tests.

```python
def test_something():
    """Your test can immediately use esgvoc."""
    import esgvoc.api as ev

    # This will work because configure_esgvoc ran first
    projects = ev.get_all_projects()
    assert "cmip6" in projects
```

### First Time Running Tests

The first time you run pytest after cloning the repository:

```bash
pytest tests/
```

You'll see output like:

```
[esgvoc] Configuring controlled vocabularies for tests...
[esgvoc] Saving test configuration...
[esgvoc] Installing controlled vocabularies (this may take a few minutes)...
Building Universe DB from repos/WCRP-universe
Filling Universe DB
Building Project DB from repos/CMIP6_CVs
Filling project DB
Building Project DB from repos/CMIP6Plus_CVs
Filling project DB
[esgvoc] Configuration complete
```

**Subsequent runs** will be fast:
```
[esgvoc] Already configured and installed
```

## What Gets Installed

The fixture downloads and configures:

1. **WCRP Universe** (~8MB database)
   - Common data descriptors used across all ESGF projects
   - Terms like "institution", "frequency", "realm", etc.

2. **CMIP6 Project** (~2MB database)
   - CMIP6-specific controlled vocabularies
   - Experiment names, model names, institutions, etc.

3. **CMIP6Plus Project** (~1MB database)
   - CMIP6Plus controlled vocabularies
   - Extended CMIP6 vocabulary

Total download: ~100MB (repositories + databases)
Total disk space: ~150MB after building databases

## File Locations

Test configuration is **completely isolated** from user configuration:

```
~/.config/esgvoc/
├── config_registry.toml           # Registry of all configs
├── default_test.toml              # User's configuration (preserved)
└── esgprep_cv_test.toml          # Test configuration (isolated)

~/.local/share/esgvoc/
├── default_test/                  # User's data (untouched)
│   ├── repos/
│   └── dbs/
└── esgprep_cv_test/              # Test data (isolated)
    ├── repos/
    │   ├── WCRP-universe/        # Test vocabulary repository
    │   ├── CMIP6_CVs/            # Test CMIP6 vocabularies
    │   └── CMIP6Plus_CVs/        # Test CMIP6Plus vocabularies
    └── dbs/
        ├── universe.sqlite       # Test universe database
        ├── cmip6.sqlite          # Test CMIP6 database
        └── cmip6plus.sqlite      # Test CMIP6Plus database
```

**Key Point**: Tests never touch `~/.local/share/esgvoc/default_test/` or any other user configuration!

## Pytest Configuration

Added to `pyproject.toml`:

```toml
[tool.pytest.ini_options]
testpaths = ["tests"]
addopts = ["-v", "--strict-markers", "--tb=short"]
markers = [
    "integration: integration tests",
    "slow: slow running tests",
]
```

## Verification

A test file `tests/test_esgvoc_setup.py` verifies the fixture works:

```bash
# Run just the esgvoc verification tests
pytest tests/test_esgvoc_setup.py -v
```

Expected output:
```
tests/test_esgvoc_setup.py::test_esgvoc_is_configured PASSED
✓ esgvoc configured with 15 descriptors and 2 projects

tests/test_esgvoc_setup.py::test_esgvoc_vocabulary_access PASSED
✓ Successfully accessed 500+ universe terms and 100+ cmip6 terms

tests/test_esgvoc_setup.py::test_esgvoc_project_validation PASSED
✓ Found 50+ institutions in cmip6
```

## Troubleshooting

### "No module named 'esgvoc'"
- Make sure esgvoc is installed: `pip install esgvoc>=1.2.1`
- Or install with dev dependencies: `uv sync`

### "Failed to fetch GitHub version"
- Check internet connection
- GitHub rate limiting (wait a few minutes)
- Or use offline mode (requires repos already cloned)

### "Controlled vocabularies are not initialized"
- The fixture should handle this automatically
- If you see this in tests, check that conftest.py is being loaded
- Run: `pytest --fixtures` to see available fixtures

### Tests are slow on first run
- Expected! First run downloads ~100MB and builds databases
- This only happens once per test environment
- Subsequent runs are fast (just checks if already installed)

### Want to re-download vocabularies
```bash
# Delete the test configuration
rm ~/.config/esgvoc/test.toml
rm -rf ~/.local/share/esgvoc/test/

# Next pytest run will re-download everything
pytest tests/
```

## Benefits

1. **Complete Isolation**: User's esgvoc configuration is never modified or affected
2. **No Manual Setup**: Tests "just work" without requiring `esgvoc install`
3. **Fast CI/CD**: Test vocabulary data is cached between test runs
4. **Consistent Environment**: All tests use the same isolated vocabulary configuration
5. **Automatic Cleanup**: User configuration automatically restored after tests
6. **No Test Pollution**: Session scope means one-time setup, no per-test overhead
7. **Safe Development**: Developers can work on esgvoc projects while running tests

## Related Files

- `tests/conftest.py` - Fixture implementation
- `tests/README.md` - Test documentation
- `tests/test_esgvoc_setup.py` - Verification tests
- `pyproject.toml` - Pytest configuration
- `esgprep/_contexts/multiprocessing.py` - Error handling for missing esgvoc

## See Also

- [esgvoc Documentation](https://github.com/IPSL-ESGF/esgvoc)
- [WCRP Universe](https://github.com/WCRP-CMIP/WCRP-universe)
- [CMIP6 CVs](https://github.com/WCRP-CMIP/CMIP6_CVs)
