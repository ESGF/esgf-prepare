#!/bin/bash

# Import utils.
source $ESGPREP_HOME/sh/utils.sh

# Main entry point.
main()
{
	export PYTHONPATH=$PYTHONPATH:$ESGPREP_HOME
	source $ESGPREP_HOME/ops/python/venv/bin/activate
}

# Invoke entry point.
main
