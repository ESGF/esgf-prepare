# -*- coding: utf-8 -*-

"""
.. module:: esgprep._collectors.dataset_id.py
   :platform: Unix
   :synopsis: Dataset ID collector.

.. moduleauthor:: Guillaume Levavasseur <glipsl@ipsl.fr>

"""

from esgprep._collectors import Collector
from esgprep._exceptions import NoFileFound
from esgprep._handlers.dataset_id import Dataset


class DatasetCollector(Collector):
    """
    Collector class to yield datasets ID(s).

    """

    def __init__(self, *args, **kwargs):
        super(DatasetCollector, self).__init__(*args, **kwargs)

    def __iter__(self):

        # StopIteration error means no files found in all input sources.
        try:

            # Iterate on input sources.
            for source in self.sources:

                # Instantiate Dataset object.
                source = Dataset(self.project, source)

                # Validate dataset identifier against CV.
                if source.validate():
                    # Yield dataset ID.
                    yield source

        except StopIteration:
            raise NoFileFound(self.sources)
