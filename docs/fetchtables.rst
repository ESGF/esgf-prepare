.. _fetchtables:


Fetch CMOR tables
=================

Some ESGF tools relating to standardization process or data quality control require tables describing CF variables,
theirs coordinates or their attributes. For instance, `PrePARE <https://cmor.llnl.gov/mydoc_cmip6_validator/>`_ relies
on those tables to ensure netCDF files comply to CMIP6 specifications and Data Reference Syntax. Such tables are
initially produced to standardize ESGF data in a CF-compliant way trhough the Climate Model Output Rewriter (CMOR).
The CMOR tables are available for different ESGF projects and hosted on an official `GitHub repository <https://github.com/PCMDI>`_.
Keep in mind that the fetched files have to be reviewed to ensure a correct configuration of your projects.

Fetch tables for one or several project
***************************************

Without project argument, all the available tables will be downloaded.

.. code-block:: bash

    $> esgfetchtables
    $> esgfetchtables --project PROJECT_ID
    $> esgfetchtables --project PROJECT_ID1 PROJECT_ID2

.. warning::
   If a table already exists for one project, the default is to overwrite it only if local and remote checksums are different.

Fetch tables from particular branch or tag
******************************************

.. code-block:: bash

    $> esgfetchtables --branch BRANCH
    $> esgfetchtables --tag TAG

.. warning:: ``--branch`` and ``--tag`` cannot be used simultaneously. Default is ``--branch master``.

Fetch tables using branch or tag regular expression
***************************************************

This can be useful to fetch several branches or tags at a time.

.. code-block:: bash

    $> esgfetchtables --branch-regex REGEX
    $> esgfetchtables --tag-regex REGEX

Change output directory
***********************

If not path submitted, the table will be download in ``/usr/local`` by default. If it doesn't exist or is inaccessible
for writing, your current working directory will be used instead. To change the tables output directory:

.. code-block:: bash

    $> esgfetchtables --table-dir PATH

.. note:: If the submitted directory doesn't exist it will be created.

``esgfetchtables`` downloads tables into the appropriate ``<project>-cmor-tables`` folder by adding a sub-folder
corresponding to the desired branch(s) or tag(s). Thus, the final output directory has the following format:
``<table_dir>/<project>-cmor-tables/<branch>/tag>``.

The branch or tag sub-folder can be disable to follow ``<table_dir>/<project>-cmor-tables/`` format only:

.. code-block:: bash

    $> esgfetchtables --no-subfolder

Keep existing file(s)
*********************

.. code-block:: bash

    $> esgfetchtables -k

Enforce overwriting
*******************

.. code-block:: bash

    $> esgfetchtables -o

.. warning:: ``-o`` and ``-k`` cannot be used simultaneously.

Enable file backup
******************

When overwriting existing files, two backup modes can be enabled:

 * ``one_version`` renames the existing file in its source directory adding a ``.bkp`` extension to the filename (the default).
 * ``keep_versions`` moves the existing file to a subdirectory called ``bkp`` and add a timestamp to the filename.

.. code-block:: bash

    $> esgfetchtables -b
    $> esgfetchtables -b keep_versions

Use your GitHub account
***********************

To release the Github API rate limit, submit your GitHub username and password.

.. code-block:: bash

    $> esgfetchini --gh-user MY_GH_USER --gh-password MY_GH_PASSWORD

Instead of submitting your login and password on the command-line, you can also simply export the following variables
``$GH_USER`` and ``$GH_PASSWORD`` in your UNIX environment.

Exit status
***********

 * Status = 0
    All the tables have been successfully fetched.
 * Status = 1
    One or several errors occurred.