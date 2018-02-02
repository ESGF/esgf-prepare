.. _log:


Changelog
=========

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
