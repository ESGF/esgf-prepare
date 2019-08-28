# -*- coding: utf-8 -*-

"""
.. module:: esgprep.fetchtables
    :platform: Unix
    :synopsis: Fetches ESGF project tables from GitHub repository.

.. moduleauthor:: Guillaume Levavasseur <glipsl@ipsl.fr>

"""

import traceback

from esgprep._utils.github import *
from esgprep.constants import GITHUB_API_PARAMETER
from esgprep.fetchtables.constants import *
from esgprep.fetchtables.context import ProcessingContext


def make_outdir(tables_dir, repository, reference=None):
    """
    Builds the CMOR table output directory.

    """

    # Output directory = submitted root + project repository name.
    outdir = os.path.join(tables_dir, repository)

    # Join GitHub reference/branch/tag.
    if reference:
        outdir = os.path.join(outdir, reference)

    # If output directory does not exist.
    if not os.path.isdir(outdir):

        # Try to make it.
        try:
            os.makedirs(outdir)
            Print.warning('{} created'.format(outdir))

        # Error rollbacks on the current working directory (default).
        except OSError as e:
            msg = 'Cannot use "{}" (OSError {}: {}) -- '.format(outdir, e.errno, e.strerror)
            msg += 'Use "{}" instead.'.format(os.getcwd())
            Print.warning(msg)
            outdir = os.path.join(os.getcwd(), repository)
            if reference:
                outdir = os.path.join(outdir, reference)
            if not os.path.isdir(outdir):
                os.makedirs(outdir)
                Print.warning('"{}" created'.format(outdir))

    # Return output directory.
    return outdir


def get_special_case(f, url, repo, ref, auth):
    """
    Get a specific file info to fetch to be used for named files in place of the file info from the general API call.

    """
    # Build corresponding GitHub API to call
    url = url.format(repo)
    url += '/{}'.format(f)
    url += GITHUB_API_PARAMETER.format('ref', ref)

    # Get the file infos to fetch.
    try:
        r = gh_request_content(url=url, auth=auth)
        Print.debug('Set special GitHub reference -- "{}": "{}"'.format(f, ref))

        # Returns a dictionary of {filename: file_info} pairs to be used by main process.
        return {f: r.json()}

    except GitHubFileNotFound:
        pass


def run(args):
    """
    Main process.

    """
    # Instantiate processing context
    with ProcessingContext(args) as ctx:

        # Iterates over project names.
        for project in ctx.project:

            # Escape in case of error.
            try:

                # Set project repository name.
                repo = REPO_PATTERN.format(project)

                # Get the list of available GitHub reference/branch/tag for that repository.
                r = gh_request_content(url=ctx.ref_url.format(repo), auth=ctx.auth)
                refs = [os.path.basename(ref['url']) for ref in r.json()]

                # Filter Github reference depending on the command-line.
                if hasattr(ctx, 'ref'):
                    if ctx.ref not in refs:
                        raise GitHubReferenceNotFound(ctx.ref, refs)
                    fetch_refs = [ctx.ref]
                else:
                    fetch_refs = filter(re.compile(ctx.ref_regex).match, refs)
                    if not fetch_refs:
                        raise GitHubReferenceNotFound(ctx.ref_regex.pattern, refs)
                Print.debug('GitHub Available reference(s): {}'.format(', '.join(sorted(refs))))
                Print.info('Selected GitHub reference(s): {}'.format(', '.join(sorted(fetch_refs))))

                # Get special case for CMIP6_CV.json file, always from master branch.
                special_cases = get_special_case(f='CMIP6_CV.json', url=ctx.url, repo=repo, ref='master', auth=ctx.auth)

                # Iterates over desired GitHub reference.
                for ref in fetch_refs:

                    # Escape in case of error.
                    try:

                        # Set reference API URL.
                        url = ctx.url.format(repo)
                        if ref:
                            url += GITHUB_API_PARAMETER.format('ref', ref)

                        Print.debug('Fetch {} tables from "{}" GitHub reference'.format(project, ref))

                        # Make output directory w/ subfolder tree structure.
                        if ctx.no_subfolder:
                            outdir = make_outdir(ctx.tables_dir, repo)
                        else:
                            outdir = make_outdir(ctx.tables_dir, repo, ref)

                        # Get available CMOR table with corresponding download URL.
                        r = gh_request_content(url=url, auth=ctx.auth)
                        ctx.files = dict([(f['name'], f) for f in r.json() if ctx.file_filter(f['name'])])

                        # Get number of files
                        nfiles = len(ctx.files)
                        if not nfiles:
                            Print.warning('No files found on remote repository: {}'.format(url))

                        # Reset counter
                        progress = 0

                        # Iterates over files to fetch.
                        for f, info in ctx.files.items():

                            # Escape in case of error.
                            try:

                                # Overwrite info by special cases ones
                                if special_cases and f in special_cases.keys():
                                    info = special_cases[f]

                                # Set output full path of the file.
                                outfile = os.path.join(outdir, f)

                                # Get remote checksum infos.
                                sha = info['sha']

                                # Get remote download URL.
                                download_url = info['download_url']

                                # Fetch GitHub file
                                fetch(url=download_url,
                                      outfile=outfile,
                                      auth=ctx.auth,
                                      sha=sha,
                                      keep=ctx.keep,
                                      overwrite=ctx.overwrite,
                                      backup_mode=ctx.backup_mode)

                            # Catch unknown exception into error log instead of stop the process.
                            except KeyboardInterrupt:
                                raise

                            # Catch known exception with its traceback.
                            except Exception:
                                download_url = info['download_url']
                                exc = traceback.format_exc().splitlines()
                                msg = TAGS.FAIL + COLORS.HEADER(download_url) + '\n'
                                msg += '\n'.join(exc)
                                Print.exception(msg, buffer=True)
                                ctx.error = True

                            # Print progress.
                            finally:
                                project = re.search(REPO_NAME_PATTERN, url).group(1).split('/')[-1]
                                ref = url.split('=')[-1]
                                progress += 1
                                percentage = int(progress * 100 / nfiles)
                                msg = COLORS.OKBLUE('\rFetching {} tables from {} reference: '.format(project, ref))
                                msg += '{}% | {}/{} files'.format(percentage, progress, nfiles)
                                Print.progress(msg)

                        Print.progress('\n')

                    # Catch known exception with its traceback.
                    except Exception:
                        exc = traceback.format_exc().splitlines()
                        msg = TAGS.FAIL
                        msg += 'Fetching {} tables from {} GitHub reference'.format(COLORS.HEADER(project),
                                                                                    COLORS.HEADER(ref)) + '\n'
                        msg += '\n'.join(exc)
                        Print.exception(msg, buffer=True)
                        ctx.error = True

            # Catch known exception with its traceback.
            except Exception:
                exc = traceback.format_exc().splitlines()
                msg = TAGS.FAIL
                msg += 'Fetching {} tables'.format(COLORS.HEADER(project)) + '\n'
                msg += '\n'.join(exc)
                Print.exception(msg, buffer=True)
                ctx.error = True

    # Flush buffer.
    Print.flush()

    # Evaluate errors & exit with corresponding return code.
    if ctx.error:
        sys.exit(1)
