.. _usage:

Generic usage
=============

.. note:: All the following arguments can be safely combined and add to the subcommand arguments.

Check the help
**************

.. code-block:: bash

    $> esgprep -h
    $> esgprep SUBCOMMAND -h

Check the version
*****************

.. code-block:: bash

    $> esgprep -V

Run the test suite
******************

.. warning::
    Not available for the time being.

.. code-block:: bash

    $> esgprep --test
    $> esgprep SUBCOMMAND --test

Add verbosity
*************

Some progress bars informs you about the processing statut of the different subcommands. You can switch to a more
verbose mode displaying each step.

.. code-block:: bash

    $> esgprep SUBCOMMAND -v

.. warning::
    The verbose mode is silently actived in the case of a logfile (i.e., no progress bars).


Specify the project
*******************

The ``--project`` argument is used to parse the corresponding configuration INI file. It is **always required**
(except for ``fetch-ini`` subcommand). This argument is case-sensitive and has to correspond to a section name of
the configuration file(s).

.. code-block:: bash

    $> esgprep SUBCOMMAND --project PROJECT_ID

Submit a configuration directory
********************************

By default, the configuration files are fetched or read from ``/esg/config/esgcet`` that is the usual configuration
directory on ESGF nodes. If you're preparing your data outside of an ESGF node, you can submit another directory to
fetch and read the configuration files.

.. code-block:: bash

    $> esgprep SUBCOMMAND -i /PATH/TO/CONFIG/

.. note::
    In the case of ``fetch-ini`` subcommand, if you're not on an ESGF node and ``/esg/config/esgcet`` doesn't exist,
    the configuration file(s) are fetched into an ``ini`` folder in your working directory.


Use a logfile
*************

All errors and exceptions are logged into a file named ``esgprep-YYYYMMDD-HHMMSS-PID.err``.
Other information are logged into a file named ``esgprep-YYYYMMDD-HHMMSS-PID.log`` only if ``--log`` is submitted.
If not, the standard output is used following the verbose mode.
By default, the logfiles are stored in a ``logs`` folder created in your current working directory (if not exists).
It can be changed by adding a optional logfile directory to the flag.

.. code-block:: bash

    $> esgprep SUBCOMMAND --log
    $> esgprep SUBCOMMAND --log /PATH/TO/LOGDIR/

Use filters
***********

``esgprep check-vocab`` and ``esgprep mapfile`` subcommands will scan your local archive to achieve proper data
management. In such a scan, you can filter the file discovery by using a Python regular expression
(see `re <https://docs.python.org/2/library/re.html>`_ Python library).

The default is to walk through your local filesystem ignoring the ``files`` and ``latest`` version levels
and any hidden folders by using the following regular expression: ``^.*/(files|latest|\.[\w]*).*$``. It can be change
with:

.. code-block:: bash

    $> esgprep SUBCOMMAND --ignore-dir-filter PYTHON_REGEX

``esgprep`` only considers unhidden NetCDF files by default using the following regular expression: ``^[!.].*\.nc$``.
It can be change with:

.. code-block:: bash

    $> esgprep SUBCOMMAND --include-file-filter PYTHON_REGEX

Keep in mind that ``--ignore-dir-filter`` specifies a direcotry pattern **NOT** to be matched, and
``--include-file-filter`` specifies a filename pattern **TO BE** matched.

.. warning:: ``esgprep fetch-ini`` does not allow those features and ``esgprep drs`` only works with unhidden
    NetCDF files.

Use multiprocessing
*******************

``esgprep`` uses a multiprocessing interface. This is useful to process a large amount of data, especially in the case
of ``drs`` and ``mapfile`` subcommands with file checksum computation. Set the number of maximal threads to
simultaneously process several files (4 threads is the default and one seems sequential processing).

.. code-block:: bash

    $> esgprep SUBCOMMAND --max-threads 4