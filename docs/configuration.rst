*************
Configuration
*************

Edit the esg_mapfiles.ini to set the number of threads you want (default is 4 threads).

.. code-block:: ini

   [DEFAULT]
   threads_number = 4

Add a new project
-----------------

To add a supported project, just add a new project section in your configuration file. The options prefix (called *facet* in the following template) must have the same name as *dataset_ID* items and *directory_format* variables.

*dataset_ID* items correspond to a sorted list of facets defining dataset master ID.

The *directory_format* option defines the DRS of your project using a regex to match with your full files paths. Feel free to defined a new tree or file extension 
if necessary using all regex facilities.

Follow this template:

.. code-block:: ini

   [your_project]
   facet1_options = value1, value2, ...
   facet2_options = value1, value2, ...
   facet3_options = value1, value2, ...
   dataset_ID = facet1, facet2, facet3
   directory_format = /(?P<root>[\w./-]+)/(?P<project>[\w.-]+)/(?P<facet1>[\w.-]+)/(?P<facet2>[\w.-]+)/(?P<facet3>[\w.-]+)/(?P<filename>[\w.-]+\.nc)
