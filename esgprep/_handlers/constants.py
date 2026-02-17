from os import link, symlink, remove
from shutil import copy2 as copy
from shutil import move

# Unix command
UNIX_COMMAND_LABEL = {
    "symlink": "ln -s",
    "link": "ln",
    "copy": "cp",
    "move": "mv",
    "remove": "rm",
}  # Lolo Change add 'remove' : 'rm'

UNIX_COMMAND = {
    "symlink": symlink,
    "link": link,
    "copy": copy,
    "move": move,
    "remove": remove,
}

# Symbolic link separator
LINK_SEPARATOR = " --> "
