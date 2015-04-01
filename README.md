# esg_mapfiles.py

## Description

The publication process of ESG-F nodes requires mapfiles. Mapfiles are text files where each line describes a file to publish. A line is composed by full file path, file size, last modification time in Unix units, the checksum and checksum type, all pipe-separated.

Security policies of computing centres that often host ESG-F data and datanodes, do not allow to easily use the ```esgscan_directory``` ESG-F command-line that is conventionally used to generate mapfiles. Moreover, this command becomes time consuming to checksums a lot of data.

```esg_mapfiles.py``` is a flexible alternative Python command-line tool allowing you to easily generate mapfiles independently from ESG-F. This tool currently supports CMIP5 and CORDEX DRS.

## Features

- Directory as input,
- Follows and currently supports CMIP5 or CORDEX DRS,
- Easily add another project,
- Matching directory format to auto-detect facets mistakes, 
- Read configuration file to check controlled vocabulary,
- Controlled vocabulary can be add if necessary,
- You can choose to produce one mapfile per dataset or not (in this last case you can define your mapfile name). Consequently, you can set your own "mapfile-granularity". A dataset is defined by all DRS tree before the version.
- You can ignored unmatching files,
- An output directory can be defined to store mapfiles,
- Possibility to init a logger,
- File multithreading (especially for MD5 checksums).

## Installing

To execute ```esg_mapfiles.py``` you has to be logged on filesystem hosting data to publish.

Fork this GitHub project or download the Python script and its configuration file:

```Shell
wget http://dods.ipsl.jussieu.fr/glipsl/esg_mapfiles.py
wget http://dods.ipsl.jussieu.fr/glipsl/esg_mapfiles.ini
```

## Configuring

Edit the ```esg_mapfiles.ini``` to set the number of threads you want (default is 4 threads).

```
[DEFAULT]
threads_number = 4
```

(See below to add a new project)

## Dependencies

```esg_mapfiles.py``` uses the following basic Python libraries includes in Python 2.5+. Becareful your Python environment includes:
- os, sys, re, logging
- argparse
- ConfigParser
- tempfile
- datetime
- multiprocessing
- shutil

Please install the ```lockfile``` library not inclued in most Python distributions:

```Shell
pip install lockfile
```

## Usage

```Shell
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
```

## Examples

- Run the script with verbosity and one mapfile per dataset:

```Shell
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
```

- Run the script with a logfile, a mapfiles output directory and without one mapfile per dataset:

```Shell
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
```

- Publish your data using the usual ```esgpublish``` command line on your ESG-F datanode:

```Shell
esgpublish [...] --map cmip5.output1.IPSL.IPSL-CM5A-LR.1pctCO2.yr.ocnBgchem.Oyr.r1i1p1.v20110427
```

## Add a new project

To add a supported project, just add a new project section in your configuration file. The options prefix (called ```facetX``` in the following template) must have the same name as ```dataset_ID``` items and ```directory_format``` variables.

```dataset_ID``` items correspond to a sorted list of facets defining dataset master ID.

The ```directory_format``` option defines the DRS of your project using a regex to match with your full files paths. Feel free to defined a new tree or file extension 
if necessary using all regex facilities.

Follow this template:

```
[your_project]
facet1_options = value1, value2, ...

facet2_options = value1, value2, ...

facet3_options = value1, value2, ...

dataset_ID = facet1, facet2, facet3

directory_format = /(?P<root>[\w./-]+)/(?P<project>[\w.-]+)/(?P<facet1>[\w.-]+)/(?P<facet2>[\w.-]+)/(?P<facet3>[\w.-]+)/(?P<filename>[\w.-]+\.nc)
```


## Frequently asked questions

## Developer/Author

LEVAVASSEUR, G. (CNRS/IPSL)

## Contacts

To submit bugs, suggestions or ideas: glipsl@ipsl.jussieu.fr or sdipsl@ipsl.jussieu.fr

## Changlog

2015-03-27 - Improve logging and synda call.

2015-03-10 : Add --keep-going option to skipped unmatching files. Remove temporary directory in any case.

2015-02-13 : Refactoring script with configuration file and using just a directory as input.

2014-09-17 : MD5 checksum compute by OS (Unix Shell) because of out memory for big data files.
