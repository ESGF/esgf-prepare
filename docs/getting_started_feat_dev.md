.. _getting_started:


Getting Started
===============

This guide will walk you through your first use of ``esgprep`` to prepare climate data for ESGF publication.
By the end, you'll understand the complete workflow from raw NetCDF files to publication-ready mapfiles.

.. note:: This guide assumes you have already installed ``esgprep``. If not, see :ref:`installation`.

Prerequisites
*************

Before starting, ensure you have:

**System Requirements:**
 * Python 3.12 or higher
 * Linux/Unix environment
 * Access to the filesystem containing your data
 * Sufficient disk space (at least 2x your data size for DRS structure)

**Data Requirements:**
 * CMOR-compliant NetCDF files
 * Files from a supported ESGF project (CMIP6, CMIP5, CORDEX, etc.)
 * Files with proper global attributes and naming conventions

**Verify Your Environment:**

.. code-block:: bash

    # Check Python version
    $ python3 --version
    Python 3.12.7

    # Check esgprep is installed
    $ esgdrs --version
    esgdrs (from esgprep v3.0.0 2019-01-09)

    $ esgmapfile --version
    esgmapfile (from esgprep v3.0.0 2019-01-09)

Understanding the Workflow
***************************

The ``esgprep`` workflow has two main stages:

.. code-block:: text

    ┌─────────────────┐
    │  NetCDF Files   │  Your incoming/raw data
    │  (any location) │
    └────────┬────────┘
             │
             │ esgdrs list    (preview datasets)
             │ esgdrs tree    (preview structure)
             │ esgdrs upgrade (organize files)
             ↓
    ┌─────────────────┐
    │  DRS Structure  │  Files organized by ESGF standards
    │  (versioned)    │
    └────────┬────────┘
             │
             │ esgmapfile make (generate publication metadata)
             ↓
    ┌─────────────────┐
    │    Mapfiles     │  Ready for ESGF publication
    └─────────────────┘

**Key Concepts:**

 * **DRS (Data Reference Syntax)**: A standardized directory structure for organizing climate data
 * **Facets**: Metadata attributes (like project, model, experiment) that define your data
 * **Dataset ID**: A unique identifier constructed from facets, like ``CMIP6.CMIP.IPSL.IPSL-CM6A-LR.historical...``
 * **Mapfiles**: Text files listing your data files with checksums, required for ESGF publication

Example Scenario
****************

Let's prepare CMIP6 data from the IPSL-CM6A-LR model for publication.

**Starting Point:**

You have NetCDF files in an incoming directory:

.. code-block:: bash

    /data/incoming/
    ├── tas_Amon_IPSL-CM6A-LR_historical_r1i1p1f1_gr_185001-201412.nc
    ├── tas_Amon_IPSL-CM6A-LR_historical_r2i1p1f1_gr_185001-201412.nc
    └── pr_Amon_IPSL-CM6A-LR_historical_r1i1p1f1_gr_185001-201412.nc

**Goal:**

Create a DRS-compliant structure and generate mapfiles for ESGF publication.

Step 1: List Datasets
**********************

First, let's see what datasets ``esgprep`` detects from your files:

.. code-block:: bash

    $ esgdrs list --project cmip6 /data/incoming/

**Expected Output:**

.. code-block:: text

    ===================
    Dataset Discovery
    ===================

    Scanning directory: /data/incoming/
    Found 3 NetCDF files

    Dataset: CMIP6.CMIP.IPSL.IPSL-CM6A-LR.historical.r1i1p1f1.Amon.tas.gr
    ├─ Latest version: None (new dataset)
    ├─ New version: v20250125
    ├─ Files: 1
    └─ Total size: 1.2 GB

    Dataset: CMIP6.CMIP.IPSL.IPSL-CM6A-LR.historical.r2i1p1f1.Amon.tas.gr
    ├─ Latest version: None (new dataset)
    ├─ New version: v20250125
    ├─ Files: 1
    └─ Total size: 1.2 GB

    Dataset: CMIP6.CMIP.IPSL.IPSL-CM6A-LR.historical.r1i1p1f1.Amon.pr.gr
    ├─ Latest version: None (new dataset)
    ├─ New version: v20250125
    ├─ Files: 1
    └─ Total size: 2.1 GB

    Total: 3 datasets, 3 files, 4.5 GB

**What This Shows:**

 * ``esgprep`` found 3 datasets based on facet combinations
 * Each will get version ``v20250125`` (today's date)
 * Files are grouped by variable (tas, pr) and ensemble member (r1i1p1f1, r2i1p1f1)

.. tip:: If you see errors here about invalid facets or unrecognized project, check that:

   * Your files are CMOR-compliant
   * The project name is spelled correctly (case-sensitive: ``cmip6`` not ``CMIP6``)
   * Files have proper global attributes

Step 2: Preview DRS Structure
******************************

Before making changes, preview what the DRS structure will look like:

.. code-block:: bash

    $ esgdrs tree --project cmip6 /data/incoming/ --root /data/esgf-data

**Expected Output:**

.. code-block:: text

    /data/esgf-data/
    └── cmip6/
        └── CMIP6/
            └── CMIP/
                └── IPSL/
                    └── IPSL-CM6A-LR/
                        └── historical/
                            ├── r1i1p1f1/
                            │   └── Amon/
                            │       ├── tas/
                            │       │   └── gr/
                            │       │       ├── v20250125/
                            │       │       │   └── tas_Amon_*.nc
                            │       │       └── latest -> v20250125/
                            │       └── pr/
                            │           └── gr/
                            │               ├── v20250125/
                            │               │   └── pr_Amon_*.nc
                            │               └── latest -> v20250125/
                            └── r2i1p1f1/
                                └── Amon/
                                    └── tas/
                                        └── gr/
                                            ├── v20250125/
                                            │   └── tas_Amon_*.nc
                                            └── latest -> v20250125/

**What This Shows:**

 * Complete directory hierarchy following ESGF DRS
 * Files organized by facets: activity, institution, model, experiment, variant, frequency, variable, grid
 * Version directories (v20250125)
 * ``latest`` symlinks pointing to newest version

.. note:: The ``--root`` option specifies where to create the DRS structure. If omitted, it uses your current directory.

Step 3: See Planned Operations
*******************************

For more detail on what operations will be performed:

.. code-block:: bash

    $ esgdrs todo --project cmip6 /data/incoming/ --root /data/esgf-data --link

**Expected Output:**

.. code-block:: text

    Planned Operations:
    ===================

    mkdir -p /data/esgf-data/cmip6/CMIP6/CMIP/IPSL/IPSL-CM6A-LR/historical/r1i1p1f1/Amon/tas/gr/v20250125
    ln /data/incoming/tas_Amon_IPSL-CM6A-LR_historical_r1i1p1f1_gr_185001-201412.nc \
       /data/esgf-data/cmip6/CMIP6/CMIP/IPSL/IPSL-CM6A-LR/historical/r1i1p1f1/Amon/tas/gr/v20250125/
    ln -s v20250125 /data/esgf-data/cmip6/CMIP6/CMIP/IPSL/IPSL-CM6A-LR/historical/r1i1p1f1/Amon/tas/gr/latest

    [... more operations ...]

    Summary:
    ├─ Directories to create: 12
    ├─ Files to link: 3
    ├─ Symlinks to create: 3
    └─ Total operations: 18

**What This Shows:**

 * Exact Unix commands that will be executed
 * Using ``--link`` creates hard links (not copies) to save disk space
 * ``latest`` symlinks will be created automatically

.. tip:: Use ``--copy`` instead of ``--link`` if you want to preserve the original files separately.
   Use ``--symlink`` for symbolic links (use with caution - broken if source moves).

Step 4: Apply DRS Structure
****************************

Now let's actually create the DRS structure:

.. code-block:: bash

    $ esgdrs upgrade --project cmip6 /data/incoming/ --root /data/esgf-data --link

**Expected Output:**

.. code-block:: text

    ╔══════════════════════════════════════╗
    ║  Upgrading Datasets to DRS Structure ║
    ╚══════════════════════════════════════╝

    Processing dataset 1/3: CMIP6.CMIP.IPSL.IPSL-CM6A-LR.historical.r1i1p1f1.Amon.tas.gr
    ├─ Creating directories... ✓
    ├─ Linking files... ✓
    ├─ Creating latest symlink... ✓
    └─ Computing checksums... ✓ (1.2 GB processed)

    Processing dataset 2/3: CMIP6.CMIP.IPSL.IPSL-CM6A-LR.historical.r2i1p1f1.Amon.tas.gr
    ├─ Creating directories... ✓
    ├─ Linking files... ✓
    ├─ Creating latest symlink... ✓
    └─ Computing checksums... ✓ (1.2 GB processed)

    Processing dataset 3/3: CMIP6.CMIP.IPSL.IPSL-CM6A-LR.historical.r1i1p1f1.Amon.pr.gr
    ├─ Creating directories... ✓
    ├─ Linking files... ✓
    ├─ Creating latest symlink... ✓
    └─ Computing checksums... ✓ (2.1 GB processed)

    ═══════════════════════════════════════
    ✓ SUCCESS
    ═══════════════════════════════════════

    Summary:
    ├─ Datasets processed: 3
    ├─ Files organized: 3
    ├─ Total data: 4.5 GB
    └─ Time elapsed: 2m 34s

**What Just Happened:**

 * DRS directory structure created under ``/data/esgf-data/cmip6/``
 * Files hard-linked to their DRS locations
 * ``latest`` symlinks created pointing to v20250125
 * Checksums computed and stored for verification

**Verify the Result:**

.. code-block:: bash

    $ ls -lh /data/esgf-data/cmip6/CMIP6/CMIP/IPSL/IPSL-CM6A-LR/historical/r1i1p1f1/Amon/tas/gr/

    drwxr-xr-x  2 user group 4.0K Nov 25 10:30 v20250125
    lrwxrwxrwx  1 user group   10 Nov 25 10:30 latest -> v20250125

    $ ls /data/esgf-data/cmip6/CMIP6/CMIP/IPSL/IPSL-CM6A-LR/historical/r1i1p1f1/Amon/tas/gr/v20250125/

    tas_Amon_IPSL-CM6A-LR_historical_r1i1p1f1_gr_185001-201412.nc

Perfect! Your data is now organized according to ESGF DRS.

Step 5: Generate Mapfiles
**************************

Now generate the mapfiles needed for ESGF publication:

.. code-block:: bash

    $ esgmapfile make --project cmip6 /data/esgf-data/cmip6/ --outdir /data/mapfiles

**Expected Output:**

.. code-block:: text

    ╔═══════════════════════════════╗
    ║  Generating ESGF Mapfiles     ║
    ╚═══════════════════════════════╝

    Scanning directory: /data/esgf-data/cmip6/
    Found 3 datasets to process

    Processing [1/3]: CMIP6.CMIP.IPSL.IPSL-CM6A-LR.historical.r1i1p1f1.Amon.tas.gr.v20250125
    ├─ Files found: 1
    ├─ Computing checksums: sha256
    ├─ Mapfile: /data/mapfiles/CMIP6.CMIP.IPSL.IPSL-CM6A-LR.historical.r1i1p1f1.Amon.tas.gr.v20250125.map
    └─ ✓ Written

    Processing [2/3]: CMIP6.CMIP.IPSL.IPSL-CM6A-LR.historical.r2i1p1f1.Amon.tas.gr.v20250125
    ├─ Files found: 1
    ├─ Computing checksums: sha256
    ├─ Mapfile: /data/mapfiles/CMIP6.CMIP.IPSL.IPSL-CM6A-LR.historical.r2i1p1f1.Amon.tas.gr.v20250125.map
    └─ ✓ Written

    Processing [3/3]: CMIP6.CMIP.IPSL.IPSL-CM6A-LR.historical.r1i1p1f1.Amon.pr.gr.v20250125
    ├─ Files found: 1
    ├─ Computing checksums: sha256
    ├─ Mapfile: /data/mapfiles/CMIP6.CMIP.IPSL.IPSL-CM6A-LR.historical.r1i1p1f1.Amon.pr.gr.v20250125.map
    └─ ✓ Written

    ═══════════════════════════════════════
    ✓ SUCCESS
    ═══════════════════════════════════════

    Generated: 3 mapfiles
    Output directory: /data/mapfiles/

**What Was Created:**

Mapfiles are text files with one line per data file:

.. code-block:: bash

    $ cat /data/mapfiles/CMIP6.CMIP.IPSL.IPSL-CM6A-LR.historical.r1i1p1f1.Amon.tas.gr.v20250125.map

**Content:**

.. code-block:: text

    CMIP6.CMIP.IPSL.IPSL-CM6A-LR.historical.r1i1p1f1.Amon.tas.gr.v20250125 | /data/esgf-data/cmip6/CMIP6/CMIP/IPSL/IPSL-CM6A-LR/historical/r1i1p1f1/Amon/tas/gr/v20250125/tas_Amon_IPSL-CM6A-LR_historical_r1i1p1f1_gr_185001-201412.nc | 1234567890 | mod_time=1732531200 | checksum=a3d5e6f7890b1c2d3e4f5a6b7c8d9e0f1a2b3c4d5e6f7a8b9c0d1e2f3a4b5c6d | checksum_type=SHA256

**Format:**
 * ``dataset_id | file_path | size_bytes | mod_time=... | checksum=... | checksum_type=...``

These mapfiles are ready for ESGF publication!

Step 6: Verify Everything
**************************

Let's verify the complete workflow succeeded:

.. code-block:: bash

    # Check DRS structure exists
    $ esgdrs tree --project cmip6 /data/esgf-data/cmip6/ | head -20

    # Check mapfiles were created
    $ ls -lh /data/mapfiles/

    # Verify checksums in mapfile
    $ grep checksum /data/mapfiles/*.map

Common Options
**************

During your workflow, you may want to use these common options:

**Performance:**

.. code-block:: bash

    # Use multiple processors for faster processing
    $ esgdrs upgrade --project cmip6 /data/incoming/ --max-processes 8

    # Skip checksums for faster testing (not for production!)
    $ esgmapfile make --project cmip6 /data/esgf-data/cmip6/ --no-checksum

**Checksums:**

.. code-block:: bash

    # Use multihash format (recommended for new data)
    $ esgmapfile make --project cmip6 /data/esgf-data/cmip6/ --checksum-type sha2-256

    # Provide pre-calculated checksums
    $ esgmapfile make --project cmip6 /data/esgf-data/cmip6/ --checksums-from checksums.txt

**Versioning:**

.. code-block:: bash

    # Specify a custom version
    $ esgdrs upgrade --project cmip6 /data/incoming/ --version 20241201

    # Process all versions (not just latest)
    $ esgmapfile make --project cmip6 /data/esgf-data/cmip6/ --all-versions

**Logging:**

.. code-block:: bash

    # Save output to logfile
    $ esgdrs upgrade --project cmip6 /data/incoming/ --log /var/log/esgprep/

    # Enable debug mode for troubleshooting
    $ esgdrs upgrade --project cmip6 /data/incoming/ --debug

What's Next?
************

Congratulations! You've successfully:

 ✓ Organized your data into ESGF DRS structure
 ✓ Generated mapfiles for ESGF publication
 ✓ Computed checksums for data integrity

**Next Steps:**

1. **Publish to ESGF:**

   Use the ESGF publisher tools with your mapfiles:

   .. code-block:: bash

       esgpublish --map /data/mapfiles/*.map --service fileservice

2. **Learn More:**

   * :ref:`drs` - Detailed DRS command reference
   * :ref:`mapfiles` - Advanced mapfile options
   * :ref:`configuration` - Checksum and vocabulary configuration
   * :ref:`migration` - Migrating from version 2.x

3. **Handle Updates:**

   When you need to publish a new version:

   .. code-block:: bash

       # New files in incoming directory
       $ esgdrs list --project cmip6 /data/incoming/
       # Will show version increment: v20250126

       $ esgdrs upgrade --project cmip6 /data/incoming/ --upgrade-from-latest
       # Only processes changed files, symlinks unchanged ones

       $ esgmapfile make --project cmip6 /data/esgf-data/cmip6/
       # Generates new mapfiles for updated version

Common Issues
*************

**Problem:** "Project 'cmip6' not found in vocabulary"

.. code-block:: bash

    ValueError: Project 'cmip6' not found in esgvoc

**Solution:** Check project name spelling (case-sensitive). Update esgvoc:

.. code-block:: bash

    pip install --upgrade esgvoc

---

**Problem:** "Invalid facet value" errors

**Solution:** Your NetCDF files may not be CMOR-compliant. Verify:

.. code-block:: bash

    # Check file attributes
    ncdump -h your_file.nc | grep ":"

Ensure global attributes match project requirements.

---

**Problem:** Checksumming is very slow

**Solution:** For large files, pre-calculate checksums:

.. code-block:: bash

    # Generate checksums separately
    sha256sum /data/incoming/*.nc > checksums.txt

    # Use them in esgmapfile
    esgmapfile make --project cmip6 /data/esgf-data/cmip6/ --checksums-from checksums.txt

---

**Problem:** Need to test without modifying data

**Solution:** Use a test directory:

.. code-block:: bash

    # Test in /tmp
    esgdrs upgrade --project cmip6 /data/incoming/ --root /tmp/test --link

    # Review output
    esgdrs tree --project cmip6 --root /tmp/test

    # If satisfied, run on production location

Getting Help
************

If you encounter issues:

1. **Check the logs:** Use ``--log`` and ``--debug`` options
2. **Read the FAQ:** See :ref:`faq` for common questions
3. **Consult detailed docs:** :ref:`usage`, :ref:`drs`, :ref:`mapfiles`
4. **Report bugs:** https://github.com/ESGF/esgf-prepare/issues

**Useful Commands for Debugging:**

.. code-block:: bash

    # Check esgprep version
    esgdrs --version

    # Check available projects
    python -c "import esgvoc; print(esgvoc.list_projects())"

    # Verify NetCDF file structure
    ncdump -h your_file.nc

    # Test with single file
    esgdrs list --project cmip6 /path/to/single/file.nc

Quick Reference
***************

**Essential Commands:**

.. code-block:: bash

    # Preview what datasets will be created
    esgdrs list --project PROJECT /path/to/incoming/

    # Preview DRS directory structure
    esgdrs tree --project PROJECT /path/to/incoming/ --root /output/path

    # See planned operations
    esgdrs todo --project PROJECT /path/to/incoming/ --root /output/path

    # Apply DRS structure
    esgdrs upgrade --project PROJECT /path/to/incoming/ --root /output/path --link

    # Generate mapfiles
    esgmapfile make --project PROJECT /path/to/drs/ --outdir /path/to/mapfiles/

    # Show mapfile paths (dry-run)
    esgmapfile show --project PROJECT --directory /path/to/drs/

**Common Projects:**
 * ``cmip6`` - CMIP6
 * ``cmip5`` - CMIP5
 * ``cordex`` - CORDEX
 * ``input4mips`` - input4MIPs
 * ``obs4mips`` - obs4MIPs

For a complete list, check the ``esgvoc`` library documentation.

---

**Ready to dive deeper?** Continue to :ref:`usage` for comprehensive command-line options, or :ref:`drs` for detailed DRS management features.
