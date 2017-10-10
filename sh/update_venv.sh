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
    pip install --upgrade pip

    # Upgrade dependencies.
    pip install --upgrade -I -r $ESGPREP_HOME/requirements.txt

    # Clean up.
    deactivate

    log "virtual environment update complete"
}

# Invoke entry point.
main
