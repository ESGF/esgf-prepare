.. _usage:

*****
Usage
*****

Here is the command-line help:

.. code-block:: bash

   $> esg_mapfiles -h
   usage: esgmapfiles.py [-h] -p PROJECT [-c CONFIG] [-o OUTDIR] [-l [LOGDIR]]
                         [-m MAPFILE] [-d] [-L] [-w] [-C] [-k] [-v] [-V]
                         directory [directory ...]

   Build ESGF mapfiles upon local ESGF datanode bypassing esgscan_directory
   command-line.

   positional arguments:
     directory             One or more directories to recursively scan. Unix wildcards are allowed.

   optional arguments:
     -h, --help            Show this help message and exit.
                           
     -p PROJECT, --project PROJECT
                           Required project name corresponding to a section of the configuration file.
                           
     -c CONFIG, --config CONFIG
                           Path of configuration INI file
                           (default is ~/anaconda/lib/python2.7/site-packages/esgmapfiles/config.ini).
                          
     -o OUTDIR, --outdir OUTDIR
                           Mapfile(s) output directory
                           (default is working directory).
                           
     -l [LOGDIR], --logdir [LOGDIR]
                           Logfile directory (default is working directory).
                           If not, standard output is used.
                           
     -m MAPFILE, --mapfile MAPFILE
                           Output mapfile name. Only used without --per-dataset option
                           (default is 'mapfile.txt').
                           
     -d, --per-dataset     Produces ONE mapfile PER dataset. It takes priority over --mapfile.
                           
     -L, --latest          Generates mapfiles with latest versions only.
                           
     -w, --with-version    Includes DRS version into dataset ID (ESGF 2.x compatibility).
                           
     -C, --checksum        Includes file checksums into mapfiles (default is a SHA256 checksum).
                           
     -v, --verbose         Verbose mode.
                           
     -V, --Version         Program version.

   Developed by Levavasseur, G. (CNRS/IPSL)

Tutorials
---------

To generate a mapfile with verbosity using default parameters:

.. code-block:: bash

   $> esg_mapfiles /path/to/scan -p cmip5 -v
   ==> Scan started
   mapfile.txt <-- /path/to/scan/.../vYYYYMMDD/.../file1.nc
   mapfile.txt <-- /path/to/scan/.../vYYYYMMDD/.../file2.nc
   mapfile.txt <-- /path/to/scan/.../vYYYYMMDD/.../file3.nc
   Delete temporary directory /tmp/tmpzspsLH
   ==> Scan completed (3 files)

   $> cat mapfile.txt
   dataset_ID1 | /path/to/scan/.../vYYYYMMDD/.../file1.nc | size1 | mod_time1
   dataset_ID2 | /path/to/scan/.../vYYYYMMDD/.../file2.nc | size2 | mod_time2
   dataset_ID3 | /path/to/scan/.../vYYYYMMDD/.../file3.nc | size3 | mod_time3

To generate a mapfile with files checksums:

.. note:: The ``-v/--verbose`` raises the tracebacks of thread-processes (default is the "silent" mode).

.. warning:: The ``-p/--project`` is case-sensitive.

.. code-block:: bash

   $> esg_mapfiles /path/to/scan -p cmip5 -C
   ==> Scan started
   mapfile.txt <-- /path/to/scan/.../vYYYYMMDD/.../file1.nc
   mapfile.txt <-- /path/to/scan/.../vYYYYMMDD/.../file2.nc
   mapfile.txt <-- /path/to/scan/.../vYYYYMMDD/.../file3.nc
   ==> Scan completed (3 files)

   $> cat mapfile.txt
   dataset_ID1 | /path/to/scan/.../vYYYYMMDD/.../file1.nc | size1 | mod_time1 | checksum1 | checksum_type=MD5
   dataset_ID2 | /path/to/scan/.../vYYYYMMDD/.../file2.nc | size2 | mod_time2 | checksum2 | checksum_type=MD5
   dataset_ID3 | /path/to/scan/.../vYYYYMMDD/.../file3.nc | size3 | mod_time3 | checksum3 | checksum_type=MD5

To generate a mapfile with DRS versions:

.. code-block:: bash

   $> esg_mapfiles /path/to/scan -p cmip5 -w
   ==> Scan started
   mapfile.txt <-- /path/to/scan/.../vYYYYMMDD/.../file1.nc
   mapfile.txt <-- /path/to/scan/.../vYYYYMMDD/.../file2.nc
   mapfile.txt <-- /path/to/scan/.../vYYYYMMDD/.../file3.nc
   ==> Scan completed (3 files)

   $> cat mapfile.txt
   dataset_ID1#YYYYMMDD | /path/to/scan/.../vYYYYMMDD/.../file1.nc | size1 | mod_time1 | checksum1 | checksum_type=MD5
   dataset_ID2#YYYYMMDD | /path/to/scan/.../vYYYYMMDD/.../file2.nc | size2 | mod_time2 | checksum2 | checksum_type=MD5
   dataset_ID3#YYYYMMDD | /path/to/scan/.../vYYYYMMDD/.../file3.nc | size3 | mod_time3 | checksum3 | checksum_type=MD5

To generate one mapfile per dataset:

.. code-block:: bash

   $> esg_mapfiles /path/to/scan -p cmip5 -d
   ==> Scan started
   dataset_ID1.vYYYYMMDD <-- /path/to/scan/.../vYYYYMMDD/.../file1.nc
   dataset_ID2.vYYYYMMDD <-- /path/to/scan/.../vYYYYMMDD/.../file2.nc
   dataset_ID3.vYYYYMMDD <-- /path/to/scan/.../vYYYYMMDD/.../file3.nc
   ==> Scan completed (3 files)

   $> cat dataset_ID.v*
   dataset_ID1.vYYYYMMDD
   dataset_ID1 | /path/to/scan/.../vYYYYMMDD/.../file1.nc | size1 | mod_time1

   dataset_ID2.vYYYYMMDD
   dataset_ID2 | /path/to/scan/.../vYYYYMMDD/.../file2.nc | size2 | mod_time2

   dataset_ID3.vYYYYMMDD
   dataset_ID3 | /path/to/scan/.../vYYYYMMDD/.../file3.nc | size3 | mod_time3

.. note:: The mapfile name corresponds to the dataset ID with the DRS version as suffix.

To specify the configuration file:

.. code-block:: bash

   $> esg_mapfiles /path/to/scan -p cmip5 -c /path/to/configfile/config.ini

To use a logfile (the logfile directory is optionnal):

.. code-block:: bash

   $> esg_mapfiles /path/to/scan -p cmip5 -l /path/to/logfile -v

   $> cat /path/to/logfile/esgmapfiles-YYYYMMDD-HHMMSS-PID.log
   YYYY/MM/DD HH:MM:SS INFO ==> Scan started
   YYYY/MM/DD HH:MM:SS INFO mapfile.txt <-- /path/to/scan/.../vYYYYMMDD/.../file1.nc
   YYYY/MM/DD HH:MM:SS INFO mapfile.txt <-- /path/to/scan/.../vYYYYMMDD/.../file2.nc
   YYYY/MM/DD HH:MM:SS INFO mapfile.txt <-- /path/to/scan/.../vYYYYMMDD/.../file3.nc
   YYYY/MM/DD HH:MM:SS WARNING Delete temporary directory /tmp/tmpzspsLH
   YYYY/MM/DD HH:MM:SS INFO ==> Scan completed (3 files)

To generate a mapfile specifying filename and output directory:

.. code-block:: bash

   $> esg_mapfiles /path/to/scan -p cmip5 -o /path/to/mapfile -m mymapfile.txt
   ==> Scan started
   mymapfile.txt <-- /path/to/scan/.../vYYYYMMDD/.../file1.nc
   mymapfile.txt <-- /path/to/scan/.../vYYYYMMDD/.../file2.nc
   mymapfile.txt <-- /path/to/scan/.../vYYYYMMDD/.../file3.nc
   ==> Scan completed (3 files)

   $> cat /path/to/mapfile/mymapfile.txt
   dataset_ID1 | /path/to/scan/.../vYYYYMMDD/.../file1.nc | size1 | mod_time1
   dataset_ID2 | /path/to/scan/.../vYYYYMMDD/.../file2.nc | size2 | mod_time2
   dataset_ID3 | /path/to/scan/.../vYYYYMMDD/.../file3.nc | size3 | mod_time3

.. warning:: The ``--per-dataset`` option takes priority over ``--mapfile`` option.

To generate a mapfile walking through *latest* directories only:

.. code-block:: bash

   $> esg_mapfiles /path/to/scan -p cmip5 -L -d -w
   ==> Scan started
   dataset_ID1.latest <-- /path/to/scan/.../latest/.../file1.nc
   dataset_ID2.latest <-- /path/to/scan/.../latest/.../file2.nc
   dataset_ID3.latest <-- /path/to/scan/.../latest/.../file3.nc
   ==> Scan completed (3 files)

   $> cat dataset_ID*
   dataset_ID1.latest
   dataset_ID1#YYYYMMDD | /path/to/scan/.../latest/.../file1.nc | size1 | mod_time1

   dataset_ID2.latest
   dataset_ID2#YYYYMMDD | /path/to/scan/.../latest/.../file2.nc | size2 | mod_time2

   dataset_ID3.latest
   dataset_ID3#YYYYMMDD | /path/to/scan/.../latest/.../file3.nc | size3 | mod_time3

.. warning:: If the ``--with-version`` and ``--per-dataset`` options are set the versions pointed by the latest symlinks are kept within the dataset ID but the mapfile name suffix is "latest".

.. note:: All the previous examples can be combined safely.
