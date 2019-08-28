# -*- coding: utf-8 -*-

"""
.. module:: esgprep.fetchcv
    :platform: Unix
    :synopsis: Fetches ESGF Controlled Vocabulary.

.. moduleauthor:: Guillaume Levavasseur <glipsl@ipsl.fr>

"""

from esgprep._contexts.multiprocessing import Runner
from esgprep._utils.github import *
from esgprep.fetchcv.constants import *
from esgprep.fetchcv.context import ProcessingContext


def run(args):
    """
    Main process.

    """
    # Instantiate processing context
    with ProcessingContext(args) as ctx:
        # Instantiate the runner.
        r = Runner(ctx.processes)

        # Get results.
        _ = r.run(ctx.files, ctx)

        # Final print.
        Print.progress('\n')

        # Flush buffer.
        Print.flush()

    # Evaluate errors & exit with corresponding return code.
    if ctx.error:
        sys.exit(1)
