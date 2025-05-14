# DRS Tests

This directory contains tests for the DRS (Data Reference Syntax) module of esgprep.

## Overview

The tests in this directory verify the correct functionality of the DRS processor,
which handles the organization of data files according to ESGF DRS specifications.

## Test Structure

The tests are organized into multiple files for better maintainability:

- `test_utils.py`: Common utilities for test functions
- `conftest.py`: Pytest fixtures for test setup
- `test_drs_basic.py`: Basic DrsProcessor functionality tests
- `test_drs_operations.py`: Tests for executing DRS operations
- `test_drs_migration_modes.py`: Tests for different migration modes (copy, link, symlink)
- `test_drs_custom_values.py`: Tests for custom facet values
- `test_drs_ignores.py`: Tests for ignoring files
- `test_drs_version_update.py`: Tests for version updates (method (a) in documentation)
- `test_drs_upgrade_from_latest.py`: Tests for upgrade from latest (method (b) in documentation)
- `run_tests.py`: Simple entry point for running all tests

## Upgrade Methods

The tests specifically cover the two upgrade methods described in the documentation:

1. **Method (a) - Default**: The incoming directory must contain the complete contents
   of the new version of the dataset. If a file is unchanged from the previous version,
   it must still be supplied in incoming, although esgprep will detect that it is
   unmodified, and will optimize disk space by removing duplicates and symlinking to
   the old version instead. Any files that are not supplied are treated as removed in
   the new version.

2. **Method (b) - With `--upgrade-from-latest`**: The new version of the dataset is
   based primarily on the previous published version. The user supplies in the incoming
   directory (or directories) only the files which are modified in the new version.
   Any file not supplied in incoming is considered to be the same as in the previous
   version, and a symlink is created accordingly.

### Observed Behavior

Based on testing, here's how the upgrade methods behave:

- In method (a), all files must be provided in the incoming directory, and they will all
  appear in the version directory (vXXXXXXXX).

- In method (b), only provide the modified files in the incoming directory. Only these files
  will appear in the new version directory (vXXXXXXXX). The files from the previous version
  are NOT automatically copied to the new version directory. The "latest" symlink will be
  updated to point to the new version, but that version will only contain the modified files.

- In both methods, the "files/dXXXXXXXX" directories will contain the actual files, with one
  directory per version, and files are only present in the version where they were added or
  modified.

## NetCDF File Creation Utilities

The test utilities provide specialized functions to create different types of NetCDF files
for testing various DRS scenarios:

- `create_files_different_models`: Creates files with same variable but different models
- `create_files_different_variables`: Creates files with same model but different variables
- `create_files_different_times`: Creates files with same model and variable but different time ranges
- `create_files_different_versions`: Creates files with same model, variable, time but different versions
- `create_files_different_members`: Creates files with same model, variable, time, version but different member IDs
- `create_version_specific_files`: Creates files for testing version upgrades with specific changes

Each function is designed for a specific test scenario, making the tests more readable
and focused.

## Running the Tests

To run all tests in this directory:

```bash
python -m pytest -v esgprep/tests/drs
```

Or use the run_tests.py script:

```bash
python esgprep/tests/drs/run_tests.py
```
