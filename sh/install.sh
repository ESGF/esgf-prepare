#!/bin/bash

# Import utils.
source $ESGPREP_HOME/sh/utils.sh

# Main entry point.
main()
{
    log "install starts ..."

	source $ESGPREP_HOME/sh/install_python.sh
	source $ESGPREP_HOME/sh/install_venv.sh

    log "install complete"
}

# Invoke entry point.
main
