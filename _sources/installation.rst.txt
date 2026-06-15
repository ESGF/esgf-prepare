.. _installation:


Installation
============

.. note:: ``esgprep`` version 3.0+ requires Python 3.12 or higher.

Installation from PyPI
**********************

.. code-block:: bash

   pip install esgprep

.. important:: **REQUIRED:** After installing ``esgprep``, you must activate the controlled vocabulary databases for each project you need:

   .. code-block:: bash

      esgvoc use cmip6@latest
      esgvoc use cordex-cmip6@latest

   This command downloads pre-built vocabulary databases for the specified project.
   Without this step, ``esgdrs`` and ``esgmapfile`` commands will fail with an error.

   **IMPORTANT:** Run ``esgvoc use <project>@latest`` periodically to update your local vocabularies with the latest
   controlled vocabulary changes from ESGF projects. Outdated vocabularies may cause validation errors
   or prevent recognition of newly added facets, experiments, or models.

   To see available projects and installed versions:

   .. code-block:: bash

      esgvoc status

   For more information about controlled vocabularies management, see the
   `esgvoc documentation <https://esgf.github.io/esgf-vocab/index.html>`_.

Installation from GitHub
************************

1. Clone `our GitHub project <https://github.com/ESGF/esgf-prepare>`_:

.. code-block:: bash

   git clone https://github.com/ESGF/esgf-prepare.git
   cd esgf-prepare

2. Install using pip:

.. code-block:: bash

   pip install -e .

3. Activate the controlled vocabulary databases for your projects:

.. code-block:: bash

   esgvoc use cmip6@latest

4. The ``esgdrs`` and ``esgmapfile`` command-lines are now available.

Using uv (recommended)
**********************

For a faster and more modern Python package manager, you can use `uv <https://github.com/astral-sh/uv>`_:

.. code-block:: bash

    # Install uv if not already installed
    curl -LsSf https://astral.sh/uv/install.sh | sh

    # Create a virtual environment and install esgprep
    uv sync

    # Activate controlled vocabulary databases
    uv run esgvoc use cmip6@latest

.. tip:: **Activate the virtual environment** to avoid prefixing every command with ``uv run``:

   .. code-block:: bash

       # Activate the virtual environment created by uv
       source .venv/bin/activate

       # Now all commands work directly
       esgvoc use cmip6@latest
       esgdrs --version
       esgmapfile --version

       # Deactivate when done
       deactivate

   Once activated, all commands in this documentation can be used without the ``uv run`` prefix.

.. warning:: To run ``esgprep`` tools you have to be logged into a machine which mounts the filesystem hosting the data to publish.

Dependencies and requirements
*****************************

**System requirements:**
 * Linux distribution
 * Python 3.12 or higher

**Python dependencies:**

``esgprep`` uses standard Python libraries and the following external packages:

 * `esgvoc <https://pypi.org/project/esgvoc/>`_ >= 4.1.1 - ESGF controlled vocabulary and configuration handler (replaces ESGConfigParser)
 * `fuzzywuzzy <https://pypi.org/project/fuzzywuzzy/>`_ >= 0.18.0 - Fuzzy string matching
 * `hurry.filesize <https://pypi.org/project/hurry.filesize/>`_ >= 0.9 - Human-readable file sizes
 * `lockfile <https://pypi.org/project/lockfile/>`_ >= 0.12.2 - File locking
 * `netCDF4 <https://unidata.github.io/netcdf4-python/>`_ >= 1.7.2 - NetCDF file handling
 * `numpy <https://numpy.org/>`_ >= 2.2.6 - Numerical computing
 * `python-levenshtein <https://pypi.org/project/python-Levenshtein/>`_ >= 0.27.1 - Fast string matching
 * `requests <https://requests.readthedocs.io/>`_ >= 2.32.3 - HTTP library
 * `treelib <https://pypi.org/project/treelib/>`_ >= 1.7.1 - Tree data structure

All dependencies are automatically installed when installing ``esgprep`` via pip.
