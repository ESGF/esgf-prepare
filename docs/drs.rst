.. _drs:

Manage local data through the DRS
=================================

``esgprep drs``
***************

The Data Reference Syntax (DRS) defines the way your data must be organised on your filesystem. This allows a proper
publication on the ESGF node. The ``drs`` command is designed to help ESGF data node managers to prepare incoming
data for publication, placing files in the DRS directory structure, and to manage multiple versions of
publication-level datasets in a way that minimises disk usage.

List the datasets related to the incoming files
***********************************************

   ``esgprep drs`` deduces the excepted DRS by scanning the incoming files against the corresponding ``esg.<project>.ini`` file.
   The DRS facets values are deduced from:
   1. The command-line using ``--set facet=value``. This flag can be used several time to set several facets values.
   2. The filename using the ``filename_format`` from the ``esg.<project>.ini``
   3. The netCDF global attributes by picking the attribute with nearest name of the facet key.

.. code-block:: bash

   $> esgprep drs list -i ~/work/esgf-config/publisher-configs/ini/ --project <project_id> /path/to/scan
   YYYY/MM/DD HH:MM:SS PM INFO ==> Scan started
   YYYY/MM/DD HH:MM:SS INFO dataset_ID1.vYYYYMMDD <-- file1.nc
   YYYY/MM/DD HH:MM:SS INFO dataset_ID1.vYYYYMMDD <-- file2.nc
   YYYY/MM/DD HH:MM:SS INFO dataset_ID2.vYYYYMMDD <-- file3.nc
   YYYY/MM/DD HH:MM:SS PM INFO [...]
   ============================================================================================================================================
                         Publication level                             Current latest   ->  Upgraded version   Files upgraded   Upgrade size
   --------------------------------------------------------------------------------------------------------------------------------------------
   <dataset_drs_path1>                                                <latest_version>  ->     <new_version>              XX                XXG
   <dataset_drs_path2>                                                <latest_version>  ->     <new_version>              XX                XXG
   [...]
   ============================================================================================================================================

.. note:: The resulting table summaries the version upgrade at the dataset level in comparison with the latest known version on the filesystem and giving the number of files to upgrade and their total size.

.. warning:: The upgraded version can be set using ``--version YYYYMMDD``.

Visualize the excepted final DRS tree
*************************************

.. code-block:: bash

   $> esgprep drs tree -i ~/work/esgf-config/publisher-configs/ini/ --project <project_id> /path/to/scan
      YYYY/MM/DD HH:MM:SS PM INFO ==> Scan started
      YYYY/MM/DD HH:MM:SS INFO dataset_ID1.vYYYYMMDD <-- file1.nc
      YYYY/MM/DD HH:MM:SS INFO dataset_ID1.vYYYYMMDD <-- file2.nc
      YYYY/MM/DD HH:MM:SS INFO dataset_ID2.vYYYYMMDD <-- file3.nc
      YYYY/MM/DD HH:MM:SS PM INFO [...]
      ============================================================================================================================================
                                                                    Upgrade DRS Tree
      --------------------------------------------------------------------------------------------------------------------------------------------
      <project>
       └── <facet1>
           └── <facet2>
               └── <...>
                   └── <...>
                       └── <...>
                           └── <...>
                               └── <...>
                                   └── <...>
                                       ├── files
                                       │   └── dYYYYMMDD
                                       │       ├── file1.nc
                                       │       ├── file2.nc
                                       │       ├── [...]
                                       ├── latest --> vYYYYMMDD
                                       └── vYYYYMMDD
                                           ├── file1.nc --> ../files/dYYYYMMDD/file1.nc
                                           ├── file2.nc --> ../files/dYYYYMMDD/file2.nc
                                           ├── [...]
      ============================================================================================================================================

.. note:: In order to save disk space, the scanned files are moved into ``files/dYYYYMMDD`` folders. The ``vYYYYMMDD`` has a symbolic links skeleton that avoid to duplicate files between two versions.

.. note:: ``esgprep drs`` compare the incoming files to the files from the latest knwon version with the same filename, using a ``sha256`` checksum. Because this could be time consuming ``--no-checksum`` allows you to only make a comparison on filenames.

.. warning:: A root path can be set to start the finale DRS from it. Use ``--root /my/drs/root``. Be careful, the finale DRS is autoamtically rebuilt from the project level.

List Unix command to apply
**************************

.. code-block:: bash

   $> esgprep drs todo -i ~/work/esgf-config/publisher-configs/ini/ --project <project_id> /path/to/scan
      YYYY/MM/DD HH:MM:SS PM INFO ==> Scan started
      YYYY/MM/DD HH:MM:SS INFO dataset_ID1.vYYYYMMDD <-- file1.nc
      YYYY/MM/DD HH:MM:SS INFO dataset_ID1.vYYYYMMDD <-- file2.nc
      YYYY/MM/DD HH:MM:SS INFO dataset_ID2.vYYYYMMDD <-- file3.nc
      YYYY/MM/DD HH:MM:SS PM INFO [...]
      ============================================================================================================================================
                                                              Unix command-lines (DRY-RUN)
      --------------------------------------------------------------------------------------------------------------------------------------------
      mkdir -p /drs/path/facet1/facet2/.../files/dYYYYMMDD
      mv /path/to/scan/file1.nc /drs/path/facet1/facet2/.../files/dYYYYMMDD/file1.nc
      mkdir -p /drs/path/facet1/facet2/.../vYYYYMMDD
      ln -s ../files/dYYYYMMDD/file1.nc /drs/path/facet1/facet2/.../vYYYYMMDD/file1.nc
      [...]
      ============================================================================================================================================

.. note:: ``todo`` action can be seen as a dry-run to check which unix commands should be apply to build the excpeted DRS.

.. warning:: At this step, no file are moved or copy to the finale DRS.

.. note:: ``esgprep drs`` allows different file migration mode. Default is to move the files from the incomping path to the finale DRS. Use ``--copy`` to make hard copies, ``--link`` to make hard links or ``--symlink`` to make symbolic links from the incoming path. We recommend to use ``--link`` and remove the incoming directory after DRS checking. This doesn't affect the symbolic link skeleton used for the dataset versioning.

Run the DRS upgrade
*******************

.. code-block:: bash

   $> esgprep drs upgrade -i ~/work/esgf-config/publisher-configs/ini/ --project <project_id> /path/to/scan
      YYYY/MM/DD HH:MM:SS PM INFO ==> Scan started
      YYYY/MM/DD HH:MM:SS INFO dataset_ID1.vYYYYMMDD <-- file1.nc
      YYYY/MM/DD HH:MM:SS INFO dataset_ID1.vYYYYMMDD <-- file2.nc
      YYYY/MM/DD HH:MM:SS INFO dataset_ID2.vYYYYMMDD <-- file3.nc
      YYYY/MM/DD HH:MM:SS PM INFO [...]
      ============================================================================================================================================
                                                              Unix command-lines
      --------------------------------------------------------------------------------------------------------------------------------------------
      mkdir -p /drs/path/facet1/facet2/.../files/dYYYYMMDD
      mv /path/to/scan/file1.nc /drs/path/facet1/facet2/.../files/dYYYYMMDD/file1.nc
      mkdir -p /drs/path/facet1/facet2/.../vYYYYMMDD
      ln -s ../files/dYYYYMMDD/file1.nc /drs/path/facet1/facet2/.../vYYYYMMDD/file1.nc
      [...]
      ============================================================================================================================================
