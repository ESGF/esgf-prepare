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

    pip install -e git://github.com/IS-ENES-Data/esgf-prepare.git@master#egg=esgprep

Installation from GitHub
************************

1. Clone `our GitHub project <https://github.com/IS-ENES-Data/esgf-prepare>`_:

.. code-block:: bash

    git clone git@github.com:IS-ENES-Data/esgf-prepare.git

3. Run the ``setup.py``:

.. code-block:: bash

    cd esgf-prepare
    python setup.py install

4. The ``esgprep`` command-line is ready.


.. warning:: To run ``esgprep`` you have to be logged on filesystem hosting the data to publish.

Dependencies and requirements
*****************************

``esgprep`` uses the following basic Python libraries includes in Python 2.5+. Becareful your Python environment includes:

 * `os <https://docs.python.org/2/library/os.html>`_
 * `re <https://docs.python.org/2/library/re.html>`_
 * `sys <https://docs.python.org/2/library/sys.html>`_
 * `string <https://docs.python.org/2/library/string.html>`_
 * `logging <https://docs.python.org/2/library/logging.html>`_
 * `argparse <https://docs.python.org/2/library/argparse.html>`_
 * `datetime <https://docs.python.org/2/library/datetime.html>`_
 * `ConfigParser <https://docs.python.org/2/library/configparser.html>`_
 * `textwrap <https://docs.python.org/2/library/textwrap.html>`_
 * `functools <https://docs.python.org/2/library/functools.html>`_
 * `multiprocessing <https://docs.python.org/2/library/multiprocessing.html>`_


Please install the ``lockfile`` and ``requests`` libraries not included in most of Python distributions using the usual
PIP command-line:

.. code-block:: bash

    pip install lockfile
    pip install requests

or download and install the sources from `PyPi <https://pypi.python.org/pypi/>`_:

.. code-block:: bash

    wget https://pypi.python.org/packages/source/l/lockfile/lockfile-0.10.2.tar.gz#md5=1aa6175a6d57f082cd12e7ac6102ab15
    tar -xzvf lockfile-0.10.2.tar.gz
    cd lockfile-0.10.2/
    python setup.py install

    wget https://pypi.python.org/packages/49/6f/183063f01aae1e025cf0130772b55848750a2f3a89bfa11b385b35d7329d/requests-2.10.0.tar.gz#md5=a36f7a64600f1bfec4d55ae021d232ae
    tar -xzvf requests-2.10.0.tar.gz
    cd requests-2.10.0/
    python setup.py install
