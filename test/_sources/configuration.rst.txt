.. _configuration:


Configuration
=============

``esgprep`` version 3.0+ uses the ``esgvoc`` library for configuration and controlled vocabulary management.
This approach replaces the previous INI file-based configuration system with a more modern and maintainable solution.

Using esgvoc
************

The ``esgvoc`` library automatically manages:
 * Controlled vocabularies for ESGF projects
 * Project-specific Data Reference Syntax (DRS) definitions
 * Facet validation and mapping
 * Vocabulary caching and updates

No manual configuration file management is required. The library handles fetching and caching of project definitions
automatically.

Supported Projects
******************

``esgvoc`` provides built-in support for major ESGF projects, including:

 * CMIP6
 * CMIP5
 * CORDEX
 * input4MIPs
 * obs4MIPs
 * And other ESGF-approved projects

Project vocabularies are maintained in the `esgvoc repository <https://github.com/ESGF/esgvoc>`_ and automatically
synchronized when using ``esgprep``.

Checksum Configuration
**********************

``esgprep`` version 3.0+ supports both standard hashlib algorithms and multihash algorithms. **Multihash is now
the recommended checksum format for ESGF data publication**, and modern publishers will only accept multihash
formats for new submissions. SHA256 legacy format support is maintained for compatibility with existing
data.

Multihash is a self-describing hash format that includes the algorithm identifier and hash length, making it
more robust for long-term data integrity verification.

For ``esgmapfile``, you can specify the checksum algorithm using the ``--checksum-type`` option:

.. code-block:: bash

    # Standard algorithm (legacy, for compatibility)
    $> esgmapfile make --project PROJECT_ID --checksum-type sha256 /PATH/TO/SCAN/

    # Multihash algorithm (recommended for new data)
    $> esgmapfile make --project PROJECT_ID --checksum-type sha2-256 /PATH/TO/SCAN/

Supported algorithms include:

* **Standard**: sha256, sha1, md5, and other hashlib algorithms
* **Multihash**: sha2-256, sha2-512, sha3-256, sha3-512, sha1

See :ref:`mapfiles` for more details on checksum options.

Advanced Configuration
**********************

For advanced use cases or custom project definitions, please refer to the `esgvoc documentation
<https://esgf.github.io/esgf-vocab/index.html>`_ for information on:

 * Adding custom project definitions
 * Modifying vocabulary mappings
 * Configuring vocabulary sources
 * Managing local vocabulary caches

Migration from INI files
*************************

If you were previously using ``esg.<project_id>.ini`` configuration files:

 * The ``esgvoc`` library replaces the functionality of ``ESGConfigParser``
 * Project definitions are now managed centrally through ``esgvoc``
 * No manual INI file management is required
 * See the :ref:`migration` guide for details on transitioning from the old system
