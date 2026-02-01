# ----------------------------------------------------------------------------------------
#   config
#   ------
#
#   JSON configuration file handling
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
from .constants import ENV_CACHE_DIR
from .constants import ENV_DEST_GROUP
from .constants import ENV_DEST_TOKEN
from .constants import ENV_DEST_URL
from .constants import ENV_INPUT_DIR
from .constants import ENV_JOBS
from .constants import ENV_OUTPUT_DIR
from .constants import ENV_SOURCE_GROUP
from .constants import ENV_SOURCE_TOKEN
from .constants import ENV_SOURCE_URL

# ----------------------------------------------------------------------------------------
#   Types
# ----------------------------------------------------------------------------------------


@dataclass
class SourceConfig:
    """Configuration for source GitLab."""

    url: str | None = None
    token: str | None = None
    group: str | None = None


@dataclass
class DestConfig:
    """Configuration for destination GitLab."""

    url: str | None = None
    token: str | None = None
    group: str | None = None


@dataclass
class Config:
    """Complete configuration."""

    source: SourceConfig
    dest: DestConfig
    output_dir: str | None = None
    input_dir: str | None = None
    cache_dir: str | None = None
    delete: bool = False
    full: bool = False
    since: int | None = None
    jobs: int = 1


# ----------------------------------------------------------------------------------------
#   Functions
# ----------------------------------------------------------------------------------------


# ----------------------------------------------------------------------------------------
def _coalesce[T](*values: T | None) -> T | None:
    """Return the first non-None value, or None if all are None."""
    for v in values:
        if v is not None:
            return v
    return None


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

    Priority: CLI args > config file > environment variables

    Parameters:
        config_file: Parsed config file data
        cli_args: Arguments from command line

    Returns:
        Merged Config object
    """
    # Extract source config
    source_file = config_file.get("source", {})
    source = SourceConfig(
        url=cli_args.get("source_url")
        or source_file.get("url")
        or os.environ.get(ENV_SOURCE_URL),
        token=cli_args.get("source_token")
        or source_file.get("token")
        or os.environ.get(ENV_SOURCE_TOKEN),
        group=cli_args.get("source_group")
        or source_file.get("group")
        or os.environ.get(ENV_SOURCE_GROUP),
    )

    # Extract dest config
    dest_file = config_file.get("dest", {})
    dest = DestConfig(
        url=cli_args.get("dest_url")
        or dest_file.get("url")
        or os.environ.get(ENV_DEST_URL),
        token=cli_args.get("dest_token")
        or dest_file.get("token")
        or os.environ.get(ENV_DEST_TOKEN),
        group=cli_args.get("dest_group")
        or dest_file.get("group")
        or os.environ.get(ENV_DEST_GROUP),
    )

    # Parse jobs from env if present
    jobs_env = os.environ.get(ENV_JOBS)
    jobs_default = int(jobs_env) if jobs_env else 1

    return Config(
        source=source,
        dest=dest,
        output_dir=cli_args.get("output_dir")
        or config_file.get("output_dir")
        or os.environ.get(ENV_OUTPUT_DIR),
        input_dir=cli_args.get("input_dir")
        or config_file.get("input_dir")
        or os.environ.get(ENV_INPUT_DIR),
        cache_dir=cli_args.get("cache_dir")
        or config_file.get("cache_dir")
        or os.environ.get(ENV_CACHE_DIR),
        delete=cli_args.get("delete") or config_file.get("delete", False),
        full=cli_args.get("full") or config_file.get("full", False),
        since=_coalesce(cli_args.get("since"), config_file.get("since")),
        jobs=_coalesce(cli_args.get("jobs"), config_file.get("jobs"), jobs_default)
        or 1,
    )
