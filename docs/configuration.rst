.. _configuration:


Configuration
=============

``esgprep`` works with `the configuration file(s) of ESGF nodes <https://acme-climate.atlassian.net/wiki/x/JADm>`_.

The only configuration you need to do at least is to define the checksum client and checksum type under the
``[default]`` section in your ``esg.ini`` file. Edit the file to set the Shell command line to use (default is
``sha256sum``).

.. code-block:: ini

    [default]
    checksum = sha256sum | SHA256

An ``esg.ini`` sample can be used from `this GitHub repository <https://github
.com/ESGF/config/tree/devel/publisher-configs/ini>`_.

Then, preset ``esg.<project_id>.ini`` files can be downloaded from `the GitHub repository <https://github
.com/ESGF/config/tree/devel/publisher-configs/ini>`_ using ``esgprep fetch-ini``.

The directory gathering all ``.ini`` files has to be submitted using the ``-i`` option (see :ref:`usage`).

.. warning:: Make sure the ``dataset_id`` and the ``directory_format`` options reflect your directory structure
   accordingly.

If no ``esg.<project_id>.ini`` corresponds to your project you can made your own following `the ESGF Best Practices
document <https://acme-climate.atlassian.net/wiki/x/JADm>`_.

.. note:: To build your own project section:

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

