import sys
import getpass
import re
from requests.auth import HTTPBasicAuth

from esgprep.utils.misc import gh_request_content


class BaseContext(object):
    """
    base class for context, containing any methods shared by more than one operation within esgprep
    """

    def target_projects(self, pattern, url_format):
        """
        Gets the available projects ids from GitHub esg.*.ini files.
        Make the intersection with the desired projects to fetch.

        :returns: The target projects
        :rtype: *list*
        """

        r = gh_request_content(url_format, auth=self.auth)
        names = [item['name'] for item in r.json()]
        p_avail = set([re.search(pattern, x).group(1) for x in names if re.search(pattern, x)])
        if self.projects:
            p = set(self.projects)
            p_avail = p_avail.intersection(p)
            if p.difference(p_avail):
                logging.warning("Unavailable project(s): {}".format(', '.join(p.difference(p_avail))))
        return list(p_avail)


    def authenticate(self):
        """
        Builds GitHub HTTP authenticator

        :returns: The HTTP authenticator
        :rtype: *requests.auth.HTTPBasicAuth*

        """
        # if the username is set but not the password, prompt for it interactively
        if self.gh_user and not self.gh_password and sys.stdout.isatty():
            self.gh_password = getpass.getpass('Github password for user {}: '.format(self.gh_user))

        return HTTPBasicAuth(self.gh_user, self.gh_password) if self.gh_user and self.gh_password else None

