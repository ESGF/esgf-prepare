"""
Unit tests for DRS make functionality.

Tests the core functionality of creating DRS directory structures
from incoming NetCDF files using the esgdrs make command.
"""

import re
from argparse import Namespace
import pytest

from esgprep.esgdrs import run
from tests.fixtures.generators import (
    create_files_different_variables,
    create_files_different_times,
    create_files_different_members,
    create_files_different_models,
    create_cmip7_file,
)
from tests.fixtures.validators import DRSValidator
# TODO : fix all


def get_default_make_args(incoming_dir, drs_root) -> Namespace:
    """Get default arguments for the DRS make command."""
    return Namespace(
        cmd="make",
        log=None,
        debug=False,
        action="upgrade",
        directory=[str(incoming_dir)],
        project="cmip6",
        ignore_dir=re.compile("^.*/(files|\\.[\\w]*).*$"),
        include_file=["^.*\\.nc$"],
        exclude_file=["^\\..*$"],
        color=False,
        no_color=False,
        max_processes=1,
        root=str(drs_root),
        version="v19810101",
        set_value=None,
        set_key=None,
        rescan=True,
        commands_file=None,
        overwrite_commands_file=False,
        upgrade_from_latest=False,
        ignore_from_latest=None,
        ignore_from_incoming=None,
        copy=True,
        link=False,
        symlink=False,
        no_checksum=False,
        checksums_from=None,
        quiet=False,
        prog="esgdrs",
    )


class TestDRSMake:
    """Test class for DRS make functionality."""

    def test_make_different_variables(self, drs_test_structure):
        """Test DRS creation from files with different variables."""
        incoming_dir = drs_test_structure["incoming"] / "incoming1"
        drs_root = drs_test_structure["root"]

        # Create test files with different variables
        create_files_different_variables(incoming_dir, count=3)

        # Run DRS make
        args = get_default_make_args(incoming_dir, drs_root)
        run(args)

        # Validate DRS structure was created
        expected_drs_path = (
            drs_root
            / "CMIP6"
            / "CMIP"
            / "IPSL"
            / "IPSL-CM6A-LR"
            / "historical"
            / "r1i1p1f1"
            / "day"
            / "hur"
            / "gn"
        )

        validator = DRSValidator(expected_drs_path)
        assert validator.validate_all(upgrade_from_latest=False, verbose=False)

    def test_make_different_times(self, drs_test_structure):
        """Test DRS creation with files containing different time ranges."""
        incoming_dir = drs_test_structure["incoming"] / "incoming2"
        drs_root = drs_test_structure["root"]

        # Create test files with different time ranges
        create_files_different_times(incoming_dir, count=3)

        # Run DRS make with a different version
        args = get_default_make_args(incoming_dir, drs_root)
        args.version = "v19810102"
        run(args)

        # Validate DRS structure
        expected_drs_path = (
            drs_root
            / "CMIP6"
            / "CMIP"
            / "IPSL"
            / "IPSL-CM6A-LR"
            / "historical"
            / "r1i1p1f1"
            / "day"
            / "tas"
            / "gn"
        )

        validator = DRSValidator(expected_drs_path)
        assert validator.validate_all(upgrade_from_latest=False, verbose=False)

    def test_make_different_members(self, drs_test_structure):
        """Test DRS creation with different member IDs."""
        incoming_dir = drs_test_structure["incoming"] / "incoming3"
        drs_root = drs_test_structure["root"]

        # Create test files with different members
        create_files_different_members(incoming_dir, count=3)

        # Run DRS make
        args = get_default_make_args(incoming_dir, drs_root)
        args.version = "v19810103"
        run(args)

        # Validate DRS structure for one of the members
        expected_drs_path = (
            drs_root
            / "CMIP6"
            / "CMIP"
            / "IPSL"
            / "IPSL-CM6A-LR"
            / "historical"
            / "r2i1p1f1"
            / "day"
            / "tas"
            / "gn"
        )

        validator = DRSValidator(expected_drs_path)
        assert validator.validate_all(upgrade_from_latest=False, verbose=False)

    def test_make_different_models(self, drs_test_structure):
        """Test DRS creation with different source models."""
        incoming_dir = drs_test_structure["incoming"] / "incoming4"
        drs_root = drs_test_structure["root"]

        # Create test files with different models
        create_files_different_models(incoming_dir, count=3)

        # Run DRS make
        args = get_default_make_args(incoming_dir, drs_root)
        args.version = "v19810104"
        run(args)

        # Validate DRS structure for one of the models (NESM3)
        expected_drs_path = (
            drs_root
            / "CMIP6"
            / "CMIP"
            / "IPSL"
            / "NESM3"
            / "historical"
            / "r1i1p1f1"
            / "day"
            / "tas"
            / "gn"
        )

        validator = DRSValidator(expected_drs_path)
        assert validator.validate_all(upgrade_from_latest=False, verbose=False)

    def test_make_upgrade_from_latest(self, drs_test_structure):
        """Test DRS make with upgrade_from_latest functionality."""
        incoming_dir = drs_test_structure["incoming"]
        drs_root = drs_test_structure["root"]

        # First, create initial DRS structure
        incoming1 = incoming_dir / "incoming1"
        create_files_different_times(incoming1, count=3)

        args = get_default_make_args(incoming1, drs_root)
        args.version = "v19810101"
        run(args)

        # Now create additional files for upgrade
        incoming2 = incoming_dir / "incoming2"
        create_files_different_times(incoming2, count=3, variable_id="tas")

        # Run upgrade from latest
        args = get_default_make_args(incoming2, drs_root)
        args.version = "v19810102"
        args.upgrade_from_latest = True
        run(args)

        # Validate the upgraded structure
        expected_drs_path = (
            drs_root
            / "CMIP6"
            / "CMIP"
            / "IPSL"
            / "IPSL-CM6A-LR"
            / "historical"
            / "r1i1p1f1"
            / "day"
            / "tas"
            / "gn"
        )

        validator = DRSValidator(expected_drs_path)
        assert validator.validate_all(upgrade_from_latest=True, verbose=False)

    def test_make_empty_directory(self, drs_test_structure):
        """Test DRS make behavior with empty input directory."""
        incoming_dir = drs_test_structure["incoming"] / "empty"
        incoming_dir.mkdir()
        drs_root = drs_test_structure["root"]

        # Run DRS make on empty directory
        args = get_default_make_args(incoming_dir, drs_root)
        run(args)

        # Should not create any DRS structure
        cmip6_dir = drs_root / "CMIP6"
        assert not cmip6_dir.exists() or len(list(cmip6_dir.rglob("*"))) == 0

    def test_make_with_different_copy_modes(self, drs_test_structure):
        """Test DRS make with different file copy modes (copy, link, symlink)."""
        incoming_dir = drs_test_structure["incoming"] / "copy_test"
        drs_root = drs_test_structure["root"]

        # Create test files
        create_files_different_variables(incoming_dir, count=2)

        # Test with symlink mode
        args = get_default_make_args(incoming_dir, drs_root)
        args.copy = False
        args.symlink = True
        run(args)

        # Verify symlinks were created in version directory
        expected_drs_path = (
            drs_root
            / "CMIP6"
            / "CMIP"
            / "IPSL"
            / "IPSL-CM6A-LR"
            / "historical"
            / "r1i1p1f1"
            / "day"
            / "tas"
            / "gn"
        )

        validator = DRSValidator(expected_drs_path)
        assert validator.validate_all(upgrade_from_latest=False, verbose=False)

        # Check that files in version directory are symlinks
        version_dir = expected_drs_path / "v19810101"
        version_files = list(version_dir.glob("*.nc"))
        assert len(version_files) > 0
        for f in version_files:
            assert f.is_symlink(), f"File {f} should be a symlink"

    def test_make_project_mismatch_error(self, drs_test_structure, capfd):
        """Test that DRS make provides clear error message when project mismatches file attributes."""
        incoming_dir = drs_test_structure["incoming"]
        drs_root = drs_test_structure["root"]

        # Create test files with CMIP6 attributes
        create_files_different_variables(incoming_dir, count=1)

        # Try to process with wrong project (cmip7 instead of cmip6)
        args = get_default_make_args(incoming_dir, drs_root)
        args.project = "cmip7"  # Wrong project

        # Should raise a SystemExit exception due to errors
        with pytest.raises(SystemExit) as exc_info:
            run(args)

        # The error message is captured in stdout, so we need to check that the process failed
        assert exc_info.value.code == 1  # Should exit with error code 1

        # Capture the output and verify error message content
        captured = capfd.readouterr()
        output = captured.out + captured.err

        # Verify the error message contains expected information
        assert "Project mismatch" in output
        assert "CLI specified 'cmip7'" in output
        assert "file contains 'cmip6'" in output
        assert "Please use '--project cmip6'" in output
        assert "esgvoc status" in output

    def test_make_project_match_succeeds(self, drs_test_structure):
        """Test that DRS make succeeds when project matches file attributes."""
        incoming_dir = drs_test_structure["incoming"]
        drs_root = drs_test_structure["root"]

        # Create test files with CMIP6 attributes
        create_files_different_variables(incoming_dir, count=1)

        # Process with correct project (cmip6)
        args = get_default_make_args(incoming_dir, drs_root)
        args.project = "cmip6"  # Correct project

        # Should succeed without raising exception
        run(args)

        # Verify DRS structure was created
        cmip6_dir = drs_root / "CMIP6"
        assert cmip6_dir.exists()

        # Check that some files were processed
        nc_files = list(cmip6_dir.rglob("*.nc"))
        assert len(nc_files) > 0

    def test_make_cmip7_real_file(self, drs_test_structure):
        """Test DRS creation with real CMIP7 file.

        Uses a real CMIP7 file with CV-compliant attributes (CNRM-CERFACS,
        CNRM-ESM2-1e, piControl). DRS generation should succeed now that the
        collection-to-field mapping correctly handles attr_field_name (e.g.
        activity_id -> activity).
        """
        import shutil
        from pathlib import Path

        incoming_dir = drs_test_structure["incoming"] / "cmip7_incoming"
        incoming_dir.mkdir(parents=True, exist_ok=True)
        drs_root = drs_test_structure["root"]

        # Copy real CMIP7 test file
        cmip7_source = Path("tests/issue_release_3_0_2/flat_cmip7/tas_tmaxavg-h2m-hxy-u_mon_glb_g101_CNRM-ESM2-1e_piControl_r1i1p1f1_185001-185012.nc")
        if cmip7_source.exists():
            shutil.copy(cmip7_source, incoming_dir)
        else:
            pytest.skip("CMIP7 test file not found")

        args = get_default_make_args(incoming_dir, drs_root)
        args.project = "cmip7"
        args.version = "v20260217"

        run(args)

        # Verify DRS structure was created
        expected_drs_path = (
            drs_root
            / "MIP-DRS7"
            / "CMIP7"
            / "CMIP"
            / "CNRM-CERFACS"
            / "CNRM-ESM2-1e"
            / "piControl"
            / "r1i1p1f1"
            / "glb"
            / "mon"
            / "tas"
            / "tmaxavg-h2m-hxy-u"
            / "g101"
        )

        validator = DRSValidator(expected_drs_path)
        assert validator.validate_all(upgrade_from_latest=False, verbose=False)


class TestCMIP7CollectionMapping:
    """Test that the collection-to-field mapping correctly handles CMIP7 attr_specs.

    In CMIP7, netCDF attributes use _id suffixed names (e.g. activity_id) while
    DRS collections use the bare names (e.g. activity). The mapping must translate
    between these so that DRS generation can find the right values.
    """

    def test_cmip7_mapping_covers_required_collections(self):
        """Verify the mapping logic produces entries for all required CMIP7 DRS collections."""
        import esgvoc.api as ev
        from esgvoc.apps.drs.report import DrsType

        proj = ev.get_project("cmip7")
        dir_spec = proj.drs_specs[DrsType.DIRECTORY]
        required = [p.source_collection for p in dir_spec.parts]

        # Reproduce the mapping logic from make.py
        collection_to_field = {}
        for attr in proj.attr_specs:
            sc = attr.source_collection
            if sc is None:
                continue
            if getattr(attr, "source_collection_key", None) is not None:
                continue
            afn = attr.attr_field_name
            if afn is not None and afn.startswith("parent_"):
                continue
            field = afn if afn is not None else sc
            if sc not in collection_to_field or field.endswith("_id"):
                collection_to_field[sc] = field

        # directory_date and compound fields (variable, branding_suffix) are handled
        # separately — they are not expected in this mapping
        separately_handled = {"directory_date", "variable", "branding_suffix"}
        expected_mapped = [r for r in required if r not in separately_handled]

        missing = [r for r in expected_mapped if r not in collection_to_field]
        assert missing == [], (
            f"Required DRS collections missing from mapping: {missing}. "
            f"Mapping has: {collection_to_field}"
        )

    def test_cmip7_mapping_prefers_id_over_description(self):
        """Verify that _id attributes are preferred over description aliases."""
        import esgvoc.api as ev

        proj = ev.get_project("cmip7")

        collection_to_field = {}
        for attr in proj.attr_specs:
            sc = attr.source_collection
            if sc is None:
                continue
            if getattr(attr, "source_collection_key", None) is not None:
                continue
            afn = attr.attr_field_name
            if afn is not None and afn.startswith("parent_"):
                continue
            field = afn if afn is not None else sc
            if sc not in collection_to_field or field.endswith("_id"):
                collection_to_field[sc] = field

        # These must map to _id form, not the bare description form
        assert collection_to_field["activity"] == "activity_id"
        assert collection_to_field["institution"] == "institution_id"
        assert collection_to_field["source"] == "source_id"
        assert collection_to_field["experiment"] == "experiment_id"

    def test_cmip7_mapping_excludes_parent_aliases(self):
        """Verify parent_* aliases don't override primary mappings."""
        import esgvoc.api as ev

        proj = ev.get_project("cmip7")

        collection_to_field = {}
        for attr in proj.attr_specs:
            sc = attr.source_collection
            if sc is None:
                continue
            if getattr(attr, "source_collection_key", None) is not None:
                continue
            afn = attr.attr_field_name
            if afn is not None and afn.startswith("parent_"):
                continue
            field = afn if afn is not None else sc
            if sc not in collection_to_field or field.endswith("_id"):
                collection_to_field[sc] = field

        # None of the mapped values should be parent_* aliases
        for sc, field in collection_to_field.items():
            assert not field.startswith("parent_"), (
                f"collection '{sc}' mapped to parent alias '{field}'"
            )

    def test_cmip6_mapping_still_works(self):
        """Verify the new mapping logic doesn't break CMIP6."""
        import esgvoc.api as ev
        from esgvoc.apps.drs.report import DrsType

        proj = ev.get_project("cmip6")
        dir_spec = proj.drs_specs[DrsType.DIRECTORY]
        required = [p.source_collection for p in dir_spec.parts]

        collection_to_field = {}
        for attr in proj.attr_specs:
            sc = attr.source_collection
            if sc is None:
                continue
            if getattr(attr, "source_collection_key", None) is not None:
                continue
            afn = attr.attr_field_name
            if afn is not None and afn.startswith("parent_"):
                continue
            field = afn if afn is not None else sc
            if sc not in collection_to_field or field.endswith("_id"):
                collection_to_field[sc] = field

        # version and member_id are handled separately in CMIP6
        separately_handled = {"version", "member_id"}
        expected_mapped = [r for r in required if r not in separately_handled]

        missing = [r for r in expected_mapped if r not in collection_to_field]
        assert missing == [], (
            f"CMIP6 collections missing from mapping: {missing}"
        )

    def test_make_cmip7_synthetic_file(self, drs_test_structure):
        """Test end-to-end DRS creation with a synthetic CMIP7 file."""
        incoming_dir = drs_test_structure["incoming"] / "cmip7_synthetic"
        incoming_dir.mkdir(parents=True, exist_ok=True)
        drs_root = drs_test_structure["root"]

        create_cmip7_file(incoming_dir)

        args = get_default_make_args(incoming_dir, drs_root)
        args.project = "cmip7"
        args.version = "v20250401"

        run(args)

        # Verify the DRS directory was created with the expected structure
        expected_drs_path = (
            drs_root
            / "MIP-DRS7"
            / "CMIP7"
            / "CMIP"
            / "CNRM-CERFACS"
            / "CNRM-ESM2-1e"
            / "piControl"
            / "r1i1p1f1"
            / "glb"
            / "day"
            / "tas"
            / "tavg-h2m-hxy-u"
            / "g101"
        )

        validator = DRSValidator(expected_drs_path)
        assert validator.validate_all(upgrade_from_latest=False, verbose=False)

    def test_set_value_overrides_attribute(self, drs_test_structure):
        """Test that --set-value overrides a DRS facet value."""
        incoming_dir = drs_test_structure["incoming"] / "cmip6_set_value"
        drs_root = drs_test_structure["root"]

        create_files_different_variables(incoming_dir, count=1)

        args = get_default_make_args(incoming_dir, drs_root)
        # --set-value experiment_id=piControl produces a list of tuples via argparse
        args.set_value = [("experiment_id", "piControl")]

        run(args)

        # The DRS path should use the overridden value
        expected_drs_path = (
            drs_root
            / "CMIP6"
            / "CMIP"
            / "IPSL"
            / "IPSL-CM6A-LR"
            / "piControl"
            / "r1i1p1f1"
            / "day"
            / "tas"
            / "gn"
        )

        validator = DRSValidator(expected_drs_path)
        assert validator.validate_all(upgrade_from_latest=False, verbose=False)

    def test_set_key_overrides_mapping(self, drs_test_structure):
        """Test that --set-key overrides the collection-to-field mapping."""
        incoming_dir = drs_test_structure["incoming"] / "cmip7_set_key"
        incoming_dir.mkdir(parents=True, exist_ok=True)
        drs_root = drs_test_structure["root"]

        # Create a CMIP7 file and add a custom attribute
        import netCDF4

        file_path = create_cmip7_file(incoming_dir)

        ds = netCDF4.Dataset(file_path, "a")
        ds.my_custom_activity = "CMIP"
        ds.close()

        args = get_default_make_args(incoming_dir, drs_root)
        args.project = "cmip7"
        args.version = "v20250401"
        # --set-key activity=my_custom_activity produces a list of tuples via argparse
        args.set_key = [("activity", "my_custom_activity")]

        run(args)

        # Should still produce the correct DRS with activity=CMIP
        expected_drs_path = (
            drs_root
            / "MIP-DRS7"
            / "CMIP7"
            / "CMIP"
            / "CNRM-CERFACS"
            / "CNRM-ESM2-1e"
            / "piControl"
            / "r1i1p1f1"
            / "glb"
            / "day"
            / "tas"
            / "tavg-h2m-hxy-u"
            / "g101"
        )

        validator = DRSValidator(expected_drs_path)
        assert validator.validate_all(upgrade_from_latest=False, verbose=False)


class TestStringArrayAttrSplitting:
    """Test that only string_array attributes are split, not scalar multi-word values.

    Regression tests for issue #120: attributes like nominal_resolution ("100 km")
    and parent_time_units ("days since 1850-01-01") were truncated to their first
    word because make.py applied .split()[0] to ALL attributes instead of only
    those whose spec type is "string_array".
    """

    def test_string_array_attrs_loaded_from_spec(self):
        """Verify string_array attrs are correctly identified from the project's attr_specs."""
        import esgvoc.api as ev

        for project_id in ("cmip6", "cmip6plus"):
            proj = ev.get_project(project_id)
            if proj is None or proj.attr_specs is None:
                pytest.skip(f"project {project_id} not available")

            string_array_names = set()
            for spec in proj.attr_specs:
                if spec.attr_field_value_type == "string_array":
                    name = spec.attr_field_name or spec.source_collection
                    if name:
                        string_array_names.add(name)

            # activity_id is a known space-separated list
            assert "activity_id" in string_array_names, (
                f"{project_id}: activity_id should be string_array"
            )
            # scalar attributes must NOT appear
            assert "experiment_id" not in string_array_names, (
                f"{project_id}: experiment_id should NOT be string_array"
            )
            assert "nominal_resolution" not in string_array_names, (
                f"{project_id}: nominal_resolution should NOT be string_array"
            )

    def test_multiword_scalar_attrs_not_truncated(self, drs_test_structure):
        """Verify that multi-word scalar attributes survive DRS processing intact.

        Creates a CMIP6 file with attributes containing spaces (like real
        CMIP6Plus files have) and checks they are passed to GAValidator
        without truncation.
        """
        import netCDF4
        from unittest.mock import patch

        incoming_dir = drs_test_structure["incoming"] / "scalar_attrs"
        incoming_dir.mkdir(parents=True, exist_ok=True)
        drs_root = drs_test_structure["root"]

        # Create a CMIP6 file with multi-word scalar attributes
        create_files_different_variables(incoming_dir, count=1)
        nc_file = list(incoming_dir.glob("*.nc"))[0]

        ds = netCDF4.Dataset(nc_file, "a")
        ds.nominal_resolution = "100 km"
        ds.parent_time_units = "days since 1850-01-01"
        ds.close()

        # Patch GAValidator to capture what attributes it receives
        captured_attrs = {}

        try:
            from esgvoc.apps.ncattvalid import GAValidator
            original_validate = GAValidator.validate
        except ImportError:
            pytest.skip("esgvoc.apps.ncattvalid not available")

        def spy_validate(self, attributes, **kwargs):
            captured_attrs.update(attributes)
            return original_validate(self, attributes, **kwargs)

        with patch.object(GAValidator, "validate", spy_validate):
            args = get_default_make_args(incoming_dir, drs_root)
            run(args)

        # Multi-word scalars must not be truncated
        assert captured_attrs.get("nominal_resolution") == "100 km", (
            f"nominal_resolution was truncated to {captured_attrs.get('nominal_resolution')!r}"
        )
        assert captured_attrs.get("parent_time_units") == "days since 1850-01-01", (
            f"parent_time_units was truncated to {captured_attrs.get('parent_time_units')!r}"
        )

    def test_string_array_attr_is_split_for_drs(self, drs_test_structure):
        """Verify that string_array attributes (e.g. activity_id) ARE still split for DRS."""
        import netCDF4

        incoming_dir = drs_test_structure["incoming"] / "array_attrs"
        incoming_dir.mkdir(parents=True, exist_ok=True)
        drs_root = drs_test_structure["root"]

        # Create a CMIP6 file with a multi-value activity_id
        create_files_different_variables(incoming_dir, count=1)
        nc_file = list(incoming_dir.glob("*.nc"))[0]

        ds = netCDF4.Dataset(nc_file, "a")
        ds.activity_id = "CMIP ScenarioMIP"  # space-separated list
        ds.close()

        args = get_default_make_args(incoming_dir, drs_root)
        run(args)

        # The DRS path should use "CMIP" (first token), not "CMIP ScenarioMIP"
        expected_drs_path = (
            drs_root
            / "CMIP6"
            / "CMIP"  # first value of the split activity_id
            / "IPSL"
            / "IPSL-CM6A-LR"
            / "historical"
            / "r1i1p1f1"
            / "day"
            / "tas"
            / "gn"
        )

        validator = DRSValidator(expected_drs_path)
        assert validator.validate_all(upgrade_from_latest=False, verbose=False)
