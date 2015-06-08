************
Installation
************

To execute esg_mapfiles.py you has to be logged on filesystem hosting data to publish.

Fork this GitHub project or download the Python script and its configuration file:

:download: `esg_mapfiles.py <http://dods.ipsl.jussieu.fr/glipsl/esg_mapfiles.py>`_
:download: `esg_mapfiles.ini <http://dods.ipsl.jussieu.fr/glipsl/esg_mapfiles.ini>`_

Dependencies
------------

*esg_mapfiles.py* uses the following basic Python libraries includes in Python 2.5+. Becareful your Python environment includes:
 * os, sys, re, logging
 * argparse
 * ConfigParser
 * tempfile
 * datetime
 * multiprocessing
 * shutil

Please install the *lockfile* library not inclued in most Python distributions:

.. code-block:: bash

   pip install lockfile
