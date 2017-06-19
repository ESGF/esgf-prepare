.. _fetch-ini:

Fetch ESGF configuration INI files
==================================

The ESGF publishing client and most of the ESGF tools rely on configuration files of different kinds, which are the
primary means of configuring the ESGF publisher. The ``esg.<project_id>.ini`` files declare all facets and allowed
values according to the *Data Reference Syntax* (DRS) and the controlled vocabularies of the corresponding project. The
``fetch-ini`` command allows you to download preset files hosted on
`a GitHub repository <https://github.com/ESGF/config/>`_. If you prepare your data outside of an ESGF node using
``esgprep`` as a full standalone toolbox, this step is mandatory. Keep in mind that the fetched files have to be
reviewed to ensure a correct configuration of your projects.

Fetch ``esg.<project_id>.ini`` file(s)
**************************************

Without project argument, all the configuration files will be downloaded.

.. code-block:: bash

    $> esgprep fetch-ini
    $> esgprep fetch-ini --project PROJECT_ID
    $> esgprep fetch-ini --project PROJECT_ID1 PROJECT_ID2

.. warning::
   If a configuration file already exists, the default is to overwrite it only if local and remote checksums are different.

Keep existing file(s)
*********************

.. code-block:: bash

    $> esgprep fetch-ini -k

Enforce overwriting
*******************

.. code-block:: bash

    $> esgprep fetch-ini -o

.. warning:: ``-o`` and ``-k`` cannot be used simultaneously.

Enable file backup
******************

When overwriting existing files, two backup modes can be enabled:

 * ``one_version`` renames the existing file in its source directory adding a ``.bkp`` extension to the filename (the default).
 * ``keep_versions`` moves the existing file to a subdirectory called ``bkp`` and add a timestamp to the filename.

.. code-block:: bash

    $> esgprep fetch-ini -b
    $> esgprep fetch-ini -b keep_versions

Use your GitHub account
***********************

To avoid the Github API rate limit, submit your GitHub username and password.

.. code-block:: bash

    $> esgprep fetch-ini --gh-user MY_GH_USER --gh-password MY_GH_PASSWORD

Exit status
***********

 * Status = 0
    All the configuration have been successfully fetched.
 * Status = 1
    One or several errors occured. See the error logfile.