************
Installation
************

Usual PIP installation 
++++++++++++++++++++++

.. code-block:: bash

  pip install esgmapfiles

PIP installation from GitHub
++++++++++++++++++++++++++++

.. code-block:: bash

  pip install -e git://github.com/Prodiguer/esgf-mapfiles.git@master#egg=esgmapfiles

Installation from GitHub
++++++++++++++++++++++++

1. Create a new directory:

.. code-block:: bash

  mkdir esgmapfiles
  cd esgmapfiles

2. Clone `our GitHub project <https://github.com/Prodiguer/esgf-mapfiles>`_:

.. code-block:: bash

  git init
  git clone git@github.com:Prodiguer/esgf-mapfiles.git

3. Run the ``setup.py``:

.. code-block:: bash

  python setup.py install

4. The ``esg_mapfile`` command-line is ready.


.. warning:: To run ``esg_mapfiles`` you have to be logged on filesystem hosting the data to publish.

Dependencies
++++++++++++

``esg_mapfiles`` uses the following basic Python libraries includes in Python 2.5+. Becareful your Python environment includes:

 * `os <https://docs.python.org/2/library/os.html>`_, `sys <https://docs.python.org/2/library/sys.html>`_, `re <https://docs.python.org/2/library/re.html>`_, `logging <https://docs.python.org/2/library/logging.html>`_
 * `argparse <https://docs.python.org/2/library/argparse.html>`_
 * `ConfigParser <https://docs.python.org/2/library/configparser.html>`_
 * `tempfile <https://docs.python.org/2/library/tempfile.html>`_
 * `datetime <https://docs.python.org/2/library/datetime.html>`_
 * `functools <https://docs.python.org/2/library/functools.html>`_
 * `multiprocessing <https://docs.python.org/2/library/multiprocessing.html>`_
 * `shutil <https://docs.python.org/2/library/shutil.html>`_

Please install the ``lockfile`` library not inclued in most Python distributions using the usual PIP command-line:

.. code-block:: bash

   pip install lockfile

or download and intall the `sources from PyPi <https://pypi.python.org/pypi/lockfile>`_:

.. code-block:: bash

  wget https://pypi.python.org/packages/source/l/lockfile/lockfile-0.10.2.tar.gz#md5=1aa6175a6d57f082cd12e7ac6102ab15
  tar -xzvf lockfile-0.10.2.tar.gz 
  cd lockfile-0.10.2/
  python setup.py install
