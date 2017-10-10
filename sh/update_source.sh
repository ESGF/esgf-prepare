#!/bin/bash

# Import utils.
source $ESGPREP_HOME/sh/utils.sh

# Main entry point.
main()
{
    log "source code update begins ..."

    cd $ESGPREP_HOME
    git pull

    log "source code update complete ..."
}

# Invoke entry point.
main
