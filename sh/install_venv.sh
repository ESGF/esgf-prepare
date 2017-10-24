#!/bin/bash

# Import utils.
source $ESGPREP_HOME/sh/utils.sh

# Main entry point.
main()
{
    # Set paths.
    export PATH=$ESGPREP_HOME/ops/python/bin:$PATH
    export PYTHONPATH=$ESGPREP_HOME/ops/python/bin:$PYTHONPATH

    # Upgrade pip.
    if ls $ESGPREP_SRC/pip-*.tar.gz 1> /dev/null 2>&1; then
        pip install --upgrade pip --no-index --find-links $ESGPREP_SRC
    else
        pip install --upgrade pip
    fi

    # Upgrade virtualenv.
    if ls $ESGPREP_SRC/virtualenv-*.tar.gz 1> /dev/null 2>&1; then
        pip install --upgrade virtualenv --no-index --find-links $ESGPREP_SRC
    else
        pip install --upgrade virtualenv
    fi

    # Create venv.
    rm -rf $ESGPREP_HOME/ops/python/venv
    mkdir -p $ESGPREP_HOME/ops/python/venv
    virtualenv -q $ESGPREP_HOME/ops/python/venv

    # Activate venv.
    source $ESGPREP_HOME/ops/python/venv/bin/activate

    # Install dependencies.
    if ls $ESGPREP_SRC/esgprep-*.tar.gz 1> /dev/null 2>&1; then
        pip install esgprep --no-index --find-links $ESGPREP_SRC
    else
        pip install -r $ESGPREP_HOME/requirements.txt
    fi

    # Clean up.
    deactivate

    log "installed virtual environment"
}

# Invoke entry point.
main
