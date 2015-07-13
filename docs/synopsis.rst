********
Synopsis
********

The publication process of ESGF nodes requires *mapfiles*. Mapfiles are text files where each line describes a file to publish on the following format:
::

   dataset_ID | absolute_path | size_bytes [ | option=value ]

i. All values have to be pipe-separated.
ii. The dataset identifier, the absolute path and the size (in bytes) are required.
iii. Adding the file checksum and the checksum type as optional values is strongly recommended.

Security policies of computing centres, that often host ESGF data and datanodes, do not allow to easily use the ``esgscan_directory`` ESGF command-line that is conventionally used to generate mapfiles. Moreover, this command becomes time consuming to checksums a lot of data.

``esg_mapfiles`` is a flexible alternative command-line tool allowing you to easily generate mapfiles independently from ESGF nodes.


Features
++++++++

**Directory as input**
  In comparison with previous versions, you only need to specifiy the directory to recursively scan. To include several data directories in one mapfile and to publish them at once, you can use all Unix wildcards in the path or submit several paths.

**Multi-project**
  ``esg_mapfiles`` is currently provided supporting CMIP5 and CORDEX *Data Reference Syntax*. Nevertheless, you can easily add a new "project" section in the configuration file to support yours. Please follow the INI syntax.

**Facets auto-detection**
  The dataset's facets will be automatically detect using the ``directory_format`` regular expression in the configuration file where all facet options have to be declared. This ensures an appropriated mapfile generation by preventing DRS mistakes and checking the controlled vocabulary.

**Multithreading**
  To compute the checksum of a lot of large files becomes time consuming. We implement multithreading at file level. Each file is processed by a thread that writes the resulting line in the corresponding mapfile. A lock file system orders the simultaneous access to mapfiles by the threads to avoid any conflicts.

**Mapfile granularity control**
  You can choose to produce one mapfile per dataset (i.e., to generate one mapfile per each version of each dataset). In this case your mapfiles automatically take the name of the dataset identifier with DRS version as suffix. Consequently, you can set your own "mapfile-granularity" and control your publications by concatenating several mapfiles. 

.. note:: A dataset is defined one version of all upstream DRS tree.

**Only latest version**
   You can choose to only include the latest versions of the datasets in your mapfile. In this case, the walk through the filesystem is filtered. Only the folders with the "latest" symbolic link are recursively scanned.

**Mapfile with DRS version**
   You can choose to include the DRS version into each dataset ID. This is compatible with the ESGF 2.0 release and lead to a full-slave behaviour of the ESGF publisher. With this mapfile syntax the ``--new-version`` option of the publisher command-lines is deprecated.

**SYNDA implemtentation**
  ``esg_mapfiles.py`` can be called by SYNDA post-processing workers. This uses the ``run()`` function instead of the ``main()``. 

**Useful configuration file**
  All projects definitions (DRS, facets) are centralized in one configuration file (INI format) in a simplier way than the ``esg.ini`` file on ESGF nodes.

**Keep going**
  You can ignored all errors raised by unmatching files in the submitted path(s) in order to keep going the generation process in any case. To help you to have a short diagnostic, the number of scanned file is displayed at the end.

**Output directory**
  An output directory can be defined to store and organized your mapfiles.

**Use a logfile**
  You can initiate a logger instead of the standard output. This could be useful for automatic workflows. The logfile name is automatically defined and unique (using the date and the job's PID). You can define an output directory for your logs.


