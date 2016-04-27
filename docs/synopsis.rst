.. _ESGF: http://pcmdi9.llnl.gov/

.. _synopsis:

Synopsis
========

The publication process of the `ESGF`_ nodes requires *mapfiles*. Mapfiles are text files where each line describes a file to publish on the following format:
::

   dataset_ID | absolute_path | size_bytes [ | option=value ]

.. warning::

   i. All values have to be pipe-separated.
   ii. The dataset identifier, the absolute path and the size (in bytes) are required.
   iii. Adding the file checksum and the checksum type as optional values is strongly recommended.
   iv. Adding the version number next to the dataset identifier is strongly recommended.

``esgscan_directory`` is a flexible command-line tool allowing you to easily generate mapfiles upon local ESGF datanode or not.

.. warning:: It implies that your directory structure strictly follows the tree fixed by the project's *Data Reference Syntax* (DRS) **including the version facet**.

Features
********

**Directory as input**
  You only need to specifiy the directory to recursively scan. To include several data directories in one mapfile and to publish them at once, you can use all Unix wildcards in the path or submit several paths.

**Compatiblity with ESGF node configuration file(s)**
  Each `ESGF`_ node:
   * Declares all technical attributes (e.g., the checksum type) into the ``[default]`` of a configuration INI file called ``esg.ini``,
   * Centralizes all projects definitions (DRS, facets) into the ``project:<project>`` sections of the same ``esg.ini`` or from independent files called ``esg.<project>.ini``.

  To ensure a right facets auto-detection, ``esgscan_directory`` directly works from these INI files.

**Dataset identifier template**
  Each dataset to publish is defined by its identifier as a string of dot-separated facets. ``esgscan_directory`` reads the identifier template (i.e., the facets within) using the ``dataset_id`` regular expression from the corresponding project section in the ``esg.ini`` or the appropriate ``esg.<project>.ini``.

**Facets values auto-detection**
  The facets values are automatically detected from the full path of the file, using the ``directory_format`` regular expression in the configuration file. These DRS values are used to fill the dataset identifier template.

**Facets values checkup**
  Each facet value from the dataset identifier is assessed in the light of configuration file(s). If the facet has been deduced from the full path of the file, its value has to be declared in an ``facet_options`` list of the configuration file(s). If the facet is missing in the full path of the file, it has to be decuded from a required ``facet_map`` maptable in the configuration file(s). This ensures an appropriated mapfile generation by preventing DRS mistakes and checking the controlled vocabulary.

**Vocabulary checkup**
  ``esgscan_directory`` is accompanied by ``esgscan_check_vocab``. This module allows you to easily check the options lists and maptables declared in your configuration file(s) depending on the directory you want to recursively scan. ``esgscan_check_vocab`` walks trough the file system, gathers each facet value of encountered datasets and displays the report with used/unsued and undeclared facet values.

**Multithreading**
  To compute the checksum of a lot of large files becomes time consuming. We implement multithreading at file level. Each file is processed by a thread that writes the resulting line in the corresponding mapfile. A lock file system orders the simultaneous access to mapfiles by the threads to avoid any conflicts.

**Mapfile granularity control**
  The mapfile name can be specifiy using a template with tokens. the available tokens are ``{dataset_id}``, ``{version}``, ``{date}`` or ``{job_id}``. These substrings will be substituted where found. If ``{dataset_id}`` token is not present in mapfile name, then all datasets will be written  to a single mapfile, overriding the default behavior of producing **ONE mapfile PER each version of each dataset**. Consequently, you can set your own "mapfile-granularity" through the template of the mapfile(s) name and control your publications.

.. note:: A dataset is defined by one version of all upstream DRS tree.

**Version filtering**
  The walk through the file system is filtered. The default behavior of ``esgscan_directory`` is to pick up only the latest version of a dataset scanned (as the greatest version number). You can change this behavior and choose to include (see :ref:`usage`):
   * All versions found with the ``--all-versions`` flag (it disables ``--no-version`` flag),
   * Only the version pointed by a "latest" symlink (if exists) with the ``--latest-symlink`` flag,
   * Only a particular version with the ``--version <version_number>`` argument or by directly specifying the version number in the supplied directory (it takes priority over ``--all-versions`` flag).

**Mapfile with DRS version**
   You can choose to include the DRS version next to each dataset identifier. This is compatible with the ESGF 2.x. With this mapfile syntax the ``--new-version`` option of the publisher command-lines becomes deprecated.

**Developer's entry point**
  ``esgscan_directory`` can be imported and called in your own scripts. Just pass a dictionnary with your flags to the ``run(job={})`` function (see :ref:`autodoc`).

**Standalone**
  Security policies of computing centres, that often host `ESGF`_ nodes, do not allow to use ``esgscan_directory`` within a node that is conventionally used to generate mapfiles.

**Keep threads tracebacks**
  The threads-processes do not shutdown the main process of ``esgscan_directory`` run. If an error occurs on a thread, the traceback of the child-process is not raised to the main process. To help you to have a fast debug, the tracebacks of each threads can be raised using the ``-v`` option (see :ref:`usage`).

**Output directory**
  An output directory can be defined to store and organized your mapfiles.

**Mapfile management**
  The output directory can be substituted or added by a mapfile tree depending on the files attributes. Just defined the mapfile DRS you want in the corresponding project section in the ``esg.ini`` or the appropriate ``esg.<project>.ini``. ``esgscan_directory`` will automatically deduce and create the corresponding tree to write mapfiles.

**Processing progress**
  A mapfile is created when its first file is proceed. The ``.part`` file extension seems the mapfile could be incomplete. When the process ends the ``.map`` extension seems the mapfile is complete and safely usable.

**Use a logfile**
  You can initiate a logger instead of the standard output. This could be useful for automatic workflows. The logfile name is automatically defined and unique (using the the job's name, the date and the job's ID). You can define an output directory for your logs too.
