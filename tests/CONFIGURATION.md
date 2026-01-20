# Test Configuration Guide

## Overview

The esgprep test suite uses an **isolated esgvoc configuration** to ensure tests don't interfere with your personal development environment. This configuration is defined in `tests/esgvoc_test_config.toml`.

## Why Isolated Configuration?

1. **Preserve User Setup**: Your personal esgvoc configuration remains untouched
2. **Reproducible Tests**: All developers use the same vocabulary branches
3. **Safe Testing**: Test different vocabulary versions without affecting your work
4. **Easy Modification**: Change test configuration without modifying code

## Configuration File: `esgvoc_test_config.toml`

This file defines which vocabulary repositories and branches to use for testing.

### Current Configuration

```toml
[[projects]]
project_name = "cmip6"
github_repo = "https://github.com/WCRP-CMIP/CMIP6_CVs"
branch = "esgvoc_dev"
local_path = "repos/CMIP6_CVs"
db_path = "dbs/cmip6.sqlite"
offline_mode = false

[[projects]]
project_name = "cmip6plus"
github_repo = "https://github.com/WCRP-CMIP/CMIP6Plus_CVs"
branch = "esgvoc_dev"
local_path = "repos/CMIP6Plus_CVs"
db_path = "dbs/cmip6plus.sqlite"
offline_mode = false

[universe]
github_repo = "https://github.com/WCRP-CMIP/WCRP-universe"
branch = "esgvoc_dev"
local_path = "repos/WCRP-universe"
db_path = "dbs/universe.sqlite"
offline_mode = false
```

### Matching Your Development Environment

To ensure tests use the same vocabularies as your development environment:

1. **Check your current configuration**:
   ```bash
   uv run esgvoc config show <your-config-name>
   ```

2. **Copy the output to `tests/esgvoc_test_config.toml`**:
   - Keep the same `branch` values
   - Keep the same `github_repo` URLs
   - Match your development setup exactly

3. **Example**: If your dev environment uses:
   - Universe branch: `esgvoc_dev`
   - CMIP6 branch: `esgvoc_dev`

   Then `esgvoc_test_config.toml` should use the same branches.

## How It Works

### Before Tests Run

1. **Save User Config**:
   ```
   Active config: "default_test" → Saved for later
   ```

2. **Create Test Config**:
   ```
   Load: tests/esgvoc_test_config.toml
   Create: ~/.config/esgvoc/esgprep_cv_test.toml
   ```

3. **Switch to Test Config**:
   ```
   Active config: "esgprep_cv_test"
   Data directory: ~/.local/share/esgvoc/esgprep_cv_test/
   ```

4. **Synchronize Vocabularies** (first run only):
   ```
   Download: WCRP-universe, CMIP6_CVs, CMIP6Plus_CVs
   Build databases: universe.sqlite, cmip6.sqlite, cmip6plus.sqlite
   ```

### During Tests

All tests use the isolated `esgprep_cv_test` configuration:
- Access vocabularies from `~/.local/share/esgvoc/esgprep_cv_test/`
- User's configuration is untouched
- User's data is untouched

### After Tests Complete

1. **Restore User Config**:
   ```
   Active config: "default_test" → Restored
   Data directory: ~/.local/share/esgvoc/default_test/
   ```

2. **Keep Test Config**:
   ```
   Test config: "esgprep_cv_test" → Kept for next run
   ```

## Verification

### Check Active Configuration

After running tests, verify your configuration was restored:

```bash
uv run python << 'EOF'
from esgvoc.core.service import config_manager
print(f"Active: {config_manager.get_active_config_name()}")
EOF
```

Should output: `Active: default_test` (or your original config name)

### Compare Configurations

Verify test config matches your dev environment:

```bash
# Your dev configuration
uv run esgvoc config show default_test

# Test configuration
uv run esgvoc config show esgprep_cv_test
```

Both should use the same `branch` values!

## Modifying Test Configuration

### Change Vocabulary Branches

Edit `tests/esgvoc_test_config.toml`:

```toml
# Use a different branch for testing
branch = "main"  # Instead of "esgvoc_dev"
```

Then remove and recreate the test configuration:

```bash
# Remove old test config
echo "y" | uv run esgvoc config remove esgprep_cv_test

# Run tests to create new config
uv run pytest tests/
```

### Add More Projects

Edit `tests/esgvoc_test_config.toml`:

```toml
[[projects]]
project_name = "cordex-cmip6"
github_repo = "https://github.com/WCRP-CORDEX/CORDEX-CMIP6_CVs"
branch = "esgvoc"
local_path = "repos/CORDEX-CMIP6_CVs"
db_path = "dbs/cordex-cmip6.sqlite"
offline_mode = false
```

### Use Local Repositories (Offline Mode)

For faster tests when you have local vocabulary repositories:

```toml
[[projects]]
project_name = "cmip6"
github_repo = "https://github.com/WCRP-CMIP/CMIP6_CVs"
branch = "esgvoc_dev"
local_path = "repos/CMIP6_CVs"
db_path = "dbs/cmip6.sqlite"
offline_mode = true  # Don't fetch from GitHub
```

**Note**: Local repositories must already exist in `~/.local/share/esgvoc/esgprep_cv_test/repos/`

## Troubleshooting

### Tests Use Wrong Branch

**Symptom**: Tests fail or use outdated vocabularies

**Solution**:
```bash
# Check test configuration
uv run esgvoc config show esgprep_cv_test

# If branches don't match your dev environment:
# 1. Edit tests/esgvoc_test_config.toml
# 2. Remove test config
echo "y" | uv run esgvoc config remove esgprep_cv_test

# 3. Run tests to recreate
uv run pytest tests/
```

### Test Config Not Restored

**Symptom**: After tests, active config is still `esgprep_cv_test`

**Solution**:
```bash
# Manually switch back
uv run python << 'EOF'
from esgvoc.core.service import config_manager
config_manager.switch_config("default_test")
EOF
```

### Want to Clean Up Test Data

**Symptom**: Test configuration taking up disk space

**Solution**:
```bash
# Remove test configuration
echo "y" | uv run esgvoc config remove esgprep_cv_test

# Remove test data
rm -rf ~/.local/share/esgvoc/esgprep_cv_test/

# Next test run will recreate everything
```

## Best Practices

1. **Keep Configuration Synced**: Regularly update `esgvoc_test_config.toml` to match your dev environment
2. **Use Same Branches**: Test and dev should use the same vocabulary branches
3. **Commit Configuration**: The `esgvoc_test_config.toml` file should be committed to git
4. **Document Changes**: If you change branches, document why in commit messages
5. **Clean Rebuilds**: When vocabulary structure changes, remove test config to force rebuild

## Files and Locations

```
esgf-prepare/
├── tests/
│   ├── esgvoc_test_config.toml    # Test configuration (version controlled)
│   ├── conftest.py                # Fixture that loads configuration
│   └── CONFIGURATION.md           # This file

~/.config/esgvoc/
├── default_test.toml              # Your configuration (preserved)
└── esgprep_cv_test.toml          # Test configuration (created from esgvoc_test_config.toml)

~/.local/share/esgvoc/
├── default_test/                  # Your data (never touched by tests)
└── esgprep_cv_test/              # Test data (isolated)
    ├── repos/                     # Vocabulary repositories
    │   ├── WCRP-universe/
    │   ├── CMIP6_CVs/
    │   └── CMIP6Plus_CVs/
    └── dbs/                       # SQLite databases
        ├── universe.sqlite
        ├── cmip6.sqlite
        └── cmip6plus.sqlite
```

## Summary

- **Configuration File**: `tests/esgvoc_test_config.toml` defines test environment
- **Isolation**: Tests never modify your personal esgvoc configuration
- **Automatic**: Fixture handles all setup and cleanup automatically
- **Modifiable**: Easy to change branches and repositories for testing
- **Reproducible**: All developers use the same test configuration
