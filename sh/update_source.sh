#!/bin/bash

# Import utils.
source $ESGPREP_HOME/sh/utils.sh

# Main entry point.
main()
{
    log "source code update begins ..."

    # Install dependencies.
    if ls $ESGPREP_SRC/esgprep-*.tar.gz 1> /dev/null 2>&1; then
        pip install esgprep --upgrade --no-index --find-links $ESGPREP_SRC
    else
        cd $ESGPREP_HOME
        git pull
    fi


    log "source code update complete ..."
}

# Invoke entry point.
main
