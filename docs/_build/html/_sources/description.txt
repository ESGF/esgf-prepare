***********
Description
***********

The publication process of ESG-F nodes requires mapfiles. Mapfiles are text files where each line describes a file to publish. A line is composed by full file path, file size, last modification time in Unix units, the checksum and checksum type, all pipe-separated.

Security policies of computing centres that often host ESG-F data and datanodes, do not allow to easily use the esgscan_directory ESG-F command-line that is conventionally used to generate mapfiles. Moreover, this command becomes time consuming to checksums a lot of data.

*esg_mapfiles* is a flexible alternative Python command-line tool allowing you to easily generate mapfiles independently from ESG-F. This tool currently supports CMIP5 and CORDEX DRS.

Features
--------

 * Directory as input,
 * Follows and currently supports CMIP5 or CORDEX DRS,
 * Easily add another project,
 * Matching directory format to auto-detect facets mistakes, 
 * Read configuration file to check controlled vocabulary,
 * Controlled vocabulary can be add if necessary,
 * You can choose to produce one mapfile per dataset or not (in this last case you can define your mapfile name). Consequently, you can set your own "mapfile-granularity". A dataset is defined by all DRS tree before the version.
 * You can ignored unmatching files,
 * An output directory can be defined to store mapfiles,
 * Possibility to init a logger,
 * File multithreading (especially for MD5 checksums).
