.. _configuration:


Configuration
=============

``esgscan_directory`` works with `the configuration file(s) of ESGF nodes <https://github.com/ESGF/esgf.github.io/wiki/ESGF_Project_Configuration>`_. Samples of the configuration file(s) can be found here: **GitHub repo**. Feel free to copy them and made your own using the ``-i`` option (see :ref:`usage`).

The only conguration you have to do at least is to define the checksum client and checksum type under the ``[default]`` section in the ``esg.ini`` file. Edit the file to set the Shell command line to use (default is ``sha256sum``)

.. code-block:: ini

   [default]
   checksum = sha256sum | SHA256

The configuration file(s) provided by the ESGF installation is ready for CMIP5 and CORDEX mapfiles. The ``projet:cmip5`` and ``project:cordex`` sections are already declared. Just make sure the ``dataset_id`` and the ``directory_format`` options reflect your directory structure.

Add a new project
*****************

1. Edit the ``esg.ini`` and add your project ``project_options`` list:

.. code-block:: ini

   project_options =
      project_id | project name | rank

.. note::
    * The project identifier is typically the same as the lowercase project name.
    * The project rank is just an incremented integer.

2. Edit the ``esg.ini`` or the ``esg.<project_id>.ini`` and define your project section in brackets:

.. code-block:: ini

   [project:project_id]

.. warning:: The ``--project`` argument of ``esgscan_directory`` directly refers to the ``project_id`` (i.e., requires lowercase).

3. Declare the template of the dataset identifier:

.. code-block:: ini

   [project:project_id]
   dataset_id = project_id.%(facet1)s.%(facet2)s.%(facet3)s.[...]

.. note::
    * The frist value of each line of a mapfile is the dataset identifier.
    * It corresponds to a string of dot-separated INI variables defining the facets used to build the identifier.

.. warning:: A variable in the ESGF configuration file(s) is set with the regular expression ``%(...)s``.

4. Define the DRS tree of your project on your file system. The ``directory_format`` is required for auto-detection and uses a regular expression to match with the full path of the files:

.. code-block:: ini

   [project:project_id]
   dataset_id = project_id.%(facet1)s.%(facet2)s.%(facet3)s.%(facet4)s[...]
   directory_format = %(root)s/%(project)/%(facet1)s/%(facet3)s/%(facet4)s/[...]

.. note:: All facets of the ``dataset_id`` are not necessarily found in the ``directory_format`` (e.g., ``facet2`` here)

.. warning:: All common facets to the ``dataset_id`` and the ``directory_format`` must have the same name.

5. Declare all the required ``facet_options`` of the *Data Reference Syntax* (DRS) of your project following this template:

.. code-block:: ini

   [project:project_id]
   facet1_options = value1, value2, value3, ...
   facet3_options = value1, value2, value3, ...
   facet4_options = value1, value2, value3, ...

6. If a facet is missing in ``directory_format`` to allow the ``dataset_id`` filling, declare the appropriate ``facet_map`` as follows:

.. code-block:: ini

   [project:project_id]
   facet_map = map(facet4 : facet2)
   value4-1 | value2-1
   value4-2 | value2-2
   value4-3 | value2-3

.. note:: The maptable uses the value of a declared facet to map the value of another missing facet in the ``directory_format``.

.. warning::
    * The missing facet has to be declared as a "destination" key (i.e., on the right of the colon).
    * Duplicated lines cannot occur in a maptable.
    * A facet has to have at least one options list or maptable.

7. Define a mapfile DRS to easily manage your mapfiles. The ``mapfile_drs`` is required to build the corresponding tree as follows:

.. code-block:: ini

   [project:project_id]
   mapfile_drs = %(project)/%(facet1)s/%(facet3)s/%(facet4)s/[...]

.. note:: All the facets can be use as token to define the mapfile DRS.

.. warning:: All the facets must have the same name as the ``dataset_id`` and/or the ``directory_format``.
