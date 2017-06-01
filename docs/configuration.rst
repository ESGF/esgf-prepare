.. _configuration:


Configuration
=============

``esgprep`` works according to
`the configuration INI file(s) of the ESGF nodes <https://acme-climate.atlassian.net/wiki/x/JADm>`_.

Location
********

On an ESGF node, the configuration directory containing those INI files is ``/esg/config/esgcet``, that is the default
for ``esgprep``. In the case you are running ``esgprep`` outside of an ESGF node, the directory gathering all ``.ini``
files has to be submitted using the ``-i`` option (see :ref:`usage`).

``esg.ini``
***********

This INI file gathers all required information to configure the datanode regarding to data publication (e.g.,
PostgreSQL access, THREDDS configuration, etc.).

The only configuration in this section is to define the checksum client and checksum
type under the ``[default]`` section. Edit the file to set the Shell command line to use (default is ``sha256sum``).

.. code-block:: ini

    [default]
    checksum = sha256sum | SHA256

``esg.<project_id>.ini``
************************

Those INI files declare all facets and allowed values according to the Data Reference Syntax (DRS) and the controlled
vocabularies of the corresponding project. Preset ``esg.<project_id>.ini`` files have been properly built by
ESGF community for the following projects:

 * CMIP6
 * CMIP5
 * CORDEX
 * CORDEX-Adjust
 * EUCLIPSE
 * GeoMIP
 * input4MIPs
 * obs4MIPs
 * PMIP3
 * LUCID
 * PRIMAVERA
 * TAMIP
 * ISIMIP-FT

They can be downloaded from `the GitHub repository <https://github.com/ESGF/config/tree/devel/publisher-configs/ini>`_
or using ``esgprep fetch-ini``.
If no ``esg.<project_id>.ini`` corresponds to your project you can made your own following `the ESGF Best Practices
document <https://acme-climate.atlassian.net/wiki/x/JADm>`_:

 * Please follow the structure detailed `here <https://acme-climate.atlassian.net/wiki/x/loDRAw>`_.
 * Add your project into the ``project_options`` list of your ``esg.ini``.
 * The ``--project`` argument of ``esgprep`` directly refers to the ``project_id`` (i.e., requires lowercase).
 * The ``directory_format`` attribute is required for auto-detection and uses a regular expression to match with the full path of the files.
 * All facets of the ``dataset_id`` are not necessarily found in the ``directory_format``.
 * All common facets to the ``dataset_id`` and the ``directory_format`` must have the same name.
 * If a facet is missing in ``directory_format`` to allow the ``dataset_id`` filling, declare the appropriate ``facet_map``. The maptable uses the value of a declared facet to map the value of another missing facet in the ``directory_format``.
 * The missing facet has to be declared as a "destination" key (i.e., on the right of the colon).
 * Duplicated lines cannot occur in a maptable.
 * A facet has to have at least one options list or maptable.
 * A ``mapfile_drs`` attribute can be added to your project section to organize related mapfiles.
 * Make sure the ``dataset_id`` and the ``directory_format`` options reflect your directory structure accordingly.

.. note:: Feel free to submit your own ``esg.<project_id>.ini`` in order to add it to the GitHub repository and make
    it available trough ``esgprep fetch-ini`` command-line.
