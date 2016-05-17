#!/usr/bin/env python
"""
   :platform: Unix
   :synopsis: Downloads ESGF configuration files from GitHub repository.

"""


def main(args):
    """
    Main process that:

     * Instantiates processing context,
     * Creates mapfiles output directory if necessary,
     * Instantiates threads pools,
     * Copies mapfile(s) to the output directory,
     * Removes the temporary directory and its content,
     * Implements exit status values.

    :param ArgumentParser args: Parsed command-line arguments (as a :func:`argparse.ArgumentParser` class instance)

    """
    # Instantiate processing context from command-line arguments or SYNDA job dictionary
    ctx = ProcessingContext(args)
    

    logging.info('==> Scan started')
    # Start threads pool over files list in supplied directory
    # Raises exception when all processed files failed (i.e., filtered list empty)
    if not outfiles:
        if process.called == 0:
            raise Exception('No files found leading to no mapfile.')
        else:
            raise Exception('All files have been ignored or have failed leading to no mapfile.')
    # Replace mapfile working extension by final extension
    for outfile in list(set(outfiles)):
        os.rename(outfile, outfile.replace(__WORKING_EXTENSION__, __FINAL_EXTENSION__))
    logging.info('==> Scan completed ({0} file(s) scanned)'.format(process.called))
    # Non-zero exit status if any files got filtered
    if None in outfiles_all:
        logging.warning('==> Scan completed '
                        '({0} file(s) skipped)'.format(len(outfiles_all) - len(outfiles)))
        sys.exit(2)
