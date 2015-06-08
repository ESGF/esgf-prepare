*****
Usage
*****

.. code-block:: bash

   $> ./esg_mapfiles.py -h

      usage: esg_mapfiles.py [-h] -p {cmip5,cordex} [-c CONFIG] [-o OUTDIR]
                             [-l [LOGDIR]] [-m MAPFILE] [-d] [-v] [-V]
                             [directory]

      Build ESG-F mapfiles upon local ESG-F datanode bypassing esgscan_directory
      command-line.

      positional arguments:
        directory             Directory to recursively scan

      optional arguments:
        -h, --help            Show this help message and exit.

        -p {cmip5,cordex}, --project {cmip5,cordex}
                              Required project to build mapfiles among:
                              - cmip5
                              - cordex

        -c CONFIG, --config CONFIG
                              Path of configuration INI file
                              (default is '{workdir}/esg_mapfiles.ini').

        -o OUTDIR, --outdir OUTDIR
                              Mapfile(s) output directory
                              (default is working directory).

        -l [LOGDIR], --logdir [LOGDIR]
                              Logfile directory. If not, standard output is used.

        -m MAPFILE, --mapfile MAPFILE
                              Output mapfile name. Only used without --per-dataset option
                              (default is 'mapfile.txt').

        -d, --per-dataset     Produce ONE mapfile PER dataset.

        -k, --keep-going      Keep going if some files cannot be processed.

        -v, --verbose         Verbose mode.

        -V, --Version         Program version.

      Developped by Levavasseur, G. (CNRS/IPSL)

Examples
--------

Run the script with verbosity and one mapfile per dataset:

.. code-block:: bash

   $> ./esg_mapfiles.py /prodigfs/esg/CMIP5/output1/IPSL/IPSL-CM5A-LR/1pctCO2/yr/ -p cmip5 -d -v
   Scan started for /prodigfs/esg/CMIP5/output1/IPSL/IPSL-CM5A-LR/1pctCO2/yr
   cmip5.output1.IPSL.IPSL-CM5A-LR.1pctCO2.yr.ocnBgchem.Oyr.r1i1p1.v20110427 <-- /prodigfs/esg/CMIP5/output1/IPSL/IPSL-CM5A-LR/1pctCO2/yr/ocnBgchem/Oyr/r1i1p1/v20110427/o2/o2_Oyr_IPSL-CM5A-LR_1pctCO2_r1i1p1_1950-1989.nc
   [...]
   cmip5.output1.IPSL.IPSL-CM5A-LR.1pctCO2.yr.ocnBgchem.Oyr.r1i1p1.v20120430 <-- /prodigfs/esg/CMIP5/output1/IPSL/IPSL-CM5A-LR/1pctCO2/yr/ocnBgchem/Oyr/r1i1p1/v20120430/o2/o2_Oyr_IPSL-CM5A-LR_1pctCO2_r1i1p1_1850-1949.nc
   Scan completed for /prodigfs/esg/CMIP5/output1/IPSL/IPSL-CM5A-LR/1pctCO2/yr
   Delete temporary directory /tmp/tmpCPadoq

   $> ls -l
   cmip5.output1.IPSL.IPSL-CM5A-LR.1pctCO2.yr.ocnBgchem.Oyr.r1i1p1.v20110427
   cmip5.output1.IPSL.IPSL-CM5A-LR.1pctCO2.yr.ocnBgchem.Oyr.r1i1p1.v20111010
   cmip5.output1.IPSL.IPSL-CM5A-LR.1pctCO2.yr.ocnBgchem.Oyr.r1i1p1.v20120430

   $> cat cmip5.output1.IPSL.IPSL-CM5A-LR.1pctCO2.yr.ocnBgchem.Oyr.r1i1p1.v20110427
   cmip5.output1.IPSL.IPSL-CM5A-LR.1pctCO2.yr.ocnBgchem.Oyr.r1i1p1 | /prodigfs/esg/CMIP5/output1/IPSL/IPSL-CM5A-LR/1pctCO2/yr/ocnBgchem/Oyr/r1i1p1/v20110427/o2/o2_Oyr_IPSL-CM5A-LR_1pctCO2_r1i1p1_1950-1989.nc | 135602104 | mod_time=1299499118.000000 | checksum=bd7823e10667f27069803e87dc7ec514 | checksum_type=MD5
   cmip5.output1.IPSL.IPSL-CM5A-LR.1pctCO2.yr.ocnBgchem.Oyr.r1i1p1 | /prodigfs/esg/CMIP5/output1/IPSL/IPSL-CM5A-LR/1pctCO2/yr/ocnBgchem/Oyr/r1i1p1/v20110427/co3satcalc/co3satcalc_Oyr_IPSL-CM5A-LR_1pctCO2_r1i1p1_1950-1989.nc | 135602192 | mod_time=1299500260.000000 | checksum=735dd172b16df41fae0994a18426cb6d | checksum_type=MD5
   [...]


Run the script with a logfile, a mapfiles output directory and without one mapfile per dataset:

.. code-block:: bash

   $> ./esg_mapfiles.py /ccc/work/cont003/cordex/cordex/output/EUR-11/IPSL-INERIS/IPSL-IPSL-CM5A-MR/historical/r1i1p1/IPSL-INERIS-WRF331F/v1/mon/tas/v20140301/ -p cordex -c esg_mapfiles.ini -o my_mapfiles_dir -l -m my_mapfile

   $> cat esg_mapfile-20150213-150235-13754.log
   2015/02/13 03:02:35 PM INFO Scan started for /ccc/work/cont003/cordex/cordex/output/EUR-11/IPSL-INERIS/IPSL-IPSL-CM5A-MR/historical/r1i1p1/IPSL-INERIS-WRF331F/v1/mon/tas/v20140301
   2015/02/13 03:02:35 PM INFO my_mapfile <-- /ccc/work/cont003/cordex/cordex/output/EUR-11/IPSL-INERIS/IPSL-IPSL-CM5A-MR/historical/r1i1p1/IPSL-INERIS-WRF331F/v1/mon/tas/v20140301/tas_EUR-11_IPSL-IPSL-CM5A-MR_historical_r1i1p1_IPSL-INERIS-WRF331F_v1_mon_200101-200512.nc
   [...]
   2015/02/13 03:02:35 PM INFO my_mapfile <-- /ccc/work/cont003/cordex/cordex/output/EUR-11/IPSL-INERIS/IPSL-IPSL-CM5A-MR/historical/r1i1p1/IPSL-INERIS-WRF331F/v1/mon/tas/v20140301/tas_EUR-11_IPSL-IPSL-CM5A-MR_historical_r1i1p1_IPSL-INERIS-WRF331F_v1_mon_198101-199012.nc
   2015/02/13 03:02:35 PM INFO Scan completed for /ccc/work/cont003/cordex/cordex/output/EUR-11/IPSL-INERIS/IPSL-IPSL-CM5A-MR/historical/r1i1p1/IPSL-INERIS-WRF331F/v1/mon/tas/v20140301

   $> cat my_mapfiles_dir/my_mapfile
   cordex.output.EUR-11.IPSL-INERIS.IPSL-IPSL-CM5A-MR.historical.r1i1p1.IPSL-INERIS-WRF331F.v1.mon.tas | /ccc/work/cont003/cordex/cordex/output/EUR-11/IPSL-INERIS/IPSL-IPSL-CM5A-MR/historical/r1i1p1/IPSL-INERIS-WRF331F/v1/mon/tas/v20140301/tas_EUR-11_IPSL-IPSL-CM5A-MR_historical_r1i1p1_IPSL-INERIS-WRF331F_v1_mon_200101-200512.nc | 27734202 | mod_time=1393851905.000000 | checksum=b7d27645058c3545cefde2b56ae512a4 | checksum_type=MD5
   cordex.output.EUR-11.IPSL-INERIS.IPSL-IPSL-CM5A-MR.historical.r1i1p1.IPSL-INERIS-WRF331F.v1.mon.tas | /ccc/work/cont003/cordex/cordex/output/EUR-11/IPSL-INERIS/IPSL-IPSL-CM5A-MR/historical/r1i1p1/IPSL-INERIS-WRF331F/v1/mon/tas/v20140301/tas_EUR-11_IPSL-IPSL-CM5A-MR_historical_r1i1p1_IPSL-INERIS-WRF331F_v1_mon_197101-198012.nc | 49880917 | mod_time=1417447725.000000 | checksum=9ace849d1573075c39b6724b22a16c2d | checksum_type=MD5
   [...]


Publish your data using the usual *esgpublish* command line on your ESG-F datanode:

.. code-block:: bash

   esgpublish [...] --map cmip5.output1.IPSL.IPSL-CM5A-LR.1pctCO2.yr.ocnBgchem.Oyr.r1i1p1.v20110427
