.. _troubleshooting:

Troubleshooting
===============

This section covers common issues and their solutions when using ``esgprep``.

.. contents:: Table of Contents
   :local:
   :depth: 2


Common Errors
-------------

Project not found in vocabulary
^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^

**Error message:**

.. code-block:: text

    ValueError: Project 'cmip8' not found in esgvoc

**Cause:**
The specified project is not in the installed controlled vocabularies.

**Solutions:**

1. Check available projects:

   .. code-block:: bash

       $> esgvoc list-projects

2. Verify spelling (project names are case-sensitive):

   .. code-block:: bash

       # Correct
       $> esgdrs list --project cmip7 /data/

       # Wrong (uppercase)
       $> esgdrs list --project CMIP7 /data/

3. Update esgvoc to get new projects:

   .. code-block:: bash

       $> pip install --upgrade esgvoc


No module named 'esgvoc'
^^^^^^^^^^^^^^^^^^^^^^^^

**Error message:**

.. code-block:: text

    ModuleNotFoundError: No module named 'esgvoc'

**Cause:**
The esgvoc library is not installed or not in your Python path.

**Solutions:**

1. Install esgvoc:

   .. code-block:: bash

       $> pip install esgvoc

2. If using a virtual environment, ensure it's activated:

   .. code-block:: bash

       $> source /path/to/venv/bin/activate
       $> pip install esgvoc


Invalid facet value
^^^^^^^^^^^^^^^^^^^

**Error message:**

.. code-block:: text

    ERROR: Invalid value 'invalid_experiment' for facet 'experiment'
    Valid values: historical, 1pctCO2-bgc, esm-flat10, ...

**Cause:**
The NetCDF file contains a facet value not recognized by the controlled vocabulary.

**Solutions:**

1. Check the value in your NetCDF file:

   .. code-block:: bash

       $> ncdump -h your_file.nc | grep experiment

2. Verify valid values:

   .. code-block:: bash

       $> esgvoc get cmip7:experiment:

3. If the value should be valid, update esgvoc:

   .. code-block:: bash

       $> pip install --upgrade esgvoc

4. Override with a valid value (if appropriate):

   .. code-block:: bash

       $> esgdrs list --project cmip7 \
                      --set-value experiment=historical \
                      /data/


No DRS attributes found in NetCDF
^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^

**Error message:**

.. code-block:: text

    WARNING: No DRS attributes found in file: /path/to/file.nc

**Cause:**
The NetCDF file is missing required global attributes for DRS construction.

**Solutions:**

1. Check the file's global attributes:

   .. code-block:: bash

       $> ncdump -h your_file.nc

2. Required attributes for CMIP7:

   - ``mip_era``
   - ``activity``
   - ``organisation``
   - ``source``
   - ``experiment``
   - ``variant_label``

3. Use ``--set-value`` to provide missing attributes:

   .. code-block:: bash

       $> esgdrs list --project cmip7 \
                      --set-value mip_era=CMIP7 \
                      --set-value activity=CMIP \
                      /data/


Permission denied
^^^^^^^^^^^^^^^^^

**Error message:**

.. code-block:: text

    PermissionError: [Errno 13] Permission denied: '/data/...'

**Cause:**
Insufficient permissions to write to the target directory.

**Solutions:**

1. Check directory permissions:

   .. code-block:: bash

       $> ls -la /data/

2. Use a directory where you have write access:

   .. code-block:: bash

       $> esgdrs upgrade --project cmip7 --root ~/my_data /incoming/

3. Create the directory with proper permissions:

   .. code-block:: bash

       $> mkdir -p /data/MIP-DRS7
       $> chmod 755 /data/MIP-DRS7


Symlink creation failed
^^^^^^^^^^^^^^^^^^^^^^^

**Error message:**

.. code-block:: text

    OSError: [Errno 1] Operation not permitted: symbolic link

**Cause:**
The filesystem doesn't support symlinks (e.g., some network filesystems, Windows).

**Solutions:**

1. Use ``--copy`` instead of ``--link``:

   .. code-block:: bash

       $> esgdrs upgrade --project cmip7 --root /data --copy /incoming/

2. Use a filesystem that supports symlinks (ext4, xfs, etc.)


Performance Issues
------------------

Slow checksum calculation
^^^^^^^^^^^^^^^^^^^^^^^^^

**Symptom:**
Mapfile generation takes hours for large files.

**Solutions:**

1. Use pre-calculated checksums:

   .. code-block:: bash

       # Generate checksums separately
       $> find /data -name "*.nc" -exec sha256sum {} \; > checksums.txt

       # Use them with esgmapfile
       $> esgmapfile make --project cmip7 \
                          --checksums-from checksums.txt \
                          /data/

2. Skip checksums for testing (not for production):

   .. code-block:: bash

       $> esgmapfile make --project cmip7 --no-checksum /data/

3. Use more processes if CPU-bound:

   .. code-block:: bash

       $> esgmapfile make --project cmip7 --max-processes 8 /data/


High memory usage
^^^^^^^^^^^^^^^^^

**Symptom:**
Process uses excessive RAM or gets killed.

**Solutions:**

1. Process files in smaller batches:

   .. code-block:: bash

       # Process one directory at a time
       for dir in /data/*/; do
           esgmapfile make --project cmip7 "$dir"
       done

2. Reduce number of parallel processes:

   .. code-block:: bash

       $> esgmapfile make --project cmip7 --max-processes 2 /data/


Slow file scanning
^^^^^^^^^^^^^^^^^^

**Symptom:**
``esgdrs list`` takes a long time to scan directories.

**Solutions:**

1. Be more specific with paths:

   .. code-block:: bash

       # Instead of scanning all data
       $> esgdrs list --project cmip7 /data/

       # Scan specific subdirectory
       $> esgdrs list --project cmip7 /data/MIP-DRS7/CMIP7/CMIP/IPSL/

2. Use include/exclude filters:

   .. code-block:: bash

       $> esgdrs list --project cmip7 \
                      --include-file '^.*tas.*\.nc$' \
                      /data/


Data Validation Failures
------------------------

Invalid filename format
^^^^^^^^^^^^^^^^^^^^^^^

**Error message:**

.. code-block:: text

    WARNING: Unable to parse filename: invalid_name.nc

**Cause:**
The filename doesn't match the expected CMOR pattern.

**Solution:**
Ensure filenames follow the project convention:

.. code-block:: text

    # CMIP7 format:
    <variable>_<frequency>_<source>_<experiment>_<variant>_<region>_<grid>[_<time>].nc

    # Example:
    tas_mon_IPSL-CM7A-LR_historical_r1i1p1f1_glb_g1_185001-201412.nc


Missing time range in filename
^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^

**Error message:**

.. code-block:: text

    WARNING: No time range found in filename

**Cause:**
Fixed-field files (like orography) don't have time ranges in filenames.

**Solution:**
This is expected for time-invariant data. The warning can be ignored.


Version Conflicts
-----------------

Duplicate dataset ID
^^^^^^^^^^^^^^^^^^^^

**Error message:**

.. code-block:: text

    WARNING: Dataset already exists: CMIP7.CMIP.IPSL...

**Cause:**
A dataset with the same ID already exists in the target directory.

**Solutions:**

1. Use ``--upgrade-from-latest`` to create a new version:

   .. code-block:: bash

       $> esgdrs upgrade --project cmip7 \
                         --root /data \
                         --upgrade-from-latest \
                         /incoming/

2. Remove the existing dataset first (if intentional):

   .. code-block:: bash

       $> rm -rf /data/MIP-DRS7/CMIP7/.../v20250101/


Broken symlinks
^^^^^^^^^^^^^^^

**Symptom:**
Files in version directories point to non-existent files.

**Cause:**
Original files in ``files/`` directory were moved or deleted.

**Solutions:**

1. Check for broken symlinks:

   .. code-block:: bash

       $> find /data -type l ! -exec test -e {} \; -print

2. Recreate the DRS structure from original files:

   .. code-block:: bash

       $> esgdrs upgrade --project cmip7 --root /data /path/to/original/files/

3. Update the ``latest`` symlink:

   .. code-block:: bash

       $> esgdrs latest --project cmip7 /data/


Getting Help
------------

Debug mode
^^^^^^^^^^

Enable verbose output for debugging:

.. code-block:: bash

    $> esgdrs list --project cmip7 --debug /data/

Check esgvoc status
^^^^^^^^^^^^^^^^^^^

Verify vocabulary installation:

.. code-block:: bash

    $> esgvoc status

Validate DRS paths
^^^^^^^^^^^^^^^^^^

Check if a path is valid according to the vocabulary:

.. code-block:: bash

    $> esgvoc drsvalid cmip7 directory /data/MIP-DRS7/CMIP7/CMIP/IPSL/... -v

Report issues
^^^^^^^^^^^^^

If you encounter a bug:

1. Collect relevant information:

   .. code-block:: bash

       $> python --version
       $> pip show esgprep esgvoc
       $> esgvoc status

2. Report at: https://github.com/ESGF/esgf-prepare/issues


See Also
--------

- :ref:`concepts` - Understanding ESGF terminology
- :ref:`examples` - Complete workflow examples
- :ref:`faq` - Frequently asked questions
