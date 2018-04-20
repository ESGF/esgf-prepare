.. _installation:


Installation
============

Usual PIP installation 
**********************

.. code-block:: bash

   pip install esgprep

PIP installation from GitHub
****************************

.. code-block:: bash

   pip install -e git://github.com/ESGF/esgf-prepare.git@master#egg=esgprep

Installation from GitHub
************************

1. Clone `our GitHub project <https://github.com/ESGF/esgf-prepare>`_:

.. code-block:: bash

   git clone git://github.com/ESGF/esgf-prepare.git

2. Run the ``setup.py``:

.. code-block:: bash

   cd esgf-prepare
   python setup.py install

3. The ``esgprep`` command-line is ready.

.. warning:: To run ``esgprep`` you have to be logged into a machine which mounts the filesystem hosting the data to
   publish.

Dependencies and requirements
*****************************

Linux distribution with Python 2.6+ is required. ``esgprep`` uses the following basic Python libraries. Ensure that
your Python environment includes:

 * `argparse <https://docs.python.org/2/library/argparse.html>`_
 * `collections <https://docs.python.org/2/library/collections.html>`_
 * `datetime <https://docs.python.org/2/library/datetime.html>`_
 * `ESGConfigParser <https://pypi.python.org/pypi/ESGConfigParser>`_
 * `fnmatch <https://docs.python.org/2/library/fnmatch.html>`_
 * `getpass <https://docs.python.org/2/library/getpass.html>`_
 * `hashlib <https://docs.python.org/2/library/hashlib.html>`_
 * `importlib <https://docs.python.org/2/library/importlib.html>`_
 * `logging <https://docs.python.org/2/library/logging.html>`_
 * `multiprocessing <https://docs.python.org/2/library/multiprocessing.html>`_
 * `os <https://docs.python.org/2/library/os.html>`_
 * `pickle <https://docs.python.org/2/library/pickle.html>`_
 * `re <https://docs.python.org/2/library/re.html>`_
 * `shutil <https://docs.python.org/2/library/shutil.html>`_
 * `sys <https://docs.python.org/2/library/sys.html>`_
 * `textwrap <https://docs.python.org/2/library/textwrap.html>`_
 * `unittest <https://docs.python.org/2/library/unittest.html>`_
 * `gettext <https://docs.python.org/2/library/gettext.html>`_

Some required libraries are not included in most Python distributions. Please install them using the usual PIP command:

 * `fuzzywuzzy <https://pypi.python.org/pypi/fuzzywuzzy>`_
 * `hurry.filesize <https://pypi.python.org/pypi/hurry.filesize>`_
 * `lockfile <https://pypi.python.org/pypi/lockfile/0.12.2>`_
 * `netCDF4 <http://unidata.github.io/netcdf4-python/>`_
 * `requests <http://docs.python-requests.org/en/master/>`_
 * `tqdm <https://pypi.python.org/pypi/tqdm>`_
 * `treelib <https://pypi.python.org/pypi/treelib>`_

.. code-block:: bash

   pip install <pkg_name>
