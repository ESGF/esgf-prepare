.. _concepts:

Concepts & Terminology
======================

This section explains key ESGF concepts that are essential for understanding how ``esgprep`` works.
Read this before diving into the tool-specific documentation.

.. contents:: Table of Contents
   :local:
   :depth: 2

Data Reference Syntax (DRS)
---------------------------

**What it is:**
The Data Reference Syntax (DRS) is a standardized way to organize climate data files in a hierarchical
directory structure. Each project (CMIP7, CORDEX, etc.) defines its own DRS specification.

**Why it matters:**
A consistent DRS structure enables:

- Automated data discovery across ESGF nodes
- Predictable file locations for scripts and tools
- Standardized dataset identification
- Efficient data management and versioning

**Structure example (CMIP7 - MIP-DRS7):**

.. code-block:: text

    <root>/
    └── MIP-DRS7/
        └── <mip_era>/
            └── <activity>/
                └── <organisation>/
                    └── <source>/
                        └── <experiment>/
                            └── <variant_label>/
                                └── <region>/
                                    └── <frequency>/
                                        └── <variable>/
                                            └── <branded_suffix>/
                                                └── <grid_label>/
                                                    └── <directory_date>/
                                                        └── <filename>.nc

**Concrete example:**

.. code-block:: text

    /data/
    └── MIP-DRS7/
        └── CMIP7/
            └── CMIP/
                └── IPSL/
                    └── IPSL-CM7A-LR/
                        └── historical/
                            └── r1i1p1f1/
                                └── glb/
                                    └── mon/
                                        └── tas/
                                            └── none/
                                                └── g1/
                                                    ├── d20250101/
                                                    │   └── tas_mon_IPSL-CM7A-LR_historical_r1i1p1f1_glb_g1_185001-201412.nc
                                                    └── latest -> d20250101/

**How esgprep uses it:**
``esgdrs`` reads your NetCDF files, extracts facet values from filenames and global attributes,
then organizes files into the correct DRS hierarchy.


Facets
------

**Definition:**
Facets are metadata attributes that categorize and identify datasets. Each project defines
which facets are required and their allowed values.

**Common CMIP7 facets:**

.. list-table::
   :header-rows: 1
   :widths: 25 50 25

   * - Facet
     - Description
     - Example
   * - ``mip_era``
     - MIP generation
     - CMIP7
   * - ``activity``
     - MIP activity
     - CMIP, C4MIP, AerChemMIP
   * - ``organisation``
     - Modeling center
     - IPSL, CCCma, MOHC
   * - ``source``
     - Model name
     - IPSL-CM7A-LR, CanESM6-MR
   * - ``experiment``
     - Experiment type
     - historical, 1pctCO2-bgc
   * - ``variant_label``
     - Ensemble member
     - r1i1p1f1
   * - ``region``
     - Geographic region
     - glb (global)
   * - ``frequency``
     - Temporal frequency
     - mon, day, 1hr, 6hr
   * - ``variable``
     - Variable name
     - tas, pr, tos
   * - ``grid_label``
     - Grid type
     - g1, g99

**How facets are extracted:**

.. code-block:: text

    NetCDF File
        │
        ├── Filename parsing
        │   tas_mon_IPSL-CM7A-LR_historical_r1i1p1f1_glb_g1_185001-201412.nc
        │    │   │        │          │         │    │  │
        │    │   │        │          │         │    │  └── grid_label
        │    │   │        │          │         │    └── region
        │    │   │        │          │         └── variant_label
        │    │   │        │          └── experiment
        │    │   │        └── source
        │    │   └── frequency
        │    └── variable
        │
        ├── Global attributes (NetCDF metadata)
        │   organisation = "IPSL"
        │   activity = "CMIP"
        │   mip_era = "CMIP7"
        │
        └── Command-line overrides (--set-value)

**Facet flow:**

.. code-block:: text

    Facets → Dataset ID → Directory Path → Mapfile Entry


Dataset IDs
-----------

**What they are:**
Dataset IDs are unique identifiers for datasets, constructed by joining facet values with dots,
followed by the version.

**Format (new - recommended):**

.. code-block:: text

    <project>.<facet1>.<facet2>.<facet3>...<facetN>.v<YYYYMMDD>

.. note::
   The dataset ID format is transitioning from ``#YYYYMMDD`` suffix to ``.vYYYYMMDD`` suffix.
   The new format integrates the version as part of the identifier, making it more consistent
   with directory naming conventions.

**Example (CMIP7):**

.. code-block:: text

    # New format (recommended):
    CMIP7.CMIP.IPSL.IPSL-CM7A-LR.historical.r1i1p1f1.glb.mon.tas.g1.v20250101

    # Legacy format (deprecated):
    CMIP7.CMIP.IPSL.IPSL-CM7A-LR.historical.r1i1p1f1.glb.mon.tas.g1#20250101

**Components breakdown:**

- ``CMIP7`` - MIP era
- ``CMIP`` - Activity
- ``IPSL`` - Organisation
- ``IPSL-CM7A-LR`` - Source (model)
- ``historical`` - Experiment
- ``r1i1p1f1`` - Variant label (realization, initialization, physics, forcing)
- ``glb`` - Region (global)
- ``mon`` - Frequency (monthly)
- ``tas`` - Variable (near-surface air temperature)
- ``g1`` - Grid label
- ``v20250101`` - Version (date: vYYYYMMDD)

**Why they matter:**
Dataset IDs are used in:

- ESGF search and discovery
- Mapfile generation
- Data citation
- Cross-node data replication


Versions
--------

**Purpose:**
Versions track dataset updates over time, allowing users to access specific data releases
and ensuring reproducibility of scientific analyses.

**Format:**
``vYYYYMMDD`` (e.g., ``v20250101``) for directories
``dYYYYMMDD`` (e.g., ``d20250101``) for files directory

**Version management in DRS:**

.. code-block:: text

    tas/g1/
    ├── files/
    │   ├── d20250101/
    │   │   └── tas_*.nc          (original files)
    │   └── d20250615/
    │       └── tas_*.nc          (updated files)
    │
    ├── v20250101/
    │   └── tas_*.nc -> ../files/d20250101/tas_*.nc    (symlinks)
    │
    ├── v20250615/
    │   ├── tas_001.nc -> ../files/d20250101/tas_001.nc  (unchanged, reuses old)
    │   └── tas_002.nc -> ../files/d20250615/tas_002.nc  (new version)
    │
    └── latest -> v20250615/      (always points to newest)

**Key concepts:**

- **files/ directory**: Contains actual data files organized by date
- **vYYYYMMDD/ directories**: Contain symlinks to files
- **Symlink reuse**: Unchanged files in new versions link to original files (saves disk space)
- **latest symlink**: Always points to the most recent version

**How esgprep handles versions:**

- ``esgdrs upgrade``: Creates new version directories with appropriate symlinks
- ``esgdrs latest``: Updates the ``latest`` symlink
- ``--upgrade-from-latest``: Reuses unchanged files from previous version


Mapfiles
--------

**What they are:**
Mapfiles are text files that list all files in a dataset for ESGF publication.
They serve as the input to the ESGF publication gateway.

**Format:**

.. code-block:: text

    dataset_id | file_path | size_bytes | mod_time | checksum_type=checksum_value | ...

.. note::
   The dataset ID in mapfiles is transitioning from ``#YYYYMMDD`` to ``.vYYYYMMDD`` format.
   ``esgmapfile`` generates mapfiles using the new format by default.

**Example mapfile content:**

.. code-block:: text

    CMIP7.CMIP.IPSL.IPSL-CM7A-LR.historical.r1i1p1f1.glb.mon.tas.g1.v20250101 | /data/MIP-DRS7/.../tas_mon_*.nc | 2456789012 | mod_time=1704067200.0 | checksum=abc123... | checksum_type=SHA256

**Field breakdown:**

.. list-table::
   :header-rows: 1
   :widths: 20 80

   * - Field
     - Description
   * - ``dataset_id``
     - Full dataset identifier with version (``.vYYYYMMDD`` format)
   * - ``file_path``
     - Absolute path to the file
   * - ``size_bytes``
     - File size in bytes
   * - ``mod_time``
     - File modification timestamp
   * - ``checksum``
     - File integrity hash value
   * - ``checksum_type``
     - Hash algorithm used (SHA256, SHA2-256, etc.)

**How to generate:**

.. code-block:: bash

    $> esgmapfile make --project cmip7 /data/MIP-DRS7/

**Output location:**
By default, mapfiles are written to the current directory with naming pattern:
``<dataset_id>.map``


CMOR (Climate Model Output Rewriter)
------------------------------------

**What it is:**
CMOR is a library that standardizes climate model output according to CF conventions
and project-specific requirements (CMIP7, CORDEX, etc.).

**CMOR-compliant files have:**

- Standardized variable names and units
- Required global attributes (organisation, source, etc.)
- Consistent filename conventions
- CF-compliant coordinate systems

**What esgprep expects:**

- NetCDF files processed by CMOR (or equivalent)
- Filenames following project naming conventions
- Required global attributes present
- Valid facet values in vocabularies

**Example CMOR filename (CMIP7):**

.. code-block:: text

    <variable>_<frequency>_<source>_<experiment>_<variant_label>_<region>_<grid_label>[_<time_range>].nc

    tas_mon_IPSL-CM7A-LR_historical_r1i1p1f1_glb_g1_185001-201412.nc

**Link:** `CMOR Documentation <https://cmor.llnl.gov/>`_


Controlled Vocabularies
-----------------------

**What they are:**
Controlled vocabularies (CVs) are approved lists of valid values for each facet.
They ensure consistency across all ESGF data providers.

**Managed by:**
The ``esgvoc`` library provides vocabulary access for ``esgprep``.

**Examples of controlled values (CMIP7):**

.. code-block:: text

    mip_era:      CMIP7
    activity:     CMIP, C4MIP, AerChemMIP, HighResMIP, ...
    organisation: IPSL, CCCma, MOHC, MPI-M, ...
    experiment:   historical, 1pctCO2-bgc, esm-flat10, ...
    frequency:    mon, day, 6hr, 3hr, 1hr, ...

**What happens with invalid values:**

.. code-block:: text

    $> esgdrs list --project cmip7 /data/
    ERROR: Invalid value 'invalid_experiment' for facet 'experiment'
    Valid values: historical, 1pctCO2-bgc, esm-flat10, ...

**Exploring available values:**

.. code-block:: bash

    # List all projects
    $> esgvoc list-projects

    # Get values for a specific collection
    $> esgvoc get cmip7:activity:

    # Validate a DRS path
    $> esgvoc drsvalid cmip7 directory /path/to/data

**Updating vocabularies:**

.. code-block:: bash

    $> pip install --upgrade esgvoc


Glossary
--------

.. glossary::

    CF Conventions
        Climate and Forecast conventions for NetCDF metadata standardization.

    Dataset
        A collection of files sharing the same facet values (except time range).

    DRS
        Data Reference Syntax - hierarchical directory structure for climate data.

    ESGF
        Earth System Grid Federation - distributed data infrastructure for climate science.

    Facet
        A metadata attribute that categorizes data (e.g., variable, experiment, source).

    Mapfile
        Text file listing dataset files for ESGF publication.

    MIP-DRS7
        The Data Reference Syntax specification designed for CMIP7 and future MIP projects.

    Variant Label
        Ensemble identifier in format ``r<N>i<M>p<L>f<K>`` (realization, initialization, physics, forcing).

    MIP
        Model Intercomparison Project (e.g., CMIP, CORDEX).

    Symlink
        Symbolic link - a file pointing to another file's location.

    Version
        Dataset release identifier in format ``vYYYYMMDD``.


See Also
--------

- :ref:`getting_started` - Hands-on tutorial
- :ref:`drs` - Detailed DRS command reference
- :ref:`mapfiles` - Mapfile generation guide
- `CMIP7 Data Request <https://wcrp-cmip.org/cmip7/>`_
- `ESGF Best Practices <https://acme-climate.atlassian.net/wiki/x/JADm>`_
