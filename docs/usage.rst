.. _usage:

Usage and tutorials
===================

Common usage
************

Specify the project
-------------------

.. code-block:: bash

    $> esgprep <command> --project <project_id>

.. warning:: This ``--project`` argument is always required.

.. warning:: The ``--project`` is case-sensitive.


Specify a configuration directory
---------------------------------

.. code-block:: bash

    $> esgprep <command> -i /path/to/config/

Add verbosity
-------------

.. code-block:: bash

    $> esgprep <command> -v

Show help message and exit
--------------------------

.. code-block:: bash

    $> esgprep <command> -h

Use a logfile
-------------

.. code-block:: bash

    $> esgprep <command> -log /path/to/logdir
    [...]
    $> cat /path/to/logdir/esgprep-YYYYMMDD-HHMMSS-PID.log
    [...]

.. note:: The logfile directory is optional.

``esgprep fetch-ini``
*********************

Download a particular esg.<project_id>.ini from GitHub
------------------------------------------------------

.. code-block:: bash

    $> esgprep fetch-ini --project <project_id>
    YYYY/MM/DD HH:MM:SS INFO Fetching https://raw.github.com/ESGF/config/master/publisher-configs/ini/esg.<project_id>.ini...
    YYYY/MM/DD HH:MM:SS INFO Result: SUCCESSFUL
    YYYY/MM/DD HH:MM:SS INFO <project_id> added to "project_options" of ~/config/esg.ini

If a esg.<project_id> already exists you are prompted to confirm overwriting (default is "no"):

.. code-block:: bash

    $> esgprep fetch-ini --project <project_id>
    YYYY/MM/DD HH:MM:SS WARNING "esg.<project_id>.ini" already exists in ~/config

    Overwrite existing "esg.<project_id>.ini"? [y/N] y
    YYYY/MM/DD HH:MM:SS INFO Fetching https://raw.github.com/ESGF/config/master/publisher-configs/ini/esg.<project_id>.ini...
    YYYY/MM/DD HH:MM:SS INFO Result: SUCCESSFUL

Keep existing file(s) without prompt
------------------------------------

.. code-block:: bash

    $> esgprep fetch-ini --project <project_id> -k
    YYYY/MM/DD HH:MM:SS WARNING "esg.<project_id>.ini" already exists in ~/config

Overwrite existing file(s) without prompt
-----------------------------------------

.. code-block:: bash

    $> esgprep fetch-ini --project <project_id> -o
    YYYY/MM/DD HH:MM:SS WARNING "esg.<project_id>.ini" already exists in ~/config
    YYYY/MM/DD HH:MM:SS INFO Fetching https://raw.github.com/ESGF/config/devel/publisher-configs/ini/esg.<project_id>.ini...
    YYYY/MM/DD HH:MM:SS INFO Result: SUCCESSFUL

.. warning:: ``-o`` and ``-k`` cannot be used simultaneously.

Download all esg.<project_id>.ini from GitHub
---------------------------------------------

.. code-block:: bash

    $> esgprep fetch-ini -v
    YYYY/MM/DD HH:MM:SS INFO Get filenames from GitHub repository: ESGF/config
    YYYY/MM/DD HH:MM:SS INFO Fetching https://raw.github.com/ESGF/config/master/publisher-configs/ini/esg.projectA.ini...
    YYYY/MM/DD HH:MM:SS INFO Result: SUCCESSFUL
    YYYY/MM/DD HH:MM:SS INFO Fetching https://raw.github.com/ESGF/config/master/publisher-configs/ini/esg.projectB.ini...
    YYYY/MM/DD HH:MM:SS INFO Result: SUCCESSFUL
    YYYY/MM/DD HH:MM:SS INFO projectB added to "project_options" of ~/config/esg.ini
    "esg.projectC.ini" already exists in ~/config
    Overwrite existing file? [y/N] N
    [...]

``esgprep drs``
***************

.. note:: **Coming soon !**

``esgprep check-vocab``
***********************

Check the facet options
-----------------------

.. code-block:: bash

    $> esgprep check-vocab /path/to/scan --project <project_id>
    YYYY/MM/DD HH:MM:SS INFO Collecting values from INI file(s) for "product" facet...
    YYYY/MM/DD HH:MM:SS INFO Collecting values from INI file(s) for "realm" facet...
    [...]
    YYYY/MM/DD HH:MM:SS INFO Harvesting facets values from DRS tree...
    YYYY/MM/DD HH:MM:SS INFO Result: ALL USED VALUES ARE PROPERLY DECLARED.

If a used option is missing:

.. code-block:: bash

    $> esgprep check-vocab /path/to/scan --project <project_id>
    YYYY/MM/DD HH:MM:SS INFO Collecting values from INI file(s) for "product" facet...
    YYYY/MM/DD HH:MM:SS INFO Collecting values from INI file(s) for "realm" facet...
    [...]
    YYYY/MM/DD HH:MM:SS INFO Harvesting facets values from DRS tree...
    YYYY/MM/DD HH:MM:SS INFO institute facet - UNDECLARED values: INPE
    YYYY/MM/DD HH:MM:SS INFO institute facet - UPDATED values to declare: ICHEC, CCCma, LASG, INPE, BNU, BCC, MIROC, CNRM-CERFACS, NASA-GMAO, MOHC, CAWCR, IPSL, CSIRO, MRI, CMCC, FIO, INM, NASA-GISS, NSF-DOE-NCAR, NOAA-GFDL, DOE-COLA-CMMAP-GMU, NCAR, NCC, NIMR-KMA, NICAM
    YYYY/MM/DD HH:MM:SS INFO ensemble facet - UNDECLARED values: r5i1p1
    YYYY/MM/DD HH:MM:SS INFO ensemble facet - UPDATED values to declare: r1i1p1, r5i1p1, r0i0p0
    YYYY/MM/DD HH:MM:SS ERROR Result: THERE WERE UNDECLARED VALUES USED.

Verbose output:

.. code-block:: bash

    $> esgprep check-vocab /path/to/scan --project <project_id> -v
    YYYY/MM/DD HH:MM:SS INFO Collecting values from INI file(s) for "product" facet...
    YYYY/MM/DD HH:MM:SS INFO Collecting values from INI file(s) for "realm" facet...
    [...]
    YYYY/MM/DD HH:MM:SS INFO Harvesting facets values from DRS tree...
    YYYY/MM/DD HH:MM:SS INFO product facet - Declared values: output2, output1
    YYYY/MM/DD HH:MM:SS INFO product facet - Used values: output1
    YYYY/MM/DD HH:MM:SS INFO product facet - Unused values: output2
    YYYY/MM/DD HH:MM:SS INFO realm facet - Declared values: seaIce, land, landIce, atmosChem, ocean, atmos, aerosol, ocnBgchem
    YYYY/MM/DD HH:MM:SS INFO realm facet - Used values: seaIce, land, landIce, ocean, atmos, ocnBgchem
    YYYY/MM/DD HH:MM:SS INFO realm facet - Unused values: atmosChem, aerosol
    YYYY/MM/DD HH:MM:SS INFO Result: ALL USED VALUES ARE PROPERLY DECLARED.

``esgprep mapfile``
*******************

.. note:: All the following examples can be combined safely.

Default mapfile generation
--------------------------

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
-------------------------------

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
----------------------------

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
-------------------------

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
----------------------

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
----------------------

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
-----------------------------------------

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
-----------------------------------------

.. warning:: By default ``esgprep mapfile`` pick up the latest version only.

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
----------------------------

.. warning:: This disables ``--no-version``.

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
-------------------

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
----------------------------

.. note:: ``--max-threads`` set to one corresponds to a sequential file processing.

.. code-block:: bash

    $> esgprep mapfile /path/to/scan --project <project_id> --max-threads <integer>

Overwrite the dataset identifier
--------------------------------

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
