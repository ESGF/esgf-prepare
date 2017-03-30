.. _ESGF: http://pcmdi.llnl.gov/

.. _synopsis:

Synopsis
========

The Earth System Grid Federation (ESGF) publication process requires a strong and effective data management, which
could also be a burden. ``esgprep`` allows the ESGF data providers to easily prepare their data for publishing to an
ESGF node.

.. note:: ``esgprep`` is designed to follow all requirements from the `ESGF Best Practices document <https://acme-climate.atlassian.net/wiki/x/JADm>`_.

``esgprep`` gathers Python command-lines covering several steps of `ESGF publication workflow <https://drive.google
.com/open?id=0B7Kis5A3U5SKTUdFbjYwRnFhQ0E>`_.

Key features
************

Directory as input
   You only need to specify the directory to recursively scan. To include several data directories, you can use all
   Unix wildcards in the path or specify several paths.

Compatibility with ESGF node configuration file(s)
   To ensure a correct auto-detection of facets, ``esgprep`` works +directly from the usual ESGF configuration files.

Facet values auto-detection
   The facet values are automatically detected from the full path of the file, using the ``directory_format``
   regular expression in the configuration files. These DRS values are used to fill the dataset identifier template.
   Each facet value from the dataset identifier is assessed in the light of configuration file(s) options or maps.

Multi-threading
   Computing the checksum of many large files becomes time consuming. We implement multi-threading at the file level.

Standalone
   Security policies of computing centres, which often host `ESGF`_ nodes, limit the tools that can be run on 
   operational data nodes (which are conventionally used to generate mapfiles). Instead, a standalone installation 
   of ``esgprep`` may be used elsewhere.

Tracebacks
   The threads-processes do not shut down the top-level ``esgprep`` process. If an error occurs on a thread, the
   traceback of the child-process is not raised to the main process. To help you to have a fast debug, the
   tracebacks of each threads can be raised using the ``-v`` option (see :ref:`usage`).

Use of a logfile
   You can initiate a logger instead of standard output. This could be useful for automatic workflows. The
   logfile name is automatically defined and unique (using the the job's name, the date and the job's ID). You can
   also define an output directory for your logs.

.. note:: For all detailed features see the help message of each ``esgprep`` sub-command.
