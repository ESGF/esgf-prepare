.. _drs:


Manage local data through the DRS
=================================

The Data Reference Syntax (DRS) defines the way your data must be organised on your filesystem. This allows a proper
publication on the ESGF node. ``esgprep drs`` is designed to help ESGF data node managers to prepare incoming data for
publication, placing files in the DRS directory structure, and to manage multiple versions of publication-level datasets
in a way that minimises disk usage.

.. warning:: Only CMORized netCDF files are supported as incoming files.

Several ``esgprep drs`` actions are available to manage your local archive:

 - ``list`` lists publication-level datasets,
 - ``tree`` displays the final DRS tree,
 - ``todo`` shows file operations pending for the next version,
 - ``upgrade`` makes the changes to upgrade datasets to the next version.

``esgprep drs`` deduces the excepted DRS by scanning the incoming files and checking the facets against the
corresponding ``esg.<project>.ini`` file. The DRS facets values are deduced from:

 1. The command-line using ``--set facet=value``. This flag can be used several times to set several facets values.
 2. The filename pattern using the ``filename_format`` from the ``esg.<project>.ini``.
 3. The NetCDF global attributes by picking the attribute with the nearest name of the facet key.

.. warning:: The incoming files are supposed to be produced by `CMOR <https://cmor.llnl.gov/>`_ (or at least be
    CMOR-compliant) and unversioned. ``esgprep drs`` will apply a version regardless of the incoming file path. The
    applied version only depends on the ``--version`` flag and the existing dataset versions in the DRS ``--root``.

List the datasets related to the incoming files
***********************************************

The resulting table lists each dataset with:
 - the latest known version on the filesystem (i.e., the root directory),
 - the upgraded version to apply,
 - the number of related incoming files,
 - the total size of the upgraded dataset (i.e., the sum of all incoming files related to this upgrade).

.. code-block:: bash

    $> esgprep drs list --project PROJECT_ID /PATH/TO/SCAN/

Set a facet value
*****************

In some cases, a DRS facet value cannot be properly deduces from the above sources. To solve this issue, a facet value
can be set for the whole scan. By duplicating the flag several facet value can be enforced. If the same facet key is
used, only the last value will be considered.

.. code-block:: bash

    $> esgprep drs list --project PROJECT_ID /PATH/TO/SCAN/ --set-value FACET_KEY=VALUE
    $> esgprep drs list --project PROJECT_ID /PATH/TO/SCAN/ --set-value FACET_KEY1=VALUE1 --set-value FACET_KEY2=VALUE2

.. note:: For instance, the ``product`` facet in CMIP5 project is not part of the filename and is often set to
    ``output`` in CMIP5 NetCDF global attributes however it should be ``output1`` or ``output2``. Consequently, you can
    use ``--set-value product=output1`` or ``--set-value product=output2`` depending on the dataset.

Enforce a facet mapping
***********************

Based on the same schema of the ``--set-value`` argument, the mapping between a (list of) facet key and a (list of)
particular NetCDF attribute can be enforced for the whole scan.

.. code-block:: bash

    $> esgprep drs list --project PROJECT_ID /PATH/TO/SCAN/ --set-key FACET_KEY=ATTRIBUTE
    $> esgprep drs list --project PROJECT_ID /PATH/TO/SCAN/ --set-key FACET_KEY1=ATTRIBUTE1 --set-value FACET_KEY2=ATTRIBUTE2

.. note:: For instance, the ``institute`` facet in CORDEX project is not part of the filename and corresponds to the
    ``institute_id`` NetCDF global attribute. Consequently, you can use ``--set-key institute=institute_id``.

Set up the version upgrade
**************************

The upgraded version can be set using ``--version YYYYMMDD`` instead of the current date (the default).

.. code-block:: bash

    $> esgprep drs list --project PROJECT_ID /PATH/TO/SCAN/ --version YYYYMMDD

Visualize the excepted DRS tree
*******************************

In order to save disk space, the scanned files are moved into ``files/dYYYYMMDD`` folders. The ``vYYYYMMDD`` has a
symbolic links skeleton that avoid to duplicate files between two versions.

.. code-block:: bash

    $> esgprep drs tree --project PROJECT_ID /PATH/TO/SCAN/

.. warning:: Some miscellaneous characters could appear due to wrong encoding configuration. To see ASCII characters,
    choose another utf-8 font in your console setup.

Set up a root directory
***********************

By default, the DRS tree is built from your current directory. This can be changed by submitting a root path.

.. code-block:: bash

    $> esgprep drs tree --project PROJECT_ID /PATH/TO/SCAN/ --root /PATH/TO/MY_ROOT

.. warning:: The DRS tree is automatically rebuilt from the project level. Be careful to not submit a root path
    including the project.

List Unix command to apply
**************************

The ``todo`` action can be seen as a dry-run to check which unix commands should be apply to build the expected DRS
tree. At this step, no file are moved or copy to the final DRS.

.. code-block:: bash

    $> esgprep drs todo --project PROJECT_ID /PATH/TO/SCAN/

Those Unix command-lines can also be written into a file for further process:

.. code-block:: bash

    $> esgprep drs todo --project PROJECT_ID /PATH/TO/SCAN/ --commands-file /PATH/TO/COMMANDS.txt

.. note:: Only the commands statements are written to the file. This is not a logfile.

By default another ``esgprep drs todo`` run will append new command-lines to the file (if exists).
To overwrite existing file:

.. code-block:: bash

    $> esgprep drs todo --project PROJECT_ID /PATH/TO/SCAN/ --commands-file /PATH/TO/COMMANDS.txt --overwrite-commands-file

Change the migration mode
*************************

``esgprep drs`` allows different file migration mode.
Default is to move the files from the incoming path to the root directory. Use ``--copy`` to make hard copies,
``--link`` to make hard links or ``--symlink`` to make symbolic links from the incoming path. We recommend to use
``--link`` and remove the incoming directory after DRS checking. This doesn't affect the symbolic link skeleton used
for the dataset versioning.

.. code-block:: bash

    $> esgprep drs todo --project PROJECT_ID /PATH/TO/SCAN/ --copy
    $> esgprep drs todo --project PROJECT_ID /PATH/TO/SCAN/ --link
    $> esgprep drs todo --project PROJECT_ID /PATH/TO/SCAN/ --symlink

.. warning:: ``esgprep drs`` temporarily stores the result of the ``list`` action to quickly generate the DRS tree
    afterwards. This requires to strictly submit the same arguments from the ``list`` action to the following ones.
    If not, the incoming files are automatically scan again.

Run the DRS upgrade
*******************

This will apply all the Unix command you can print with the ``todo`` action.

.. code-block:: bash

    $> esgprep drs upgrade --project PROJECT_ID /PATH/TO/SCAN/

Disable checksum comparison
***************************

To avoid mistakes in versioning, ``esgprep drs`` compares the incoming files to the files from the latest known version
on the filesystem using a ``sha256`` checksum. Because this could be time consuming ``--no-checksum`` allows you to only
make a comparison on filenames.

.. code-block:: bash

    $> esgprep drs upgrade --project PROJECT_ID /PATH/TO/SCAN/ --no-checksum

Exit status
***********

 * Status = 0
    All the files have been successfully scanned and the DRS tree properly generated.
 * Status = 1
    No files found. No DRS tree can be built.
 * Status = 2
    Some scan errors occurred. Some files have been skipped or failed during the scan potentially leading to an
    incomplete DRS tree. See the error logfile.
 * Status = 3
    All the files have been skipped or failed during the scan leading to no DRS tree. See the error logfile.
