.. _index:


``esgprep`` toolbox
===================

The Earth System Grid Federation (`ESGF <https://esgf.llnl.gov/>`_) publication process requires a strong and effective
data management, which could also be a burden. The ESGF ``esgprep`` toolbox is a piece of software that enables data
preparation according to ESGF best practices. ``esgprep`` allows the ESGF data providers and datanode managers to
easily prepare their data for publishing to an ESGF node. It can be used to fetch required configuration files, apply
the *Data Reference Syntax* on local filesystems and/or generate mapfiles for ESGF publication.

.. note:: ``esgprep`` is designed to follow all requirements from the `ESGF Best Practices document
    <https://acme-climate.atlassian.net/wiki/x/JADm>`_.

.. note:: ``esgprep`` is built as a full standalone toolbox allowing you to prepare your data outside of an ESGF node.

``esgprep`` gathers Python command-lines covering several steps of `ESGF publication workflow <https://drive.google
.com/open?id=0B7Kis5A3U5SKTUdFbjYwRnFhQ0E>`_.

.. toctree::
   :maxdepth: 1

   installation
   configuration
   usage
   fetch-ini
   drs
   check-vocab
   mapfiles
   faq
   credits
   log
   autodoc

Indices and tables
==================

* :ref:`genindex`
* :ref:`modindex`
* :ref:`search`

