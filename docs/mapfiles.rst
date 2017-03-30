.. _mapfiles:

Generation mapfiles for ESGF publication
========================================

The publication process on the ESGF nodes requires *mapfiles*. Mapfiles are text files where each line
describes a file to publish, using the following format:
::

   dataset_ID | absolute_path | size_bytes [ | option=value ]

``mapfile`` is a flexible command-line allowing you to easily generate mapfiles, whether run on the local ESGF data node or elsewhere.

.. warning:: ``esgprep`` requires that your directory structure strictly follows the tree fixed by the project's *Data
   Reference Syntax* (DRS) **including the version facet**.


.. note:: All the following examples can be combined safely.

Default mapfile generation
**************************

.. note:: The default behavior is to pickup the latest version in the DRS.

.. warning:: This required a date version format (e.g., v20151023).

.. code-block:: bash

   $> esgprep mapfile /path/to/scan --project <project_id> -v
   YYYY/MM/DD HH:MM:SS INFO ==> Scan started
   YYYY/MM/DD HH:MM:SS INFO dataset_ID1.vYYYYMMDD <-- /path/to/scan/.../vYYYYMMDD/.../file1.nc
   YYYY/MM/DD HH:MM:SS INFO dataset_ID2.vYYYYMMDD <-- /path/to/scan/.../vYYYYMMDD/.../file2.nc
   YYYY/MM/DD HH:MM:SS INFO dataset_ID3.vYYYYMMDD <-- /path/to/scan/.../vYYYYMMDD/.../file3.nc
   YYYY/MM/DD HH:MM:SS INFO ==> Scan completed (3 files)

   $> cat dataset_ID.v*.map
   dataset_ID1.vYYYYMMDD
   dataset_ID1.vYYYYMMDD | /path/to/scan/.../vYYYYMMDD/.../file1.nc | size1 | mod_time1 | checksum1 | checksum_type=SHA256

   dataset_ID2.vYYYYMMDD.map
   dataset_ID2.vYYYYMMDD | /path/to/scan/.../vYYYYMMDD/.../file2.nc | size2 | mod_time2 | checksum2 | checksum_type=SHA256

   dataset_ID3.vYYYYMMDD.map
   dataset_ID3.vYYYYMMDD | /path/to/scan/.../vYYYYMMDD/.../file3.nc | size3 | mod_time3 | checksum3 | checksum_type=SHA256

Mapfile without files checksums
*******************************

.. note:: The ``-v`` raises the tracebacks of thread-processes (default is the "silent" mode).

.. code-block:: bash

   $> esgprep mapfile /path/to/scan --project <project_id> --no-checksum
   YYYY/MM/DD HH:MM:SS INFO ==> Scan started
   YYYY/MM/DD HH:MM:SS INFO dataset_ID1.vYYYYMMDD <-- /path/to/scan/.../vYYYYMMDD/.../file1.nc
   YYYY/MM/DD HH:MM:SS INFO dataset_ID2.vYYYYMMDD <-- /path/to/scan/.../vYYYYMMDD/.../file2.nc
   YYYY/MM/DD HH:MM:SS INFO dataset_ID3.vYYYYMMDD <-- /path/to/scan/.../vYYYYMMDD/.../file3.nc
   YYYY/MM/DD HH:MM:SS INFO ==> Scan completed (3 files)

   $> cat dataset_ID.v*.map
   dataset_ID1.vYYYYMMDD.map
   dataset_ID1.vYYYYMMDD | /path/to/scan/.../vYYYYMMDD/.../file1.nc | size1 | mod_time1

   dataset_ID2.vYYYYMMDD.map
   dataset_ID2.vYYYYMMDD | /path/to/scan/.../vYYYYMMDD/.../file2.nc | size2 | mod_time2

   dataset_ID3.vYYYYMMDD.map
   dataset_ID3.vYYYYMMDD | /path/to/scan/.../vYYYYMMDD/.../file3.nc | size3 | mod_time3

Mapfile without DRS versions
****************************

.. code-block:: bash

   $> esgprep mapfile /path/to/scan --project <project_id> --no-version
   YYYY/MM/DD HH:MM:SS INFO ==> Scan started
   YYYY/MM/DD HH:MM:SS INFO dataset_ID1.vYYYYMMDD <-- /path/to/scan/.../vYYYYMMDD/.../file1.nc
   YYYY/MM/DD HH:MM:SS INFO dataset_ID2.vYYYYMMDD <-- /path/to/scan/.../vYYYYMMDD/.../file2.nc
   YYYY/MM/DD HH:MM:SS INFO dataset_ID3.vYYYYMMDD <-- /path/to/scan/.../vYYYYMMDD/.../file3.nc
   YYYY/MM/DD HH:MM:SS INFO ==> Scan completed (3 files)

   $> cat dataset_ID.v*.map
   dataset_ID1.vYYYYMMDD.map
   dataset_ID1 | /path/to/scan/.../vYYYYMMDD/.../file1.nc | size1 | mod_time1 | checksum1 | checksum_type=SHA256

   dataset_ID2.vYYYYMMDD.map
   dataset_ID2 | /path/to/scan/.../vYYYYMMDD/.../file2.nc | size2 | mod_time2 | checksum2 | checksum_type=SHA256

   dataset_ID3.vYYYYMMDD.map
   dataset_ID3 | /path/to/scan/.../vYYYYMMDD/.../file3.nc | size3 | mod_time3 | checksum3 | checksum_type=SHA256

Mapfile name using tokens
*************************

.. warning:: If ``{dataset_id}`` is not present in the mapfile name, then all datasets will be written to a single
   mapfile, overriding the default behavior of producing ONE mapfile PER dataset.

.. note:: The extension ``.map`` is added in any case.

.. code-block:: bash

   $> esgprep mapfile /path/to/scan --project <project_id> --mapfile {dataset_id}.{job_id}
   YYYY/MM/DD HH:MM:SS INFO ==> Scan started
   YYYY/MM/DD HH:MM:SS INFO dataset_ID1.job_id <-- /path/to/scan/.../vYYYYMMDD/.../file1.nc
   YYYY/MM/DD HH:MM:SS INFO dataset_ID2.job_id <-- /path/to/scan/.../vYYYYMMDD/.../file2.nc
   YYYY/MM/DD HH:MM:SS INFO dataset_ID3.job_id <-- /path/to/scan/.../vYYYYMMDD/.../file3.nc
   YYYY/MM/DD HH:MM:SS INFO ==> Scan completed (3 files)

   $> cat dataset_ID*.job_id.map
   dataset_ID1.job_id.map
   dataset_ID1.vYYYYMMDD | /path/to/scan/.../vYYYYMMDD/.../file1.nc | size1 | mod_time1 | checksum1 | checksum_type=SHA256

   dataset_ID2.job_id.map
   dataset_ID2.vYYYYMMDD | /path/to/scan/.../vYYYYMMDD/.../file2.nc | size2 | mod_time2 | checksum2 | checksum_type=SHA256

   dataset_ID3.job_id.map
   dataset_ID3.vYYYYMMDD | /path/to/scan/.../vYYYYMMDD/.../file3.nc | size3 | mod_time3 | checksum3 | checksum_type=SHA256

   $> esgprep mapfile /path/to/scan --project <project_id> --mapfile {date}
   YYYY/MM/DD HH:MM:SS INFO ==> Scan started
   YYYY/MM/DD HH:MM:SS INFO <date> <-- /path/to/scan/.../vYYYYMMDD/.../file1.nc
   YYYY/MM/DD HH:MM:SS INFO <date> <-- /path/to/scan/.../vYYYYMMDD/.../file2.nc
   YYYY/MM/DD HH:MM:SS INFO <date> <-- /path/to/scan/.../vYYYYMMDD/.../file3.nc
   YYYY/MM/DD HH:MM:SS INFO ==> Scan completed (3 files)

   $> cat <date>.map
   dataset_ID1.vYYYYMMDD | /path/to/scan/.../vYYYYMMDD/.../file1.nc | size1 | mod_time1 | checksum1 | checksum_type=SHA256
   dataset_ID2.vYYYYMMDD | /path/to/scan/.../vYYYYMMDD/.../file2.nc | size2 | mod_time2 | checksum2 | checksum_type=SHA256
   dataset_ID3.vYYYYMMDD | /path/to/scan/.../vYYYYMMDD/.../file3.nc | size3 | mod_time3 | checksum3 | checksum_type=SHA256

To an output directory
**********************

.. code-block:: bash

   $> esgprep mapfile /path/to/scan --project <project_id> --outdir /path/to/mapfiles/
   YYYY/MM/DD HH:MM:SS INFO ==> Scan started
   YYYY/MM/DD HH:MM:SS INFO dataset_ID1.vYYYYMMDD <-- /path/to/scan/.../vYYYYMMDD/.../file1.nc
   YYYY/MM/DD HH:MM:SS INFO dataset_ID2.vYYYYMMDD <-- /path/to/scan/.../vYYYYMMDD/.../file2.nc
   YYYY/MM/DD HH:MM:SS INFO dataset_ID3.vYYYYMMDD <-- /path/to/scan/.../vYYYYMMDD/.../file3.nc
   YYYY/MM/DD HH:MM:SS INFO ==> Scan completed (3 files)

   $> cat /path/to/mapfiles/dataset_ID*.v*.map
   dataset_ID1.vYYYYMMDD.map
   dataset_ID1.vYYYYMMDD | /path/to/scan/.../vYYYYMMDD/.../file1.nc | size1 | mod_time1 | checksum1 | checksum_type=SHA256

   dataset_ID2.vYYYYMMDD.map
   dataset_ID2.vYYYYMMDD | /path/to/scan/.../vYYYYMMDD/.../file2.nc | size2 | mod_time2 | checksum2 | checksum_type=SHA256

   dataset_ID3.vYYYYMMDD.map
   dataset_ID3.vYYYYMMDD | /path/to/scan/.../vYYYYMMDD/.../file3.nc | size3 | mod_time3 | checksum3 | checksum_type=SHA256

Organize your mapfiles
**********************

.. note:: A ``mapfile_drs`` attribute can be added into the corresponding project section of the configuration files.
   In the same way as the ``directory_format`` it defines a tree depending on the facets. Each mapfile is then
   written into the corresponding output directory.

.. warning:: The ``mapfile_drs`` directory structure is added to the root output directory submitted by the flag
   ``--outdir``.

.. code-block:: bash

   $> esgprep mapfile /path/to/scan --project <project_id> --outdir /path/to/mapfiles/
   YYYY/MM/DD HH:MM:SS INFO ==> Scan started
   YYYY/MM/DD HH:MM:SS INFO dataset_ID1.vYYYYMMDD <-- /path/to/scan/.../vYYYYMMDD/.../file1.nc
   YYYY/MM/DD HH:MM:SS INFO dataset_ID2.vYYYYMMDD <-- /path/to/scan/.../vYYYYMMDD/.../file2.nc
   YYYY/MM/DD HH:MM:SS INFO dataset_ID3.vYYYYMMDD <-- /path/to/scan/.../vYYYYMMDD/.../file3.nc
   YYYY/MM/DD HH:MM:SS INFO ==> Scan completed (3 files)

   $> cat /path/to/mapfiles/facet1/facet2/facet3/dataset_ID1.vYYYYMMDD.map
   dataset_ID1.vYYYYMMDD | /path/to/scan/.../vYYYYMMDD/.../file1.nc | size1 | mod_time1 | checksum1 | checksum_type=SHA256

   $> cat /path/to/mapfiles/facet1/facet2/facet3/dataset_ID2.vYYYYMMDD.map
   dataset_ID2.vYYYYMMDD | /path/to/scan/.../vYYYYMMDD/.../file2.nc | size2 | mod_time2 | checksum2 | checksum_type=SHA256

   $> cat /path/to/mapfiles/facet1/facet2/facet3/dataset_ID3.vYYYYMMDD.map
   dataset_ID3.vYYYYMMDD | /path/to/scan/.../vYYYYMMDD/.../file3.nc | size3 | mod_time3 | checksum3 | checksum_type=SHA256


Walking through *latest* directories only
*****************************************

.. warning:: If the version is directly specified in positional argument, the version number from supplied directory
   is used.

.. code-block:: bash

   $> esgprep mapfile /path/to/scan --project <project_id> --latest-symlink
   YYYY/MM/DD HH:MM:SS INFO ==> Scan started
   YYYY/MM/DD HH:MM:SS INFO dataset_ID1.latest <-- /path/to/scan/.../latest/.../file1.nc
   YYYY/MM/DD HH:MM:SS INFO dataset_ID2.latest <-- /path/to/scan/.../latest/.../file2.nc
   YYYY/MM/DD HH:MM:SS INFO dataset_ID3.latest <-- /path/to/scan/.../latest/.../file3.nc
   YYYY/MM/DD HH:MM:SS INFO ==> Scan completed (3 files)

   $> cat dataset_ID*.latest.map
   dataset_ID1.latest.map
   dataset_ID1.vYYYYMMDD | /path/to/scan/.../latest/.../file1.nc | size1 | mod_time1 | checksum1 | checksum_type=SHA256

   dataset_ID2.latest.map
   dataset_ID2.vYYYYMMDD | /path/to/scan/.../latest/.../file2.nc | size2 | mod_time2 | checksum2 | checksum_type=SHA256

   dataset_ID3.latest.map
   dataset_ID3.vYYYYMMDD | /path/to/scan/.../latest/.../file3.nc | size3 | mod_time3 | checksum3 | checksum_type=SHA256

Walking through a particular version only
*****************************************

.. warning:: By default ``esgprep mapfile`` pick up the latest version only.

.. warning:: If the version is directly specified in positional argument, the version number from supplied directory
   is used.

.. code-block:: bash

   $> esgprep mapfile /path/to/scan --project <project_id> --version <version>
   YYYY/MM/DD HH:MM:SS INFO ==> Scan started
   YYYY/MM/DD HH:MM:SS INFO dataset_ID1.v<version> <-- /path/to/scan/.../v<version>/.../file1.nc
   YYYY/MM/DD HH:MM:SS INFO dataset_ID2.v<version> <-- /path/to/scan/.../v<version>/.../file2.nc
   YYYY/MM/DD HH:MM:SS INFO dataset_ID3.v<version> <-- /path/to/scan/.../v<version>/.../file3.nc
   YYYY/MM/DD HH:MM:SS INFO ==> Scan completed (3 files)

   $> cat dataset_ID*.v<version>.map
   dataset_ID1.v<version>.map
   dataset_ID1.v<version> | /path/to/scan/.../v<version>/.../file1.nc | size1 | mod_time1 | checksum1 | checksum_type=SHA256

   dataset_ID2.v<version>.map
   dataset_ID2.v<version> | /path/to/scan/.../v<version>/.../file2.nc | size2 | mod_time2 | checksum2 | checksum_type=SHA256

   dataset_ID3.v<version>.map
   dataset_ID3.v<version> | /path/to/scan/.../v<version>/.../file3.nc | size3 | mod_time3 | checksum3 | checksum_type=SHA256

Walking through all versions
****************************

.. warning:: This disables ``--no-version``.

.. warning:: If the version is directly specified in positional argument, the version number from supplied directory
   is used.

.. code-block:: bash

   $> esgprep mapfile /path/to/scan --project <project_id> --all-versions
   YYYY/MM/DD HH:MM:SS INFO ==> Scan started
   YYYY/MM/DD HH:MM:SS INFO dataset_ID.v1 <-- /path/to/scan/.../v1/.../file1.nc
   YYYY/MM/DD HH:MM:SS INFO dataset_ID.v1 <-- /path/to/scan/.../v1/.../file2.nc
   YYYY/MM/DD HH:MM:SS INFO dataset_ID.v2 <-- /path/to/scan/.../v2/.../file1.nc
   YYYY/MM/DD HH:MM:SS INFO ==> Scan completed (3 files)

   $> cat dataset_ID*.v\*.map
   dataset_ID.v1.map
   dataset_ID.v1 | /path/to/scan/.../v1/.../file1.nc | size1 | mod_time1 | checksum1 | checksum_type=SHA256
   dataset_ID.v1 | /path/to/scan/.../v1/.../file2.nc | size2 | mod_time2 | checksum2 | checksum_type=SHA256

   dataset_ID.v2.map
   dataset_ID.v2 | /path/to/scan/.../v2/.../file3.nc | size3 | mod_time3 | checksum3 | checksum_type=SHA256

Add technical notes
*******************

.. code-block:: bash

   $> esgprep mapfile /path/to/scan --project <project_id> --tech-notes-url <url> --tech-notes-title <title>
   YYYY/MM/DD HH:MM:SS INFO ==> Scan started
   YYYY/MM/DD HH:MM:SS INFO dataset_ID.vYYYYMMDD <-- /path/to/scan/.../vYYYYMMDD/.../file1.nc
   YYYY/MM/DD HH:MM:SS INFO dataset_ID.vYYYYMMDD <-- /path/to/scan/.../vYYYYMMDD/.../file2.nc
   YYYY/MM/DD HH:MM:SS INFO dataset_ID.vYYYYMMDD <-- /path/to/scan/.../vYYYYMMDD/.../file1.nc
   YYYY/MM/DD HH:MM:SS INFO ==> Scan completed (3 files)

   $> cat dataset_ID*.vYYYYMMDD.map
   dataset_ID.vYYYYMMDD | /path/to/scan/.../vYYYYMMDD/.../file1.nc | size1 | mod_time1 | checksum1 | checksum_type=SHA256 | dataset_tech_notes=<url> | dataset_tech_notes_title=<title>
   dataset_ID.vYYYYMMDD | /path/to/scan/.../vYYYYMMDD/.../file2.nc | size2 | mod_time2 | checksum2 | checksum_type=SHA256 | dataset_tech_notes=<url> | dataset_tech_notes_title=<title>
   dataset_ID.vYYYYMMDD | /path/to/scan/.../vYYYYMMDD/.../file3.nc | size3 | mod_time3 | checksum3 | checksum_type=SHA256 | dataset_tech_notes=<url> | dataset_tech_notes_title=<title>

Change the number of threads
****************************

.. note:: ``--max-threads`` set to one corresponds to a sequential file processing.

.. code-block:: bash

   $> esgprep mapfile /path/to/scan --project <project_id> --max-threads <integer>

Overwrite the dataset identifier
********************************

.. note:: All files will belong to the specified dataset, regardless of the DRS.

.. code-block:: bash

   $> esgprep mapfile /path/to/scan --project <project_id> --dataset <dataset_ID_test>
   YYYY/MM/DD HH:MM:SS INFO ==> Scan started
   YYYY/MM/DD HH:MM:SS INFO dataset_ID_test <-- /path/to/scan/.../vYYYYMMDD/.../file1.nc
   YYYY/MM/DD HH:MM:SS INFO dataset_ID_test <-- /path/to/scan/.../vYYYYMMDD/.../file2.nc
   YYYY/MM/DD HH:MM:SS INFO dataset_ID_test <-- /path/to/scan/.../vYYYYMMDD/.../file1.nc
   YYYY/MM/DD HH:MM:SS INFO ==> Scan completed (3 files)

   $> cat dataset_ID_test.map
   dataset_ID_test | /path/to/scan/.../vYYYYMMDD/.../file1.nc | size1 | mod_time1 | checksum1 | checksum_type=SHA256
   dataset_ID_test | /path/to/scan/.../vYYYYMMDD/.../file2.nc | size2 | mod_time2 | checksum2 | checksum_type=SHA256
   dataset_ID_test | /path/to/scan/.../vYYYYMMDD/.../file3.nc | size3 | mod_time3 | checksum3 | checksum_type=SHA256
