.. _ESGF: http://pcmdi.llnl.gov/

.. _synopsis:

Synopsis
========

The Earth System Grid Federation (ESGF) publication process requires a strong and effective data management that
could also be a burden. ``esgprep`` allows the ESGF data providers to easily prepare their data for publishing to an
ESGF node.

.. note:: ``esgprep`` is designed to follow all requirements from the `ESGF Best Practices document <https://acme-climate.atlassian.net/wiki/x/JADm>`_.

``esgprep`` gathers Python command-lines covering several steps of `ESGF publication workflow <https://drive.google
.com/open?id=0B7Kis5A3U5SKTUdFbjYwRnFhQ0E>`_.

``esgprep fetch-ini``
*********************

The ESGF publishing client and most of ESGF tools rely on configuration files of different kinds, that are the
primary means of configuring the ESGF publisher.

The ``esg.ini`` file gathers all required information to configure the datanode regarding to data publication (e
.g., PostgreSQL access, THREDDS configuration, etc.).

The ``esg.<project_id>.ini`` files declare all facets and allowed values according to the *Data Reference Syntax*
(DRS) and the controlled vocabularies of the corresponding project.

The ``esgcet_models_table.txt`` declares the models and their descriptions among the projects.

The ``<project_id>_handler.py`` are Python methods to guide the publisher in metadata harvesting.

The ``fetch-ini`` command allows you to download and configure "on the fly" preset files hosted on `a GitHub repository
<https://github.com/ESGF/config/>`_.

If you prepare your data outside of an ESGF node using ``esgprep`` as a full standalone toolbox, this step
is mandatory. Keep in mind that the fetched files have to be reviewed to ensure a correct configuration
of your projects.

``esgprep drs``
***************

The Data Reference Syntax (DRS) defines the way your data have to follow on your filesystem. This allows a proper
publication on ESGF node. The ``drs`` command is designed to help ESGF datanode managers to prepare incoming
data for publication, placing files in the DRS directory structure, and manage multiple versions of
publication-level datasets to minimise disk usage.

**This feature is coming soon !**

``esgprep check-vocab``
***********************

In the case of your data already follow the appropriate directory structure, you may want to check that all
values of each facet are correctly declared into ``esg.<project_id>.ini`` sections. The ``check-vocab`` command
allows you to easily check the configuration file attributes by scanning your data tree.

``esgprep mapfile``
*******************

The publication process of the ESGF nodes requires *mapfiles*. Mapfiles are text files where each line
describes a file to publish on the following format:
::

   dataset_ID | absolute_path | size_bytes [ | option=value ]

``mapfile`` is a flexible command-line allowing you to easily generate mapfiles upon local ESGF datanode or not.

.. warning:: ``esgprep`` implies that your directory structure strictly follows the tree fixed by the project's *Data
   Reference Syntax* (DRS) **including the version facet**.

Key features
************

Directory as input
   You only need to specify the directory to recursively scan. To include several data directories, you can use all
   Unix wildcards in the path or submit several paths.

Compatibility with ESGF node configuration file(s)
   To ensure a right facets auto-detection, ``esgprep`` directly works from the usual ESGF configuration files.

Facets values auto-detection
   The facets values are automatically detected from the full path of the file, using the ``directory_format``
   regular expression in the configuration files. These DRS values are used to fill the dataset identifier template.
   Each facet value from the dataset identifier is assessed in the light of configuration file(s) options or maps.

Multi-threading
   To compute the checksum of a lot of large files becomes time consuming. We implement multi-threading at file level.

Standalone
   Security policies of computing centres, that often host `ESGF`_ nodes, do not allow to use ``esgprep`` within a
   node that is conventionally used to generate mapfiles.

Tracebacks
   The threads-processes do not shutdown the main process of ``esgprep`` run. If an error occurs on a thread, the
   traceback of the child-process is not raised to the main process. To help you to have a fast debug, the
   tracebacks of each threads can be raised using the ``-v`` option (see :ref:`usage`).

Use a logfile
   You can initiate a logger instead of the standard output. This could be useful for automatic workflows. The
   logfile name is automatically defined and unique (using the the job's name, the date and the job's ID). You can
   define an output directory for your logs too.

.. note:: For all detailed features see the help message of each ``esgprep`` sub-command.
