*************
Configuration
*************

The only conguration you have to do at least is to define the threads number under the ``[DEFAULT]`` section in the configuration INI file. Edit the ``config.ini`` to set the number of threads you want (default is 4 threads).

.. code-block:: ini

   [DEFAULT]
   threads_number = 4

The configuration file is included in the package and is in the default installation directory of your Python packages (see ``esg_mapfiles -h``). Feel free to copy it and made your own using the ``-c/--config`` option (see :ref:`usage`).

You can also define the checksum type you want in this section. MD5 or SHA256 (default) checksums are supported. Only SHA256 checksums are allowed for ESGF publication.

.. code-block:: ini

   checksum_type = SHA256


Add a new project
+++++++++++++++++

Edit the ``config.ini`` as follows:

1. Define your "project" section in brackets:

.. code-block:: ini

   [your_project]

.. warning:: The ``-p`` option directly refers to the name of "project" sections.

2. Declare all options of each facet/attribute of your *Data Reference Syntax* (DRS) following this template:

.. code-block:: ini

   facet1_options = value1, value2, value3, ...
   facet2_options = value1, value2, value3, ...
   facet3_options = value1, value2, value3, ...

3. Define the dataset identifier format. The dataset identifier is the ordered list of facets dot-separated ending with the hash-separated version.

.. code-block:: ini

   dataset_ID = facet1.facet2.facet3#version

.. note:: The frist attribute of each line of a mapfile is the master ID of the corresponding dataset. It corresponds to the ``dataset ID`` dot-separated.

4. Define the DRS tree of your project on your filesystem. The ``directory_format`` is requiered for auto-detection and uses a regular expression to match with your full files paths.

.. code-block:: ini

   directory_format = /(?P<root>[\w./-]+)/(?P<project>[\w.-]+)/(?P<facet1>[\w.-]+)/(?P<facet2>[\w.-]+)/(?P<facet3>[\w.-]+)/(?P<filename>[\w.-]+\.nc)

.. note:: Feel free to defined a new tree or file extension if necessary using all regex facilities.

.. warning:: The options prefix ("facet") must have the same name as the ``dataset_ID`` items and the ``directory_format`` variables.

