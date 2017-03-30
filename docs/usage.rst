.. _usage:

Generic usage
=============

Specify the project
*******************

.. code-block:: bash

   $> esgprep <command> --project <project_id>

.. warning:: This ``--project`` argument is always required (except 
             it is optional for command ``fetch-ini``)

.. warning:: This ``--project`` name has to correspond to a section of the configuration file.

.. warning:: The ``--project`` is case-sensitive.


Specify a configuration directory
*********************************

.. code-block:: bash

   $> esgprep <command> -i /path/to/config/

Add verbosity
*************

.. code-block:: bash

   $> esgprep <command> -v

Show help message and exit
**************************

.. code-block:: bash

   $> esgprep <command> -h

Use a logfile
*************

.. code-block:: bash

   $> esgprep <command> --log /path/to/logdir
   [...]
   $> cat /path/to/logdir/esgprep-YYYYMMDD-HHMMSS-PID.log
   [...]

.. note:: The logfile directory is optional.


