"""
Test to verify esgvoc is properly configured and accessible.

This test verifies that esgvoc:
- Has vocabulary databases available
- Makes vocabulary data accessible via the public API
"""


def test_esgvoc_is_configured():
    """Test that esgvoc is properly configured."""
    import esgvoc.api as ev

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

    # Test that we can get project list
    projects = ev.get_all_projects()
    assert "cmip6" in projects, "cmip6 should be available"

    # Test that we can get project specs
    cmip6_specs = ev.get_project("cmip6")
    assert cmip6_specs is not None, "cmip6 specs should be accessible"
    assert cmip6_specs.drs_specs is not None, "cmip6 should have DRS specs"

    # Test active database info for cmip6
    db_info = ev.get_active_database_info("cmip6")
    assert db_info is not None, "Should have active database info for cmip6"

    print(
        f"\n✓ Verified {len(projects)} projects are configured"
    )
