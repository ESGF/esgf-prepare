.. _usage:

Usage
=====

esgscan_check_vocab
+++++++++++++++++++

Here is the command-line help:

.. code-block:: bash

   $> esgscan_check_vocab -h
   usage: esgscan_check_vocab --project <project_id> [-i /esg/config/esgcet/.] [--log [$PWD]] [-h] [-V]
                              directory [directory ...]

   The mapfile generation relies on the ESGF node configuration files. These "esg.<project>.ini" files
   declares the Data Reference Syntax (DRS) and the controlled vocabularies of each project.

   "esgscan_check_vocab" allows you to easily check the configuration file. It implies that your
   directory structure strictly follows the project DRS including the version facet.

   Positional arguments:
     directory                One or more directories to recursively scan. Unix wildcards
                              are allowed.

   Optional arguments:
     --project <project_id>   Required lower-cased project name.

     -i /esg/config/esgcet/.  Initialization/configuration directory containing "esg.ini"
                              and "esg.<project>.ini" files. If not specified, the usual
                              datanode directory is used.

     --log [$PWD]             Logfile directory. If not, standard output is used.

     -h, --help               Show this help message and exit.

     -V, --Version            Program version.

   Developed by:
   Levavasseur, G. (CNRS/IPSL - glipsl@ipsl.jussieu.fr)
   Iwi, A. (STFC/BADC - alan.iwi@stfc.ac.uk)

Tutorials
---------

To check the facet options declared in your configuration file:

.. code-block:: bash

   $> esgscan_check_vocab /path/to/scan --project PROJECT -i /path/to/configfiles/
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
   usage: esgscan_directory --project <project_id> [-i /esg/config/esgcet/.]
                            [--mapfile {dataset_id}.{version}.map] [--outdir $PWD]
                            [--all-versions | --version 20162704 | --latest-symlink] [--no-version]
                            [--no-checksum] [--filter ".*\.nc$"] [--tech-notes-url <url>]
                            [--tech-notes-title <title>] [--dataset <dataset_id>] [--max-threads 4]
                            [--log [$PWD]] [-h] [-v] [-V]
                            directory [directory ...]

   The publication process of the ESGF nodes requires mapfiles. Mapfiles are text files where each line
   describes a file to publish on the following format:

   dataset_ID | absolute_path | size_bytes [ | option=value ]

   1. All values have to be pipe-separated,
   2. The dataset identifier, the absolute path and the size (in bytes) are required,
   3. Adding the file checksum and the checksum type as optional values is strongly recommended,
   4. Adding the version number to the dataset identifier is useful to publish in a in bulk.

   "esgscan_directory" allows you to easily generate ESGF mapfiles upon local ESGF datanode or not. It
   implies that your directory structure strictly follows the project DRS including the version facet.

   Exit status:
   [0]: Successful scanning of all files encountered,
   [1]: No valid data or files have been found and no mapfile was produced,
   [2]: A mapfile was produced but some files were skipped.

   See full documentation on http://esgscan.readthedocs.org/

   The default values are displayed next to the corresponding flags.

   Positional arguments:
     directory                             One or more directories to recursively scan. Unix wildcards
                                           are allowed.

   Optional arguments:
     --project <project_id>                Required lower-cased project name.

     -i /esg/config/esgcet/.               Initialization/configuration directory containing "esg.ini"
                                           and "esg.<project>.ini" files. If not specified, the usual
                                           datanode directory is used.

     --mapfile {dataset_id}.{version}.map  Specifies template for the output mapfile(s) name.
                                           Substrings {dataset_id}, {version}, {job_id} or {date}
                                           (in YYYYDDMM) will be substituted where found. If
                                           {dataset_id} is not present in mapfile name, then all
                                           datasets will be written to a single mapfile, overriding
                                           the default behavior of producing ONE mapfile PER dataset.

     --outdir $PWD                         Mapfile(s) output directory. A "mapfile_drs" can be defined
                                           in "esg.ini" and joined to build a mapfiles tree.

     --all-versions                        Generates mapfile(s) with all versions found in the
                                           directory recursively scanned (default is to pick up only
                                           the latest one). It disables --no-version.

     --version 20162704                    Generates mapfile(s) scanning datasets with the
                                           corresponding version number only. It takes priority over
                                           --all-versions. If directly specified in positional
                                           argument, use the version number from supplied directory.

     --latest-symlink                      Generates mapfile(s) following latest symlinks only. This
                                           sets the {version} token to "latest" into the mapfile name,
                                           but picked up the pointed version to build the dataset
                                           identifier (if --no-version is disabled).

     --no-version                          Does not includes DRS version into the dataset identifier.

     --no-checksum                         Does not include files checksums into the mapfile(s).

     --filter ".*\.nc$"                    Filter files matching the regular expression (default only
                                           support NetCDF files). Regular expression syntax is defined
                                           by the Python re module.

     --tech-notes-url <url>                URL of the technical notes to be associated with each
                                           dataset.

     --tech-notes-title <title>            Technical notes title for display.

     --dataset <dataset_id>                String name of the dataset. If specified, all files will
                                           belong to the specified dataset, regardless of the DRS.

     --max-threads 4                       Number of maximal threads for checksum calculation.

     --log [$PWD]                          Logfile directory. If not, standard output is used.

     -h, --help                            Show this help message and exit.

     -v                                    Verbose mode.

     -V                                    Program version.

   Developed by:
   Levavasseur, G. (UPMC/IPSL - glipsl@ipsl.jussieu.fr)
   Berger, K. (DKRZ - berger@dkrz.de)
   Iwi, A. (STFC/BADC - alan.iwi@stfc.ac.uk)

Tutorials
---------

To generate a mapfile with verbosity using default parameters:

.. warning:: Default behavior to pickup the latest version in the DRS is ensured with a date version format (e.g., v20151023).

.. code-block:: bash

   $> esgscan_directory /path/to/scan --project PROJECT -v
   ==> Scan started
   dataset_ID1.vYYYYMMDD <-- /path/to/scan/.../vYYYYMMDD/.../file1.nc
   dataset_ID2.vYYYYMMDD <-- /path/to/scan/.../vYYYYMMDD/.../file2.nc
   dataset_ID3.vYYYYMMDD <-- /path/to/scan/.../vYYYYMMDD/.../file3.nc
   Delete temporary directory /tmp/tmpzspsLH
   ==> Scan completed (3 files)

   $> cat dataset_ID.v*.map
   dataset_ID1.vYYYYMMDD
   dataset_ID1.vYYYYMMDD | /path/to/scan/.../vYYYYMMDD/.../file1.nc | size1 | mod_time1 | checksum1 | checksum_type=SHA256

   dataset_ID2.vYYYYMMDD.map
   dataset_ID2.vYYYYMMDD | /path/to/scan/.../vYYYYMMDD/.../file2.nc | size2 | mod_time2 | checksum2 | checksum_type=SHA256

   dataset_ID3.vYYYYMMDD.map
   dataset_ID3.vYYYYMMDD | /path/to/scan/.../vYYYYMMDD/.../file3.nc | size3 | mod_time3 | checksum3 | checksum_type=SHA256

To generate a mapfile without files checksums:

.. note:: The ``-v`` raises the tracebacks of thread-processes (default is the "silent" mode).

.. warning:: The ``--project`` is case-sensitive.

.. code-block:: bash

   $> esgscan_directory /path/to/scan --project PROJECT --no-checksum
   ==> Scan started
   dataset_ID1.vYYYYMMDD <-- /path/to/scan/.../vYYYYMMDD/.../file1.nc
   dataset_ID2.vYYYYMMDD <-- /path/to/scan/.../vYYYYMMDD/.../file2.nc
   dataset_ID3.vYYYYMMDD <-- /path/to/scan/.../vYYYYMMDD/.../file3.nc
   Delete temporary directory /tmp/tmpzspsLH
   ==> Scan completed (3 files)

   $> cat dataset_ID.v*.map
   dataset_ID1.vYYYYMMDD.map
   dataset_ID1.vYYYYMMDD | /path/to/scan/.../vYYYYMMDD/.../file1.nc | size1 | mod_time1

   dataset_ID2.vYYYYMMDD.map
   dataset_ID2.vYYYYMMDD | /path/to/scan/.../vYYYYMMDD/.../file2.nc | size2 | mod_time2

   dataset_ID3.vYYYYMMDD.map
   dataset_ID3.vYYYYMMDD | /path/to/scan/.../vYYYYMMDD/.../file3.nc | size3 | mod_time3

To generate a mapfile without DRS versions:

.. code-block:: bash

   $> esgscan_directory /path/to/scan --p PROJECT --no-version
   ==> Scan started
   dataset_ID1.vYYYYMMDD <-- /path/to/scan/.../vYYYYMMDD/.../file1.nc
   dataset_ID2.vYYYYMMDD <-- /path/to/scan/.../vYYYYMMDD/.../file2.nc
   dataset_ID3.vYYYYMMDD <-- /path/to/scan/.../vYYYYMMDD/.../file3.nc
   Delete temporary directory /tmp/tmpzspsLH
   ==> Scan completed (3 files)

   $> cat dataset_ID.v*.map
   dataset_ID1.vYYYYMMDD.map
   dataset_ID1 | /path/to/scan/.../vYYYYMMDD/.../file1.nc | size1 | mod_time1 | checksum1 | checksum_type=SHA256

   dataset_ID2.vYYYYMMDD.map
   dataset_ID2 | /path/to/scan/.../vYYYYMMDD/.../file2.nc | size2 | mod_time2 | checksum2 | checksum_type=SHA256

   dataset_ID3.vYYYYMMDD.map
   dataset_ID3 | /path/to/scan/.../vYYYYMMDD/.../file3.nc | size3 | mod_time3 | checksum3 | checksum_type=SHA256

Define mapfile name using tokens:

.. warning:: If ``{dataset_id}`` is not present in mapfile name, then all datasets will be written to a single mapfile, overriding the default behavior of producing ONE mapfile PER dataset.

.. code-block:: bash

   $> esgscan_directory /path/to/scan --project PROJECT --mapfile {dataset_id}.{job_id}
   ==> Scan started
   dataset_ID1.job_id <-- /path/to/scan/.../vYYYYMMDD/.../file1.nc
   dataset_ID2.job_id <-- /path/to/scan/.../vYYYYMMDD/.../file2.nc
   dataset_ID3.job_id <-- /path/to/scan/.../vYYYYMMDD/.../file3.nc
   ==> Scan completed (3 files)

   $> cat dataset_ID*.job_id.map
   dataset_ID1.job_id.map
   dataset_ID1.vYYYYMMDD | /path/to/scan/.../vYYYYMMDD/.../file1.nc | size1 | mod_time1 | checksum1 | checksum_type=SHA256

   dataset_ID2.job_id.map
   dataset_ID2.vYYYYMMDD | /path/to/scan/.../vYYYYMMDD/.../file2.nc | size2 | mod_time2 | checksum2 | checksum_type=SHA256

   dataset_ID3.job_id.map
   dataset_ID3.vYYYYMMDD | /path/to/scan/.../vYYYYMMDD/.../file3.nc | size3 | mod_time3 | checksum3 | checksum_type=SHA256

   $> esgscan_directory /path/to/scan --project PROJECT --mapfile {date}
   ==> Scan started
   date <-- /path/to/scan/.../vYYYYMMDD/.../file1.nc
   date <-- /path/to/scan/.../vYYYYMMDD/.../file2.nc
   date <-- /path/to/scan/.../vYYYYMMDD/.../file3.nc
   ==> Scan completed (3 files)

   $> cat date.map
   dataset_ID1.vYYYYMMDD | /path/to/scan/.../vYYYYMMDD/.../file1.nc | size1 | mod_time1 | checksum1 | checksum_type=SHA256
   dataset_ID2.vYYYYMMDD | /path/to/scan/.../vYYYYMMDD/.../file2.nc | size2 | mod_time2 | checksum2 | checksum_type=SHA256
   dataset_ID3.vYYYYMMDD | /path/to/scan/.../vYYYYMMDD/.../file3.nc | size3 | mod_time3 | checksum3 | checksum_type=SHA256

To specify the configuration directory:

.. code-block:: bash

   $> esgscan_directory /path/to/scan --project PROJECT -i /path/to/configfiles/

To use a logfile (the logfile directory is optional):

.. code-block:: bash

   $> esgscan_directory /path/to/scan --project PROJECT -log /path/to/logdir -v

   $> cat /path/to/logfile/esgmapfiles-YYYYMMDD-HHMMSS-PID.log
   YYYY/MM/DD HH:MM:SS INFO ==> Scan started
   YYYY/MM/DD HH:MM:SS INFO dataset_ID1.vYYYYMMDD <-- /path/to/scan/.../vYYYYMMDD/.../file1.nc
   YYYY/MM/DD HH:MM:SS INFO dataset_ID2.vYYYYMMDD <-- /path/to/scan/.../vYYYYMMDD/.../file2.nc
   YYYY/MM/DD HH:MM:SS INFO dataset_ID3.vYYYYMMDD <-- /path/to/scan/.../vYYYYMMDD/.../file3.nc
   YYYY/MM/DD HH:MM:SS WARNING Delete temporary directory /tmp/tmpzspsLH
   YYYY/MM/DD HH:MM:SS INFO ==> Scan completed (3 files)

To specify an output directory:

.. code-block:: bash

   $> esgscan_directory /path/to/scan --project PROJECT --outdir /path/to/mapfiles/
   ==> Scan started
   dataset_ID1.vYYYYMMDD <-- /path/to/scan/.../vYYYYMMDD/.../file1.nc
   dataset_ID2.vYYYYMMDD <-- /path/to/scan/.../vYYYYMMDD/.../file2.nc
   dataset_ID3.vYYYYMMDD <-- /path/to/scan/.../vYYYYMMDD/.../file3.nc
   Delete temporary directory /tmp/tmpzspsLH
   ==> Scan completed (3 files)

   $> cat /path/to/mapfiles/dataset_ID*.v*.map
   dataset_ID1.vYYYYMMDD.map
   dataset_ID1.vYYYYMMDD | /path/to/scan/.../vYYYYMMDD/.../file1.nc | size1 | mod_time1 | checksum1 | checksum_type=SHA256

   dataset_ID2.vYYYYMMDD.map
   dataset_ID2.vYYYYMMDD | /path/to/scan/.../vYYYYMMDD/.../file2.nc | size2 | mod_time2 | checksum2 | checksum_type=SHA256

   dataset_ID3.vYYYYMMDD.map
   dataset_ID3.vYYYYMMDD | /path/to/scan/.../vYYYYMMDD/.../file3.nc | size3 | mod_time3 | checksum3 | checksum_type=SHA256

To add a mapfile tree to an output directory (i.e., if a ``mapfile_drs`` has been defined):

.. code-block:: bash

   $> esgscan_directory /path/to/scan --project PROJECT --outdir /path/to/mapfiles/
   ==> Scan started
   dataset_ID1.vYYYYMMDD <-- /path/to/scan/.../vYYYYMMDD/.../file1.nc
   dataset_ID2.vYYYYMMDD <-- /path/to/scan/.../vYYYYMMDD/.../file2.nc
   dataset_ID3.vYYYYMMDD <-- /path/to/scan/.../vYYYYMMDD/.../file3.nc
   ==> Scan completed (3 files)

   $> cat /path/to/mapfiles/facet1/facet2/facet3/dataset_ID1.vYYYYMMDD.map
   dataset_ID1.vYYYYMMDD | /path/to/scan/.../vYYYYMMDD/.../file1.nc | size1 | mod_time1 | checksum1 | checksum_type=SHA256

   $> cat /path/to/mapfiles/facet1/facet2/facet3/dataset_ID2.vYYYYMMDD.map
   dataset_ID2.vYYYYMMDD | /path/to/scan/.../vYYYYMMDD/.../file2.nc | size2 | mod_time2 | checksum2 | checksum_type=SHA256

   $> cat /path/to/mapfiles/facet1/facet2/facet3/dataset_ID3.vYYYYMMDD.map
   dataset_ID3.vYYYYMMDD | /path/to/scan/.../vYYYYMMDD/.../file3.nc | size3 | mod_time3 | checksum3 | checksum_type=SHA256


To generate a mapfile walking through *latest* directories only:

.. code-block:: bash

   $> esgscan_directory /path/to/scan --project PROJECT --latest-symlink
   ==> Scan started
   dataset_ID1.latest <-- /path/to/scan/.../latest/.../file1.nc
   dataset_ID2.latest <-- /path/to/scan/.../latest/.../file2.nc
   dataset_ID3.latest <-- /path/to/scan/.../latest/.../file3.nc
   Delete temporary directory /tmp/tmpzspsLH
   ==> Scan completed (3 files)

   $> cat dataset_ID*.latest.map
   dataset_ID1.latest.map
   dataset_ID1.vYYYYMMDD | /path/to/scan/.../latest/.../file1.nc | size1 | mod_time1 | checksum1 | checksum_type=SHA256

   dataset_ID2.latest.map
   dataset_ID2.vYYYYMMDD | /path/to/scan/.../latest/.../file2.nc | size2 | mod_time2 | checksum2 | checksum_type=SHA256

   dataset_ID3.latest.map
   dataset_ID3.vYYYYMMDD | /path/to/scan/.../latest/.../file3.nc | size3 | mod_time3 | checksum3 | checksum_type=SHA256

To generate a mapfile walking through a particular version only:

.. warning:: By default ``esgscan_directory`` pick up the latest version only.

.. note:: Use the ``--all-versions`` flag to generate a mapfile walking through all versions.

.. code-block:: bash

   $> esgscan_directory /path/to/scan --project PROJECT --version 20151104
   ==> Scan started
   dataset_ID1.v20151104 <-- /path/to/scan/.../v20151104/.../file1.nc
   dataset_ID2.v20151104 <-- /path/to/scan/.../v20151104/.../file2.nc
   dataset_ID3.v20151104 <-- /path/to/scan/.../v20151104/.../file3.nc
   Delete temporary directory /tmp/tmpzspsLH
   ==> Scan completed (3 files)

   $> cat dataset_ID*.v20151104.map
   dataset_ID1.v20151104.map
   dataset_ID1.v20151104 | /path/to/scan/.../v20151104/.../file1.nc | size1 | mod_time1 | checksum1 | checksum_type=SHA256

   dataset_ID2.v20151104.map
   dataset_ID2.v20151104 | /path/to/scan/.../v20151104/.../file2.nc | size2 | mod_time2 | checksum2 | checksum_type=SHA256

   dataset_ID3.v20151104.map
   dataset_ID3.v20151104 | /path/to/scan/.../v20151104/.../file3.nc | size3 | mod_time3 | checksum3 | checksum_type=SHA256

.. note:: All the previous examples can be combined safely.
