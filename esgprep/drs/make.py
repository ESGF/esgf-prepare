"""
This module handles the generation of Data Reference Syntax (DRS) directory structures
for various ESGF projects by dynamically adapting to project-specific requirements.
"""

from pathlib import Path

# Import the refactored components
from esgprep.drs.model.process import Process
from esgprep.drs.model.processor import DrsProcessor


def determine_migration_mode(args) -> str:
    """
    Determine the migration mode from the command-line arguments.

    Args:
        args: Parsed command-line arguments

    Returns:
        Migration mode string ('move', 'copy', 'link', 'symlink')
    """
    # Default is 'move'
    mode = "move"

    # Check for explicit mode flags
    if getattr(args, "copy", False):
        mode = "copy"
    elif getattr(args, "link", False):
        mode = "link"
    elif getattr(args, "symlink", False):
        mode = "symlink"

    # If cmd is set and not 'make', use that (for 'remove', etc.)
    if hasattr(args, "cmd") and args.cmd != "make":
        mode = args.cmd

    return mode


def process_esgdrs_command(args) -> int:
    """
    Process ESGDRS command using the enhanced DrsProcessor.

    This function integrates the DrsProcessor with the command-line interface.

    Args:
        args: Command-line arguments

    Returns:
        Exit code (0 for success, 1 for failure)
    """
    try:
        # Create processor with arguments
        processor = DrsProcessor(
            root_dir=Path(args.root),
            project=args.project,
            mode=determine_migration_mode(args),
            checksum_type=None if getattr(args, "no_checksum", False) else "sha256",
            upgrade_from_latest=getattr(args, "upgrade_from_latest", False),
            ignore_from_latest=[
                line.strip() for line in getattr(args, "ignore_from_latest", []) or []
            ],
            ignore_from_incoming=[
                line.strip() for line in getattr(args, "ignore_from_incoming", []) or []
            ],
            version=getattr(args, "version", None),
            set_values=dict(args.set_value) if getattr(args, "set_value", None) else {},
            set_keys=dict(args.set_key) if getattr(args, "set_key", None) else {},
        )

        # Process files from directory
        results = []
        for directory in args.directory:
            results.extend(list(processor.process_directory(Path(directory))))

        # Report results
        success_count = sum(1 for r in results if r.success)
        print(
            f"Processed {len(results)} files: {success_count} succeeded, {len(results) - success_count} failed"
        )

        # If action is 'upgrade', execute operations
        if getattr(args, "action", "") == "upgrade":
            operations = []
            for result in results:
                if result.success:
                    operations.extend(result.operations)

            success = processor.execute_operations(operations)
            if success:
                print("All operations completed successfully")
            else:
                print("Some operations failed")
                return 1

        # Return success if no errors
        return 0 if success_count == len(results) else 1

    except Exception as e:
        print(f"Error processing command: {e}")
        return 1


# # Re-export imported classes and functions to maintain backward compatibility
# __all__ = [
#     'Process',
#     'DrsProcessor',
#     'determine_migration_mode',
#     'process_esgdrs_command'
# ]
