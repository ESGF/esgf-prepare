.. _mapfiles:


Generate mapfile for ESGF publication
=====================================

The publication process on the ESGF nodes requires *mapfiles*. Mapfiles are text files where each line
describes a file to publish, using the following format:

``dataset_ID | absolute_path | size_bytes [ | option=value ]``

 1. All values have to be pipe-separated.
 2. The dataset identifier, the absolute path and the size (in bytes) are required.
 3. Adding the version number to the dataset identifier is strongly recommended to publish in a in bulk.
 4. Strongly recommended optional values are:

  - ``mod_time``: last modification date of the file (since Unix EPOCH time, i.e., seconds since January, 1st, 1970),
  - ``checksum``: file checksum,
  - ``checksum_type``: checksum type (MD5 or the default SHA256).

 5. Your directory structure has to strictly follows the tree fixed by the DRS including the version facet.
 6. To store ONE mapfile PER dataset is strongly recommended.

Several ``esgmapfile`` actions are available to manage your mapfiles:
 - ``make`` generates the mapfiles (the default),
 - ``show`` displays the expected mapfiles path to be generated.

Default mapfile generation
**************************

The default behavior is to pick up the latest version in the DRS. This required version with a date format
(e.g., v20151023). If the version is directly specified in positional argument, the version number from supplied
directory is used.

.. code-block:: bash

    $> esgmapfile make --project PROJECT_ID /PATH/TO/SCAN/

Mapfile without files checksums
*******************************

Because this could be time consuming ``--no-checksum`` allows you not include the file checksum into your mapfile(s).

.. code-block:: bash

    $> esgmapfile make --project PROJECT_ID /PATH/TO/SCAN/ --no-checksum

Mapfile with pre-calculated checksums
*************************************

If your file checkusms have been already caclulated apart, you can submit a file to ``esgmapfile`` with the checksum
list. This checksum file must have the same format as the output of the UNIX command-lines "*sum".

.. code-block:: bash

    $> esgmapfile make --project PROJECT_ID /PATH/TO/SCAN/ --checksums-from /PATH/TO/CHECKSUMS/FILE


.. note:: In the case of unfound checksums, it falls back to compute the checksum as normal.

Mapfile without DRS versions
****************************

.. code-block:: bash

    $> esgmapfile make --project PROJECT_ID /PATH/TO/SCAN/ --no-version

Mapfile name using tokens
*************************

The mapfile name is composed by the dataset ID and the dataset version dot-separated. Another template
can be specified for the output mapfile(s) name using several tokens. Substrings ``{dataset_id}``, ``{version}``,
``{job_id}`` or ``{date}`` (in YYYYDDMM) will be substituted where found. If ``{dataset_id}`` is not present in mapfile
name, then all datasets will be written to a single mapfile, overriding the default behavior of producing ONE mapfile
PER dataset.

.. code-block:: bash

    $> esgmapfile make --project PROJECT_ID /PATH/TO/SCAN/ --mapfile {dataset_id}.{job_id}
    $> esgmapfile make --project PROJECT_ID /PATH/TO/SCAN/ --mapfile {date}.{job_id}
    $> esgmapfile make --project PROJECT_ID /PATH/TO/SCAN/ --mapfile MY_MAPFILE.{version}.{date}

Organize your mapfiles
**********************

The mapfile(s) are generated into a ``mapfile`` folder created in your working directory (if exists). This can be
changed by submitting an output directory for your mapfiles.

In addition, a ``mapfile_drs`` attribute can be added into the corresponding project section of the configuration INI
file(s) (see :ref:`configuration`). In the same way as the ``directory_format`` it defines a tree depending on the
facets. Each mapfile is then written into the corresponding output directory. This ``mapfile_drs`` directory structure
will be added to the output directory if submitted.

.. code-block:: bash

    $> esgmapfile make --project PROJECT_ID /PATH/TO/SCAN/ --outdir /PATH/TO/MY_MAPFILES/

The output directory is cleaned up prior to mapfile process to avoid uncompleted mapfiles. In the case of several
``esgmapfile`` instances run with the same output directory it is recommended to disable the cleanup:

.. code-block:: bash

    $> esgmapfile make --project PROJECT_ID /PATH/TO/SCAN/ --no-cleanup

Walking through *latest* directories only
*****************************************

.. code-block:: bash

    $> esgmapfile make --project PROJECT_ID /PATH/TO/SCAN/ --latest-symlink

Walking through a particular version only
*****************************************

.. code-block:: bash

    $> esgmapfile make --project PROJECT_ID /PATH/TO/SCAN/ --version VERSION

Walking through all versions
****************************

.. code-block:: bash

    $> esgmapfile make --project PROJECT_ID /PATH/TO/SCAN/ --all-versions

.. warning:: This disables ``--no-version``.

Add technical notes
*******************

.. code-block:: bash

    $> esgmapfile make --project PROJECT_ID /PATH/TO/SCAN/ --tech-notes-url URL --tech-notes-title TITLE

Overwrite the dataset identifier
********************************

.. code-block:: bash

    $> esgmapfile make --project PROJECT_ID /PATH/TO/SCAN/ --dataset-name DATASET_NAME

.. warning:: All files will belong to the specified dataset, regardless of the DRS.

Show the expected mapfile name and path
***************************************

The ``show`` works as a "dry-run" of the ``make`` and supports different types inputs.
You can show the mapfiles full path to be generated from:

 - a directory to scan:

.. code-block:: bash

    $> esgmapfile show --project PROJECT_ID --directory /PATH/TO/SCAN

 - a text file with one dataset ID per line:

.. code-block:: bash

    $> esgmapfile show --project PROJECT_ID --dataset-list /PATH/TO/TXT_FILE

 - a unique dataset ID:

.. code-block:: bash

    $> esgmapfile show --project PROJECT_ID --dataset-id DATASET_ID

In the case of ``--dataset-list`` if no file submitted, the standard input is used.

.. code-block:: bash

    $> esgmapfile show --project PROJECT_ID --dataset-list < /PATH/TO/TXT_FILE

.. warning:: In the case of dataset IDs the version suffix is expected.

.. note:: All the ``make`` arguments can be safely combined with ``show``.

.. note:: Print only mapfile basename instead of the mapfile full path adding ``--basename`` flag.

.. note:: To only print the result without any other info use ``--quiet`` flag.

Exit status
***********

 * Status = 0
    All the files have been successfully scanned and the mapfile(s) properly generated.
 * Status > 0
    Some scan errors occurred or files have been skipped. The error code indicates the number of errors.
