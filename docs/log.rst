.. _log:


Change Log
==========

`v2.7.37 <https://github.com/ESGF/esgf-prepare/tree/v2.7.37>`__ (2018-02-14)
----------------------------------------------------------------------------

`Full
Changelog <https://github.com/ESGF/esgf-prepare/compare/v2.7.36...v2.7.37>`__

`v2.7.36 <https://github.com/ESGF/esgf-prepare/tree/v2.7.36>`__ (2018-02-06)
----------------------------------------------------------------------------

`Full
Changelog <https://github.com/ESGF/esgf-prepare/compare/v2.7.35...v2.7.36>`__

**Closed issues:**

-  Tags missing and issue with publishing CORDEX data
   `#18 <https://github.com/ESGF/esgf-prepare/issues/18>`__
-  --commands-file option is being written to the tree file
   `#17 <https://github.com/ESGF/esgf-prepare/issues/17>`__

`v2.7.35 <https://github.com/ESGF/esgf-prepare/tree/v2.7.35>`__ (2018-02-02)
----------------------------------------------------------------------------

**Closed issues:**

-  dataset\_id names
   `#15 <https://github.com/ESGF/esgf-prepare/issues/15>`__
-  use consistent delete command in "esgprep drs todo"
   `#14 <https://github.com/ESGF/esgf-prepare/issues/14>`__
-  unicode ascii conversion error in "esgprep drs tree"
   `#12 <https://github.com/ESGF/esgf-prepare/issues/12>`__
-  hard coded strings in directory\_format are ignored without warning
   in "esgprep drs"
   `#11 <https://github.com/ESGF/esgf-prepare/issues/11>`__
-  root directory stored in tree file in "esgprep drs"
   `#10 <https://github.com/ESGF/esgf-prepare/issues/10>`__
-  "tree" file breaking logging in "esgprep drs"
   `#9 <https://github.com/ESGF/esgf-prepare/issues/9>`__
-  esgprep fails to install under esgf-installer
   `#8 <https://github.com/ESGF/esgf-prepare/issues/8>`__
-  enhancement: sanity check esg.ini for mistakes
   `#7 <https://github.com/ESGF/esgf-prepare/issues/7>`__
-  UnicodeEncode Error in fetchini/main.py
   `#6 <https://github.com/ESGF/esgf-prepare/issues/6>`__
-  The esg.cmip6.ini file is blank when downloaded.
   `#5 <https://github.com/ESGF/esgf-prepare/issues/5>`__
-  version tagging
   `#4 <https://github.com/ESGF/esgf-prepare/issues/4>`__
-  string facets shouldn't need options
   `#1 <https://github.com/ESGF/esgf-prepare/issues/1>`__

**Merged pull requests:**

-  when max\_threads=1, do not create a thread pool
   `#16 <https://github.com/ESGF/esgf-prepare/pull/16>`__
   (`alaniwi <https://github.com/alaniwi>`__)
-  Changes related to --commands-file
   `#13 <https://github.com/ESGF/esgf-prepare/pull/13>`__
   (`alaniwi <https://github.com/alaniwi>`__)
-  updated pull request to include new commit
   `#2 <https://github.com/ESGF/esgf-prepare/pull/2>`__
   (`alaniwi <https://github.com/alaniwi>`__)

Untagged older changes
----------------------

+------------+---------+-------------------------------------------------------------------------------------+
| Date       | Version | Modifications                                                                       |
+============+=========+=====================================================================================+
| 2017-05-09 | 2.7     | | Major review from Alan Iwi (CEDA).                                                |
|            |         | | MAjor refactoring.                                                                |
|            |         | | Improve logger management.                                                        |
|            |         | | Improve all outputs.                                                              |
|            |         | | Improve file discovery.                                                           |
|            |         | | Remove ``esg.ini`` fetching and ``fetch-ini`` code simplified .                   |
|            |         | | Add ``--set-*``, ``--symlink`` features and ``drs`` result recording.             |
|            |         | | Add ``--no-cleanup`` features to ``mapfile`` command.                             |
|            |         | | Add filters features to ``check-vocab`` and ``mapfile`` commands.                 |
|            |         | | CMIP6 enabled.                                                                    |
+------------+---------+-------------------------------------------------------------------------------------+
| 2016-09-27 | 2.5     | | Improvement of ``fetch-ini`` command to fetch all configuration files.            |
|            |         | | Small refactoring.                                                                |
+------------+---------+-------------------------------------------------------------------------------------+
| 2016-07-22 | 2.4     | | Improvement of ``mapfile`` and ``check-vocab`` commands                           |
|            |         | | according to the 3.0 publisher release.                                           |
+------------+---------+-------------------------------------------------------------------------------------+
| 2016-07-05 | 2.1     | | Add ``-k`` option to ``fetch-ini`` command.                                       |
+------------+---------+-------------------------------------------------------------------------------------+
| 2016-07-01 | 2.0     | | Full rewriting.                                                                   |
|            |         | | Subcommands merging.                                                              |
+------------+---------+-------------------------------------------------------------------------------------+
| 2016-04-27 | 0.8     | | Mapfile management and output writing enhance for user experience.                |
+------------+---------+-------------------------------------------------------------------------------------+
| 2015-10-23 | 0.7     | | Merging ``esgscan_directory`` and ``esg_mapfiles`` features into a single tool.   |
+------------+---------+-------------------------------------------------------------------------------------+
| 2015-07-06 | 0.6     | | Free case project section.                                                        |
|            |         | | Add ``esg_mapfiles_check_vocab`` command-line.                                    |
|            |         | | Raise thread traceback.                                                           |
|            |         | | Add exit status.                                                                  |
|            |         | | Documentation completion.                                                         |
+------------+---------+-------------------------------------------------------------------------------------+
| 2015-07-06 | 0.5.3   | | Add version within master ID                                                      |
|            |         | | according to the 2.0 publisher release.                                           |
+------------+---------+-------------------------------------------------------------------------------------+
| 2015-06-25 | 0.5.2   | | Checksum type support (MD5 or SHA256).                                            |
+------------+---------+-------------------------------------------------------------------------------------+
| 2015-06-16 | 0.5.1   | | PyPi packaging.                                                                   |
+------------+---------+-------------------------------------------------------------------------------------+
| 2015-06-12 | 0.4.1   | | Sphinx documentation rewriting.                                                   |
+------------+---------+-------------------------------------------------------------------------------------+
| 2015-06-09 | 0.4     | | Add Unix wildacards support and ``--latest`` option                               |
|            |         | | to only scan latest versions.                                                     |
+------------+---------+-------------------------------------------------------------------------------------+
| 2015-03-27 | 0.3.1   | | Improve logging.                                                                  |
|            |         | | Includes developer's entry point.                                                 |
+------------+---------+-------------------------------------------------------------------------------------+
| 2015-03-10 | 0.3     | | Add ``--keep-going`` option to skipped unmatching files.                          |
|            |         | | Remove temporary directory in any case.                                           |
+------------+---------+-------------------------------------------------------------------------------------+
| 2015-02-13 | 0.2     | | Refactoring script with PEP008 convention.                                        |
|            |         | | Add configuration file.                                                           |
|            |         | | Add directory as input.                                                           |
+------------+---------+-------------------------------------------------------------------------------------+
| 2014-09-17 | 0.1     | | MD5 checksum compute by OS (Unix Shell) because of                                |
|            |         | | out memory for big data files.                                                    |
+------------+---------+-------------------------------------------------------------------------------------+