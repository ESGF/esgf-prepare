# -*- coding: utf-8 -*-

"""
.. module:: esgprep._handlers.drs_tree.py
   :platform: Unix
   :synopsis: DRS tree parsing utilities.

.. moduleauthor:: Guillaume Levavasseur <glipsl@ipsl.fr>

"""

import getpass
from pathlib import Path
from tempfile import NamedTemporaryFile

from hurry.filesize import size
from treelib import Tree
from treelib.tree import DuplicatedNodeIdError

from esgprep import _STDOUT
from esgprep._exceptions import DuplicatedDataset
from esgprep._exceptions.io import *
from esgprep._handlers.constants import LINK_SEPARATOR, UNIX_COMMAND, UNIX_COMMAND_LABEL
from esgprep._utils.print import *


class DRSLeaf(object):
    """
    Class handling DRS tree leaf actions.

    """

    def __init__(self, dst, mode, src=None):
        # Source data path.
        self.src = src

        # Destination data path.
        self.dst = dst

        # Migration mode.
        self.mode = mode

    def upgrade(self, quiet=False, todo_only=True):
        """
        Upgrade the DRS tree.

        """
        # BE CAREFUL: Avoid any changes in the print statements here
        # Someone could use display outputs for parsing and further processing.
        # Any change of the line outputs can break this for users.

        # --commands-file writes print statements ONLY in the submitted file

        # Make directory for destination path if not exist.
        if not Path(self.dst).exists():
            if not todo_only:
                try:
                    os.makedirs(os.path.dirname(self.dst))
                    line = f"{'mkdir -p'} {os.path.dirname(self.dst)}"
                    print_cmd(line, quiet, todo_only)

                except OSError:
                    pass

        # Unlink symbolic link if already exists.
        if self.mode == "symlink" and os.path.lexists(self.dst):
            line = f"{'rm -f'} {self.dst}"
            print_cmd(line, quiet, todo_only)
            if not todo_only:
                os.remove(self.dst)

        # Make upgrade depending on the migration mode.
        line = UNIX_COMMAND_LABEL[self.mode]
        if self.src:
            line += " " + str(self.src)  # Lolo change add str(Posix)
        line += " " + str(self.dst)  # Lolo change str(Posix)
        print_cmd(line, quiet, todo_only)
        if not todo_only:
            if self.src:
                UNIX_COMMAND[self.mode](self.src, self.dst)
            else:
                UNIX_COMMAND[self.mode](self.dst)

    def has_permissions(self, root):
        """
        Checks permissions for DRS leaf migration.
        Discards relative paths.

        """
        # Check src access.
        # Define src access depending on the migration mode
        if self.mode == "move":
            if os.path.isabs(self.src) and not os.access(self.src, os.W_OK):
                raise WriteAccessDenied(getpass.getuser(), self.src)
        elif self.mode != "remove":
            if os.path.isabs(self.src) and not os.access(self.src, os.R_OK):
                raise ReadAccessDenied(getpass.getuser(), self.src)

        # Check dst access (always write).
        # Backward the DRS if path does not exist.
        dst = self.dst
        while not os.path.exists(dst) and dst != root:
            dst = os.path.split(dst)[0]
        if os.path.isabs(dst) and not os.access(dst, os.W_OK):
            raise WriteAccessDenied(getpass.getuser(), dst)

    def migration_granted(self, root):
        """
        Check if migration mode is allowed by filesystem.
        Bacially, copy or move will always succeed.
        Only hardlinks could fail depending on the filesystem partition.

        """
        # Apply test for "--link" migration only.
        if self.mode == "link":
            # Create a temporary file in the source directory.
            with NamedTemporaryFile(dir=os.path.dirname(self.src)) as f:
                # Pickup the first existing parent if the destination folder does not exist.
                dst = os.path.dirname(self.dst)
                while not os.path.exists(dst) and dst != root:
                    dst = os.path.split(dst)[0]
                dst = os.path.join(dst, os.path.basename(f.name))

                # Try migration with temporary file.
                try:
                    UNIX_COMMAND[self.mode](f.name, dst)

                # Catch OS errors.
                except OSError as e:
                    # Invalid corss-device link.
                    if e.errno == 18:
                        raise CrossMigrationDenied(self.src, self.src, self.mode)

                    # Other OSError.
                    else:
                        raise MigrationDenied(self.src, self.src, self.mode, e.strerror)

                # Always remove temporary file.
                finally:
                    if os.path.exists(dst):
                        os.remove(dst)


class DRSTree(Tree):
    """
    Class handling DRS tree leaf actions.

    """

    def __init__(
        self, root=None, mode=None, outfile=None
    ):  # Lolo Change version=Node en 2eme argument remove
        # Retrieve original class init
        Tree.__init__(self)
        # Dataset and files record.
        self.paths = dict()

        # DRS root directory.
        self.drs_root = root

        # Migration mode.
        self.drs_mode = mode

        # Display width.
        self.d_lengths = list()

        # Output commands file path.
        self.commands_file = outfile

        # List of duplicates to remove.
        self.duplicates = list()

        # Dataset hash record.
        self.hash = dict()

    def add_path(self, key: str, value: dict):
        self.paths[key] = value

    def append_path(self, key: str, what: str, value: dict):
        self.paths[key][what].append(value)

    def has_path(self, key: str) -> bool:
        return key in self.paths

    def get_path(self, key: str):
        return self.paths.get(key)

    def get_path_value(self, key: str, field: str):
        if key in self.paths:
            return self.paths[key].get(field)
        return None

    def get_display_lengths(self):
        """
        Gets the string lengths for comfort display of "list" action.

        """
        self.d_lengths = [50, 20, 20, 16, 16]
        if self.paths:
            self.d_lengths[0] = max([len(i) for i in self.paths.keys()])
        self.d_lengths.append(sum(self.d_lengths) + 2)

    def create_leaf(self, nodes, label, src, mode, force=False):
        """
        Creates all nodes from DRS root to a DRS leaf.

        """
        # Iterate over DRS levels..
        for i in range(len(nodes)):
            # Node id = node "path"
            node_id = os.path.join(*nodes[: i + 1])

            # Escape in case of duplicated node.
            try:
                # Create first DRS node.
                if i == 0:
                    self.create_node(tag=nodes[i], identifier=node_id)

                # Create DRS leaf nodes.
                elif i == len(nodes) - 1:
                    # Force DRS node removal if exists.
                    if self.contains(node_id) and force:
                        self.remove_node(node_id)

                    # Get parent node id.
                    parent_node_id = os.path.join(*nodes[:i])

                    # Create DRS node embedding DRSLeaf object.
                    self.create_node(
                        tag=label,
                        identifier=node_id,
                        parent=parent_node_id,
                        data=DRSLeaf(
                            src=src, dst=node_id.split(LINK_SEPARATOR)[0], mode=mode
                        ),
                    )

                # Create DRS nodes between DRS root and DRS leaf.
                else:
                    parent_node_id = os.path.join(*nodes[:i])
                    self.create_node(
                        tag=nodes[i], identifier=node_id, parent=parent_node_id
                    )

            # Pass duplicated node error to recursively generated the tree
            except DuplicatedNodeIdError:
                pass

    def leaves(self, root=None):
        """
        Yield leaves of the whole DRS tree of a subtree.
        Overwrites basic tree.leaves() method that generates a list.

        """
        if root is None:
            for node in self._nodes.values():
                if node.is_leaf():
                    yield node
        else:
            for node in self.expand_tree(root):
                if self[node].is_leaf():
                    yield self[node]

    def check_uniqueness(self):
        """
        Check tree upgrade uniqueness.
        Each data version to upgrade has to be stricly different from the latest version if exists.

        """
        for dataset, infos in self.paths.items():
            # Retrieve the latest existing version.
            latest_version = infos["latest"]

            # Check dataset uniqueness only if a latest version exists.
            if latest_version:
                # Get the list of filenames from the incoming dataset.
                if "files" in infos.keys():
                    filenames = [
                        file["src"].name
                        for file in infos["files"]
                        if "src" in file.keys()
                    ]  # Lolo Change :  if "src" in file.keys()
                    # filenames = [file for file in infos['files']  ]  # Lolo Change :  if "src" in file.keys()

                # Get the list of duplicate status from the incoming dataset.
                duplicates = [file["is_duplicate"] for file in infos["files"]]

                # Get the list of filenames from the latest existing version.
                latest_filenames = list()
                for _, _, filenames in os.walk(
                    Path(self.drs_root or "", dataset, latest_version)
                ):  # change or '' to deal with error with remove
                    latest_filenames += filenames

                # An upgrade version is different if it contains at least one file with is_duplicate = False
                # And it has the same number of files than the "latest" version.
                if all(duplicates) and set(latest_filenames) == set(filenames):
                    raise DuplicatedDataset(dataset, latest_version)

    def rmdir(self):
        """
        Remove empty version directory and its empty parents.

        """
        # TEST ça à l'air de marcher ..: au lieu de regarder dans self.path => qu'on a remplit au fur et à mesure .. on va directement checker le Tree
        all_tree_nodes = self.all_nodes()
        for node in all_tree_nodes[::-1]:
            if node.is_root() == False:
                str_path = node.identifier
                # c = node.data
                # d = c.dst
                # m_path = Path(node["data"]["dst"])
                if Path(str_path).is_dir():
                    if len(os.listdir(str(str_path))) == 0:
                        print("remove empty dir ", str_path)
                        os.rmdir(str_path)
        """ manque le latest ? il n'y a pas de noeud latest dans le DRSTree ? """

        """
        for dataset, infos in self.paths.items():
            # dans infos .. il y les records qu'on a rempli dans le Tree remove : self.tree.paths[key]['files'] = [record]
            a = infos["files"]
            list_dir_to_check = [i["dst"] for i in infos["files"]]
            for f in list_dir_to_check:
                if f.is_dir():
                    if len(os.listdir(f)) == 0:  # empty dir
                        print("remove dir ", f)
                        os.rmdir(f)
                    for parent in f.parents:
                        try:
                            if len(os.listdir(parent)) == 0:
                                os.rmdir(parent)
                                print("remove dir ", parent)
                        except OSError:
                            break
            """
        # os.rmdir(infos['current']) # Lolo There is not infos["current"] ??? Why ???
        # for parent in infos['current'].parents:
        #    try:
        #        os.rmdir(parent)
        #    except OSError:
        #        break

    def list(self, **kwargs):
        """
        Lists and summaries upgrade information at the publication level.

        """
        # Header.
        print("".center(self.d_lengths[-1], "="))
        header = "Publication level".center(self.d_lengths[0])
        header += "Latest version".center(self.d_lengths[1])
        if self.drs_mode == "remove":
            header += "<-"
            header += "Remove version".center(self.d_lengths[2])
            header += "Files to remove".rjust(self.d_lengths[3])
        else:
            header += "->"
            header += "Upgrade version".center(self.d_lengths[2])
            header += "Files to upgrade".rjust(self.d_lengths[3])
        header += "Total size".rjust(self.d_lengths[4])
        print(header)
        print("".center(self.d_lengths[-1], "-"))

        # Body.
        for dataset, infos in self.paths.items():
            pub_lvl = dataset
            nfiles = len(infos["files"])
            latest_version = infos["latest"]
            total_size = 0
            if "upgrade" in infos.keys():  # Lolo Change
                upgrade_version = infos["upgrade"]
            else:
                upgrade_version = ""
            if not self.drs_mode == "remove":  # Lolo Change entire line
                total_size = size(
                    sum([file["src"].stat().st_size for file in infos["files"]])
                )
            body = pub_lvl.ljust(self.d_lengths[0])
            body += latest_version.center(self.d_lengths[1])
            if self.drs_mode == "remove":
                body += "<-"
            else:
                body += "->"
            body += upgrade_version.center(self.d_lengths[2])
            body += str(nfiles).rjust(self.d_lengths[3])
            if not self.drs_mode == "remove":  # Lolo Change entire line
                body += total_size.rjust(self.d_lengths[4])
            print(body)

        # Footer.
        print("".center(self.d_lengths[-1], "="))

    def tree(self, **kwargs):
        """
        Prints the whole DRS tree in a visual way.

        """
        # Header.
        print("".center(self.d_lengths[-1], "="))
        if self.drs_mode == "remove":
            print("Remove DRS Tree".center(self.d_lengths[-1]))
        else:
            print("Upgrade DRS Tree".center(self.d_lengths[-1]))
        print("".center(self.d_lengths[-1], "-"))
        import codecs

        # Body.
        self.show()

        # Footer.
        print("".center(self.d_lengths[-1], "="))

    def todo(self, **kwargs):
        """
        Prints command-lines to do as in a "dry-run" mode.

        """
        self.upgrade(todo_only=True)

    def upgrade(self, todo_only=False, quiet=False):
        """
        Upgrades the whole DRS tree.

        """
        # Check permissions and migration availability before upgrade
        if not todo_only:
            for leaf in self.leaves():
                leaf.data.has_permissions(self.drs_root)
                leaf.data.migration_granted(self.drs_root)

        # Header.
        # print(self.paths)
        print("".center(self.d_lengths[-1], "="))
        if todo_only:
            print("Unix command-lines (DRY-RUN)".center(self.d_lengths[-1]))
        else:
            print("Unix command-lines".center(self.d_lengths[-1]))
        print("".center(self.d_lengths[-1], "-"))

        # Apply DRSLeaf action/migration.
        for leaf in self.leaves():
            leaf.data.upgrade(quiet=quiet, todo_only=todo_only)

        # Remove duplicates.
        for duplicate in self.duplicates:
            line = f"{'rm -f'} {duplicate}"
            print_cmd(line, quiet, todo_only)
            if not todo_only:
                # Check src access.
                if os.path.isabs(duplicate) and not os.access(duplicate, os.W_OK):
                    raise WriteAccessDenied(getpass.getuser(), self.src)
                else:
                    os.remove(duplicate)

        # Print info in case of commands file output.
        if todo_only and self.commands_file:
            print(
                "Command-lines to apply have been exported to {}".format(
                    self.commands_file
                )
            )

        # Footer.
        print("".center(self.d_lengths[-1], "="))


def print_cmd(line, quiet=False, todo_only=False):
    """
    Print unix command-line depending on the choosen output and DRS action.

    """
    if quiet and todo_only:
        _STDOUT.stdout_on()
        print(line)
        _STDOUT.stdout_off()
    else:
        print(line)


#    if commands_file and todo_only:
#       with open(commands_file, mode) as f:
#          f.write('{}\n'.format(line))
# else:
#    print(line)
