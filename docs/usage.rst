.. _usage:

*****
Usage
*****

Here is the command-line help:

.. code-block:: bash

   $> esg_mapfiles -h
   usage: esg_mapfiles.py [-h] -p [{cmip5,cordex}] [-c [CONFIG]] [-o [OUTDIR]]
                         [-l [LOGDIR]] [-m [MAPFILE]] [-d] [-L] [-C] [-k] [-v]
                         [-V]
                         directory [directory ...]

   Build ESG-F mapfiles upon local ESG-F datanode bypassing esgscan_directory
   command-line.

   positional arguments:
     directory             One or more directories to recursively scan. Unix wildcards are allowed.

   optional arguments:
     -h, --help            Show this help message and exit.
                           
     -p [{cmip5,cordex}], --project [{cmip5,cordex}]
                           Required project to build mapfiles among:
                           - cmip5
                           - cordex
                           
     -c [CONFIG], --config [CONFIG]
                           Path of configuration INI file
                           (default is ~/anaconda/lib/python2.7/site-packages/esgmapfiles/config.ini).
                           
     -o [OUTDIR], --outdir [OUTDIR]
                           Mapfile(s) output directory
                           (default is working directory).
                           
     -l [LOGDIR], --logdir [LOGDIR]
                           Logfile directory (default is working directory).
                           If not, standard output is used.
                           
     -m [MAPFILE], --mapfile [MAPFILE]
                           Output mapfile name. Only used without --per-dataset option
                           (default is 'mapfile.txt').
                           
     -d, --per-dataset     Produces ONE mapfile PER dataset.
                           
     -L, --latest          Generates mapfiles with latest versions only.
                           
     -C, --checksum        Includes file checksums into mapfiles.
                           
     -k, --keep-going      Keep going if some files cannot be processed.
                           
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

.. code-block:: bash

   $> esg_mapfiles /path/to/scan -p cmip5 -C
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
   dataset_ID1#YYYYMMDD <-- /path/to/scan/.../vYYYYMMDD/.../file1.nc
   dataset_ID2#YYYYMMDD <-- /path/to/scan/.../vYYYYMMDD/.../file2.nc
   dataset_ID3#YYYYMMDD <-- /path/to/scan/.../vYYYYMMDD/.../file3.nc
   ==> Scan completed (3 files)

   $> cat dataset_ID*
   dataset_ID1#YYYYMMDD
   dataset_ID1#YYYYMMDD | /path/to/scan/.../vYYYYMMDD/.../file1.nc | size1 | mod_time1

   dataset_ID2#YYYYMMDD
   dataset_ID2#YYYYMMDD | /path/to/scan/.../vYYYYMMDD/.../file2.nc | size2 | mod_time2

   dataset_ID3#YYYYMMDD
   dataset_ID3#YYYYMMDD | /path/to/scan/.../vYYYYMMDD/.../file3.nc | size3 | mod_time3

.. note:: The mapfile name corresponds to the dataset ID.

To specify the configuration file:

.. code-block:: bash

   $> esg_mapfiles /path/to/scan -p cmip5 -c /path/to/configfile/config.ini

To skip files that cannot be processed:

.. code-block:: bash

   $> esg_mapfiles /path/to/scan -p cmip5
   ==> Scan started
   mapfile.txt <-- /path/to/scan/.../vYYYYMMDD/.../file1.nc
   Traceback (most recent call last):
     File "./esg_mapfiles.py", line 411, in <module>
       main()
     File "./esg_mapfiles.py", line 405, in main
       _directory_process(ctx)
     File "./esg_mapfiles.py", line 380, in _directory_process
       outmaps = pool.map(_wrapper, _yield_inputs(ctx))
     File "/home/glipsl/anaconda/lib/python2.7/multiprocessing/pool.py", line 251, in map
       return self.map_async(func, iterable, chunksize).get()
     File "/home/glipsl/anaconda/lib/python2.7/multiprocessing/pool.py", line 558, in get
       raise self._value
   __main__._Exception
   Matching failed for file2.pdf

   $> esg_mapfiles /path/to/scan -p cmip5 -k
   ==> Scan started
   mapfile.txt <-- /path/to/scan/.../vYYYYMMDD/.../file1.nc
   mapfile.txt <-- /path/to/scan/.../vYYYYMMDD/.../file3.nc
   Delete temporary directory /tmp/tmpzspsLH
   ==> Scan completed (2 files)


To use a logfile (the logfile directory is optionnal):

.. code-block:: bash

   $> esg_mapfiles /path/to/scan -p cmip5 -l /path/to/logfile -v

   $> cat /path/to/logfile/esg_mapfiles-YYYYMMDD-HHMMSS-PID.log
   YYYY/MM/DD HH:MM:SS INFO ==> Scan started
   YYYY/MM/DD HH:MM:SS INFO mapfile.txt <-- /path/to/scan/.../vYYYYMMDD/.../file1.nc
   YYYY/MM/DD HH:MM:SS INFO mapfile.txt <-- /path/to/scan/.../vYYYYMMDD/.../file2.nc
   YYYY/MM/DD HH:MM:SS INFO mapfile.txt <-- /path/to/scan/.../vYYYYMMDD/.../file3.nc
   YYYY/MM/DD HH:MM:SS WARNING Delete temporary directory /tmp/tmpzspsLH
   YYYY/MM/DD HH:MM:SS INFO ==> Scan completed (3 files)

To generate a mapfile specifying filename and output directory (the ``--per-dataset`` option takes priority over ``--mapfile`` option):

.. code-block:: bash

   $> esg_mapfiles /path/to/scan -p cmip5 -o /path/to/mapfile -m mymapfile.txt
   ==> Scan started
   mymapfile.txt <-- /path/to/scan/.../vYYYYMMDD/.../file1.nc
   mymapfile.txt <-- /path/to/scan/.../vYYYYMMDD/.../file2.nc
   mymapfile.txt <-- /path/to/scan/.../vYYYYMMDD/.../file3.nc
   ==> Scan completed (3 files)

   $> cat /path/to/mapfile/mymapfile.txt
   dataset_ID1#YYYYMMDD | /path/to/scan/.../vYYYYMMDD/.../file1.nc | size1 | mod_time1
   dataset_ID2#YYYYMMDD | /path/to/scan/.../vYYYYMMDD/.../file2.nc | size2 | mod_time2
   dataset_ID3#YYYYMMDD | /path/to/scan/.../vYYYYMMDD/.../file3.nc | size3 | mod_time3

To generate a mapfile walking through *latest* directories only. The versions pointed by the latest symlinks are kept within the dataset ID but not in the mapfile name:

.. code-block:: bash

   $> esg_mapfiles /path/to/scan -p cmip5 -L -d
   ==> Scan started
   dataset_ID1#YYYYMMDD <-- /path/to/scan/.../latest/.../file1.nc
   dataset_ID2#YYYYMMDD <-- /path/to/scan/.../latest/.../file2.nc
   dataset_ID3#YYYYMMDD <-- /path/to/scan/.../latest/.../file3.nc
   ==> Scan completed (3 files)

   $> cat dataset_ID*
   dataset_ID1#latest
   dataset_ID1#YYYYMMDD | /path/to/scan/.../latest/.../file1.nc | size1 | mod_time1

   dataset_ID2#latest
   dataset_ID2#YYYYMMDD | /path/to/scan/.../latest/.../file2.nc | size2 | mod_time2

   dataset_ID3#latest
   dataset_ID3#YYYYMMDD | /path/to/scan/.../latest/.../file3.nc | size3 | mod_time3

.. note:: All the previous examples can be combined safely.
