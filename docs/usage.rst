.. _usage:

Usage
=====

esgscan_check_vocab 
+++++++++++++++++++

Here is the command-line help:

.. code-block:: bash

   $> esgscan_check_vocab -h
   usage: esgscan_check_vocab [-h] -p PROJECT [-c CONFIG] [-l [LOGDIR]] [-V]
                                   directory [directory ...]

   Check the configuration file to use with esgscan_directory command-line.

   positional arguments:
     directory             One or more directories to recursively scan. Unix wildcards are allowed.

   optional arguments:
     -h, --help            Show this help message and exit.
                           
     -p PROJECT, --project PROJECT
                           Required project name corresponding to a section of the configuration file.
                           
     -c CONFIG, --config CONFIG
                           Path of the configuration INI file to check
                           (default is ~/lib/python2.7/site-packages/esgmapfiles-0.5-py2.7.egg/esgmapfiles/config.ini).
                           
     -l [LOGDIR], --logdir [LOGDIR]
                           Logfile directory (default is working directory).
                           If not, standard output is used.
                           
     -V, --Version         Program version.

   Developed by Iwi, A. (BADC) and Levavasseur, G. (CNRS/IPSL)

Tutorials
---------

To check the facet options declared in your configuration file:

.. code-block:: bash

   $> esgscan_check_vocab /path/to/scan -p PROJECT -c /path/to/configfile/config.ini
   project_options - No declared values
   project_options - Used values: CMIP5
   product_options - Declared values: output2, output, output1
   product_options - Used values: output1
   product_options - Unused values: output2, output
   institute_options - Declared values: UNSW, ICHEC, CCCma, LASG-CESS, BCC, MIROC, NCEP, MOHC, IPSL, SMHI, CMCC, CSIRO-BOM, COLA-CFS, MPI-M, NCAR, NIMR-KMA, CSIRO-QCCCE, CCCMA, INPE, BNU, NOAA-NCEP, CNRM-CERFACS, NASA-GMAO, NASA-GISS, FIO, NOAA-GFDL, LASG-IAP, INM, NSF-DOE-NCAR, NICAM, NCC, MRI
   institute_options - Used values: IPSL
   institute_options - Unused values: ICHEC, CCCma, LASG-CESS, BCC, UNSW, CSIRO-BOM, MOHC, INM, CMCC, NCEP, COLA-CFS, MPI-M, NCAR, NIMR-KMA, CSIRO-QCCCE, CCCMA, INPE, BNU, NOAA-NCEP, CNRM-CERFACS, NASA-GMAO, NASA-GISS, FIO, NOAA-GFDL, NSF-DOE-NCAR, LASG-IAP, SMHI, MIROC, NICAM, NCC, MRI
   model_options - Declared values: MIROC4h, ACCESS1-0, ACCESS1-3, CESM1-CAM5-1-FV2, FGOALS-g2, MIROC5, GFDL-ESM2M, FIO-ESM, MIROC-ESM, CMCC-CMS, MPI-ESM-LR, HadCM3, INM-CM4, IPSL-CM5B-LR, GEOS-5, HadGEM2-AO, CanESM2, FGOALS-s2, MRI-AGCM3-2S, MPI-ESM-P, HadGEM2-A, MRI-ESM1, MPI-ESM-MR, CSIRO-Mk3-6-0, MRI-CGCM3, CESM1-BGC, SP-CCSM4, MRI-AGCM3.2H, inmcm4, CESM1-FASTCHEM, GISS-E2-R-CC, BNU-ESM, CNRM-CM5-2, CCSM4, GFDL-CM2p1, GFDL-ESM2G, FGOALS-gl, bcc-csm1-1-m, CanCM4, MRI-AGCM3.2S, NorESM1-M, CESM1-WACCM, IPSL-CM5A-MR, IPSL-CM5A-LR, GFDL-CM3, NICAM-09, MRI-AGCM3-2H, CNRM-CM5, GFDL-HIRAM-C180, GISS-E2-H, EC-EARTH, MIROC-ESM-CHEM, CSIRO-Mk3L-1-2, NorESM1-ME, CMCC-CM, GISS-E2-R, HadGEM2-CC, GISS-E2-H-CC, CanAM4, CMCC-CESM, CFSv2-2011, HadGEM2-ES, bcc-csm1-1, CESM1-CAM5, GFDL-HIRAM-C360
   [...]
   MIP_table_options - Used values: Amon, cfMon, Omon, fx, aero, Oyr, OImon, cfDay, Lmon, day
   MIP_table_options - Unused values: cf3hr, 3hr, cfOff, grids, 6hrLev, 6hrPlev, Aclim, LIclim, cfSites, Lclim, LImon, Oclim
   ensemble_options - No declared values
   ensemble_options - Used values: r1i1p1, r0i0p0

If a used option is missing:

.. code-block:: bash

   $> esgscan_check_vocab /path/to/scan -p PROJECT -c /path/to/configfile/config.ini
   project_options - No declared values
   project_options - Used values: CMIP5
   product_options - Declared values: output2, output
   product_options - Used values: output1
   product_options - UNDECLARED values: output1
   product_options - UPDATED values to delcare: output2, output, output1
   product_options - Unused values: output2, output
   institute_options - Declared values: UNSW, ICHEC, CCCma, LASG-CESS, BCC, MIROC, NCEP, MOHC, IPSL, SMHI, CMCC, CSIRO-BOM, COLA-CFS, MPI-M, NCAR, NIMR-KMA, CSIRO-QCCCE, CCCMA, INPE, BNU, NOAA-NCEP, CNRM-CERFACS, NASA-GMAO, NASA-GISS, FIO, NOAA-GFDL, LASG-IAP, INM, NSF-DOE-NCAR, NICAM, NCC, MRI
   institute_options - Used values: IPSL
   institute_options - Unused values: ICHEC, CCCma, LASG-CESS, BCC, UNSW, CSIRO-BOM, MOHC, INM, CMCC, NCEP, COLA-CFS, MPI-M, NCAR, NIMR-KMA, CSIRO-QCCCE, CCCMA, INPE, BNU, NOAA-NCEP, CNRM-CERFACS, NASA-GMAO, NASA-GISS, FIO, NOAA-GFDL, NSF-DOE-NCAR, LASG-IAP, SMHI, MIROC, NICAM, NCC, MRI
   model_options - Declared values: MIROC4h, ACCESS1-0, ACCESS1-3, CESM1-CAM5-1-FV2, FGOALS-g2, MIROC5, GFDL-ESM2M, FIO-ESM, MIROC-ESM, CMCC-CMS, MPI-ESM-LR, HadCM3, INM-CM4, IPSL-CM5B-LR, GEOS-5, HadGEM2-AO, CanESM2, FGOALS-s2, MRI-AGCM3-2S, MPI-ESM-P, HadGEM2-A, MRI-ESM1, MPI-ESM-MR, CSIRO-Mk3-6-0, MRI-CGCM3, CESM1-BGC, SP-CCSM4, MRI-AGCM3.2H, inmcm4, CESM1-FASTCHEM, GISS-E2-R-CC, BNU-ESM, CNRM-CM5-2, CCSM4, GFDL-CM2p1, GFDL-ESM2G, FGOALS-gl, bcc-csm1-1-m, CanCM4, MRI-AGCM3.2S, NorESM1-M, CESM1-WACCM, IPSL-CM5A-MR, IPSL-CM5A-LR, GFDL-CM3, NICAM-09, MRI-AGCM3-2H, CNRM-CM5, GFDL-HIRAM-C180, GISS-E2-H, EC-EARTH, MIROC-ESM-CHEM, CSIRO-Mk3L-1-2, NorESM1-ME, CMCC-CM, GISS-E2-R, HadGEM2-CC, GISS-E2-H-CC, CanAM4, CMCC-CESM, CFSv2-2011, HadGEM2-ES, bcc-csm1-1, CESM1-CAM5, GFDL-HIRAM-C360
   [...]
   MIP_table_options - Used values: Amon, cfMon, Omon, fx, aero, Oyr, OImon, cfDay, Lmon, day
   MIP_table_options - Unused values: cf3hr, 3hr, cfOff, grids, 6hrLev, 6hrPlev, Aclim, LIclim, cfSites, Lclim, LImon, Oclim
   ensemble_options - No declared values
   ensemble_options - Used values: r1i1p1, r0i0p0
   !!!!!!! THERE WERE UNDECLARED VALUES USED !!!!!!!!

esgscan_directory 
+++++++++++++++++

Here is the command-line help:

.. code-block:: bash

   $> esgscan_directory -h
   usage: esgmapfiles.py [-h] -p PROJECT [-c CONFIG] [-o OUTDIR] [-l [LOGDIR]]
                         [-m MAPFILE] [-d] [-L] [-w] [-C] [-v] [-V]
                         directory [directory ...]

   Build ESGF mapfiles upon local ESGF datanode bypassing esgscan_directory command-line.

   Exit status:
   [0]: Successful scanning of all files encountered,
   [1]: No valid data files found and no mapfile produced and,
   [2]: A mapfile was produced but some files were skipped.

   positional arguments:
    directory             One or more directories to recursively scan. Unix wildcards are allowed.

   optional arguments:
    -h, --help            Show this help message and exit.
                          
    -p PROJECT, --project PROJECT
                          Required project name corresponding to a section of the configuration file.
                          
    -c CONFIG, --config CONFIG
                          Path of configuration INI file
                          (default is ~/lib/python2.7/site-packages/esgmapfiles-0.5-py2.7.egg/esgmapfiles/config.ini).
                          
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

   $> esgscan_directory /path/to/scan -p PROJECT -v
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

   $> esgscan_directory /path/to/scan -p PROJECT -C
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

   $> esgscan_directory /path/to/scan -p PROJECT -w
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

   $> esgscan_directory /path/to/scan -p PROJECT -d
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

   $> esgscan_directory /path/to/scan -p PROJECT -c /path/to/configfile/config.ini

To use a logfile (the logfile directory is optionnal):

.. code-block:: bash

   $> esgscan_directory /path/to/scan -p PROJECT -l /path/to/logfile -v

   $> cat /path/to/logfile/esgmapfiles-YYYYMMDD-HHMMSS-PID.log
   YYYY/MM/DD HH:MM:SS INFO ==> Scan started
   YYYY/MM/DD HH:MM:SS INFO mapfile.txt <-- /path/to/scan/.../vYYYYMMDD/.../file1.nc
   YYYY/MM/DD HH:MM:SS INFO mapfile.txt <-- /path/to/scan/.../vYYYYMMDD/.../file2.nc
   YYYY/MM/DD HH:MM:SS INFO mapfile.txt <-- /path/to/scan/.../vYYYYMMDD/.../file3.nc
   YYYY/MM/DD HH:MM:SS WARNING Delete temporary directory /tmp/tmpzspsLH
   YYYY/MM/DD HH:MM:SS INFO ==> Scan completed (3 files)

To generate a mapfile specifying filename and output directory:

.. code-block:: bash

   $> esgscan_directory /path/to/scan -p PROJECT -o /path/to/mapfile -m mymapfile.txt
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

   $> esgscan_directory /path/to/scan -p PROJECT -L -d -w
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
