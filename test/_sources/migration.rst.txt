.. _migration:


Migration Guide from esgprep 2.x to 3.0
========================================

``esgprep`` version 3.0 introduces significant changes from the previous Python 2 version. This guide helps you
transition from version 2.x to 3.0.

.. note:: Version 3.0 is a Python 3.12+ rewrite with modernized architecture and dependencies.

Breaking Changes
****************

**Removed Commands**

The following commands have been removed in version 3.0:

 * ``esgfetchini`` - Configuration file fetching
 * ``esgfetchtables`` - CMOR table fetching
 * ``esgcheckvocab`` - Vocabulary checking

**Remaining Commands**

The core data preparation commands remain available:

 * ``esgdrs`` - DRS tree management
 * ``esgmapfile`` - Mapfile generation

Migration from esgfetchini
***************************

**What changed:**

The ``esgfetchini`` command previously downloaded ``esg.<project_id>.ini`` configuration files from the ESGF GitHub
repository. This functionality is now integrated into the ``esgvoc`` library.

**Old workflow (version 2.x):**

.. code-block:: bash

    # Fetch configuration files
    $> esgfetchini --project cmip6
    $> esgfetchini --project cmip5 cordex

**New workflow (version 3.0+):**

No action required. The ``esgvoc`` library automatically handles configuration and vocabulary management:

.. code-block:: bash

    # Just use esgdrs or esgmapfile directly
    $> esgdrs make --project cmip6 /path/to/data/
    $> esgmapfile make --project cmip6 /path/to/data/

**What happens behind the scenes:**

 * ``esgvoc`` automatically fetches and caches project definitions
 * Vocabularies are updated automatically when needed
 * No manual configuration file management required
 * Cache is stored locally for offline use

**Advanced configuration:**

If you need to customize vocabulary sources or manage caching, refer to the `esgvoc documentation
<https://esgvoc.readthedocs.io/>`_.

Migration from esgfetchtables
******************************

**What changed:**

The ``esgfetchtables`` command downloaded CMOR tables from PCMDI GitHub repositories. This functionality has been
removed as CMOR table management is outside the scope of ``esgprep``.

**Old workflow (version 2.x):**

.. code-block:: bash

    # Fetch CMOR tables
    $> esgfetchtables --project cmip6
    $> esgfetchtables --branch master --table-dir /path/to/tables/

**New workflow (version 3.0+):**

CMOR table management should be handled separately using appropriate tools:

 * Download tables directly from `PCMDI repositories <https://github.com/PCMDI>`_
 * Use CMOR-specific tools for table validation
 * Manage tables according to your project's requirements

``esgprep`` focuses on DRS tree management and mapfile generation, not on CMOR table management.

Migration from esgcheckvocab
****************************

**What changed:**

The ``esgcheckvocab`` command validated facet values against configuration files. This functionality is now integrated
into the core ``esgdrs`` and ``esgmapfile`` commands through the ``esgvoc`` library.

**Old workflow (version 2.x):**

.. code-block:: bash

    # Check vocabulary compliance
    $> esgcheckvocab --project cmip6 --directory /path/to/data/
    $> esgcheckvocab --project cmip6 --incoming /path/to/incoming/
    $> esgcheckvocab --project cmip6 --dataset-list datasets.txt

**New workflow (version 3.0+):**

Vocabulary checking is now automatic when using ``esgdrs`` or ``esgmapfile``:

.. code-block:: bash

    # Vocabulary is automatically validated during processing
    $> esgdrs list --project cmip6 /path/to/data/
    $> esgmapfile make --project cmip6 /path/to/data/

**What happens behind the scenes:**

 * ``esgvoc`` validates facet values automatically
 * Invalid values are reported as errors during processing
 * No separate validation step required
 * Validation uses the same controlled vocabularies as before

Python Version Requirements
****************************

**Version 2.x:**
 * Python 2.6+ (Python 2.7 recommended)

**Version 3.0+:**
 * Python 3.12+ (required)

You must upgrade your Python environment to Python 3.12 or higher. See :ref:`installation` for details.

Dependency Changes
******************

**Removed dependencies:**

 * ``ESGConfigParser`` - Replaced by ``esgvoc``
 * ``tqdm`` - Progress bars modernized

**New dependencies:**

 * ``esgvoc`` >= 1.0.1 - Controlled vocabulary and configuration management
 * ``python-levenshtein`` >= 0.27.1 - Enhanced string matching
 * Updated versions of ``numpy``, ``netCDF4``, and other core libraries

All dependencies are installed automatically via ``pip install esgprep``.

Configuration File Migration
*****************************

**Old system (version 2.x):**

Configuration stored in ``/esg/config/esgcet/`` or custom directories:

 * ``esg.ini`` - General configuration
 * ``esg.<project_id>.ini`` - Project-specific configuration

**New system (version 3.0+):**

Configuration managed by ``esgvoc``:

 * No manual file management required
 * Vocabularies cached automatically
 * Updates handled transparently

If you have custom ``esg.<project_id>.ini`` files, you will need to work with the ``esgvoc`` maintainers to integrate
them into the vocabulary system. See :ref:`configuration` for details.

Command-Line Argument Changes
******************************

Most command-line arguments remain the same between versions. Key changes:

**Removed arguments:**

 * ``-i, --ini`` - Configuration directory (no longer needed with ``esgvoc``)

**Unchanged arguments:**

 * ``-p, --project`` - Project identifier
 * ``-l, --log`` - Logfile location
 * ``-d, --debug`` - Debug mode
 * ``--max-processes`` - Multiprocessing control
 * ``--color, --no-color`` - Color output control
 * All filter arguments (``--ignore-dir``, ``--include-file``, ``--exclude-file``)

Quick Reference
***************

+---------------------------+------------------------------------------+
| Old Command (2.x)         | New Approach (3.0+)                      |
+===========================+==========================================+
| ``esgfetchini``           | Automatic via ``esgvoc``                 |
+---------------------------+------------------------------------------+
| ``esgfetchtables``        | Use CMOR tools directly                  |
+---------------------------+------------------------------------------+
| ``esgcheckvocab``         | Automatic in ``esgdrs``/``esgmapfile``   |
+---------------------------+------------------------------------------+
| ``esgdrs``                | ``esgdrs`` (unchanged)                   |
+---------------------------+------------------------------------------+
| ``esgmapfile``            | ``esgmapfile`` (unchanged)               |
+---------------------------+------------------------------------------+

Getting Help
************

If you encounter issues during migration:

 * Check the updated documentation for :ref:`usage`, :ref:`drs`, and :ref:`mapfiles`
 * Review the :ref:`configuration` section for ``esgvoc`` details
 * Report issues on `GitHub <https://github.com/ESGF/esgf-prepare/issues>`_
 * Consult the `esgvoc documentation <https://esgvoc.readthedocs.io/>`_ for vocabulary management
