# -*- coding: utf-8 -*-

"""
    :platform: Unix
    :synopsis: Manages the filesystem tree according to the project the Data Reference Syntax and versioning.

"""
from esgprep.constants import FRAMES, FINAL_FRAME, FINAL_STATUS
from collections import namedtuple
from multiprocessing import Pool
import traceback
import signal
from esgprep._exceptions import *
from esgprep._utils.ncfile import drs_path, get_tracking_id, get_ncattrs
from esgprep._utils.path import *
from esgprep._handlers.drs_tree import DRSTree
from esgprep._utils import load, store
from esgprep._utils.checksum import get_checksum
from esgprep._utils.print import *
from esgprep.drs.constants import *
from esgprep.drs.context import ProcessingContext
from esgprep import _STDOUT


def process(source):
    """
    Child process.
    Any error switches to the next child process.
    It does not stop the main process at all.

    """
    # Get process content from process global env
    assert 'pctx' in globals().keys()
    pctx = globals()['pctx']

    # Escape in case of error.
    try:

        # Si remove/latest
        # source est un DRSPath validé
        # comme mapfile ? > renvoie une fichier only
        # but : trouver dans "--root" la version correspondante
        # checker exister
        # ici doit renvoyé le "publication-level" > dataset_path()

        # Si remove
        # "scanner" le dataset_path() pour reconstruire l'arbre -> DRSTree
        # repérérer la version à supprimer puis agir à l'intérieure POUR CHAQUE FICHIER
        # principle -> si fichier != symlink => supprimer fichier sans autre action
        # -> si fichier symlink anaylser le lien:
        # --> le symlink pointe toujours vers [..]/files/[..]/...nc
        # --> obtenir la cible des symlink équivalent des versions précédente et suivante (si elles existent)

        # if suivante & précédentes ==> les trois versions existent
            # if target(suivante) = target(précédente) ==> les trois target sont identique (à checker avec assert)
                # --> supprimer symlink
                # --> ne pas supprimer la cible dans files car pointée par les autres versions
            # elif target(précédente) = target(courant) ==> la cible à supprimer et lié à la précédente version

            # elif target(suivante) = target(courant) ==> la cible à supprimer et lié à la suivante version

            # else: ==> les cibles des trois versions sont différentes
                # --> supprimer symlink
                # --> supprimer la cible dans files car pointée par AUCUNE autre version
        # elif précédente ==> seule la version à supprimer et la précédente existent

        # elif suivante ==> seule la version à supprimer et la suivante existent

        # else: = seule la version à supprimer existent
            # --> supprimer symlink
            # --> supprimer la cible dans files car pointée par AUCUNE autre version
        # checker le latest -> appeler le process du subparser "latest"

        # supprimer le dossier "vYYYYMMDD"

        # (vérifier si les dossier "dversion" ou 'var_version" correspondant à la version à supprimer sont vide.
        # si empty supprimer le dossier.)
        # faire equivalent rmdir dans dataset_path() pour supprimer les dossiers vides
        # assurer qu'il n'y a pas de symlink mort.






        # Si latest
        # faire un os.readlink("latest"
        # checker target = latest version
        # voir script ad-hoc
        # généré le DRSTree associé avec uniquement des DRSLeak "latest symlink"

        # supprimer en replaçant les liens des fichiers et du latest.

        # Ignore files from incoming
        if source.name in pctx.ignore_from_incoming:
            msg = TAGS.SKIP + COLORS.HEADER(str(source))
            with pctx.lock:
                Print.exception(msg, buffer=True)
            return None

        # Print info.
        msg = 'Scanning {}'.format(source)
        Print.debug(msg)

        # Get current file attributes.
        current_attrs = get_ncattrs(source)
        # Add filename to attributes.
        current_attrs['filename'] = source.name
        # Add dataset-version to attributes.
        current_attrs['dataset-version'] = tree.drs_version

        # Instantiate file as no duplicate.
        is_duplicate = False

        # Build directory structure.
        # DRS terms are validated during this step.
        try:
            current_path = Path(pctx.root, drs_path(current_attrs, pctx.set_values, pctx.set_keys), source.name)
        except TypeError:
            Print.debug('Directory structure is None')
            return False

        # Instantiate latest version to "Initial"
        latest_version = 'Initial'

        # Get latest existing version of the file.
        latest_path = with_latest_version(current_path)

        # 1. Check if a latest file version exists (i.e. with the same filename).
        if latest_path and latest_path.exists():

            # 2. Check latest version is older than current version.
            current_version = get_version(current_path)
            latest_version = get_version(latest_path)
            if latest_version < current_version:
                raise OlderUpgrade(current_version, latest_version)

            # Get latest file version attributes.
            latest_attrs = get_ncattrs(latest_path)

            # 3. Check tracking IDs are different.
            current_tracking_id = get_tracking_id(current_attrs)
            latest_tracking_id = get_tracking_id(latest_attrs)
            if current_tracking_id == latest_tracking_id:

                # 4. Check if file sizes are different.
                if current_path.stat().st_size == latest_path.stat().st_size and not pctx.no_checksum:

                    # 5. Check if file checksums are different.
                    current_checksum = get_checksum(current_path, pctx.checksum_type, pctx.checksums_from)
                    latest_checksum = get_checksum(latest_path, pctx.checksum_type, pctx.checksums_from)
                    if current_checksum == latest_checksum:

                        # Flags file to duplicate.
                        is_duplicate = True

                    # If different checksums, tracking IDs must be different too if exist.
                    elif current_tracking_id and latest_tracking_id:
                        raise UnchangedTrackingID(latest_path, latest_tracking_id, current_path, current_tracking_id)

                # If different sizes, tracking IDs must be different too if exist.
                elif current_tracking_id and latest_tracking_id:
                    raise UnchangedTrackingID(latest_path, latest_tracking_id, current_path, current_tracking_id)

        # Print info.
        Print.debug('Processing {}'.format(source))

        # Start DRS tree generation.
        if not is_duplicate:

            # Add the current file to the "vYYYYMMDD" folder.
            src = ['..'] * len(get_drs_down(current_path).parts)
            src.append('files')
            src += get_drs_down(with_file_folder(current_path)).parts
            tree.create_leaf(nodes=current_path.parts,
                             label='{}{}{}'.format(current_path.name, LINK_SEPARATOR, os.path.join(*src)),
                             src=os.path.join(*src),
                             mode='symlink',
                             force=True)

            # Add the "latest" symlink node.
            nodes = list(dataset_path(current_path).parent.parts)
            nodes.append('latest')
            tree.create_leaf(nodes=nodes,
                             label='{}{}{}'.format('latest', LINK_SEPARATOR, tree.drs_version),
                             src=tree.drs_version,
                             mode='symlink')

            # Add the current file to the "files" folder.
            tree.create_leaf(nodes=with_file_folder(current_path).parts,
                             label=current_path.name,
                             src=current_path,
                             mode=pctx.mode)

            # If latest file version exist and --upgrade-from-latest submitted.
            if latest_path and latest_path.exists() and pctx.upgrade_from_latest:

                # Walk through the latest dataset version.
                # Create a symlink for each file with a different filename than the current one
                for root, _, filenames in os.walk(latest_path):
                    for latest_name in filenames:

                        # Add latest files as tree leaves with version to upgrade instead of latest version
                        # i.e., copy latest dataset leaves to the current tree.
                        # Except if file has be ignored from latest version (i.e., with known issue)
                        # Except if file leaf has already been created to avoid overwriting new version
                        # Leaf is not created if already exists (i.e., force = False).
                        if latest_name != current_path.name and latest_name not in pctx.ignore_from_latest:
                            src = os.path.join(root, latest_name)
                            tree.create_leaf(nodes=current_path.parent.parts.append(latest_name),
                                             label='{}{}{}'.format(latest_name, LINK_SEPARATOR, os.readlink(src)),
                                             src=os.readlink(src),
                                             mode='symlink')

        # In the case of the file is duplicated.
        # i.e., incoming file already exists in the latest version folder.
        else:

            # If upgrade from latest is activated, raise the error, no duplicated files allowed.
            # Incoming must only contain modifed/corrected files.
            if pctx.upgrade_from_latest:
                raise DuplicatedFile(latest_path, source)

            # If default behavior, the incoming contains all data for a new version
            # In the case of a duplicated file, just pass to the expected symlink creation
            # and records duplicated file for further removal only if migration mode is the
            # default (i.e., moving files). In the case of --copy or --link, keep duplicates
            # in place into the incoming directory.
            else:
                src = os.readlink(latest_path)
                tree.create_leaf(nodes=current_path.parts,
                                 label='{}{}{}'.format(current_path.name, LINK_SEPARATOR, src),
                                 src=src,
                                 mode='symlink')
                if pctx.mode == 'move':
                    tree.duplicates.append(source)

        # Record entry for list() and uniqueness checkup.
        record = {'src': source,
                  'dst': current_path,
                  'is_duplicate': is_duplicate}
        key = str(get_drs_up(current_path).parent)
        if key in tree.paths:
            tree.paths[key]['files'].append(record)
            assert latest_version == tree.paths[key]['latest']
        else:
            tree.paths[key] = {}
            tree.paths[key]['files'] = [record]
            tree.paths[key]['latest'] = latest_version

        # Print info.
        msg = 'DRS Path = {}'.format(get_drs_up(current_path))
        msg += ' <-- ' + current_path.name
        Print.success(msg)

        # Return True if success.
        return True

    except KeyboardInterrupt:

        # Lock error number.
        with pctx.lock:

            # Increase error counter.
            pctx.errors.value += 1

        raise

    # Catch known exception with its traceback.
    except Exception:

        # Lock error number.
        with pctx.lock:

            # Increase error counter.
            pctx.errors.value += 1

            # Format & print exception traceback.
            exc = traceback.format_exc().splitlines()
            msg = TAGS.SKIP + COLORS.HEADER(str(source)) + '\n'
            msg += '\n'.join(exc)
            Print.exception(msg, buffer=True)

        return None

    finally:

        # Lock progress value.
        with pctx.lock:

            # Increase progress counter.
            pctx.progress.value += 1

            # Clear previous print.
            msg = '\r{}'.format(' ' * pctx.msg_length.value)
            Print.progress(msg)

            # Print progress bar.
            msg = '\r{} {} {}'.format(COLORS.OKBLUE(SPINNER_DESC),
                                      FRAMES[pctx.progress.value % len(FRAMES)],
                                      source)
            Print.progress(msg)

            # Set new message length.
            pctx.msg_length.value = len(msg)


class Runner(object):

    def __init__(self, processes, init_args):

        # Initialize the pool.
        self.pool = None
        if processes != 1:
            self.pool = Pool(processes=processes,
                             initializer=self._initializer,
                             initargs=(init_args.keys(), init_args.values()))

        # Initialise context.
        else:
            self._initializer(init_args.keys(), init_args.values())

    @staticmethod
    def _initializer(keys, values):
        """
        Initialize process context by setting particular variables as global variables.

        """
        assert len(keys) == len(values)
        global pctx
        pctx = namedtuple("ChildProcess", keys)(*values)

    def _handle_sigterm(self, signum, frame):
        if self.pool:
            self.pool.terminate()
        os._exit(1)

    def run(self, sources):

        # Instantiate signal handler.
        sig_handler = signal.signal(signal.SIGTERM, self._handle_sigterm)

        # Instantiate pool of processes.
        if self.pool:

            # Instantiate pool iterator.
            processes = self.pool.imap(process, sources)

        # Sequential processing use basic map function.
        else:

            # Instantiate processes iterator.
            processes = map(process, sources)

        # Run processes & get the list of results.
        results = [x for x in processes]

        # Terminate pool in case of SIGTERM signal.
        signal.signal(signal.SIGTERM, sig_handler)

        # Close the pool.
        if self.pool:
            self.pool.close()
            self.pool.join()

        return results


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
                msg = '"{}" argument has changed: "{}" instead of "{}" -- '.format(k,
                                                                                   getattr(ctx, k),
                                                                                   old_args[k])
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
    quiet = args.quiet if hasattr(args, 'quiet') else False
    if quiet:
        _STDOUT.stdout_off()

    # Instantiate processing context.
    with ProcessingContext(args) as ctx:

        # Set DRS tree as global variable.
        global tree

        # Instantiate DRS tree.
        tree = DRSTree(ctx.root, ctx.version, ctx.mode, ctx.commands_file)

        # Shared processing context between child processes as dictionary.
        cctx = {name: getattr(ctx, name) for name in PROCESS_VARS}

        # Disable file scan if a previous DRS tree have generated using same context and no "list" action.
        if do_scanning(ctx):

            # Instantiate the runner.
            r = Runner(ctx.processes, init_args=cctx)

            # Get runner results.
            results = r.run(ctx.sources)

            # Final print.
            msg = '\r{}'.format(' ' * ctx.msg_length.value)
            Print.progress(msg)
            msg = '\r{} {} {}\n'.format(COLORS.OKBLUE(SPINNER_DESC), FINAL_FRAME, FINAL_STATUS)
            Print.progress(msg)

        # Load cached DRS tree.
        else:
            reader = load(TREE_FILE)
            msg = 'Skip incoming files scan (use "--rescan" to force it) -- '
            msg += 'Using cached DRS tree from {}'.format(TREE_FILE)
            Print.warning(msg)
            _ = next(reader)
            tree = next(reader)
            results = next(reader)

        # Flush buffer
        Print.flush()

        # Get number of sources.
        ctx.nbsources = ctx.progress.value

        # Number of success (excluding errors/skipped files).
        ctx.success = len(list(filter(None, results)))

        # Rollback --commands-file value to command-line argument in any case
        tree.commands_file = ctx.commands_file

        # Backup DRS tree and context for later usage.
        store(TREE_FILE, data=[{key: ctx.__getattribute__(key) for key in CONTROLLED_ARGS},
                               tree,
                               results])
        Print.info('DRS tree recorded for next usage onto {}.'.format(TREE_FILE))

        # Evaluate the list of results triggering action.
        if any(results):
            # Check upgrade uniqueness
            tree.check_uniqueness()

            # Apply tree action
            tree.get_display_lengths()
            getattr(tree, ctx.action)(quiet=quiet)

    # Evaluate errors & exit with corresponding return code.
    if ctx.errors.value > 0:
        sys.exit(ctx.errors.value)
