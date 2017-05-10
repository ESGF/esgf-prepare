.. _usage:

Generic usage
=============

Check the help
**************

.. code-block:: bash

   $> esgprep -h
   $> esgprep <subcommand> -h

Specify the project
*******************

The ``--project`` argument is used to parse the corresponding configuration file. It is **always required**
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

   $> esgprep SUBCOMMAND -i /path/to/config/

.. note::
   In the case of ``fetch-ini`` subcommand, if you're not on an ESGF node and ``/esg/config/esgcet`` doesn't exist,
   the configuration file(s) are fetched into an ``ini`` folder in your working directory.

Add verbosity
*************

Some progress bars informs you about the processing statut of the different subcommands. You can switch to a more
verbose mode displaying each step.

.. code-block:: bash

   $> esgprep SUBCOMMAND -v

.. warning::
   The verbose mode is silently actived in the case of a logfile (i.e., no progress bars).

Use a logfile
*************

All errors and exceptions are logged into a file named ``esgprep-YYYYMMDD-HHMMSS-PID.err``.
Other information are logged into a file named ``esgprep-YYYYMMDD-HHMMSS-PID.log`` only if ``--log`` is submitted.
If not, the standard output is used following the verbose mode.
By default, the logifles are stored in a ``logs`` folder made in your current working directory (if not exists).
It can be changed by submitting a logfile directory.

.. code-block:: bash

   $> esgprep SUBCOMMAND --log /path/to/logdir

.. note:: The logfile directory is optional.


