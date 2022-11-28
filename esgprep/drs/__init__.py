# -*- coding: utf-8 -*-

"""
.. module:: esgprep.drs
    :platform: Unix
    :synopsis: Manages the filesystem tree according to the project the Data Reference Syntax and versioning.

.. moduleauthor:: Guillaume Levavasseur <glipsl@ipsl.fr>

"""
import json
from esgprep import _STDOUT
from esgprep._contexts.multiprocessing import Runner
from esgprep._utils import load, store
from esgprep._utils.print import *
from esgprep.constants import FINAL_FRAME, FINAL_STATUS
from esgprep.drs.constants import *
from esgprep.drs.context import ProcessingContext
from esgprep.drs.context import ProcessingContext


def do_scanning(ctx):
    """
    Returns True if file scanning is necessary regarding command-line arguments

    """
    # Rescan forced from command-line.
    if ctx.rescan:
        return True

    # Rescan forced if "list" action.
    elif ctx.action == 'list':
        return True

    # Rescan forced if other action & different flags value.
    elif os.path.isfile(TREE_FILE):

        # Load results from previous run.
        reader = load(TREE_FILE)

        # Read command-line args.
        old_args = next(reader)

        # Ensure that processing context is similar to previous run.
        for k in CONTROLLED_ARGS:
            if getattr(ctx, k) != old_args[k]:
                # msg = '"{}" argument has changed: "{}" instead of "{}" -- '.format(k,
                #                                                                    getattr(ctx, k),
                #                                                                    old_args[k])
                msg = f'"{k}" argument has changed: "{getattr(ctx, k)}" instead of "{old_args[k]}" -- '
                msg += 'Rescanning files.'
                Print.warning(msg)
                return True

        return False

    else:
        return True


def run(args):
    """
    Main process.

    """
    #print("OYYY : ",args)
    quiet = args.quiet if hasattr(args, 'quiet') else False
    if quiet:
        _STDOUT.stdout_off()

    # Instantiate processing context.
    with ProcessingContext(args) as ctx:

        # Disable file scan if a previous DRS tree have generated using same context and no "list" action.
        if do_scanning(ctx):

            # Instantiate the runner.
            r = Runner(ctx.processes)

            # Get runner results.
            results = r.run(ctx.sources, ctx)

            # Final print.
            msg = f"\r{' ' * ctx.msg_length.value}"
            Print.progress(msg)
            msg = f"\r{COLORS.OKBLUE(SPINNER_DESC)} {FINAL_FRAME} {FINAL_STATUS}\n"
            Print.progress(msg)

        # Load cached DRS tree.
        else:
            reader = load(TREE_FILE)
            msg = 'Skip incoming files scan (use "--rescan" to force it) -- '
            msg += f'Using cached DRS tree from {TREE_FILE}'
            Print.warning(msg)
            _ = next(reader)
            ctx.tree = next(reader)
            results = next(reader)

        # Flush buffer
        Print.flush()

        # Get number of sources.
        ctx.nbsources = ctx.progress.value

        # Number of success (excluding errors/skipped files).
        ctx.success = len(list(filter(None, results)))

        # Rollback --commands-file value to command-line argument in any case
        ctx.tree.commands_file = ctx.commands_file

        # Backup DRS tree and context for later usage.
        store(TREE_FILE, data=[{key: ctx.__getattribute__(key) for key in CONTROLLED_ARGS},
                               ctx.tree,
                               results])
        Print.info(f'DRS tree recorded for next usage onto {TREE_FILE}.')

        # Evaluate the list of results triggering action.
        if any(results):
            # Check upgrade uniqueness
            ctx.tree.check_uniqueness()
            # Apply tree action
            ctx.tree.get_display_lengths()
            getattr(ctx.tree, ctx.action)(quiet=quiet)

            # (vérifier si les dossier "dversion" ou 'var_version" correspondant à la version à supprimer sont vide.
            #             # si empty supprimer le dossier.)
            #             # faire equivalent rmdir dans dataset_path() pour supprimer les dossiers vides
            #             # assurer qu'il n'y a pas de symlink mort.

            # remove empty folder # seems to work
            ctx.tree.rmdir()

            # ctx.tree.show(line_type='ascii-ex',level=0)
            # print(json.dumps(json.loads(ctx.tree.to_json()), indent=2))
            # print()

    # Evaluate errors & exit with corresponding return code.
    if ctx.errors.value > 0:
        sys.exit(ctx.errors.value)
