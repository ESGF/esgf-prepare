.. _synopsis:

Synopsis
========

The publication process of the `ESG-F <http://pcmdi9.llnl.gov/>`_ nodes requires *mapfiles*. Mapfiles are text files where each line describes a file to publish on the following format:
::

   dataset_ID | absolute_path | size_bytes [ | option=value ]

.. warning::

   i. All values have to be pipe-separated.
   ii. The dataset identifier, the absolute path and the size (in bytes) are required.
   iii. Adding the file checksum and the checksum type as optional values is strongly recommended.

``esgscan_directory`` is a flexible command-line tool allowing you to easily generate mapfiles. 

Prerequisite
************

``esgscan_directory`` implies that the *Data Reference Syntax* (DRS) if the projects includes a version directory.

Features
********

**Directory as input**
  You only need to specifiy the directory to recursively scan. To include several data directories in one mapfile and to publish them at once, you can use all Unix wildcards in the path or submit several paths.

**Multi-project**
   ``time_axis`` is currently provided supporting `CMIP5 <http://cmip-pcmdi.llnl.gov/cmip5/docs/cmip5_data_reference_syntax.pdf>`_ and `CORDEX <https://www.medcordex.eu/cordex_archive_specifications_2.2_30sept2013.pdf>`_ *Data Reference Syntax* (DRS). Nevertheless, you can easily add a new "project" section in the configuration file to support yours. Please follow the `INI syntax <https://en.wikipedia.org/wiki/INI_file>`_.

**Facets auto-detection**
  The dataset facets will be automatically detect using the ``directory_format`` regular expression in the configuration file where all facet options have to be declared. This ensures an appropriated mapfile generation by preventing DRS mistakes and checking the controlled vocabulary.

**Multithreading**
  To compute the checksum of a lot of large files becomes time consuming. We implement multithreading at file level. Each file is processed by a thread that writes the resulting line in the corresponding mapfile. A lock file system orders the simultaneous access to mapfiles by the threads to avoid any conflicts.

**Mapfile granularity control**
  You can choose to produce one mapfile per dataset (i.e., to generate one mapfile per each version of each dataset). In this case your mapfiles automatically take the name of the dataset identifier with DRS version as suffix. Consequently, you can set your own "mapfile-granularity" and control your publications by concatenating several mapfiles. 

.. note:: A dataset is defined by one version of all upstream DRS tree.

**Only latest version**
   You can choose to only include the latest versions of the datasets in your mapfile. In this case, the walk through the filesystem is filtered. Only the folders pointed by a "latest" symbolic link are recursively scanned.

**Mapfile with DRS version**
   You can choose to include the DRS version into each dataset ID. This is compatible with the `ESG-F <http://pcmdi9.llnl.gov/>`_ 2.0 release and leads to a full-slave behaviour of the `ESG-F publisher <https://github.com/ESGF/esg-publisher>`_. With this mapfile syntax the ``--new-version`` option of the publisher command-lines is deprecated.

**Developer's entry point**
  ``esgscan_directory`` can be imported and called in your own scripts. Just pass a dictionnary with your flags to the ``run(job={})`` function (see :ref:`autodoc`). 

**Standalone**
  Security policies of computing centres, that often host `ESG-F <http://pcmdi9.llnl.gov/>`_ data and datanodes, do not allow to easily access the node configuration. ``esgscan_directory`` is not part of `ESG-F <http://pcmdi9.llnl.gov/>`_ software stack and can be run as standalone tool outside any `ESG-F <http://pcmdi9.llnl.gov/>`_ node.

**Compatible with ESG-F node configuration file**
  Each `ESG-F <http://pcmdi9.llnl.gov/>`_ node centralizes all projects definitions (DRS, facets) one INI configuration file ``esg.ini`` file. To ensure a right facets auto-detection, ``esgscan_directory`` directly works from ``esg.ini``.

**Vocabulary checkup**
  ``esgscan_directory`` was accompanied by ``esgscan_check_vocab``. This module allows you to easily check the facet options declared in your configuration file depending on the direcotires you want to recursively scan.

**Keep threads tracebacks**
  The threads-processes do not shutdown the main process of ``esgscan_directory`` run. If an error occurs on a thread, the traceback of the child-process is not raised to the main process. To help you to have a fast debug, the tracebacks of each threads can be raised using the ``-v/--verbose`` option (see :ref:`usage`).

**Output directory**
  An output directory can be defined to store and organized your mapfiles.

**Use a logfile**
  You can initiate a logger instead of the standard output. This could be useful for automatic workflows. The logfile name is automatically defined and unique (using the the job's name, the date and the job's PID). You can define an output directory for your logs too.


