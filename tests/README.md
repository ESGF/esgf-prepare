# Test Structure Documentation

This directory contains the reorganized test suite for esgf-prepare, providing a cleaner and more maintainable testing structure.

## Structure Overview

```
tests_new/
├── unit/                           # Unit tests
│   ├── test_drs_make.py           # DRS creation functionality
│   ├── test_drs_latest.py         # DRS latest symlink management
│   ├── test_mapfile_make.py       # Mapfile generation
│   └── test_multihash.py          # Multihash functionality
├── integration/                    # Integration tests
│   ├── test_full_workflow.py      # Complete DRS + mapfile workflow
│   └── test_multihash_integration.py  # End-to-end multihash testing
├── fixtures/                      # Test utilities and data
│   ├── generators.py              # NetCDF test file generation
│   ├── validators.py              # DRS structure validation
│   ├── conftest.py                # Pytest fixtures for test data
│   ├── sample_data/               # Generated test data (gitignored)
│   │   ├── incoming/              # Input test data templates
│   │   └── expected/              # Expected output structures
│   └── real_data/                 # Real NetCDF files for integration tests
│       └── incoming/
├── tmp/                           # Temporary test outputs (gitignored)
└── conftest.py                    # Global pytest configuration
```

## Key Improvements

### 1. Clear Separation of Concerns
- **Unit tests**: Test individual components in isolation
- **Integration tests**: Test complete workflows with real data
- **Fixtures**: Centralized test utilities and data management

### 2. Reusable Test Utilities
- `generators.py`: Create NetCDF files with various characteristics
- `validators.py`: Validate DRS structures for compliance
- Pytest fixtures for common test setup/teardown

### 3. Organized Test Data
- **Generated data**: Created on-demand for specific test scenarios
- **Real data**: Small subset of actual NetCDF files for integration testing
- **Temporary data**: Isolated test outputs that don't interfere with each other

### 4. Better Test Configuration
- Global pytest configuration with custom markers
- Integration test marking for selective test execution
- Proper fixture scoping for performance

## Running Tests

### Run All Tests
```bash
pytest tests_new/
```

### Run Only Unit Tests
```bash
pytest tests_new/unit/
```

### Run Only Integration Tests
```bash
pytest tests_new/integration/
```

### Run Tests Excluding Integration Tests
```bash
pytest tests_new/ -m "not integration"
```

### Run Specific Test Categories
```bash
# Run only slow tests
pytest tests_new/ -m "slow"

# Run excluding slow tests
pytest tests_new/ -m "not slow"
```

## Test Markers

- `@pytest.mark.integration`: Integration tests that may take longer
- `@pytest.mark.slow`: Tests that are particularly slow running
- `@pytest.mark.skip_this`: Tests that should be skipped

## Fixtures Available

### Global Fixtures (conftest.py)
- `tmp_dir`: Temporary directory for test outputs
- `test_data_dir`: Path to test data fixtures
- `real_data_dir`: Path to real test data
- `clean_tmp_dir`: Clean temporary directory
- `drs_test_structure`: Basic DRS directory structure
- `project_root`: Project root directory

### Test Data Fixtures (fixtures/conftest.py)
- `netcdf_generator`: Access to NetCDF generation functions
- `sample_netcdf_files`: Pre-created sample NetCDF files

## Migration from Old Structure

The old test structure (`tests/` and `esgprep/tests/`) is kept for backwards compatibility but should be gradually migrated to this new structure. Key differences:

1. **Centralized utilities**: No more duplicated test utilities
2. **Proper isolation**: Each test gets its own temporary directory
3. **Clear naming**: Test files clearly indicate what they test
4. **Better organization**: Logical separation of unit vs integration tests

## Contributing

When adding new tests:

1. **Unit tests**: Add to `unit/` directory, test single components
2. **Integration tests**: Add to `integration/` directory, test workflows
3. **Test utilities**: Add to `fixtures/` directory if reusable
4. **Use fixtures**: Leverage existing fixtures for common setup
5. **Mark appropriately**: Use pytest markers for categorization

## Test Data Management

- **Never commit large files**: Use gitignore for temporary and generated data
- **Keep real data minimal**: Only essential files for integration testing
- **Generate on demand**: Use generators for synthetic test data
- **Clean up**: Tests should clean up their temporary data