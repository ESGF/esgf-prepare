#!/bin/bash

# Import utils.
source $ESGPREP_HOME/sh/utils.sh

# Main entry point.
main()
{
    # Set paths.
    export PATH=$ESGPREP_HOME/ops/python/bin:$PATH
    export PYTHONPATH=$ESGPREP_HOME/ops/python/bin:$PYTHONPATH

    # Upgrade pip/virtualenv.
    pip install --upgrade pip
    pip install --upgrade virtualenv

    # Create venv.
    rm -rf $ESGPREP_HOME/ops/python/venv
    mkdir -p $ESGPREP_HOME/ops/python/venv
    virtualenv -q $ESGPREP_HOME/ops/python/venv

    # Activate venv.
    source $ESGPREP_HOME/ops/python/venv/bin/activate

    # Install dependencies.
    pip install -r $ESGPREP_HOME/requirements.txt

    # Clean up.
    deactivate

    log "installed virtual environment"
}

# Invoke entry point.
main
