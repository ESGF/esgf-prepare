.. _faq:


Frequently Asked Questions
==========================

This page answers common questions about ``esgprep``. For detailed troubleshooting,
see :ref:`troubleshooting`.

.. contents:: Table of Contents
   :local:
   :depth: 2


General
-------

What is esgprep and why should I use it?
^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^

``esgprep`` is a tool suite for preparing climate data for publication on the
Earth System Grid Federation (ESGF). It handles two main tasks:

1. **DRS organization** (``esgdrs``): Organizes your NetCDF files into the
   standardized Data Reference Syntax directory structure required by ESGF.

2. **Mapfile generation** (``esgmapfile``): Creates mapfiles containing file
   metadata (paths, sizes, checksums) needed by the ESGF publication system.

You should use it if you're publishing climate model output or observational
data to ESGF and need to comply with project data standards (CMIP6, CMIP7,
CORDEX, etc.).


Do I need to be on an ESGF node to use esgprep?
^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^

No. ``esgprep`` can run on any Linux/Unix system with Python 3.12+. You can
prepare your data locally and then transfer the DRS structure and mapfiles
to your ESGF node for publication.


What data formats are supported?
^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^

``esgprep`` works with **NetCDF files** (``.nc``). The files should be:

- CMOR-compliant (following CF conventions)
- Named according to project conventions
- Containing required global attributes

Other formats (HDF5, GRIB, etc.) are not supported.


Can I use esgprep for non-ESGF projects?
^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^

``esgprep`` is designed specifically for ESGF projects with controlled
vocabularies managed by ``esgvoc``. It validates facet values against
these vocabularies.

For custom projects, you would need to:

1. Define your project in ``esgvoc`` (see esgvoc documentation)
2. Or use alternative tools for non-ESGF data organization


Installation
------------

What Python version do I need?
^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^

Python **3.12 or higher** is required. Check your version:

.. code-block:: bash

    $ python3 --version
    Python 3.12.7

If you have an older version, consider using ``pyenv`` or ``conda`` to
install a newer Python.


How do I upgrade from version 2.x?
^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^

Version 3.0 has significant changes from 2.x:

1. **Install the new version:**

   .. code-block:: bash

       $ pip install --upgrade esgprep

2. **Install controlled vocabularies:**

   .. code-block:: bash

       $ esgvoc install

3. **Update your scripts:**

   - Remove ``esgfetchini`` calls (no longer needed)
   - Configuration is now handled by ``esgvoc``
   - Command syntax is mostly compatible

See :ref:`migration` for detailed migration instructions.


What if pip install fails?
^^^^^^^^^^^^^^^^^^^^^^^^^^

Common solutions:

1. **Upgrade pip first:**

   .. code-block:: bash

       $ pip install --upgrade pip

2. **Use a virtual environment:**

   .. code-block:: bash

       $ python3 -m venv esgprep-env
       $ source esgprep-env/bin/activate
       $ pip install esgprep

3. **Check for conflicting packages:**

   .. code-block:: bash

       $ pip check

4. **Install build dependencies (if compilation fails):**

   .. code-block:: bash

       # Debian/Ubuntu
       $ sudo apt-get install python3-dev libnetcdf-dev

       # RHEL/CentOS
       $ sudo yum install python3-devel netcdf-devel


Usage
-----

How do I know which project to specify?
^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^

The ``--project`` argument must match a project defined in the ``esgvoc``
controlled vocabularies. Common values:

- ``cmip6`` - CMIP6 data
- ``cmip7`` - CMIP7 data
- ``cordex`` - CORDEX regional projections
- ``cordex-cmip6`` - CORDEX driven by CMIP6 models
- ``input4mips`` - Input datasets for MIPs
- ``obs4mips`` - Observational datasets for MIPs

To list available projects:

.. code-block:: bash

    $ esgvoc list-projects

.. note::
   Project names are **case-sensitive**. Use ``cmip6``, not ``CMIP6``.


What if my project isn't supported?
^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^

If your project isn't in the vocabulary:

1. **Check for updates:**

   .. code-block:: bash

       $ pip install --upgrade esgvoc
       $ esgvoc install

2. **Verify the project name** (check spelling, case)

3. **Contact your project administrators** - new projects need to be
   added to the official ESGF vocabularies

4. **For testing purposes**, you may be able to use a similar project's
   vocabulary, but this is not recommended for production.


Can I test without modifying my files?
^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^

Yes, several approaches:

1. **Use dry-run commands:**

   .. code-block:: bash

       # Preview datasets
       $ esgdrs make list --project cmip6 /data/incoming/

       # Preview structure
       $ esgdrs make tree --project cmip6 /data/incoming/

       # See planned operations
       $ esgdrs make todo --project cmip6 /data/incoming/ --root /tmp/test

2. **Use a temporary output directory:**

   .. code-block:: bash

       $ esgdrs make upgrade --project cmip6 /data/incoming/ \
                             --root /tmp/test-drs --link

3. **Use hard links (``--link``)** to avoid copying files - original
   files remain untouched.


How do I undo an esgdrs upgrade?
^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^

There's no automatic "undo" command. However:

1. **If you used ``--link`` (hard links):**

   Your original files are untouched. Simply delete the DRS structure:

   .. code-block:: bash

       $ rm -rf /path/to/drs/PROJECT/

2. **If you used ``--symlink``:**

   Original files are untouched. Delete the DRS structure.

3. **If you used default mode (move) or ``--copy``:**

   Files were moved/copied. You'll need to move them back manually or
   restore from backup.

.. tip::
   Always use ``--link`` when testing to preserve your original files.


Checksums
---------

Which checksum algorithm should I use?
^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^

**Recommended: SHA256** (default)

.. code-block:: bash

    $ esgmapfile make --project cmip6 --directory /data/

For new ESGF infrastructure, you can use **multihash format**:

.. code-block:: bash

    $ esgmapfile make --project cmip6 --directory /data/ \
                      --checksum-type sha2-256

**Comparison:**

.. list-table::
   :header-rows: 1
   :widths: 20 30 25 25

   * - Algorithm
     - Use Case
     - Speed
     - ESGF Support
   * - sha256
     - General use (default)
     - Fast
     - Full
   * - sha2-256
     - Multihash format
     - Fast
     - Modern nodes
   * - sha2-512
     - Higher security
     - Slower
     - Modern nodes
   * - md5
     - Legacy only
     - Fastest
     - Deprecated


Can I skip checksums?
^^^^^^^^^^^^^^^^^^^^^

Yes, for **testing only**:

.. code-block:: bash

    $ esgmapfile make --project cmip6 --directory /data/ --no-checksum

.. warning::
   Never skip checksums for production data. Checksums are required for
   ESGF publication and data integrity verification.


How do I provide pre-calculated checksums?
^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^

For large datasets, pre-calculate checksums to save time:

1. **Generate checksums:**

   .. code-block:: bash

       $ find /data -name "*.nc" -exec sha256sum {} \; > checksums.txt

2. **Use them with esgmapfile:**

   .. code-block:: bash

       $ esgmapfile make --project cmip6 --directory /data/ \
                         --checksums-from checksums.txt

The file format should be standard ``sha256sum`` output:

.. code-block:: text

    abc123def456...  /path/to/file1.nc
    789xyz012abc...  /path/to/file2.nc


Troubleshooting
---------------

Why is my project not recognized?
^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^

.. code-block:: text

    ValueError: Project 'cmip6' not found in esgvoc

**Solutions:**

1. Initialize vocabularies (required after installation):

   .. code-block:: bash

       $ esgvoc install

2. Check spelling (case-sensitive):

   .. code-block:: bash

       # Correct
       $ esgdrs make list --project cmip6 /data/

       # Wrong
       $ esgdrs make list --project CMIP6 /data/

3. Update esgvoc:

   .. code-block:: bash

       $ pip install --upgrade esgvoc
       $ esgvoc install

4. List available projects:

   .. code-block:: bash

       $ esgvoc list-projects


What if I get facet validation errors?
^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^

.. code-block:: text

    ERROR: Invalid value 'my_experiment' for facet 'experiment'

**This means** your data contains values not in the controlled vocabulary.

**Solutions:**

1. **Check your NetCDF attributes:**

   .. code-block:: bash

       $ ncdump -h your_file.nc | grep experiment

2. **See valid values:**

   .. code-block:: bash

       $ esgvoc get cmip6:experiment:

3. **If the value should be valid**, update esgvoc:

   .. code-block:: bash

       $ pip install --upgrade esgvoc
       $ esgvoc install

4. **Override temporarily** (use with caution):

   .. code-block:: bash

       $ esgdrs make list --project cmip6 \
                          --set-value experiment=historical \
                          /data/


How do I handle duplicate files?
^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^

If you get warnings about duplicate datasets:

1. **Check if files are truly duplicates:**

   .. code-block:: bash

       $ md5sum /path/to/file1.nc /path/to/file2.nc

2. **If publishing an update**, use versioning:

   .. code-block:: bash

       $ esgdrs make upgrade --project cmip6 /data/incoming/ \
                             --upgrade-from-latest

3. **If replacing existing data**, remove the old version first:

   .. code-block:: bash

       $ rm -rf /data/drs/CMIP6/.../v20240101/


Migration from v2.x
-------------------

What changed from version 2.x?
^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^

Major changes in v3.0:

1. **esgfetchini removed** - Configuration now handled by ``esgvoc``
2. **esgvoc required** - Must run ``esgvoc install`` before first use
3. **Python 3.12+ required** - Older Python versions not supported
4. **Command structure** - Some subcommands reorganized
5. **Mapfile format** - Version separator changed from ``#`` to ``.v``

See :ref:`migration` for complete details.


Where did esgfetchini go?
^^^^^^^^^^^^^^^^^^^^^^^^^

``esgfetchini`` is **no longer needed**. In v2.x, it downloaded INI
configuration files. In v3.0, configuration is handled by the ``esgvoc``
library:

.. code-block:: bash

    # Old way (v2.x) - NO LONGER NEEDED
    $ esgfetchini

    # New way (v3.0)
    $ esgvoc install

The ``esgvoc`` library manages controlled vocabularies and project
definitions automatically.


Do my old scripts still work?
^^^^^^^^^^^^^^^^^^^^^^^^^^^^^

Most scripts will work with minor modifications:

1. **Remove esgfetchini calls:**

   .. code-block:: bash

       # Remove this line
       esgfetchini

       # Add this once (or in setup)
       esgvoc install

2. **Check command syntax:**

   Most commands are compatible, but verify with ``--help``:

   .. code-block:: bash

       $ esgdrs --help
       $ esgmapfile --help

3. **Update Python version** if needed (3.12+ required)

4. **Test with sample data** before running on production


See Also
--------

- :ref:`getting_started` - Step-by-step tutorial
- :ref:`troubleshooting` - Detailed error solutions
- :ref:`concepts` - ESGF terminology explained
- :ref:`migration` - Upgrading from v2.x
