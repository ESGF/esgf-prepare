.. _check-vocab:

Check CV against configuration INI files
========================================

In the case that your data already follows the appropriate directory structure, you may want to check that all
values of each facet are correctly declared in the ``esg.<project_id>.ini`` sections. The ``check-vocab`` command
allows you to easily check the configuration file attributes by scanning your data tree, and the facet values
will be derived from the directory pattern.

Alternatively, you may supply a list of dataset IDs in a text file. In this case, the ``check-vocab`` command will
perform a similar operation without scanning the file system, and the facet values will be derived from the
dataset ID pattern.

.. note::
    ``esgprep check-vocab`` is useless if you rebuilt your DRS tree using ``esgprep drs`` with official configuration INI files.

Check from the directory structure
**********************************

.. code-block:: bash

    $> esgprep check-vocab --directory /PATH/TO/SCAN/ --project PROJECT_ID

Check from a dataset list
*************************

The file must contain one dataset ID per line. This can be without version, or with a version suffix of the form
``.v<version>`` or ``#<version>`` which is ignored.

.. code-block:: bash

    $> esgprep check-vocab --dataset-list /PATH/TO/TXT_FILE/ --project PROJECT_ID

Exit status
***********

 * Status = 0
    All the files have been successfully scanned and there were no undeclared values in the configuration INI files.
 * Status = 1
    Some scan errors occured. Some files have been skipped or failed during the scan. See the error logfile.
 * Status = 2
    There were undeclared values in the configuration INI files. See the error logfile.
