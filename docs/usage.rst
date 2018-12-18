.. _usage:


Generic usage
=============

All the following arguments can be safely combined and add to each of the esgprep **COMMAND**:
 - ``esgfetchini``
 - ``esgfetchtables``
 - ``esgdrs``
 - ``esgcheckvocab``
 - ``esgmapfile``

Check the help
**************

.. code-block:: bash

    $> COMMAND [SUBCOMMAND] {-h,--help}

Check the version
*****************

.. code-block:: bash

    $> COMMAND {-v,--version}

.. note:: The program version will be the same for all the esgprep tools.

Debug mode
**********

Some progress bars informs you about the processing status of the different subcommands. You can switch to a more
verbose mode displaying each step with useful additional information.

.. code-block:: bash

    $> COMMAND [SUBCOMMAND] {-d,--debug}

.. warning::
    This debug/verbose mode is silently activated in the case of a logfile (i.e., no progress bars).

Specify the project
*******************

The ``--project`` argument is used to parse the corresponding configuration INI file. It is **always required**
(except for ``esgfetchini`` and ``esgfetchtables`` subcommands). This argument is case-sensitive and has to
correspond to a section name of the configuration file(s).

.. code-block:: bash

    $> COMMAND [SUBCOMMAND] {-p,--project} PROJECT_ID

Submit a configuration directory
********************************

By default, the configuration files are fetched or read from the ``$ESGINI_DIR`` environment variable. If not exists,
``/esg/config/esgcet`` that is the usual configuration directory on ESGF nodes is used. If you're preparing your data
outside of an ESGF node, you can submit another directory to fetch and read the configuration files.

.. code-block:: bash

    $> COMMAND [SUBCOMMAND] -i /PATH/TO/CONFIG/

.. note::
    In the case of ``esgfetchini`` command, if you're not on an ESGF node and ``/esg/config/esgcet`` doesn't exist,
    the configuration file(s) are fetched into an ``ini`` folder in your working directory.

Use a logfile
*************

Outputs can be logged into a file named ``PROG-YYYYMMDD-HHMMSS-PID.log``. If not, the standard output is used following the verbose mode.
By default, the logfiles are stored in a ``logs`` folder created in your current working directory (if not exists).
It can be changed by adding a optional logfile directory to the flag.

.. code-block:: bash

    $> COMMAND [SUBCOMMAND] -l [/PATH/TO/LOGDIR/]

Use filters
***********

``esgcheckvocab`` and ``esgmapfile`` subcommands will scan your local archive to achieve proper data
management. In such a scan, you can filter the file discovery by using a Python regular expression
(see `re <https://docs.python.org/2/library/re.html>`_ Python library).

The default is to walk through your local filesystem ignoring the ``files`` and ``latest`` version levels
and any hidden folders by using the following regular expression: ``^.*/(files|latest|\.[\w]*).*$``. It can be change
with:

.. code-block:: bash

    $> COMMAND [SUBCOMMAND] --ignore-dir PYTHON_REGEX

``esgprep`` only considers unhidden NetCDF files by default excuding the regular expression ``^\..*$`` and
including the following one ``.*\.nc$``. It can be independently change with:

.. code-block:: bash

    $> COMMAND [SUBCOMMAND] --include-file PYTHON_REGEX --exclude-file PYTHON_REGEX

Keep in mind that ``--ignore-dir`` and ``--exclude-file`` specifie a directory pattern **NOT** to be matched, while
``--include-file`` specifies a filename pattern **TO BE** matched.

.. warning:: ``esgfetchini`` does not allow those features and ``esgdrs`` only works with unhidden
    NetCDF files. ``esgfetchtables`` only supports ``--include-file`` and ``--exclude-file`` flags.

Use multiprocessing
*******************

``esgprep`` uses a multiprocessing. This is useful to process a large amount of data, especially in the case
of ``drs`` and ``mapfile`` subcommands with file checksum computation. Set the number of maximal processes to
simultaneously treat several files. One process seems sequential processing. Set it to -1 to use all available
CPU processes (as returned by ``multiprocessing.cpu_count()``). Default is set to 4 processes.

.. code-block:: bash

    $> COMMAND [SUBCOMMAND] --max-processes INTEGER

.. warning:: The number of maximal processes is limited to the maximum CPU count in any case.

Toggle color prompt
*******************

``esgprep`` commands prompot you different results in a color fashion to emphasise useful information.
Those colors can lead to undesired characters into the logs or machine-readable processes. Default is to
enable colors when priting to a terminal. You can switch on/off colors print by using:

.. code-block:: bash

    $> COMMAND [SUBCOMMAND] {--color, --no-color}

Exit status
***********

 * Status = -1
    Argument parsing error.