.. _check-vocab:


Check CV against configuration INI files
========================================

Before migrate your data in the appropriate directory structure, or generating the corresponding mapfiles,
you may want to check that all values of each facet are correctly declared in the ``esg.<project_id>.ini`` sections.
The ``check-vocab`` command allows you to easily check the configuration file attributes by scanning your data,
and the facet values will be derived from the directory pattern or the file attributes.

Alternatively, you may supply a list of dataset IDs in a text file. In this case, the ``check-vocab`` command will
perform a similar operation without scanning the file system, and the facet values will be derived from the
dataset ID pattern.

Check from incoming files
*************************

.. code-block:: bash

    $> esgcheckvocab  --project PROJECT_ID --incoming /PATH/TO/SCAN/

.. note:: This doesn't require to have the appropriate directory structure. Facets values will be directly deduces from
  netCDF file attributes.

Check from the directory structure
**********************************

.. code-block:: bash

    $> esgcheckvocab  --project PROJECT_ID --directory /PATH/TO/SCAN/

Check from a dataset list
*************************

The file must contain one dataset ID per line. This can be without version, or with a version suffix of the form
``.v<version>`` or ``#<version>`` which is ignored.

.. code-block:: bash

    $> esgcheckvocab --project PROJECT_ID --dataset-list /PATH/TO/TXT_FILE

If no file submitted, the standard input is used:

.. code-block:: bash

    $> esgcheckvocab --project PROJECT_ID --dataset-list < /PATH/TO/TXT_FILE

You can also check only one particular dataset ID:

.. code-block:: bash

    $> esgcheckvocab --project PROJECT_ID --dataset-id DATASET_ID

Exit status
***********

 * Status = 0
    All the files have been successfully scanned and there were no undeclared values in the configuration INI files.
 * Status > 0
    Some scan errors occurred and files have been skipped.
 * Status = -2
    There were undeclared values in the configuration INI files.
