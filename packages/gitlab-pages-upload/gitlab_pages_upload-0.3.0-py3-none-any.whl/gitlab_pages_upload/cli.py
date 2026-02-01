# ----------------------------------------------------------------------------------------
#   cli
#   ---
#
#   CLI definition and command dispatch
#
#   License
#   -------
#   MIT License - Copyright 2026 Cyber Assessment Labs
#
#   Authors
#   -------
#   bena (via claude)
#
#   Version History
#   ---------------
#   Jan 2026 - Created
# ----------------------------------------------------------------------------------------

# ----------------------------------------------------------------------------------------
#   Imports
# ----------------------------------------------------------------------------------------

import logging
import re
import sys
import traceback
from pathlib import Path
from .argbuilder import ArgsParser
from .argbuilder import Namespace
from .config import load_config_file
from .config import merge_config
from .constants import DEFAULT_GITLAB_URL
from .constants import DEFAULT_GROUP
from .constants import DEFAULT_HOST
from .upload import upload_docs
from .version import VERSION_STR

# Pattern to extract project and version from zip filename
# Matches: project-name-1.2.3-docs.zip or project-name-1.2.3.zip
ZIP_NAME_PATTERN = re.compile(r"^(.+?)-(\d[^-]*?)(?:-docs)?\.zip$", re.IGNORECASE)

# ----------------------------------------------------------------------------------------
#   Functions
# ----------------------------------------------------------------------------------------


# ----------------------------------------------------------------------------------------
def parse_zip_filename(filename: str) -> tuple[str, str] | None:
    """
    Extract project name and version from a zip filename.

    Supported formats:
        - project-name-1.2.3-docs.zip
        - project-name-1.2.3.zip
        - project_name-1.2.3-docs.zip

    Parameters:
        filename: The zip filename (without path)

    Returns:
        Tuple of (project, version) or None if pattern doesn't match
    """
    match = ZIP_NAME_PATTERN.match(filename)
    if match:
        return match.group(1), match.group(2)
    return None


# ----------------------------------------------------------------------------------------
def get_args(argv: list[str]) -> Namespace:
    """
    Parse the CLI args
    """

    p = ArgsParser(
        prog="gitlab-pages-upload",
        description=(
            "Upload prebuilt HTML documentation to GitLab Pages. "
            "Project and version can be auto-detected from zip filenames "
            "like 'myproject-1.2.3-docs.zip'."
        ),
        version=f"gitlab-pages-upload: {VERSION_STR}",
    )

    # =========== Required Arguments ===========

    p.add_argument(
        "--html",
        "-H",
        required=True,
        metavar="PATH",
        help="Path to HTML documentation (directory or .zip file)",
    )

    # =========== Project/Version Arguments (mutually exclusive with --auto) ===========

    p.add_argument(
        "--auto",
        "-a",
        action="store_true",
        help=(
            "Auto-detect project and version from zip filename (mutually exclusive with"
            " -p/-V)"
        ),
    )

    p.add_argument(
        "--project",
        "-p",
        metavar="NAME",
        help="Project/package name (required unless --auto is used)",
    )

    p.add_argument(
        "--doc-version",
        "-V",
        metavar="VERSION",
        dest="doc_version",
        help="Documentation version (required unless --auto is used)",
    )

    # =========== Optional Arguments ===========

    p.add_argument(
        "--force",
        "-f",
        action="store_true",
        help="Overwrite existing version if it already exists",
    )

    p.add_argument(
        "--set-latest",
        "-l",
        action="store_true",
        help="Also copy docs to 'latest/' directory",
    )

    p.add_argument(
        "--group",
        "-g",
        metavar="GROUP",
        help=f"GitLab group for docs projects (default: {DEFAULT_GROUP})",
    )

    p.add_argument(
        "--gitlab-url",
        "-u",
        metavar="URL",
        help=f"GitLab instance URL (default: {DEFAULT_GITLAB_URL})",
    )

    p.add_argument(
        "--host",
        metavar="HOST",
        help=f"Documentation host backend (default: {DEFAULT_HOST})",
    )

    p.add_argument(
        "--config",
        "-c",
        metavar="FILE",
        help="Path to JSON configuration file",
    )

    p.add_argument(
        "--verbose",
        "-v",
        action="count",
        default=0,
        help="Display verbose output. Use twice for debug logging",
    )

    return p.parse(argv)


# ----------------------------------------------------------------------------------------
def main(argv: list[str] | None = None) -> int:
    """
    Main entry point for the CLI.

    Parameters:
        argv: Command line arguments (without program name). If None, uses sys.argv[1:].

    Returns:
        Exit code (0 for success, non-zero for error)
    """
    if argv is None:
        argv = sys.argv[1:]

    try:
        return _main_inner(argv)
    except KeyboardInterrupt:
        print()
        print("---- Manually Terminated ----")
        print()
        return 1
    except SystemExit:
        raise
    except BaseException as e:
        t = "-----------------------------------------------------------------------------\n"
        t += "UNHANDLED EXCEPTION OCCURRED!!\n"
        t += "\n"
        t += traceback.format_exc()
        t += "\n"
        t += f"EXCEPTION: {type(e)} {e}\n"
        t += "-----------------------------------------------------------------------------\n"
        t += "\n"
        print(t, file=sys.stderr)
        return 1


# ----------------------------------------------------------------------------------------
def _main_inner(argv: list[str]) -> int:
    """Inner main function that does the actual work."""
    args = get_args(argv)

    # Configure logging
    if args.verbose >= 2:
        logging.basicConfig(level=logging.DEBUG, format="%(levelname)s: %(message)s")
    elif args.verbose >= 1:
        logging.basicConfig(level=logging.INFO, format="%(levelname)s: %(message)s")
    else:
        logging.basicConfig(level=logging.WARNING, format="%(levelname)s: %(message)s")

    # Load config file if specified
    config_file_data = {}
    if args.config:
        config_file_data = load_config_file(args.config)

    # Handle --auto vs --project/--doc-version mutex
    html_path = Path(args.html)

    if args.auto:
        # --auto mode: cannot specify --project or --doc-version
        if args.project or args.doc_version:
            print("Error: --auto cannot be used with --project or --doc-version")
            return 1

        # Must be a zip file for auto-detection
        if html_path.suffix.lower() != ".zip":
            print("Error: --auto requires a .zip file input")
            return 1

        parsed = parse_zip_filename(html_path.name)
        if not parsed:
            print(
                "Error: Could not parse project/version from filename:"
                f" {html_path.name}"
            )
            print(
                "Expected format: project-name-1.2.3-docs.zip or project-name-1.2.3.zip"
            )
            return 1

        project, version = parsed
        if args.verbose >= 1:
            print(f"Auto-detected project: {project}")
            print(f"Auto-detected version: {version}")
    else:
        # Manual mode: both --project and --doc-version are required
        if not args.project:
            print("Error: --project is required (or use --auto with a .zip file)")
            return 1
        if not args.doc_version:
            print("Error: --doc-version is required (or use --auto with a .zip file)")
            return 1

        project = args.project
        version = args.doc_version

    # Build CLI args dict for merge_config
    cli_args = {
        "project": project,
        "version": version,
        "html_dir": args.html,
        "force": args.force,
        "set_latest": args.set_latest,
        "host": args.host,
        "gitlab_url": args.gitlab_url,
        "group": args.group,
    }

    # Merge configuration
    config = merge_config(config_file_data, cli_args)

    # Validate host
    if config.host != DEFAULT_HOST:
        print(
            f"Error: Unsupported host '{config.host}'. Only '{DEFAULT_HOST}' is"
            " supported."
        )
        return 1

    # Convert html_dir to absolute path
    config.html_dir = Path(config.html_dir).resolve()

    verbose = args.verbose >= 1

    if verbose:
        print("Validating inputs...")

    # Perform upload
    result = upload_docs(config, verbose=verbose)

    if not result.success:
        print(f"\nError: {result.error_message}")
        return 1

    # Success message
    print()
    print("Success! Documentation will be available at:")
    print(f"  {result.version_url}")
    if result.latest_url:
        print(f"  {result.latest_url}")
    print()
    print("Note: GitLab Pages deployment may take 1-2 minutes.")

    return 0
