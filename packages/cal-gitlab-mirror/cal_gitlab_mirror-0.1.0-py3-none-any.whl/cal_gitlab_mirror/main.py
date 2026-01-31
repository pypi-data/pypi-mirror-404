# ----------------------------------------------------------------------------------------
#   main
#   ----
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
from .argbuilder import ArgsParser
from .argbuilder import Namespace
from .config import Config
from .config import load_config_file
from .config import merge_config
from .version import VERSION_STR

# ----------------------------------------------------------------------------------------
#   Functions
# ----------------------------------------------------------------------------------------


# ----------------------------------------------------------------------------------------
def get_args(argv: list[str]) -> Namespace:
    """
    Parse the CLI args
    """

    p = ArgsParser(
        prog="cal-gitlab-mirror",
        description=(
            "A tool to mirror GitLab repositories between two GitLab instances. "
            "Supports full mirrors and incremental transfers."
        ),
        version=f"cal-gitlab-mirror: {VERSION_STR}",
    )

    # =========== Common Options ===========

    common = p.create_common_collection()

    common.add_argument(
        "--verbose",
        "-v",
        action="count",
        default=0,
        help="Display verbose logging to stderr. Can be used twice for extra verbose",
    )

    common.add_argument(
        "--config",
        "-c",
        metavar="FILE",
        help="Path to JSON configuration file",
    )

    common.add_argument(
        "--jobs",
        "-j",
        type=int,
        metavar="N",
        help="Number of parallel jobs (default: 1)",
    )

    # =========== Source Options ===========

    source_options = ArgsParser.new_collection()
    source_options.add_argument(
        "--source-url",
        "-u",
        metavar="URL",
        help="Source GitLab instance URL (e.g., https://gitlab.com)",
    )
    source_options.add_argument(
        "--source-token",
        "-t",
        metavar="TOKEN",
        help=(
            "Personal access token for source GitLab (needs read_api, read_repository)"
        ),
    )
    source_options.add_argument(
        "--source-group",
        "-g",
        metavar="GROUP",
        help="Source group/namespace to mirror (e.g., myorg/mygroup)",
    )

    # =========== Destination Options ===========

    dest_options = ArgsParser.new_collection()
    dest_options.add_argument(
        "--dest-url",
        "-u",
        metavar="URL",
        help="Destination GitLab instance URL",
    )
    dest_options.add_argument(
        "--dest-token",
        "-t",
        metavar="TOKEN",
        help=(
            "Personal access token for destination GitLab (needs api, write_repository)"
        ),
    )
    dest_options.add_argument(
        "--dest-group",
        "-g",
        metavar="GROUP",
        help="Destination group/namespace to push to",
    )

    # =========== Pull Command ===========

    pull_cmd = p.add_command(
        "pull",
        help=(
            "Pull repositories from source GitLab to local storage. "
            "Creates bundle files in the output directory for transfer."
        ),
    )
    pull_cmd.add(source_options)

    pull_cmd.add_argument(
        "--output-dir",
        "-o",
        metavar="DIR",
        help="Local directory to store bundle files for transfer",
    )

    pull_cmd.add_argument(
        "--cache-dir",
        metavar="DIR",
        help="Directory for cached bare repos (default: .mirror-cache in current dir)",
    )

    pull_cmd.add_argument(
        "--since",
        "-s",
        type=int,
        metavar="DAYS",
        help="Only include changes from the last N days (incremental mode)",
    )

    pull_cmd.add_argument(
        "--full",
        "-f",
        action="store_true",
        help="Force full mirror clone even if repo already exists locally",
    )

    pull_cmd.add_argument(
        "--delete",
        action="store_true",
        help="Delete the output directory before mirroring (fresh start)",
    )

    # =========== Push Command ===========

    push_cmd = p.add_command(
        "push",
        help=(
            "Push repositories from local storage to destination GitLab. "
            "Creates projects in the destination group if they don't exist."
        ),
    )
    push_cmd.add(dest_options)

    push_cmd.add_argument(
        "--input-dir",
        "-i",
        metavar="DIR",
        help="Local directory containing mirrored repositories",
    )

    return p.parse(argv)


# ----------------------------------------------------------------------------------------
def main(argv: list[str]) -> int:
    """
    Main entry point for the CLI.

    Parameters:
        argv: Command line arguments (without program name)

    Returns:
        Exit code (0 for success, non-zero for error)
    """
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

    # Merge configuration
    config = merge_config(config_file_data, vars(args))

    # Dispatch to command handler
    if args.command == "pull":
        return cmd_pull(config, args)
    elif args.command == "push":
        return cmd_push(config, args)
    else:
        print(f"Unknown command: {args.command}")
        return 1


# ----------------------------------------------------------------------------------------
def cmd_pull(config: Config, args: Namespace) -> int:
    """Handle the 'pull' command."""
    from .mirror_read import read_from_source

    # Validate required options
    if not config.source.url:
        print("Error: --source-url is required")
        return 1
    if not config.source.token:
        print(
            "Error: --source-token is required (or set CAL_GITLAB_MIRROR_SOURCE_TOKEN)"
        )
        return 1
    if not config.source.group:
        print("Error: --source-group is required")
        return 1
    if not config.output_dir:
        print("Error: --output-dir is required")
        return 1

    return read_from_source(
        source_url=config.source.url,
        source_token=config.source.token,
        source_group=config.source.group,
        output_dir=config.output_dir,
        cache_dir=config.cache_dir,
        since_days=args.since or config.since,
        full_mirror=args.full or config.full,
        delete_first=args.delete or config.delete,
        jobs=config.jobs,
    )


# ----------------------------------------------------------------------------------------
def cmd_push(config: Config, _args: Namespace) -> int:
    """Handle the 'push' command."""
    from .mirror_write import write_to_dest

    # Validate required options
    if not config.dest.url:
        print("Error: --dest-url is required")
        return 1
    if not config.dest.token:
        print("Error: --dest-token is required (or set CAL_GITLAB_MIRROR_DEST_TOKEN)")
        return 1
    if not config.dest.group:
        print("Error: --dest-group is required")
        return 1
    if not config.input_dir:
        print("Error: --input-dir is required")
        return 1

    return write_to_dest(
        dest_url=config.dest.url,
        dest_token=config.dest.token,
        dest_group=config.dest.group,
        input_dir=config.input_dir,
        jobs=config.jobs,
    )
