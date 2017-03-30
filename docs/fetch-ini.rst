.. _fetch-ini:

Fetch ESGF configuration INI files
==================================

The ESGF publishing client and most of the ESGF tools rely on configuration files of different kinds, which are the
primary means of configuring the ESGF publisher.

* The ``esg.ini`` file gathers all information needed to configure the data node for data publication (e.g., PostgreSQL access, THREDDS configuration, etc.).

* The ``esg.<project_id>.ini`` files declare all facets and allowed values according to the *Data Reference Syntax* (DRS) and the controlled vocabularies of the corresponding project.

* The ``esgcet_models_table.txt`` declares the models and their descriptions for all the projects.

* The ``<project_id>_handler.py`` are Python methods to guide the publisher in metadata harvesting.

The ``fetch-ini`` command allows you to download and configure "on the fly" preset files hosted on `a GitHub repository <https://github.com/ESGF/config/>`_.

If you prepare your data outside of an ESGF node using ``esgprep`` as a full standalone toolbox, this step
is mandatory. Keep in mind that the fetched files have to be reviewed to ensure a correct configuration
of your projects.

Download a particular esg.<project_id>.ini from GitHub
******************************************************

.. code-block:: bash

   $> esgprep fetch-ini --project <project_id> --db-password xxxx --tds-password xxxx --esgf-host <data.node.fr> --esg-root-id <institute> --esgf-index-peer <index.node.fr> --db-port <port> --db-host <host>
   YYYY/MM/DD HH:MM:SS INFO https://github.com/ESGF/config/blob/master/publisher-configs/ini/esg.<project_id>.ini --> /esg/config/esgcet/esg.<project_id>.ini
   Overwrite existing "esg.ini"? [y/N] y
   YYYY/MM/DD HH:MM:SS INFO https://github.com/ESGF/config/blob/master/publisher-configs/ini/esg.ini --> /esg/config/esgcet/esg.ini
   Root path for "<project_name>" data: /path/to/data/<project_name>
   YYYY/MM/DD HH:MM:SS INFO "thredds_dataset_roots" in "/esg/config/esgcet/esg.ini" successfully updated
   YYYY/MM/DD HH:MM:SS INFO "project_options" in "/esg/config/esgcet/esg.ini" successfully updated
   YYYY/MM/DD HH:MM:SS INFO "thredds_aggregation/file_services" in "/esg/config/esgcet/esg.ini" successfully formatted
   YYYY/MM/DD HH:MM:SS INFO https://github.com/ESGF/config/blob/master/publisher-configs/esgcet_models_table.txt --> /esg/config/esgcet/esgcet_models_table.txt
   YYYY/MM/DD HH:MM:SS INFO https://github.com/ESGF/config/blob/master/publisher-configs/handlers/ipcc5_handler.py --> /usr/local/uvcdat/2.2.0/lib/python2.7/site-packages/esgcet-2.14.6-py2.7.egg/esgcet/ipcc5_handler.py

.. note:: If a configuration file already exists you are prompted to confirm overwriting (default is "no").

.. warning:: If you choose to overwrite your existing ``esg.ini`` , you should at least provide your ``--db-password`` and ``--tds-password``. The other flags are optional if you run ``esgprep fetch-ini`` within your ESGF node (because ``esgf.properties`` includes the required information). Otherwise, all flags are required to properly configure the ``esg.ini`` (see ``esgprep fetch-ini -h``).

.. note:: ``thredds_dataset_roots``, ``project_options`` and ``thredds_aggregation/file_services`` are updated in any case depending on the project list submitted on the command-line or the available local ``esg.<project_id>.ini``.

.. note:: ``--data-root-path`` can point to a file table with the following line-syntax: ``<project_id> | <data_root_path>``. Each ``<data_root_path>`` should exist and end with the project name (e.g., /path/to/data/CMIP5). If not you are prompted to valid your choice.

Keep existing file(s) without prompt
************************************

.. code-block:: bash

   $> esgprep fetch-ini --project <project_id> -k
   YYYY/MM/DD HH:MM:SS INFO "thredds_dataset_roots" in "/esg/config/esgcet/esg.ini" successfully updated
   YYYY/MM/DD HH:MM:SS INFO "project_options" in "/esg/config/esgcet/esg.ini" successfully updated
   YYYY/MM/DD HH:MM:SS INFO "thredds_aggregation/file_services" in "/esg/config/esgcet/esg.ini" successfully formatted

Overwrite existing file(s) without prompt
*****************************************

.. code-block:: bash

   $> esgprep fetch-ini --project <project_id> -o
   YYYY/MM/DD HH:MM:SS INFO https://github.com/ESGF/config/blob/master/publisher-configs/ini/esg.<project_id>.ini --> /esg/config/esgcet/esg.<project_id>.ini
   YYYY/MM/DD HH:MM:SS INFO https://github.com/ESGF/config/blob/master/publisher-configs/ini/esg.ini --> /esg/config/esgcet/esg.ini
   YYYY/MM/DD HH:MM:SS INFO "thredds_dataset_roots" in "/esg/config/esgcet/esg.ini" successfully updated
   YYYY/MM/DD HH:MM:SS INFO "project_options" in "/esg/config/esgcet/esg.ini" successfully updated
   YYYY/MM/DD HH:MM:SS INFO "thredds_aggregation/file_services" in "/esg/config/esgcet/esg.ini" successfully formatted

.. warning:: ``-o`` and ``-k`` cannot be used simultaneously.

Download all esg.<project_id>.ini from GitHub
*********************************************

.. code-block:: bash

   $> esgprep fetch-ini -v
   YYYY/MM/DD HH:MM:SS INFO https://github.com/ESGF/config/blob/master/publisher-configs/ini/esg.projectA.ini --> /esg/config/esgcet/esg.projectA.ini
   YYYY/MM/DD HH:MM:SS INFO https://github.com/ESGF/config/blob/master/publisher-configs/ini/esg.projectB.ini --> /esg/config/esgcet/esg.projectB.ini
   Overwrite existing "esg.projectC.ini"? [y/N] y
   YYYY/MM/DD HH:MM:SS INFO https://github.com/ESGF/config/blob/master/publisher-configs/ini/esg.projectC.ini --> /esg/config/esgcet/esg.projectC.ini
   Overwrite existing "esg.ini"? [y/N] N
   YYYY/MM/DD HH:MM:SS INFO https://github.com/ESGF/config/blob/master/publisher-configs/ini/esg.ini --> /esg/config/esgcet/esg.ini
   YYYY/MM/DD HH:MM:SS INFO "thredds_dataset_roots" in "/esg/config/esgcet/esg.ini" successfully updated
   YYYY/MM/DD HH:MM:SS INFO "project_options" in "/esg/config/esgcet/esg.ini" successfully updated
   YYYY/MM/DD HH:MM:SS INFO "thredds_aggregation/file_services" in "/esg/config/esgcet/esg.ini" successfully formatted