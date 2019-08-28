# -*- coding: utf-8 -*-

"""
.. module:: esgprep.checkvocab
    :platform: Unix
    :synopsis: Checks DRS vocabulary against CV.

.. moduleauthor:: Guillaume Levavasseur <glipsl@ipsl.fr>

"""

from esgprep._contexts.multiprocessing import Runner
from esgprep._utils.print import *
from esgprep.checkvocab.constants import *
from esgprep.checkvocab.context import ProcessingContext
from esgprep.constants import FINAL_FRAME, FINAL_STATUS


def run(args):
    """
    Main process.

    """
    # Instantiate processing context
    with ProcessingContext(args) as ctx:
        # Instantiate the runner.
        r = Runner(ctx.processes)

        # Get results.
        results = r.run(ctx.sources, ctx)

        # Final print.
        msg = '\r{}'.format(' ' * ctx.msg_length.value)
        Print.progress(msg)
        msg = '\r{} {} {}\n'.format(COLORS.OKBLUE(SPINNER_DESC), FINAL_FRAME, FINAL_STATUS)
        Print.progress(msg)

        # Flush buffer
        Print.flush()

        # Get number of sources (without "Completed" step).
        ctx.nbsources = ctx.progress.value

        # Number of success (excluding errors/skipped files).
        ctx.success = sum(filter(None, results))

    # Evaluate errors & exit with corresponding return code.
    if ctx.errors.value > 0:
        sys.exit(ctx.errors.value)
