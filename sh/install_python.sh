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

    # Download source.
    cd $ESGPREP_HOME/ops/python/src
    wget http://www.python.org/ftp/python/$PYTHON_VERSION/Python-$PYTHON_VERSION.tgz --no-check-certificate
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
    wget http://bootstrap.pypa.io/ez_setup.py
    python ez_setup.py

    # Install & upgrade pip / virtual env.
    easy_install --prefix $ESGPREP_HOME/ops/python pip virtualenv
    pip install --upgrade pip
    pip install --upgrade virtualenv

    log "Python v"$PYTHON_VERSION" installation complete"
}

# Invoke entry point.
main
