import getpass
import re
from requests.auth import HTTPBasicAuth

from esgprep.utils.github import gh_request_content
from esgprep.utils.custom_print import *



class GitHubBaseContext(object):
    """
    Base class for processing context manager.

    """
    def __init__(self, args):
        self.projects = args.project
        self.keep = args.k
        self.overwrite = args.o
        self.backup_mode = args.b
        self.gh_user = args.gh_user
        self.gh_password = args.gh_password
        self.auth = None
        self.config_dir = os.path.realpath(os.path.normpath(args.i))

    def __enter__(self):
        # If the username is set but not the password, prompt for it interactively
        if self.gh_user and not self.gh_password and sys.stdout.isatty():
            msg = COLOR().bold('Github password for user {}: '.format(self.gh_user))
            self.gh_password = getpass.getpass(msg)
        # Init GitHub authentication
        self.auth = self.authenticate()

    def __exit__(self, exc_type, exc_val, exc_tb):
        # Print log path if exists
        Print.log()

    def target_projects(self, pattern, url_format):
        """
        Gets the available projects ids from GitHub esg.*.ini files.
        Make the intersection with the desired projects to fetch.

        :returns: The target projects
        :rtype: *list*

        """
        r = gh_request_content(url_format, auth=self.auth)
        names = [content['name'] for content in r.json()]
        p_found = set([re.search(pattern, x).group(1) for x in names if re.search(pattern, x)])
        if self.projects:
            p = set(self.projects)
            p_avail = p_found.intersection(p)
            if p.difference(p_avail):
                msg = 'No such project(s): {} -- '.format(', '.join(p.difference(p_avail)))
                msg += 'Available remote projects are: {}'.format(', '.join(list(p_found)))
                Print.warning(msg)
        else:
            p_avail = p_found
        return list(p_avail)


    def authenticate(self):
            """
            Builds GitHub HTTP authenticator

            :returns: The HTTP authenticator
            :rtype: *requests.auth.HTTPBasicAuth*

            """
            return HTTPBasicAuth(self.gh_user, self.gh_password) if self.gh_user and self.gh_password else None

