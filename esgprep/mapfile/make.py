"""
Mapfile generation process for ESGF datasets.

This module provides the Process class used in the multiprocessing context
for generating ESGF mapfiles.
"""

import os
import traceback
from pathlib import Path
from typing import Optional, Dict, Any, Union

from esgprep.constants import FRAMES
from esgprep.mapfile import build_mapfile_name, build_mapfile_entry, write
from esgprep.mapfile.constants import SPINNER_DESC
from esgprep.mapfile.processor import MapfileProcessor
from esgprep.mapfile.models import FileInput, MapfileEntry
from esgprep._utils.checksum import get_checksum
from esgprep._utils.print import Print, COLORS, TAGS


class Process:
    """
    Process class for mapfile generation, compatible with multiprocessing.

    This class bridges the gap between the old multiprocessing approach
    and the new MapfileProcessor implementation.
    """

    def __init__(self, ctx):
        """
        Initialize with context from the multiprocessing runner.

        Args:
            ctx: Shared processing context between child processes
        """
        # Initialize from context
        self.mapfile_name = ctx.mapfile_name
        self.outdir = ctx.outdir
        self.basename = getattr(ctx, "basename", False)
        self.no_checksum = ctx.no_checksum
        self.checksums_from = ctx.checksums_from
        self.checksum_type = ctx.checksum_type
        self.notes_url = ctx.notes_url
        self.notes_title = ctx.notes_title
        self.progress = ctx.progress
        self.msg_length = ctx.msg_length
        self.lock = ctx.lock
        self.errors = ctx.errors
        self.project = ctx.project
        self.latest_symlink = getattr(ctx, "latest_symlink", False)
        self.all_versions = getattr(ctx, "all_versions", False)
        self.version = getattr(ctx, "version", None)

        # Create MapfileProcessor instance
        self.processor = MapfileProcessor(
            outdir=self.outdir,
            project=self.project,
            mapfile_name=self.mapfile_name,
            no_checksum=self.no_checksum,
            checksum_type=self.checksum_type if not self.no_checksum else None,
            checksums_from=self.checksums_from or {},
            tech_notes_url=self.notes_url,
            tech_notes_title=self.notes_title,
            latest_symlink=self.latest_symlink,
            all_versions=self.all_versions,
            version=self.version,
        )

    def _handle_legacy_file(self, source: Union[str, Path]) -> Optional[Path]:
        """
        Process a file using the legacy approach.
        This is kept for backward compatibility.

        Args:
            source: Source file to process

        Returns:
            Path to the generated mapfile or None on failure
        """
        source_path = Path(source)

        try:
            # Import legacy utilities that expect Path objects
            from esgprep._utils.path import dataset_id, get_project

            # Get dataset ID - this should validate DRS terms
            identifier = dataset_id(source_path)
            if not identifier:
                raise ValueError(f"Failed to extract dataset ID from {source_path}")

            # Split identifier into name & version
            dataset = identifier
            version = None

            if "." in identifier:
                parts = identifier.split(".")
                version_part = parts[-1]
                if version_part.startswith("v") or version_part == "latest":
                    version = (
                        version_part[1:]
                        if version_part.startswith("v")
                        else version_part
                    )
                    dataset = ".".join(parts[:-1])

            # Build mapfile name
            outfile = build_mapfile_name(self.mapfile_name, dataset, version)

            # Build full mapfile path
            outpath = Path(self.outdir) / outfile

            # Create mapfile directory
            try:
                os.makedirs(outpath.parent, exist_ok=True)
            except OSError:
                pass  # Directory already exists

            # Get file stats
            stats = source_path.stat()

            # Gather optional mapfile info
            optional_attrs = {}
            optional_attrs["mod_time"] = stats.st_mtime

            if not self.no_checksum:
                optional_attrs["checksum"] = get_checksum(
                    str(source_path), self.checksum_type, self.checksums_from
                )
                optional_attrs["checksum_type"] = self.checksum_type.upper()

            optional_attrs["dataset_tech_notes"] = self.notes_url
            optional_attrs["dataset_tech_notes_title"] = self.notes_title

            # Generate mapfile entry
            line = build_mapfile_entry(
                dataset_name=dataset,
                dataset_version=version,
                ffp=str(source_path),
                size=stats.st_size,
                optional_attrs=optional_attrs,
            )

            # Write to mapfile
            write(outpath, line)

            # Print success message
            with self.lock:
                msg = f"{outfile.with_suffix('')} <-- {source_path}"
                Print.success(msg)

            # Return mapfile path
            if self.basename:
                return outfile
            else:
                return outpath

        except Exception as e:
            print(f"Legacy processing failed: {e}")
            return None

    def __call__(self, source):
        """
        Process a source file or dataset and generate a mapfile entry.

        Any error switches to the next child process without stopping the main process.

        Args:
            source: Source file or dataset to process

        Returns:
            Path to the generated mapfile or None on failure
        """
        try:
            # First try the modern approach
            try:
                # Process the file using our modern processor
                result = self.processor.process_file(source)

                # Check if processing was successful
                if not result.success:
                    raise Exception(result.error_message or "Unknown error")

                # Get the mapfile path
                mapfile_path = result.mapfile_path
                if not mapfile_path:
                    raise ValueError("Mapfile path not set")

                # Create mapfile directory
                try:
                    os.makedirs(mapfile_path.parent, exist_ok=True)
                except OSError:
                    pass  # Directory already exists

                # Write the mapfile immediately (compatibility with old approach)
                # In the new approach, we would batch writes for efficiency
                for mapfile in self.processor.mapfiles.values():
                    mapfile.write()

                # Print success message
                with self.lock:
                    msg = f"{mapfile_path.name} <-- {source}"
                    Print.success(msg)

                # Return the mapfile path (basename only if requested)
                if self.basename:
                    return mapfile_path.name
                else:
                    return mapfile_path

            except ImportError as ie:
                # If modern approach fails due to missing dependencies, try legacy approach
                print(
                    f"Warning: Modern processing unavailable ({ie}), falling back to legacy approach"
                )
                return self._handle_legacy_file(source)

            except Exception as e:
                # If modern approach fails for any other reason, try legacy approach
                print(
                    f"Warning: Modern processing failed ({e}), falling back to legacy approach"
                )
                legacy_result = self._handle_legacy_file(source)
                if legacy_result:
                    return legacy_result
                else:
                    # If legacy approach also fails, re-raise the original error
                    raise Exception(f"Error processing file: {e}")

        except KeyboardInterrupt:
            # Handle keyboard interrupt
            with self.lock:
                self.errors.value += 1
            raise

        except Exception:
            # Handle any other exception
            with self.lock:
                # Increase error counter
                self.errors.value += 1

                # Format & print exception traceback
                exc = traceback.format_exc().splitlines()
                msg = TAGS.SKIP + COLORS.HEADER(str(source)) + "\n"
                msg += "\n".join(exc)
                Print.exception(msg, buffer=True)

            return None

        finally:
            # Update progress display
            with self.lock:
                # Increase progress counter
                self.progress.value += 1

                # Clear previous print
                msg = f"\r{' ' * self.msg_length.value}"
                Print.progress(msg)

                # Print progress bar
                msg = f"\r{COLORS.OKBLUE(SPINNER_DESC)} {FRAMES[self.progress.value % len(FRAMES)]} {source}"
                Print.progress(msg)

                # Set new message length
                self.msg_length.value = len(msg)


class LegacyProcess:
    """
    Legacy process class for backward compatibility.

    This class uses the old approach to mapfile generation and is maintained
    for compatibility with existing code that might expect this implementation.
    """

    def __init__(self, ctx):
        """
        Initialize with context from the multiprocessing runner.

        Args:
            ctx: Shared processing context between child processes
        """
        # Initialize from context
        self.mapfile_name = ctx.mapfile_name
        self.outdir = ctx.outdir
        self.basename = getattr(ctx, "basename", False)
        self.no_checksum = ctx.no_checksum
        self.checksums_from = ctx.checksums_from
        self.checksum_type = ctx.checksum_type
        self.notes_url = ctx.notes_url
        self.notes_title = ctx.notes_title
        self.progress = ctx.progress
        self.msg_length = ctx.msg_length
        self.lock = ctx.lock
        self.errors = ctx.errors

    def __call__(self, source):
        """
        Process a source file and generate a mapfile entry.

        Args:
            source: Source file to process

        Returns:
            Path to the generated mapfile or None on failure
        """
        # Escape in case of error.
        try:
            # Import utilities depending on the source type.
            if isinstance(source, Path):
                from esgprep._utils.path import get_terms, dataset_id, get_project
            else:
                from esgprep._utils.dataset import get_terms, dataset_id, get_project

            # Build dataset identifier.
            # DRS terms are validated during this step.
            identifier = dataset_id(source)

            # Check dataset identifier is not None.
            if not identifier:
                Print.debug("Dataset identifier is None")
                return False

            # Split identifier into name & version.
            # Identifier does not always end by a version.
            dataset = identifier
            version = None

            if re.search(r"\.latest|\.v[0-9]*$", str(identifier)):
                version = identifier.split(".")[-1][
                    1:
                ]  # remove "v" only for name in mapfile NOT for the mapfile name
                dataset = ".".join(identifier.split(".")[:-1])

            # Build mapfile name.
            outfile = build_mapfile_name(self.mapfile_name, dataset, version)

            # Build mapfile directory.
            outdir = Path(self.outdir).resolve(strict=False)

            # Build full mapfile path.
            outpath = outdir.joinpath(outfile)

            # Create mapfile directory.
            try:
                os.makedirs(outdir)
            except OSError:
                pass

            # Gathers optional mapfile info into a dictionary.
            optional_attrs = dict()
            optional_attrs["mod_time"] = source.stat().st_mtime
            if not self.no_checksum:
                optional_attrs["checksum"] = get_checksum(
                    str(source), self.checksum_type, self.checksums_from
                )
                optional_attrs["checksum_type"] = self.checksum_type.upper()
            optional_attrs["dataset_tech_notes"] = self.notes_url
            optional_attrs["dataset_tech_notes_title"] = self.notes_title

            # Generate the corresponding mapfile entry/line.
            line = build_mapfile_entry(
                dataset_name=dataset,
                dataset_version=version,
                ffp=str(source),
                size=source.stat().st_size,
                optional_attrs=optional_attrs,
            )

            # Write line into mapfile.
            write(outpath, line)

            # Print success.
            msg = "{} <-- {}".format(outfile.with_suffix(""), source)
            with self.lock:
                Print.success(msg)

            # Return mapfile path.
            return outpath

        except KeyboardInterrupt:
            # Lock error number.
            with self.lock:
                # Increase error counter.
                self.errors.value += 1

            raise

        # Catch known exception with its traceback.
        except Exception:
            # Lock error number.
            with self.lock:
                # Increase error counter.
                self.errors.value += 1

                # Format & print exception traceback.
                exc = traceback.format_exc().splitlines()
                msg = TAGS.SKIP + COLORS.HEADER(str(source)) + "\n"
                msg += "\n".join(exc)
                Print.exception(msg, buffer=True)

            return None

        finally:
            # Lock progress value.
            with self.lock:
                # Increase progress counter.
                self.progress.value += 1

                # Clear previous print.
                msg = "\r{}".format(" " * self.msg_length.value)
                Print.progress(msg)

                # Print progress bar.
                msg = "\r{} {} {}".format(
                    COLORS.OKBLUE(SPINNER_DESC),
                    FRAMES[self.progress.value % len(FRAMES)],
                    source,
                )
                Print.progress(msg)

                # Set new message length.
                self.msg_length.value = len(msg)
