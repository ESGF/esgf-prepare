#!/bin/bash

# Import utils.
source $ESGPREP_HOME/sh/utils.sh

# Main entry point.
main()
{
    # Set variables.
    declare PYTHON_VERSION_SHORT=2.7
    declare PYTHON_VERSION=2.7.14

    log "Python v"$PYTHON_VERSION" installation begins ..."

    # Reset.
    rm -rf $ESGPREP_HOME/ops/python
    mkdir -p $ESGPREP_HOME/ops/python/src

    # Get source.
    cd $ESGPREP_HOME/ops/python/src
    if [ -f "$ESGPREP_HOME/requirements/Python-$PYTHON_VERSION.tgz" ]; then
        cp $ESGPREP_HOME/requirements/Python-$PYTHON_VERSION.tgz .
    else
        wget http://www.python.org/ftp/python/$PYTHON_VERSION/Python-$PYTHON_VERSION.tgz --no-check-certificate
    fi
    tar -xvf ./Python-$PYTHON_VERSION.tgz

    # Compile.
    cd Python-$PYTHON_VERSION
    ./configure --prefix=$ESGPREP_HOME/ops/python
    make
    make install

    # Update paths.
    export PATH=$ESGPREP_HOME/ops/python/bin:$PATH
    export PYTHONPATH=$ESGPREP_HOME/ops/python/bin:$PYTHONPATH
    export PYTHONPATH=$ESGPREP_HOME/ops/python/lib/python$PYTHON_VERSION_SHORT/site-packages:$PYTHONPATH

    # Install setuptools.
    cd $ESGPREP_HOME/ops/python/src
    if [ -f "$ESGPREP_HOME/sources/ez_setup.py" ]; then
        cp $ESGPREP_HOME/sources/ez_setup.py .
    else
        wget http://bootstrap.pypa.io/ez_setup.py
    fi
    python ez_setup.py

    # Install & upgrade pip / virtual env.
    if ls $ESGPREP_HOME/requirements/pip-*.tar.gz 1> /dev/null 2>&1; then
        cp $ESGPREP_HOME/requirements/pip-*.tar.gz .
        pip install --upgrade pip --no-index --find-links $ESGPREP_HOME/requirements
    else
        easy_install --prefix $ESGPREP_HOME/ops/python pip virtualenv
        pip install --upgrade pip
    fi

    if ls $ESGPREP_HOME/requirements/virtualenv-*.tar.gz 1> /dev/null 2>&1; then
        cp $ESGPREP_HOME/requirements/virtualenv-*.tar.gz .
        pip install --upgrade virtualenv --no-index --find-links $ESGPREP_HOME/requirements

    else
        pip install --upgrade virtualenv
    fi

    log "Python v"$PYTHON_VERSION" installation complete"
}

# Invoke entry point.
main
