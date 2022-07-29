# -*- coding: utf-8 -*-

"""
.. module:: esgprep._collectors.drs_path.py
   :platform: Unix
   :synopsis: DRS path collector.

.. moduleauthor:: Guillaume Levavasseur <glipsl@ipsl.fr>

"""

from esgprep._collectors import Collector
from esgprep._exceptions import NoFileFound
from esgprep._utils.path import *


class DRSPathCollector(Collector):
    """
    Collector class to yield files from a structured and versioned tree, aka DRS.

    """

    def __init__(self, *args, **kwargs):
        super(DRSPathCollector, self).__init__(*args, **kwargs)

        # Initialize default behavior to False.
        self.default = False

        # Initialize dataset path switch.
        self.dataset_parent = False

    def __iter__(self):

        # StopIteration error means no files found in all input sources.
        try:

            # Iterate on input sources.
            for source in self.sources:
                #print("SOURCE ",source)
                # Walk through each source.
                for root, dirs, filenames in os.walk(str(source), followlinks=True):
                    print(root,dirs,filenames)
                    # Instantiate path object.
                    path = Path(root)

                    # Get project from path.
                    project = get_project(path)
                    #print("COUCOU",project)
                    # Get version index.
                    idx = version_idx(project, 'directory_structure')
                    #print("INDEX",idx) # pour cmip6 .. dans directory_structure .. la version est à l'indice 10 (précisé dans le MANIFEST)
                    # When DRS version depth/level is reached, it takes priority.

                    #print(' Or on est là')
                    #print(get_drs(path).parts)
                    if len(get_drs(path).parts) == idx: # on en est à la version
                        #print("len(get_drs(path).parts) == idx",len(get_drs(path).parts),idx)
                        # Apply default behavior.
                        if self.default:
                            #  Pick up the latest existing versions for the corresponding dataset.
                            latest_version = get_versions(path)[-1]
                            #print("La latest reperé :", latest_version)
                            # Add version filter with latest version.
                            self.PathFilter.add(name='version_filter', regex='/{}'.format(latest_version.name))

                        # Remove undesired subdirectories to prune os.walk.
                        dirs[:] = [d for d in dirs if self.PathFilter('/{}'.format(d))]

                        if self.dataset_parent and self.PathFilter(root):

                            # Iterate of sub-directories.
                            for dir in dirs:

                                # Yield the version directory.
                                yield Path(root, dir)

                    elif len(get_drs(path).parts) > idx and self.dataset_parent:

                        # yield the version directory
                        yield dataset_path(path) # Lolo change to Path(...) or not

                    # Iterate on discovered sorted filenames.
                    for filename in sorted(filenames):

                        # Ensure that root path satisfies PathFilter.
                        if self.PathFilter(root):

                            # Instantiate DRSPath object.
                            path = Path(root, filename)

                            # Dereference "latest" symlink version.
                            if is_latest_symlink(path):
                                path = with_latest_target(path)

                            # Apply file filters on filename.
                            if path.is_file() and self.FileFilter(path.name):
                                # Yield DRSPath object.
                                yield path

        except StopIteration:
            raise NoFileFound(self.sources)
