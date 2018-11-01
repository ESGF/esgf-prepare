.. _fetchini:


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

    $> esgfetchini
    $> esgfetchini --project PROJECT_ID
    $> esgfetchini --project PROJECT_ID1 PROJECT_ID2

.. warning::
   If a configuration file already exists, the default is to overwrite it only if local and remote checksums are different.

Fetch file(s) from the devel branch
***********************************

.. code-block:: bash

    $> esgfetchini --devel

Keep existing file(s)
*********************

.. code-block:: bash

    $> esgfetchini -k

Enforce overwriting
*******************

.. code-block:: bash

    $> esgfetchini -o

.. warning:: ``-o`` and ``-k`` cannot be used simultaneously.

Enable file backup
******************

When overwriting existing files, two backup modes can be enabled:

 * ``one_version`` renames the existing file in its source directory adding a ``.bkp`` extension to the filename (the default).
 * ``keep_versions`` moves the existing file to a subdirectory called ``bkp`` and add a timestamp to the filename.

.. code-block:: bash

    $> esgfetchini -b
    $> esgfetchini -b keep_versions

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
    All the configuration files have been successfully fetched.
 * Status = 1
    One or several errors occurred.