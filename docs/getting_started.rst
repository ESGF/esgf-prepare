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
    esgdrs (from esgprep v3.0.0)

    $ esgmapfile --version
    esgmapfile (from esgprep v3.0.0)

.. important:: **Initialize Controlled Vocabularies**

   Before using ``esgprep`` for the first time, you must initialize the controlled vocabularies:

   .. code-block:: bash

       $ esgvoc install

   This downloads ESGF project vocabularies and builds local databases. The installation may take a few minutes.

   **What happens if you skip this?** You'll see an error like:
   ``RuntimeError: universe connection is not initialized``

   **Keep your vocabularies updated:** Run ``esgvoc install`` periodically to get the latest controlled
   vocabulary updates from ESGF projects. This ensures you can work with newly added experiments, models,
   or updated facet values.

   For more details about controlled vocabularies, see the `esgvoc documentation <https://esgf.github.io/esgf-vocab/index.html>`_.

Understanding the Workflow
***************************

The ``esgprep`` workflow has two main stages:

.. code-block:: text

    ┌─────────────────┐
    │  NetCDF Files   │  Your incoming CMOR-compliant standardized data
    │  (any location) │  (following project norms: CMIP7, CMIP6, etc.)
    └────────┬────────┘
             │
             │ esgdrs list    (preview datasets)
             │ esgdrs tree    (preview structure)
             │ esgdrs upgrade (organize files)
             ↓
    ┌─────────────────┐
    │  DRS Structure  │  Files organized following the project DRS
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

.. note:: Your files must be **CMOR-compliant standardized NetCDF files** that follow your project's
   conventions (CMIP7, CMIP6, CORDEX, etc.). Files produced by CMOR or following the same standards
   will work correctly.

You have standardized NetCDF files in an incoming directory:

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

    $ esgdrs make list --project cmip6 /data/incoming/

**Expected Output:**

.. code-block:: text

    DRS tree generation [----<-] ...
    DRS tree generation [<<<<<<] Completed
    Number of success(es): 3
    Number of error(s): 0
    ===================================================================================================================================
                        Publication level                       Latest version   ->  Upgrade version   Files to upgrade      Total size
    -----------------------------------------------------------------------------------------------------------------------------------
    CMIP6/CMIP/IPSL/IPSL-CM6A-LR/historical/r1i1p1f1/Amon/tas/gr      Initial       ->     v20250125                     1            1.2G
    CMIP6/CMIP/IPSL/IPSL-CM6A-LR/historical/r2i1p1f1/Amon/tas/gr      Initial       ->     v20250125                     1            1.2G
    CMIP6/CMIP/IPSL/IPSL-CM6A-LR/historical/r1i1p1f1/Amon/pr/gr       Initial       ->     v20250125                     1            2.1G
    ===================================================================================================================================

**What This Shows:**

* Progress spinner during file scanning: ``[----<-]`` → ``[<<<<<<]``
* Success/error counts for processed files
* Table showing:

  * **Publication level**: Dataset path in DRS structure
  * **Latest version**: "Initial" for new datasets, or existing version number
  * **Upgrade version**: New version to be created (vYYYYMMDD format, typically today's date)
  * **Files to upgrade**: Count of files in this dataset
  * **Total size**: Human-readable size of the dataset

.. tip:: If you see errors here about invalid facets or unrecognized project, check that:

   * Your files are CMOR-compliant
   * The project name is spelled correctly (case-sensitive: ``cmip6`` not ``CMIP6``)
   * Files have proper global attributes

Step 2: Preview DRS Structure
******************************

Before making changes, preview what the DRS structure will look like:

.. code-block:: bash

    $ esgdrs make tree --project cmip6 /data/incoming/ --root /data/esgf-data

**Expected Output:**

.. code-block:: text

    DRS tree generation [----<-] ...
    DRS tree generation [<<<<<<] Completed
    Number of success(es): 3
    Number of error(s): 0
    ===================================================================================================================================
                                                              Upgrade DRS Tree
    -----------------------------------------------------------------------------------------------------------------------------------
    /data/esgf-data
    CMIP6
    └── CMIP
        └── IPSL
            └── IPSL-CM6A-LR
                └── historical
                    ├── r1i1p1f1
                    │   └── Amon
                    │       ├── tas
                    │       │   └── gr
                    │       │       ├── files
                    │       │       │   └── d20250125
                    │       │       │       └── tas_Amon_IPSL-CM6A-LR_historical_r1i1p1f1_gr_185001-201412.nc
                    │       │       ├── latest -> v20250125
                    │       │       └── v20250125
                    │       │           └── tas_Amon_*.nc -> ../files/d20250125/tas_Amon_*.nc
                    │       └── pr
                    │           └── gr
                    │               ├── files
                    │               │   └── d20250125
                    │               ├── latest -> v20250125
                    │               └── v20250125
                    └── r2i1p1f1
                        └── Amon
                            └── tas
                                └── gr
                                    ├── files
                                    │   └── d20250125
                                    ├── latest -> v20250125
                                    └── v20250125
    ===================================================================================================================================

**What This Shows:**

* Complete directory hierarchy following project DRS
* Files organized by facets: activity, institution, model, experiment, variant, frequency, variable, grid
* **files/dYYYYMMDD/** directories containing actual data files
* **vYYYYMMDD/** directories with symlinks pointing to files
* **latest** symlinks pointing to newest version directory
* Arrow notation (``->``) showing symlink targets

.. note:: The ``--root`` option specifies where to create the DRS structure. If omitted, it uses your current directory.

Step 3: See Planned Operations
*******************************

For more detail on what operations will be performed:

.. code-block:: bash

    $ esgdrs make todo --project cmip6 /data/incoming/ --root /data/esgf-data --link

**Expected Output:**

.. code-block:: text

    DRS tree generation [----<-] ...
    DRS tree generation [<<<<<<] Completed
    Number of success(es): 3
    Number of error(s): 0
    ===================================================================================================================================
                                                        Unix command-lines (DRY-RUN)
    -----------------------------------------------------------------------------------------------------------------------------------
    mkdir -p /data/esgf-data/CMIP6/CMIP/IPSL/IPSL-CM6A-LR/historical/r1i1p1f1/Amon/tas/gr/v20250125
    ln -s ../files/d20250125/tas_Amon_IPSL-CM6A-LR_historical_r1i1p1f1_gr_185001-201412.nc /data/esgf-data/CMIP6/CMIP/IPSL/IPSL-CM6A-LR/historical/r1i1p1f1/Amon/tas/gr/v20250125/tas_Amon_IPSL-CM6A-LR_historical_r1i1p1f1_gr_185001-201412.nc
    mkdir -p /data/esgf-data/CMIP6/CMIP/IPSL/IPSL-CM6A-LR/historical/r1i1p1f1/Amon/tas/gr
    ln -s v20250125 /data/esgf-data/CMIP6/CMIP/IPSL/IPSL-CM6A-LR/historical/r1i1p1f1/Amon/tas/gr/latest
    mkdir -p /data/esgf-data/CMIP6/CMIP/IPSL/IPSL-CM6A-LR/historical/r1i1p1f1/Amon/tas/gr/files/d20250125
    ln /data/incoming/tas_Amon_IPSL-CM6A-LR_historical_r1i1p1f1_gr_185001-201412.nc /data/esgf-data/CMIP6/CMIP/IPSL/IPSL-CM6A-LR/historical/r1i1p1f1/Amon/tas/gr/files/d20250125/tas_Amon_IPSL-CM6A-LR_historical_r1i1p1f1_gr_185001-201412.nc

    [... similar commands for other files ...]
    ===================================================================================================================================

**What This Shows:**

* Header: "Unix command-lines (DRY-RUN)" indicates no actual changes
* Exact Unix commands that will be executed:

  1. ``mkdir -p`` - Create version directories
  2. ``ln -s`` - Create symlinks from version dir to files/
  3. ``ln -s`` - Create latest symlink pointing to version
  4. ``mkdir -p`` - Create files/dYYYYMMDD directory
  5. ``ln`` - Create hard link (with ``--link`` flag) or ``mv`` - Move file (default)

* Sequence shows complete operation for each dataset

.. tip:: Use ``--copy`` instead of ``--link`` if you want to preserve the original files separately.
   Use ``--symlink`` for symbolic links (use with caution - broken if source moves).

Step 4: Apply DRS Structure
****************************

Now let's actually create the DRS structure:

.. code-block:: bash

    $ esgdrs make upgrade --project cmip6 /data/incoming/ --root /data/esgf-data --link

**Expected Output:**

.. code-block:: text

    DRS tree generation [----<-] ...
    DRS tree generation [<<<<<<] Completed
    Number of success(es): 3
    Number of error(s): 0
    ===================================================================================================================================
                                                             Unix command-lines
    -----------------------------------------------------------------------------------------------------------------------------------
    mkdir -p /data/esgf-data/CMIP6/CMIP/IPSL/IPSL-CM6A-LR/historical/r1i1p1f1/Amon/tas/gr/v20250125
    ln -s ../files/d20250125/tas_Amon_IPSL-CM6A-LR_historical_r1i1p1f1_gr_185001-201412.nc /data/esgf-data/CMIP6/CMIP/IPSL/IPSL-CM6A-LR/historical/r1i1p1f1/Amon/tas/gr/v20250125/tas_Amon_IPSL-CM6A-LR_historical_r1i1p1f1_gr_185001-201412.nc
    ln -s v20250125 /data/esgf-data/CMIP6/CMIP/IPSL/IPSL-CM6A-LR/historical/r1i1p1f1/Amon/tas/gr/latest
    mkdir -p /data/esgf-data/CMIP6/CMIP/IPSL/IPSL-CM6A-LR/historical/r1i1p1f1/Amon/tas/gr/files/d20250125
    ln /data/incoming/tas_Amon_IPSL-CM6A-LR_historical_r1i1p1f1_gr_185001-201412.nc /data/esgf-data/CMIP6/CMIP/IPSL/IPSL-CM6A-LR/historical/r1i1p1f1/Amon/tas/gr/files/d20250125/tas_Amon_IPSL-CM6A-LR_historical_r1i1p1f1_gr_185001-201412.nc

    [... similar commands for other datasets ...]
    ===================================================================================================================================

**What Just Happened:**

* Commands shown are actually being executed (no longer "DRY-RUN")
* DRS directory structure created under ``/data/esgf-data/CMIP6/``
* Files hard-linked (with ``--link``) to their DRS locations
* ``latest`` symlinks created pointing to v20250125
* Success count confirms all operations completed

**Verify the Result:**

.. code-block:: bash

    $ ls -lh /data/esgf-data/cmip6/CMIP6/CMIP/IPSL/IPSL-CM6A-LR/historical/r1i1p1f1/Amon/tas/gr/

    drwxr-xr-x  2 user group 4.0K Nov 25 10:30 v20250125
    lrwxrwxrwx  1 user group   10 Nov 25 10:30 latest -> v20250125

    $ ls /data/esgf-data/cmip6/CMIP6/CMIP/IPSL/IPSL-CM6A-LR/historical/r1i1p1f1/Amon/tas/gr/v20250125/

    tas_Amon_IPSL-CM6A-LR_historical_r1i1p1f1_gr_185001-201412.nc

Perfect! Your data is now organized according to the project DRS.

Step 5: Generate Mapfiles
**************************

Now generate the mapfiles needed for ESGF publication:

.. code-block:: bash

    $ esgmapfile make --project cmip6 --directory /data/esgf-data/CMIP6/ --outdir /data/mapfiles

**Expected Output:**

.. code-block:: text

    Mapfiles generation [----<-] ...
    Mapfiles generation [<<<<<<] Completed

    Mapfile(s) generated: 3 (in /data/mapfiles)
    Number of success(es): 3
    Number of error(s): 0

**What Was Created:**

Mapfiles are text files with one line per data file:

.. code-block:: bash

    $ cat /data/mapfiles/CMIP6.CMIP.IPSL.IPSL-CM6A-LR.historical.r1i1p1f1.Amon.tas.gr.v20250125.map

**Content:**

.. code-block:: text

    CMIP6.CMIP.IPSL.IPSL-CM6A-LR.historical.r1i1p1f1.Amon.tas.gr#20250125 | /data/esgf-data/CMIP6/CMIP/IPSL/IPSL-CM6A-LR/historical/r1i1p1f1/Amon/tas/gr/v20250125/tas_Amon_IPSL-CM6A-LR_historical_r1i1p1f1_gr_185001-201412.nc | 1234567890 | mod_time=1732531200.0 | checksum=a3d5e6f7890b1c2d3e4f5a6b7c8d9e0f1a2b3c4d5e6f7a8b9c0d1e2f3a4b5c6d

**Format:**
 * ``dataset_id#version | file_path | size_bytes | mod_time=TIMESTAMP | checksum=HEXDIGEST``
 * Note: Version uses ``#`` separator (not ``.v``) in the dataset ID within mapfiles
 * Checksum type defaults to SHA256 unless specified with ``--checksum-type``

These mapfiles are ready for ESGF publication!

Step 6: Verify Everything
**************************

Let's verify the complete workflow succeeded:

.. code-block:: bash

    # Check DRS structure exists
    $ tree /data/esgf-data/CMIP6/ | head -20
    # or use: find /data/esgf-data/CMIP6/ -type f -o -type l

    # Check mapfiles were created
    $ ls -lh /data/mapfiles/
    -rw-r--r-- 1 user group 350 Jan 25 10:30 CMIP6.CMIP.IPSL.IPSL-CM6A-LR.historical.r1i1p1f1.Amon.tas.gr.v20250125.map
    -rw-r--r-- 1 user group 350 Jan 25 10:30 CMIP6.CMIP.IPSL.IPSL-CM6A-LR.historical.r2i1p1f1.Amon.tas.gr.v20250125.map
    -rw-r--r-- 1 user group 350 Jan 25 10:30 CMIP6.CMIP.IPSL.IPSL-CM6A-LR.historical.r1i1p1f1.Amon.pr.gr.v20250125.map

    # View mapfile content
    $ cat /data/mapfiles/*.map | head -1
    CMIP6.CMIP.IPSL.IPSL-CM6A-LR.historical.r1i1p1f1.Amon.tas.gr#20250125 | /data/esgf-data/CMIP6/... | 1234567890 | ...

Common Options
**************

During your workflow, you may want to use these common options:

**Performance:**

.. code-block:: bash

    # Use multiple processors for faster processing
    $ esgdrs make upgrade --project cmip6 /data/incoming/ --max-processes 8

    # Skip checksums for faster testing (not for production!)
    $ esgmapfile make --project cmip6 --directory /data/esgf-data/CMIP6/ --no-checksum

**Checksums:**

.. code-block:: bash

    # Use multihash format (recommended for new data)
    $ esgmapfile make --project cmip6 --directory /data/esgf-data/CMIP6/ --checksum-type sha2-256

    # Provide pre-calculated checksums
    $ esgmapfile make --project cmip6 --directory /data/esgf-data/CMIP6/ --checksums-from checksums.txt

**Versioning:**

.. code-block:: bash

    # Specify a custom version
    $ esgdrs make upgrade --project cmip6 /data/incoming/ --version 20241201

    # Process all versions (not just latest)
    $ esgmapfile make --project cmip6 --directory /data/esgf-data/CMIP6/ --all-versions

**Logging:**

.. code-block:: bash

    # Save output to logfile
    $ esgdrs make upgrade --project cmip6 /data/incoming/ --log /var/log/esgprep/

    # Enable debug mode for troubleshooting
    $ esgdrs make upgrade --project cmip6 /data/incoming/ --debug

What's Next?
************

Congratulations! You've successfully:

* ✓ Organized your data into project DRS structure
* ✓ Generated mapfiles for ESGF publication
* ✓ Computed checksums for data integrity

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
       $ esgdrs make list --project cmip6 /data/incoming/
       # Will show version increment: v20250126

       $ esgdrs make upgrade --project cmip6 /data/incoming/ --upgrade-from-latest
       # Only processes changed files, symlinks unchanged ones

       $ esgmapfile make --project cmip6 --directory /data/esgf-data/CMIP6/
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
    esgmapfile make --project cmip6 --directory /data/esgf-data/CMIP6/ --checksums-from checksums.txt

---

**Problem:** Need to test without modifying data

**Solution:** Use a test directory:

.. code-block:: bash

    # Create test directory
    mkdir -p /tmp/test

    # Test in /tmp
    esgdrs make upgrade --project cmip6 /data/incoming/ --root /tmp/test --link

    # Review output with tree or find
    tree /tmp/test/CMIP6/

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
    esgmapfile --version

    # Check available projects (if esgvoc accessible)
    python -c "import esgvoc; print(esgvoc.list_projects())"

    # Verify NetCDF file structure
    ncdump -h your_file.nc

    # Test with single file
    esgdrs make list --project cmip6 /path/to/single/file.nc

Quick Reference
***************

**Essential Commands:**

.. code-block:: bash

    # Preview what datasets will be created
    esgdrs make list --project PROJECT /path/to/incoming/

    # Preview DRS directory structure
    esgdrs make tree --project PROJECT /path/to/incoming/ --root /output/path

    # See planned operations (dry-run)
    esgdrs make todo --project PROJECT /path/to/incoming/ --root /output/path --link

    # Apply DRS structure
    esgdrs make upgrade --project PROJECT /path/to/incoming/ --root /output/path --link

    # Generate mapfiles
    esgmapfile make --project PROJECT --directory /path/to/drs/ --outdir /path/to/mapfiles/

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
