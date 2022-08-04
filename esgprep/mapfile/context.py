# -*- coding: utf-8 -*-

"""
    :platform: Unix
    :synopsis: Processing context used in this module.

"""

import fnmatch

from esgprep._collectors.dataset_id import DatasetCollector
from esgprep._collectors.drs_path import DRSPathCollector
from esgprep._contexts.multiprocessing import MultiprocessingContext
from esgprep._utils.print import *
from esgprep.mapfile.constants import *


class ProcessingContext(MultiprocessingContext):
    """
    Processing context class to drive main process.

    """

    def __init__(self, args):
        super(ProcessingContext, self).__init__(args)

        # Set notes title.
        self.notes_title = self.set('tech_notes_title')

        # Set notes url.
        self.notes_url = self.set('tech_notes_url')

        # Set a fixed mapfile name.
        self.mapfile_name = self.set('mapfile')

        # Set mapfile output directory.
        self.outdir = self.set('outdir')

        # Enable/disable working mapfile cleanup.
        self.no_cleanup = self.set('no_cleanup', None)

        # Enable/disable mapfile basename display only.
        self.basename = self.set('basename')

        # Discover DRS "latest" symlink as version.
        if args.latest_symlink:
            self.version = 'latest'

        # Discover all DRS versions.
        self.all = self.set('all_versions')

        # Set mapfile counter.
        self.nbmap = 0

    def __enter__(self):
        super(ProcessingContext, self).__enter__()

        # Run mapfile directory cleanup.
        if not self.no_cleanup:
            self.clean()

        # Instantiate data collector.
        # The input source is a list directories.
        if self.directory:

            # Instantiate file collector to walk through the tree.
            self.sources = DRSPathCollector(sources=self.directory)

            # Initialize file filters.
            for regex, inclusive in self.file_filter:
                self.sources.FileFilter.add(regex=regex, inclusive=inclusive)

            # Initialize directory filter.
            self.sources.PathFilter.add(regex=self.dir_filter, inclusive=False)

            # Set version filter.
            if self.all:
                # Pick up all encountered versions by adding "/latest" exclusion
                self.sources.PathFilter.add(name='version_filter', regex='/latest', inclusive=False)
            elif self.version:
                # Pick up the specified version only (--version flag) by adding "/v{version}" inclusion
                # If --latest-symlink, --version is set to "latest"
                self.sources.PathFilter.add(name='version_filter', regex=f'/{self.version}')
            else:
                # Default behavior: pick up the latest version among encountered versions.
                self.sources.PathFilter.add(name='version_filter', regex='/latest', inclusive=False)
                self.sources.default = True

        # The input source is a list of dataset identifiers (potentially from stdin).
        else:

            # Instantiate dataset collector.
            self.sources = DatasetCollector(sources=self.dataset)

        return self

    def __exit__(self, exc_type, exc_val, traceback):

        # Summary message about mapfiles.
        if self.cmd == 'show':
            msg = '\nMapfile(s) to be generated: {}'.format(self.nbmap)
        else:
            msg = '\nMapfile(s) generated: {} (in {})'.format(self.nbmap, self.outdir)

        # All files have been successfully scanned without errors.
        if self.nbsources == self.success:
            msg = COLORS.SUCCESS(msg)

        # All files have been skipped with errors.
        elif self.nbsources == self.errors.value:
            msg = COLORS.FAIL(msg)

        # Some files have been scanned with at least one error.
        else:
            msg = COLORS.WARNING(msg)

        # Print summary
        Print.summary(msg)

        super(ProcessingContext, self).__exit__(exc_type, exc_val, traceback)

    def clean(self):
        """
        Clean directory from incomplete mapfiles.
        Incomplete mapfiles from a previous run are silently removed.

        """
        msg = 'Removing incomplete mapfiles with "{}" extension in "{}" -- '.format(WORKING_EXTENSION, self.outdir)
        msg += 'Please use "--no-cleanup" in the case of parallel "esgmapfile" instances with the same "--outdir".'
        Print.info(msg)
        Print.flush()
        for root, _, filenames in os.walk(self.outdir):
            for filename in fnmatch.filter(filenames, '*{}'.format(WORKING_EXTENSION)):
                os.remove(os.path.join(root, filename))
