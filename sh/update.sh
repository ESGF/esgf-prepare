#!/bin/bash

# Import utils.
source $ESGPREP_HOME/sh/utils.sh

# Main entry point.
main()
{
    log "update begins ..."

	source $ESGPREP_HOME/sh/update_source.sh
	source $ESGPREP_HOME/sh/update_venv.sh

    log "update complete"
}

# Invoke entry point.
main
