.. _check-vocab:

Check CV from configuration INI files
=====================================

In the case that your data already follows the appropriate directory structure, you may want to check that all
values of each facet are correctly declared in the ``esg.<project_id>.ini`` sections. The ``check-vocab`` command
allows you to easily check the configuration file attributes by scanning your data tree, and the facet values
will be derived from the directory pattern.

Alternatively, you may supply a list of dataset IDs in a text file. In this case, the ``check-vocab`` command will
perform a similar operation without scanning the file system, and the facet values will be derived from the
dataset ID pattern.

Check the facet options
***********************

The datasets IDs can be found by scanning the filesystem:

.. code-block:: bash

   $> esgprep check-vocab --directory /path/to/scan --project <project_id>
   YYYY/MM/DD HH:MM:SS INFO Collecting values from INI file(s) for "product" facet...
   YYYY/MM/DD HH:MM:SS INFO Collecting values from INI file(s) for "realm" facet...
   [...]
   YYYY/MM/DD HH:MM:SS INFO Harvesting facets values from DRS tree...
   YYYY/MM/DD HH:MM:SS INFO Result: ALL USED VALUES ARE PROPERLY DECLARED.

Or dataset IDs they can be supplied in a file:

.. code-block:: bash

   $> esgprep check-vocab --dataset-list path_of_text_file --project <project_id>
   YYYY/MM/DD HH:MM:SS INFO Collecting values from INI file(s) for "product" facet...
   YYYY/MM/DD HH:MM:SS INFO Collecting values from INI file(s) for "realm" facet...
   [...]
   YYYY/MM/DD HH:MM:SS INFO Harvesting facets values from DRS tree...
   YYYY/MM/DD HH:MM:SS INFO Result: ALL USED VALUES ARE PROPERLY DECLARED.

In this case, the file must contain one dataset ID per line. This can be
without version, or with a version suffix of the form ``.v<version>``
or ``#<version>`` which is ignored.

If a used option is missing:

.. code-block:: bash

   $> esgprep check-vocab --directory /path/to/scan --project <project_id>
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

   $> esgprep check-vocab --directory /path/to/scan --project <project_id> -v
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