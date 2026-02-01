# ----------------------------------------------------------------------------------------
#   config
#   ------
#
#   Configuration handling - merges CLI args, config file, and environment variables
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

import json
import logging
import os
from dataclasses import dataclass
from pathlib import Path
from typing import Any
from .constants import DEFAULT_GITLAB_URL
from .constants import DEFAULT_GROUP
from .constants import DEFAULT_HOST
from .constants import ENV_GITLAB_TOKEN
from .constants import ENV_GITLAB_URL
from .constants import ENV_GROUP

# ----------------------------------------------------------------------------------------
#   Types
# ----------------------------------------------------------------------------------------


@dataclass
class Config:
    """Complete configuration for upload."""

    project: str
    version: str
    html_dir: Path  # Can be a directory or .zip file
    force: bool = False
    set_latest: bool = False
    host: str = DEFAULT_HOST
    gitlab_url: str = DEFAULT_GITLAB_URL
    group: str = DEFAULT_GROUP
    token: str | None = None


# ----------------------------------------------------------------------------------------
#   Functions
# ----------------------------------------------------------------------------------------


# ----------------------------------------------------------------------------------------
def load_config_file(path: str | Path) -> dict[str, Any]:
    """
    Load configuration from a JSON file.

    Parameters:
        path: Path to the config file

    Returns:
        Parsed JSON as dictionary, or empty dict if file doesn't exist
    """
    path = Path(path)
    if not path.exists():
        logging.debug(f"Config file not found: {path}")
        return {}

    try:
        with open(path) as f:
            data: dict[str, Any] = json.load(f)
            logging.debug(f"Loaded config from: {path}")
            return data
    except json.JSONDecodeError as e:
        logging.warning(f"Invalid JSON in config file {path}: {e}")
        return {}
    except Exception as e:
        logging.warning(f"Error reading config file {path}: {e}")
        return {}


# ----------------------------------------------------------------------------------------
def merge_config(
    config_file: dict[str, Any],
    cli_args: dict[str, Any],
) -> Config:
    """
    Merge configuration from file, CLI args, and environment variables.

    Priority: CLI args > config file > environment variables > defaults

    Parameters:
        config_file: Parsed config file data
        cli_args: Arguments from command line

    Returns:
        Merged Config object
    """
    # Required arguments (must come from CLI)
    project = cli_args["project"]
    version = cli_args["version"]
    html_dir = Path(cli_args["html_dir"])

    # Optional arguments with fallback chain
    force = cli_args.get("force", False)
    set_latest = cli_args.get("set_latest", False)

    host = cli_args.get("host") or config_file.get("host") or DEFAULT_HOST

    gitlab_url = (
        cli_args.get("gitlab_url")
        or config_file.get("gitlab_url")
        or os.environ.get(ENV_GITLAB_URL)
        or DEFAULT_GITLAB_URL
    )

    group = (
        cli_args.get("group")
        or config_file.get("group")
        or os.environ.get(ENV_GROUP)
        or DEFAULT_GROUP
    )

    token = (
        cli_args.get("token")
        or config_file.get("token")
        or os.environ.get(ENV_GITLAB_TOKEN)
    )

    return Config(
        project=project,
        version=version,
        html_dir=html_dir,
        force=force,
        set_latest=set_latest,
        host=host,
        gitlab_url=gitlab_url,
        group=group,
        token=token,
    )
