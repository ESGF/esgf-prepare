"""
Show mapfile paths that would be generated from datasets.

This module provides the Process class used in the multiprocessing context
for showing mapfile paths without actually generating the mapfiles.
"""

import traceback
from pathlib import Path

from esgprep.constants import FRAMES
from esgprep.mapfile.constants import SPINNER_DESC
from esgprep.mapfile.processor import MapfileProcessor
from esgprep._utils.print import Print, COLORS, TAGS


class Process:
    """
    Process class for showing mapfile paths, compatible with multiprocessing.
    
    This class bridges the gap between the old multiprocessing approach
    and the new MapfileProcessor implementation for showing mapfile paths.
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
        self.basename = getattr(ctx, 'basename', False)
        self.progress = ctx.progress
        self.msg_length = ctx.msg_length
        self.lock = ctx.lock
        self.errors = ctx.errors
        self.project = ctx.project
        self.latest_symlink = getattr(ctx, 'latest_symlink', False)
        self.all_versions = getattr(ctx, 'all_versions', False)
        self.version = getattr(ctx, 'version', None)
        
        # Create MapfileProcessor instance for path generation only
        self.processor = MapfileProcessor(
            outdir=self.outdir,
            project=self.project,
            mapfile_name=self.mapfile_name,
            no_checksum=True,  # Don't need checksums for path generation
            latest_symlink=self.latest_symlink,
            all_versions=self.all_versions,
            version=self.version
        )
        
    def __call__(self, source):
        """
        Show mapfile path for a source file or dataset.
        
        Args:
            source: Source file or dataset to process
            
        Returns:
            Path to the mapfile or None on failure
        """
        try:
            # Extract dataset info to determine mapfile path
            dataset_info = self.processor._extract_dataset_info(source)
            if not dataset_info:
                raise ValueError(f"Failed to extract dataset info from {source}")
                
            dataset_id, version = dataset_info
            
            # Build mapfile path
            mapfile_path = self.processor._build_mapfile_path(dataset_id, version)
            
            # Print success message
            with self.lock:
                msg = f'{mapfile_path.name} <-- {source}'
                Print.success(msg)
            
            # Return the mapfile path (basename only if requested)
            if self.basename:
                return mapfile_path.name
            else:
                return mapfile_path
            
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
                msg = TAGS.SKIP + COLORS.HEADER(str(source)) + '\n'
                msg += '\n'.join(exc)
                Print.exception(msg, buffer=True)
                
            return None
            
        finally:
            # Update progress display
            with self.lock:
                # Increase progress counter
                self.progress.value += 1
                
                # Clear previous print
                msg = f'\r{" " * self.msg_length.value}'
                Print.progress(msg)
                
                # Print progress bar
                msg = f'\r{COLORS.OKBLUE(SPINNER_DESC)} {FRAMES[self.progress.value % len(FRAMES)]} {source}'
                Print.progress(msg)
                
                # Set new message length
                self.msg_length.value = len(msg)
