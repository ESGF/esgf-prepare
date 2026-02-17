.. _examples:

Real-World Examples
===================

This section provides complete, copy-paste-ready examples for common ESGF projects.
Each example shows the full workflow from raw data to publication-ready mapfiles.

.. contents:: Table of Contents
   :local:
   :depth: 2


CMIP7 Example
-------------

CMIP7 (Coupled Model Intercomparison Project Phase 7) is the latest generation of coordinated
climate model experiments. This example demonstrates preparing CMIP7 data for ESGF publication.

Scenario
^^^^^^^^

You have CMIP7 model output from IPSL-CM7A-LR for the historical experiment:

.. code-block:: text

    /incoming/
    ├── tas_mon_IPSL-CM7A-LR_historical_r1i1p1f1_glb_g1_185001-201412.nc
    ├── tas_mon_IPSL-CM7A-LR_historical_r2i1p1f1_glb_g1_185001-201412.nc
    └── pr_mon_IPSL-CM7A-LR_historical_r1i1p1f1_glb_g1_185001-201412.nc

Step 1: List datasets
^^^^^^^^^^^^^^^^^^^^^

First, check what datasets will be created:

.. code-block:: bash

    $> esgdrs list --project cmip7 /incoming/

Expected output:

.. code-block:: text

    Dataset: CMIP7.CMIP.IPSL.IPSL-CM7A-LR.historical.r1i1p1f1.glb.mon.tas.g1
    Files: 1, Size: 2.3 GB, Version: v20250120

    Dataset: CMIP7.CMIP.IPSL.IPSL-CM7A-LR.historical.r2i1p1f1.glb.mon.tas.g1
    Files: 1, Size: 2.3 GB, Version: v20250120

    Dataset: CMIP7.CMIP.IPSL.IPSL-CM7A-LR.historical.r1i1p1f1.glb.mon.pr.g1
    Files: 1, Size: 1.8 GB, Version: v20250120

Step 2: Preview the DRS structure
^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^

See how files will be organized:

.. code-block:: bash

    $> esgdrs tree --project cmip7 /incoming/

Expected output:

.. code-block:: text

    /data/MIP-DRS7/
    └── CMIP7/
        └── CMIP/
            └── IPSL/
                └── IPSL-CM7A-LR/
                    └── historical/
                        ├── r1i1p1f1/
                        │   └── glb/
                        │       └── mon/
                        │           ├── tas/
                        │           │   └── none/
                        │           │       └── g1/
                        │           │           ├── v20250120/
                        │           │           └── latest -> v20250120/
                        │           └── pr/
                        │               └── none/
                        │                   └── g1/
                        │                       ├── v20250120/
                        │                       └── latest -> v20250120/
                        └── r2i1p1f1/
                            └── ...

Step 3: Apply the DRS structure
^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^

Create the directory structure using symlinks (recommended to save disk space):

.. code-block:: bash

    $> esgdrs upgrade --project cmip7 --root /data --link /incoming/

.. note::
   Use ``--link`` to create symlinks instead of copying files. This saves disk space
   and allows the original files to remain in place.

Step 4: Generate mapfiles
^^^^^^^^^^^^^^^^^^^^^^^^^

Create mapfiles for ESGF publication:

.. code-block:: bash

    $> esgmapfile make --project cmip7 /data/MIP-DRS7/

Output files:

.. code-block:: text

    CMIP7.CMIP.IPSL.IPSL-CM7A-LR.historical.r1i1p1f1.glb.mon.tas.g1.v20250120.map
    CMIP7.CMIP.IPSL.IPSL-CM7A-LR.historical.r2i1p1f1.glb.mon.tas.g1.v20250120.map
    CMIP7.CMIP.IPSL.IPSL-CM7A-LR.historical.r1i1p1f1.glb.mon.pr.g1.v20250120.map

Example mapfile content:

.. code-block:: text

    CMIP7.CMIP.IPSL.IPSL-CM7A-LR.historical.r1i1p1f1.glb.mon.tas.g1.v20250120 | /data/MIP-DRS7/CMIP7/CMIP/IPSL/IPSL-CM7A-LR/historical/r1i1p1f1/glb/mon/tas/none/g1/v20250120/tas_mon_IPSL-CM7A-LR_historical_r1i1p1f1_glb_g1_185001-201412.nc | 2469134567 | mod_time=1737331200.0 | checksum=a1b2c3d4... | checksum_type=SHA256


CORDEX-CMIP6 Example
--------------------

CORDEX (Coordinated Regional Climate Downscaling Experiment) provides high-resolution
regional climate projections. This example shows preparing CORDEX-CMIP6 data.

Scenario
^^^^^^^^

You have CORDEX data for the European domain from the ALARO1-SFX model:

.. code-block:: text

    /incoming/
    ├── tas_EUR-12_MPI-ESM1-2-HR_historical_r1i1p1f1_RMIB-UGent_ALARO1-SFX_v1_day_19500101-19501231.nc
    └── pr_EUR-12_MPI-ESM1-2-HR_historical_r1i1p1f1_RMIB-UGent_ALARO1-SFX_v1_day_19500101-19501231.nc

Step 1: List datasets
^^^^^^^^^^^^^^^^^^^^^

.. code-block:: bash

    $> esgdrs list --project cordex-cmip6 /incoming/

Expected output:

.. code-block:: text

    Dataset: CORDEX.DD.EUR-12.RMIB-UGent.MPI-ESM1-2-HR.historical.r1i1p1f1.ALARO1-SFX.v1.day.tas
    Files: 1, Size: 450 MB, Version: v20250120

    Dataset: CORDEX.DD.EUR-12.RMIB-UGent.MPI-ESM1-2-HR.historical.r1i1p1f1.ALARO1-SFX.v1.day.pr
    Files: 1, Size: 380 MB, Version: v20250120

Step 2: Preview and apply DRS
^^^^^^^^^^^^^^^^^^^^^^^^^^^^^

.. code-block:: bash

    # Preview structure
    $> esgdrs tree --project cordex-cmip6 /incoming/

    # Apply structure
    $> esgdrs upgrade --project cordex-cmip6 --root /data --link /incoming/

Step 3: Generate mapfiles
^^^^^^^^^^^^^^^^^^^^^^^^^

.. code-block:: bash

    $> esgmapfile make --project cordex-cmip6 /data/CORDEX/


Key Differences Between Projects
--------------------------------

.. list-table::
   :header-rows: 1
   :widths: 20 40 40

   * - Aspect
     - CMIP7
     - CORDEX-CMIP6
   * - **Scope**
     - Global climate models
     - Regional downscaling
   * - **Resolution**
     - ~100-250 km
     - 12-50 km
   * - **Key facets**
     - source, experiment, frequency
     - domain_id, driving_source_id, source_id
   * - **DRS root**
     - MIP-DRS7/CMIP7/
     - CORDEX/


Dataset Updates (New Versions)
------------------------------

When you need to publish an updated version of existing data:

Scenario
^^^^^^^^

You have corrections to existing CMIP7 data:

.. code-block:: text

    /incoming_v2/
    └── tas_mon_IPSL-CM7A-LR_historical_r1i1p1f1_glb_g1_185001-201412.nc  (corrected)

Using --upgrade-from-latest
^^^^^^^^^^^^^^^^^^^^^^^^^^^

This option reuses unchanged files from the previous version:

.. code-block:: bash

    $> esgdrs upgrade --project cmip7 \
                      --root /data \
                      --link \
                      --upgrade-from-latest \
                      /incoming_v2/

Result:

.. code-block:: text

    /data/MIP-DRS7/CMIP7/.../tas/none/g1/
    ├── files/
    │   ├── d20250101/
    │   │   └── tas_*.nc          (original)
    │   └── d20250120/
    │       └── tas_*.nc          (corrected)
    │
    ├── v20250101/
    │   └── tas_*.nc -> ../files/d20250101/tas_*.nc
    │
    ├── v20250120/
    │   └── tas_*.nc -> ../files/d20250120/tas_*.nc  (new version)
    │
    └── latest -> v20250120/      (updated)

Generate mapfiles for the new version:

.. code-block:: bash

    $> esgmapfile make --project cmip7 --latest /data/MIP-DRS7/


Testing Before Production
-------------------------

Always test your workflow before modifying production data:

.. code-block:: bash

    # Create a test directory
    mkdir -p /tmp/esgprep_test

    # Copy a few sample files
    cp /incoming/tas_*.nc /tmp/esgprep_test/

    # Test the workflow
    $> esgdrs list --project cmip7 /tmp/esgprep_test/
    $> esgdrs tree --project cmip7 /tmp/esgprep_test/
    $> esgdrs upgrade --project cmip7 --root /tmp/test_output --link /tmp/esgprep_test/

    # Verify structure
    tree /tmp/test_output/

    # Generate test mapfiles
    $> esgmapfile make --project cmip7 /tmp/test_output/

    # Review mapfiles
    cat *.map

    # Clean up when satisfied
    rm -rf /tmp/esgprep_test /tmp/test_output


Large Dataset Processing
------------------------

For datasets with many files (>10,000), optimize processing:

Pre-calculate checksums
^^^^^^^^^^^^^^^^^^^^^^^

For large files, pre-calculating checksums can save time:

.. code-block:: bash

    # Create checksum file
    find /incoming -name "*.nc" -exec sha256sum {} \; > checksums.txt

    # Use pre-calculated checksums
    $> esgmapfile make --project cmip7 \
                       --checksums-from checksums.txt \
                       /data/MIP-DRS7/

Optimize multiprocessing
^^^^^^^^^^^^^^^^^^^^^^^^

Adjust the number of processes based on your system:

.. code-block:: bash

    # Use 8 processes (default is 4)
    $> esgmapfile make --project cmip7 \
                       --max-processes 8 \
                       /data/MIP-DRS7/

.. tip::
   For I/O-bound operations (reading many files), more processes may not help.
   For CPU-bound operations (checksum calculation), use as many cores as available.


See Also
--------

- :ref:`concepts` - Understanding ESGF terminology
- :ref:`drs` - Detailed esgdrs command reference
- :ref:`mapfiles` - Detailed esgmapfile command reference
- :ref:`troubleshooting` - Common issues and solutions
