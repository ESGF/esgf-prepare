"""
Test to verify esgvoc configuration fixture works correctly.

This test verifies that the configure_esgvoc fixture properly:
- Configures esgvoc with test settings
- Downloads vocabularies from GitHub
- Builds SQLite databases
- Makes vocabulary data accessible to tests
"""


def test_esgvoc_is_configured():
    """Test that esgvoc is properly configured after fixture runs."""
    from esgvoc.core.service import current_state
    import esgvoc.api as ev

    # Check that universe connection is initialized
    assert current_state.universe.db_connection is not None, (
        "Universe database connection should be initialized"
    )

    # Check that we can access vocabularies
    descriptors = ev.get_all_data_descriptors_in_universe()
    assert len(descriptors) > 0, "Should have data descriptors"
    assert "institution" in descriptors, "Should have 'institution' descriptor"

    # Check that projects are available
    projects = ev.get_all_projects()
    assert len(projects) > 0, "Should have projects"
    assert "cmip6" in projects, "Should have cmip6 project"

    print(
        f"\n✓ esgvoc configured with {len(descriptors)} descriptors and {len(projects)} projects"
    )


def test_esgvoc_vocabulary_access():
    """Test that we can query vocabulary data."""
    import esgvoc.api as ev

    # Test getting all data descriptors
    descriptors = ev.get_all_data_descriptors_in_universe()
    assert len(descriptors) > 0, "Should have data descriptors"
    assert "institution" in descriptors, "Should have 'institution' descriptor"

    # Test getting all projects
    projects = ev.get_all_projects()
    assert len(projects) > 0, "Should have projects"
    assert "cmip6" in projects, "Should have cmip6"

    print(
        f"\n✓ Successfully accessed {len(descriptors)} universe descriptors and {len(projects)} projects"
    )


def test_esgvoc_project_basics():
    """Test basic project access."""
    import esgvoc.api as ev
    from esgvoc.core.service import current_state

    # Test that we can get project list
    projects = ev.get_all_projects()
    assert "cmip6" in projects, "cmip6 should be available"
    assert "cmip6plus" in projects, "cmip6plus should be available"

    # Test that projects have database connections
    assert current_state.projects["cmip6"].db_connection is not None, (
        "cmip6 should have database connection"
    )
    assert current_state.projects["cmip6plus"].db_connection is not None, (
        "cmip6plus should have database connection"
    )

    print(
        f"\n✓ Verified {len(projects)} projects are configured with database connections"
    )
