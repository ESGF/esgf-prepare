.. _usage:

Usage and tutorials
===================

Common usage
************

Specify the project
-------------------

.. code-block:: bash

   $> esgprep <command> --project <project_id>

.. warning:: This ``--project`` argument is always required (except 
             it is optional for command ``fetch-ini``)

.. warning:: This ``--project`` name has to correspond to a section of the configuration file.

.. warning:: The ``--project`` is case-sensitive.


Specify a configuration directory
---------------------------------

.. code-block:: bash

   $> esgprep <command> -i /path/to/config/

Add verbosity
-------------

.. code-block:: bash

   $> esgprep <command> -v

Show help message and exit
--------------------------

.. code-block:: bash

   $> esgprep <command> -h

Use a logfile
-------------

.. code-block:: bash

   $> esgprep <command> --log /path/to/logdir
   [...]
   $> cat /path/to/logdir/esgprep-YYYYMMDD-HHMMSS-PID.log
   [...]

.. note:: The logfile directory is optional.

``esgprep fetch-ini``
*********************

Download a particular esg.<project_id>.ini from GitHub
------------------------------------------------------

.. code-block:: bash

   $> esgprep fetch-ini --project <project_id> --db-password xxxx --tds-password xxxx --esgf-host <data.node.fr> --esg-root-id <institute> --esgf-index-peer <index.node.fr> --db-port <port> --db-host <host>
   YYYY/MM/DD HH:MM:SS INFO https://github.com/ESGF/config/blob/master/publisher-configs/ini/esg.<project_id>.ini --> /esg/config/esgcet/esg.<project_id>.ini
   Overwrite existing "esg.ini"? [y/N] y
   YYYY/MM/DD HH:MM:SS INFO https://github.com/ESGF/config/blob/master/publisher-configs/ini/esg.ini --> /esg/config/esgcet/esg.ini
   Root path for "<project_name>" data: /path/to/data/<project_name>
   YYYY/MM/DD HH:MM:SS INFO "thredds_dataset_roots" in "/esg/config/esgcet/esg.ini" successfully updated
   YYYY/MM/DD HH:MM:SS INFO "project_options" in "/esg/config/esgcet/esg.ini" successfully updated
   YYYY/MM/DD HH:MM:SS INFO "thredds_aggregation/file_services" in "/esg/config/esgcet/esg.ini" successfully formatted
   YYYY/MM/DD HH:MM:SS INFO https://github.com/ESGF/config/blob/master/publisher-configs/esgcet_models_table.txt --> /esg/config/esgcet/esgcet_models_table.txt
   YYYY/MM/DD HH:MM:SS INFO https://github.com/ESGF/config/blob/master/publisher-configs/handlers/ipcc5_handler.py --> /usr/local/uvcdat/2.2.0/lib/python2.7/site-packages/esgcet-2.14.6-py2.7.egg/esgcet/ipcc5_handler.py

.. note:: If a configuration file already exists you are prompted to confirm overwriting (default is "no").

.. warning:: If you choose to overwrite your existing ``esg.ini`` , you should at least provide your ``--db-password`` and ``--tds-password``. The other flags are optional if you run ``esgprep fetch-ini`` within your ESGF node (because ``esgf.properties`` includes the required information). Otherwise, all flags are required to properly configure the ``esg.ini`` (see ``esgprep fetch-ini -h``).

.. note:: ``thredds_dataset_roots``, ``project_options`` and ``thredds_aggregation/file_services`` are updated in any case depending on the project list submitted on the command-line or the available local ``esg.<project_id>.ini``.

.. note:: ``--data-root-path`` can point to a file table with the following line-syntax: ``<project_id> | <data_root_path>``. Each ``<data_root_path>`` should exist and end with the project name (e.g., /path/to/data/CMIP5). If not you are prompted to valid your choice.

Keep existing file(s) without prompt
------------------------------------

.. code-block:: bash

   $> esgprep fetch-ini --project <project_id> -k
   YYYY/MM/DD HH:MM:SS INFO "thredds_dataset_roots" in "/esg/config/esgcet/esg.ini" successfully updated
   YYYY/MM/DD HH:MM:SS INFO "project_options" in "/esg/config/esgcet/esg.ini" successfully updated
   YYYY/MM/DD HH:MM:SS INFO "thredds_aggregation/file_services" in "/esg/config/esgcet/esg.ini" successfully formatted

Overwrite existing file(s) without prompt
-----------------------------------------

.. code-block:: bash

   $> esgprep fetch-ini --project <project_id> -o
   YYYY/MM/DD HH:MM:SS INFO https://github.com/ESGF/config/blob/master/publisher-configs/ini/esg.<project_id>.ini --> /esg/config/esgcet/esg.<project_id>.ini
   YYYY/MM/DD HH:MM:SS INFO https://github.com/ESGF/config/blob/master/publisher-configs/ini/esg.ini --> /esg/config/esgcet/esg.ini
   YYYY/MM/DD HH:MM:SS INFO "thredds_dataset_roots" in "/esg/config/esgcet/esg.ini" successfully updated
   YYYY/MM/DD HH:MM:SS INFO "project_options" in "/esg/config/esgcet/esg.ini" successfully updated
   YYYY/MM/DD HH:MM:SS INFO "thredds_aggregation/file_services" in "/esg/config/esgcet/esg.ini" successfully formatted

.. warning:: ``-o`` and ``-k`` cannot be used simultaneously.

Download all esg.<project_id>.ini from GitHub
---------------------------------------------

.. code-block:: bash

   $> esgprep fetch-ini -v
   YYYY/MM/DD HH:MM:SS INFO https://github.com/ESGF/config/blob/master/publisher-configs/ini/esg.projectA.ini --> /esg/config/esgcet/esg.projectA.ini
   YYYY/MM/DD HH:MM:SS INFO https://github.com/ESGF/config/blob/master/publisher-configs/ini/esg.projectB.ini --> /esg/config/esgcet/esg.projectB.ini
   Overwrite existing "esg.projectC.ini"? [y/N] y
   YYYY/MM/DD HH:MM:SS INFO https://github.com/ESGF/config/blob/master/publisher-configs/ini/esg.projectC.ini --> /esg/config/esgcet/esg.projectC.ini
   Overwrite existing "esg.ini"? [y/N] N
   YYYY/MM/DD HH:MM:SS INFO https://github.com/ESGF/config/blob/master/publisher-configs/ini/esg.ini --> /esg/config/esgcet/esg.ini
   YYYY/MM/DD HH:MM:SS INFO "thredds_dataset_roots" in "/esg/config/esgcet/esg.ini" successfully updated
   YYYY/MM/DD HH:MM:SS INFO "project_options" in "/esg/config/esgcet/esg.ini" successfully updated
   YYYY/MM/DD HH:MM:SS INFO "thredds_aggregation/file_services" in "/esg/config/esgcet/esg.ini" successfully formatted

``esgprep drs``
***************

.. note:: **Coming soon !**

``esgprep check-vocab``
***********************

Check the facet options
-----------------------

The datasets IDs can be found by scanning the filesystem:

.. code-block:: bash

   $> esgprep check-vocab --directory /path/to/scan --project <project_id>
   YYYY/MM/DD HH:MM:SS INFO Collecting values from INI file(s) for "product" facet...
   YYYY/MM/DD HH:MM:SS INFO Collecting values from INI file(s) for "realm" facet...
   [...]
   YYYY/MM/DD HH:MM:SS INFO Harvesting facets values from DRS tree...
   YYYY/MM/DD HH:MM:SS INFO Result: ALL USED VALUES ARE PROPERLY DECLARED.

Or dataset IDs they can be supplied in a file:

.. code-block:: bash

   $> esgprep check-vocab --dataset-list path_of_text_file --project <project_id>
   YYYY/MM/DD HH:MM:SS INFO Collecting values from INI file(s) for "product" facet...
   YYYY/MM/DD HH:MM:SS INFO Collecting values from INI file(s) for "realm" facet...
   [...]
   YYYY/MM/DD HH:MM:SS INFO Harvesting facets values from DRS tree...
   YYYY/MM/DD HH:MM:SS INFO Result: ALL USED VALUES ARE PROPERLY DECLARED.

In this case, the file must contain one dataset ID per line. This can be
without version, or with a version suffix of the form ``.v<version>`` 
or ``#<version>`` which is ignored.

If a used option is missing:

.. code-block:: bash

   $> esgprep check-vocab --directory /path/to/scan --project <project_id>
   YYYY/MM/DD HH:MM:SS INFO Collecting values from INI file(s) for "product" facet...
   YYYY/MM/DD HH:MM:SS INFO Collecting values from INI file(s) for "realm" facet...
   [...]
   YYYY/MM/DD HH:MM:SS INFO Harvesting facets values from DRS tree...
   YYYY/MM/DD HH:MM:SS INFO institute facet - UNDECLARED values: INPE
   YYYY/MM/DD HH:MM:SS INFO institute facet - UPDATED values to declare: ICHEC, CCCma, LASG, INPE, BNU, BCC, MIROC, CNRM-CERFACS, NASA-GMAO, MOHC, CAWCR, IPSL, CSIRO, MRI, CMCC, FIO, INM, NASA-GISS, NSF-DOE-NCAR, NOAA-GFDL, DOE-COLA-CMMAP-GMU, NCAR, NCC, NIMR-KMA, NICAM
   YYYY/MM/DD HH:MM:SS INFO ensemble facet - UNDECLARED values: r5i1p1
   YYYY/MM/DD HH:MM:SS INFO ensemble facet - UPDATED values to declare: r1i1p1, r5i1p1, r0i0p0
   YYYY/MM/DD HH:MM:SS ERROR Result: THERE WERE UNDECLARED VALUES USED.

Verbose output:

.. code-block:: bash

   $> esgprep check-vocab --directory /path/to/scan --project <project_id> -v
   YYYY/MM/DD HH:MM:SS INFO Collecting values from INI file(s) for "product" facet...
   YYYY/MM/DD HH:MM:SS INFO Collecting values from INI file(s) for "realm" facet...
   [...]
   YYYY/MM/DD HH:MM:SS INFO Harvesting facets values from DRS tree...
   YYYY/MM/DD HH:MM:SS INFO product facet - Declared values: output2, output1
   YYYY/MM/DD HH:MM:SS INFO product facet - Used values: output1
   YYYY/MM/DD HH:MM:SS INFO product facet - Unused values: output2
   YYYY/MM/DD HH:MM:SS INFO realm facet - Declared values: seaIce, land, landIce, atmosChem, ocean, atmos, aerosol, ocnBgchem
   YYYY/MM/DD HH:MM:SS INFO realm facet - Used values: seaIce, land, landIce, ocean, atmos, ocnBgchem
   YYYY/MM/DD HH:MM:SS INFO realm facet - Unused values: atmosChem, aerosol
   YYYY/MM/DD HH:MM:SS INFO Result: ALL USED VALUES ARE PROPERLY DECLARED.

``esgprep mapfile``
*******************

.. note:: All the following examples can be combined safely.

Default mapfile generation
--------------------------

.. note:: The default behavior is to pickup the latest version in the DRS.

.. warning:: This required a date version format (e.g., v20151023).

.. code-block:: bash

   $> esgprep mapfile /path/to/scan --project <project_id> -v
   YYYY/MM/DD HH:MM:SS INFO ==> Scan started
   YYYY/MM/DD HH:MM:SS INFO dataset_ID1.vYYYYMMDD <-- /path/to/scan/.../vYYYYMMDD/.../file1.nc
   YYYY/MM/DD HH:MM:SS INFO dataset_ID2.vYYYYMMDD <-- /path/to/scan/.../vYYYYMMDD/.../file2.nc
   YYYY/MM/DD HH:MM:SS INFO dataset_ID3.vYYYYMMDD <-- /path/to/scan/.../vYYYYMMDD/.../file3.nc
   YYYY/MM/DD HH:MM:SS INFO ==> Scan completed (3 files)

   $> cat dataset_ID.v*.map
   dataset_ID1.vYYYYMMDD
   dataset_ID1.vYYYYMMDD | /path/to/scan/.../vYYYYMMDD/.../file1.nc | size1 | mod_time1 | checksum1 | checksum_type=SHA256

   dataset_ID2.vYYYYMMDD.map
   dataset_ID2.vYYYYMMDD | /path/to/scan/.../vYYYYMMDD/.../file2.nc | size2 | mod_time2 | checksum2 | checksum_type=SHA256

   dataset_ID3.vYYYYMMDD.map
   dataset_ID3.vYYYYMMDD | /path/to/scan/.../vYYYYMMDD/.../file3.nc | size3 | mod_time3 | checksum3 | checksum_type=SHA256

Mapfile without files checksums
-------------------------------

.. note:: The ``-v`` raises the tracebacks of thread-processes (default is the "silent" mode).

.. code-block:: bash

   $> esgprep mapfile /path/to/scan --project <project_id> --no-checksum
   YYYY/MM/DD HH:MM:SS INFO ==> Scan started
   YYYY/MM/DD HH:MM:SS INFO dataset_ID1.vYYYYMMDD <-- /path/to/scan/.../vYYYYMMDD/.../file1.nc
   YYYY/MM/DD HH:MM:SS INFO dataset_ID2.vYYYYMMDD <-- /path/to/scan/.../vYYYYMMDD/.../file2.nc
   YYYY/MM/DD HH:MM:SS INFO dataset_ID3.vYYYYMMDD <-- /path/to/scan/.../vYYYYMMDD/.../file3.nc
   YYYY/MM/DD HH:MM:SS INFO ==> Scan completed (3 files)

   $> cat dataset_ID.v*.map
   dataset_ID1.vYYYYMMDD.map
   dataset_ID1.vYYYYMMDD | /path/to/scan/.../vYYYYMMDD/.../file1.nc | size1 | mod_time1

   dataset_ID2.vYYYYMMDD.map
   dataset_ID2.vYYYYMMDD | /path/to/scan/.../vYYYYMMDD/.../file2.nc | size2 | mod_time2

   dataset_ID3.vYYYYMMDD.map
   dataset_ID3.vYYYYMMDD | /path/to/scan/.../vYYYYMMDD/.../file3.nc | size3 | mod_time3

Mapfile without DRS versions
----------------------------

.. code-block:: bash

   $> esgprep mapfile /path/to/scan --project <project_id> --no-version
   YYYY/MM/DD HH:MM:SS INFO ==> Scan started
   YYYY/MM/DD HH:MM:SS INFO dataset_ID1.vYYYYMMDD <-- /path/to/scan/.../vYYYYMMDD/.../file1.nc
   YYYY/MM/DD HH:MM:SS INFO dataset_ID2.vYYYYMMDD <-- /path/to/scan/.../vYYYYMMDD/.../file2.nc
   YYYY/MM/DD HH:MM:SS INFO dataset_ID3.vYYYYMMDD <-- /path/to/scan/.../vYYYYMMDD/.../file3.nc
   YYYY/MM/DD HH:MM:SS INFO ==> Scan completed (3 files)

   $> cat dataset_ID.v*.map
   dataset_ID1.vYYYYMMDD.map
   dataset_ID1 | /path/to/scan/.../vYYYYMMDD/.../file1.nc | size1 | mod_time1 | checksum1 | checksum_type=SHA256

   dataset_ID2.vYYYYMMDD.map
   dataset_ID2 | /path/to/scan/.../vYYYYMMDD/.../file2.nc | size2 | mod_time2 | checksum2 | checksum_type=SHA256

   dataset_ID3.vYYYYMMDD.map
   dataset_ID3 | /path/to/scan/.../vYYYYMMDD/.../file3.nc | size3 | mod_time3 | checksum3 | checksum_type=SHA256

Mapfile name using tokens
-------------------------

.. warning:: If ``{dataset_id}`` is not present in the mapfile name, then all datasets will be written to a single
   mapfile, overriding the default behavior of producing ONE mapfile PER dataset.

.. note:: The extension ``.map`` is added in any case.

.. code-block:: bash

   $> esgprep mapfile /path/to/scan --project <project_id> --mapfile {dataset_id}.{job_id}
   YYYY/MM/DD HH:MM:SS INFO ==> Scan started
   YYYY/MM/DD HH:MM:SS INFO dataset_ID1.job_id <-- /path/to/scan/.../vYYYYMMDD/.../file1.nc
   YYYY/MM/DD HH:MM:SS INFO dataset_ID2.job_id <-- /path/to/scan/.../vYYYYMMDD/.../file2.nc
   YYYY/MM/DD HH:MM:SS INFO dataset_ID3.job_id <-- /path/to/scan/.../vYYYYMMDD/.../file3.nc
   YYYY/MM/DD HH:MM:SS INFO ==> Scan completed (3 files)

   $> cat dataset_ID*.job_id.map
   dataset_ID1.job_id.map
   dataset_ID1.vYYYYMMDD | /path/to/scan/.../vYYYYMMDD/.../file1.nc | size1 | mod_time1 | checksum1 | checksum_type=SHA256

   dataset_ID2.job_id.map
   dataset_ID2.vYYYYMMDD | /path/to/scan/.../vYYYYMMDD/.../file2.nc | size2 | mod_time2 | checksum2 | checksum_type=SHA256

   dataset_ID3.job_id.map
   dataset_ID3.vYYYYMMDD | /path/to/scan/.../vYYYYMMDD/.../file3.nc | size3 | mod_time3 | checksum3 | checksum_type=SHA256

   $> esgprep mapfile /path/to/scan --project <project_id> --mapfile {date}
   YYYY/MM/DD HH:MM:SS INFO ==> Scan started
   YYYY/MM/DD HH:MM:SS INFO <date> <-- /path/to/scan/.../vYYYYMMDD/.../file1.nc
   YYYY/MM/DD HH:MM:SS INFO <date> <-- /path/to/scan/.../vYYYYMMDD/.../file2.nc
   YYYY/MM/DD HH:MM:SS INFO <date> <-- /path/to/scan/.../vYYYYMMDD/.../file3.nc
   YYYY/MM/DD HH:MM:SS INFO ==> Scan completed (3 files)

   $> cat <date>.map
   dataset_ID1.vYYYYMMDD | /path/to/scan/.../vYYYYMMDD/.../file1.nc | size1 | mod_time1 | checksum1 | checksum_type=SHA256
   dataset_ID2.vYYYYMMDD | /path/to/scan/.../vYYYYMMDD/.../file2.nc | size2 | mod_time2 | checksum2 | checksum_type=SHA256
   dataset_ID3.vYYYYMMDD | /path/to/scan/.../vYYYYMMDD/.../file3.nc | size3 | mod_time3 | checksum3 | checksum_type=SHA256

To an output directory
----------------------

.. code-block:: bash

   $> esgprep mapfile /path/to/scan --project <project_id> --outdir /path/to/mapfiles/
   YYYY/MM/DD HH:MM:SS INFO ==> Scan started
   YYYY/MM/DD HH:MM:SS INFO dataset_ID1.vYYYYMMDD <-- /path/to/scan/.../vYYYYMMDD/.../file1.nc
   YYYY/MM/DD HH:MM:SS INFO dataset_ID2.vYYYYMMDD <-- /path/to/scan/.../vYYYYMMDD/.../file2.nc
   YYYY/MM/DD HH:MM:SS INFO dataset_ID3.vYYYYMMDD <-- /path/to/scan/.../vYYYYMMDD/.../file3.nc
   YYYY/MM/DD HH:MM:SS INFO ==> Scan completed (3 files)

   $> cat /path/to/mapfiles/dataset_ID*.v*.map
   dataset_ID1.vYYYYMMDD.map
   dataset_ID1.vYYYYMMDD | /path/to/scan/.../vYYYYMMDD/.../file1.nc | size1 | mod_time1 | checksum1 | checksum_type=SHA256

   dataset_ID2.vYYYYMMDD.map
   dataset_ID2.vYYYYMMDD | /path/to/scan/.../vYYYYMMDD/.../file2.nc | size2 | mod_time2 | checksum2 | checksum_type=SHA256

   dataset_ID3.vYYYYMMDD.map
   dataset_ID3.vYYYYMMDD | /path/to/scan/.../vYYYYMMDD/.../file3.nc | size3 | mod_time3 | checksum3 | checksum_type=SHA256

Organize your mapfiles
----------------------

.. note:: A ``mapfile_drs`` attribute can be added into the corresponding project section of the configuration files.
   In the same way as the ``directory_format`` it defines a tree depending on the facets. Each mapfile is then
   written into the corresponding output directory.

.. warning:: The ``mapfile_drs`` directory structure is added to the root output directory submitted by the flag
   ``--outdir``.

.. code-block:: bash

   $> esgprep mapfile /path/to/scan --project <project_id> --outdir /path/to/mapfiles/
   YYYY/MM/DD HH:MM:SS INFO ==> Scan started
   YYYY/MM/DD HH:MM:SS INFO dataset_ID1.vYYYYMMDD <-- /path/to/scan/.../vYYYYMMDD/.../file1.nc
   YYYY/MM/DD HH:MM:SS INFO dataset_ID2.vYYYYMMDD <-- /path/to/scan/.../vYYYYMMDD/.../file2.nc
   YYYY/MM/DD HH:MM:SS INFO dataset_ID3.vYYYYMMDD <-- /path/to/scan/.../vYYYYMMDD/.../file3.nc
   YYYY/MM/DD HH:MM:SS INFO ==> Scan completed (3 files)

   $> cat /path/to/mapfiles/facet1/facet2/facet3/dataset_ID1.vYYYYMMDD.map
   dataset_ID1.vYYYYMMDD | /path/to/scan/.../vYYYYMMDD/.../file1.nc | size1 | mod_time1 | checksum1 | checksum_type=SHA256

   $> cat /path/to/mapfiles/facet1/facet2/facet3/dataset_ID2.vYYYYMMDD.map
   dataset_ID2.vYYYYMMDD | /path/to/scan/.../vYYYYMMDD/.../file2.nc | size2 | mod_time2 | checksum2 | checksum_type=SHA256

   $> cat /path/to/mapfiles/facet1/facet2/facet3/dataset_ID3.vYYYYMMDD.map
   dataset_ID3.vYYYYMMDD | /path/to/scan/.../vYYYYMMDD/.../file3.nc | size3 | mod_time3 | checksum3 | checksum_type=SHA256


Walking through *latest* directories only
-----------------------------------------

.. warning:: If the version is directly specified in positional argument, the version number from supplied directory
   is used.

.. code-block:: bash

   $> esgprep mapfile /path/to/scan --project <project_id> --latest-symlink
   YYYY/MM/DD HH:MM:SS INFO ==> Scan started
   YYYY/MM/DD HH:MM:SS INFO dataset_ID1.latest <-- /path/to/scan/.../latest/.../file1.nc
   YYYY/MM/DD HH:MM:SS INFO dataset_ID2.latest <-- /path/to/scan/.../latest/.../file2.nc
   YYYY/MM/DD HH:MM:SS INFO dataset_ID3.latest <-- /path/to/scan/.../latest/.../file3.nc
   YYYY/MM/DD HH:MM:SS INFO ==> Scan completed (3 files)

   $> cat dataset_ID*.latest.map
   dataset_ID1.latest.map
   dataset_ID1.vYYYYMMDD | /path/to/scan/.../latest/.../file1.nc | size1 | mod_time1 | checksum1 | checksum_type=SHA256

   dataset_ID2.latest.map
   dataset_ID2.vYYYYMMDD | /path/to/scan/.../latest/.../file2.nc | size2 | mod_time2 | checksum2 | checksum_type=SHA256

   dataset_ID3.latest.map
   dataset_ID3.vYYYYMMDD | /path/to/scan/.../latest/.../file3.nc | size3 | mod_time3 | checksum3 | checksum_type=SHA256

Walking through a particular version only
-----------------------------------------

.. warning:: By default ``esgprep mapfile`` pick up the latest version only.

.. warning:: If the version is directly specified in positional argument, the version number from supplied directory
   is used.

.. code-block:: bash

   $> esgprep mapfile /path/to/scan --project <project_id> --version <version>
   YYYY/MM/DD HH:MM:SS INFO ==> Scan started
   YYYY/MM/DD HH:MM:SS INFO dataset_ID1.v<version> <-- /path/to/scan/.../v<version>/.../file1.nc
   YYYY/MM/DD HH:MM:SS INFO dataset_ID2.v<version> <-- /path/to/scan/.../v<version>/.../file2.nc
   YYYY/MM/DD HH:MM:SS INFO dataset_ID3.v<version> <-- /path/to/scan/.../v<version>/.../file3.nc
   YYYY/MM/DD HH:MM:SS INFO ==> Scan completed (3 files)

   $> cat dataset_ID*.v<version>.map
   dataset_ID1.v<version>.map
   dataset_ID1.v<version> | /path/to/scan/.../v<version>/.../file1.nc | size1 | mod_time1 | checksum1 | checksum_type=SHA256

   dataset_ID2.v<version>.map
   dataset_ID2.v<version> | /path/to/scan/.../v<version>/.../file2.nc | size2 | mod_time2 | checksum2 | checksum_type=SHA256

   dataset_ID3.v<version>.map
   dataset_ID3.v<version> | /path/to/scan/.../v<version>/.../file3.nc | size3 | mod_time3 | checksum3 | checksum_type=SHA256

Walking through all versions
----------------------------

.. warning:: This disables ``--no-version``.

.. warning:: If the version is directly specified in positional argument, the version number from supplied directory
   is used.

.. code-block:: bash

   $> esgprep mapfile /path/to/scan --project <project_id> --all-versions
   YYYY/MM/DD HH:MM:SS INFO ==> Scan started
   YYYY/MM/DD HH:MM:SS INFO dataset_ID.v1 <-- /path/to/scan/.../v1/.../file1.nc
   YYYY/MM/DD HH:MM:SS INFO dataset_ID.v1 <-- /path/to/scan/.../v1/.../file2.nc
   YYYY/MM/DD HH:MM:SS INFO dataset_ID.v2 <-- /path/to/scan/.../v2/.../file1.nc
   YYYY/MM/DD HH:MM:SS INFO ==> Scan completed (3 files)

   $> cat dataset_ID*.v\*.map
   dataset_ID.v1.map
   dataset_ID.v1 | /path/to/scan/.../v1/.../file1.nc | size1 | mod_time1 | checksum1 | checksum_type=SHA256
   dataset_ID.v1 | /path/to/scan/.../v1/.../file2.nc | size2 | mod_time2 | checksum2 | checksum_type=SHA256

   dataset_ID.v2.map
   dataset_ID.v2 | /path/to/scan/.../v2/.../file3.nc | size3 | mod_time3 | checksum3 | checksum_type=SHA256

Add technical notes
-------------------

.. code-block:: bash

   $> esgprep mapfile /path/to/scan --project <project_id> --tech-notes-url <url> --tech-notes-title <title>
   YYYY/MM/DD HH:MM:SS INFO ==> Scan started
   YYYY/MM/DD HH:MM:SS INFO dataset_ID.vYYYYMMDD <-- /path/to/scan/.../vYYYYMMDD/.../file1.nc
   YYYY/MM/DD HH:MM:SS INFO dataset_ID.vYYYYMMDD <-- /path/to/scan/.../vYYYYMMDD/.../file2.nc
   YYYY/MM/DD HH:MM:SS INFO dataset_ID.vYYYYMMDD <-- /path/to/scan/.../vYYYYMMDD/.../file1.nc
   YYYY/MM/DD HH:MM:SS INFO ==> Scan completed (3 files)

   $> cat dataset_ID*.vYYYYMMDD.map
   dataset_ID.vYYYYMMDD | /path/to/scan/.../vYYYYMMDD/.../file1.nc | size1 | mod_time1 | checksum1 | checksum_type=SHA256 | dataset_tech_notes=<url> | dataset_tech_notes_title=<title>
   dataset_ID.vYYYYMMDD | /path/to/scan/.../vYYYYMMDD/.../file2.nc | size2 | mod_time2 | checksum2 | checksum_type=SHA256 | dataset_tech_notes=<url> | dataset_tech_notes_title=<title>
   dataset_ID.vYYYYMMDD | /path/to/scan/.../vYYYYMMDD/.../file3.nc | size3 | mod_time3 | checksum3 | checksum_type=SHA256 | dataset_tech_notes=<url> | dataset_tech_notes_title=<title>

Change the number of threads
----------------------------

.. note:: ``--max-threads`` set to one corresponds to a sequential file processing.

.. code-block:: bash

   $> esgprep mapfile /path/to/scan --project <project_id> --max-threads <integer>

Overwrite the dataset identifier
--------------------------------

.. note:: All files will belong to the specified dataset, regardless of the DRS.

.. code-block:: bash

   $> esgprep mapfile /path/to/scan --project <project_id> --dataset <dataset_ID_test>
   YYYY/MM/DD HH:MM:SS INFO ==> Scan started
   YYYY/MM/DD HH:MM:SS INFO dataset_ID_test <-- /path/to/scan/.../vYYYYMMDD/.../file1.nc
   YYYY/MM/DD HH:MM:SS INFO dataset_ID_test <-- /path/to/scan/.../vYYYYMMDD/.../file2.nc
   YYYY/MM/DD HH:MM:SS INFO dataset_ID_test <-- /path/to/scan/.../vYYYYMMDD/.../file1.nc
   YYYY/MM/DD HH:MM:SS INFO ==> Scan completed (3 files)

   $> cat dataset_ID_test.map
   dataset_ID_test | /path/to/scan/.../vYYYYMMDD/.../file1.nc | size1 | mod_time1 | checksum1 | checksum_type=SHA256
   dataset_ID_test | /path/to/scan/.../vYYYYMMDD/.../file2.nc | size2 | mod_time2 | checksum2 | checksum_type=SHA256
   dataset_ID_test | /path/to/scan/.../vYYYYMMDD/.../file3.nc | size3 | mod_time3 | checksum3 | checksum_type=SHA256
