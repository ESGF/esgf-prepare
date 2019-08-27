# -*- coding: utf-8 -*-

"""
.. module:: esgprep._utils.checksum.py
   :platform: Unix
   :synopsis: Checksumming utilities.

.. moduleauthor:: Guillaume Levavasseur <glipsl@ipsl.fr>

"""

import hashlib

from esgprep._exceptions import InvalidChecksumType, ChecksumFail
from esgprep._utils.print import *


def checksum(ffp, checksum_type, include_filename=False, human_readable=True):
    """
    Computes a file checksum.

    """
    try:
        # Get checksum client.
        hash_algo = getattr(hashlib, checksum_type)()

        # Checksumming file.
        with open(ffp, 'rb') as f:
            blocksize = os.stat(ffp).st_blksize
            for block in iter(lambda: f.read(blocksize), b''):
                hash_algo.update(block)

        # Include filename into the checksum.
        if include_filename:
            hash_algo.update(os.path.basename(ffp))

        # Return human readable checksum.
        if human_readable:
            return hash_algo.hexdigest()

        else:
            return hash_algo.digest()

    # Catch checksum type error.
    except AttributeError:
        raise InvalidChecksumType(checksum_type)

    # Catch manual stop error.
    except KeyboardInterrupt:
        raise

    # Catch any other error.
    except Exception:
        raise ChecksumFail(ffp, checksum_type)


def get_checksum_pattern(checksum_type):
    """
    Builds a regular expression describing a checksum pattern.

    """
    # Get checksum client.
    hash_algo = getattr(hashlib, checksum_type)()

    # Get checksum length.
    checksum_length = len(hash_algo.hexdigest())

    # Return corresponding regex.
    return re.compile('^[0-9a-f]{{{}}}$'.format(checksum_length))


def get_checksum(ffp, checksum_type='sha256', checksums=None):
    """
    Global method to get file checksum:
    1. By computing the checksum directly.
    2. Through a list of checksums in a dictionary way {file: checksum}.

    """
    # Verify checksum dictionary.
    if checksums:

        # Verify file in dictionary keys.
        if ffp in checksums:

            # Verify checksum pattern.
            if re.match(get_checksum_pattern(checksum_type), checksums[ffp]):
                # Return pre-computed checksum.
                return checksums[ffp]

    # Return computed checksum.
    return checksum(ffp, checksum_type)
