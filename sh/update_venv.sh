#!/bin/bash

# Import utils.
source $ESGPREP_HOME/sh/utils.sh

# Main entry point.
main()
{
    log "virtual environment update begins ..."

    # Activate venv.
	source $ESGPREP_HOME/sh/activate_venv.sh

    # Upgrade pip.
    if ls $ESGPREP_SRC/pip-*.tar.gz 1> /dev/null 2>&1; then
        pip install --upgrade pip --no-index --find-links $ESGPREP_SRC
    else
        pip install --upgrade pip
    fi

    # Upgrade dependencies.
    if ls $ESGPREP_SRC/esgprep-*.tar.gz 1> /dev/null 2>&1; then
        pip install --upgrade -I -r $ESGPREP_HOME/requirements.txt --no-index --find-links $ESGPREP_SRC
    else
    pip install --upgrade -I -r $ESGPREP_HOME/requirements.txt
    fi

    # Clean up.
    deactivate

    log "virtual environment update complete"
}

# Invoke entry point.
main
