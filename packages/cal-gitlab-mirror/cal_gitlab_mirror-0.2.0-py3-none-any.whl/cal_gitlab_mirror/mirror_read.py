# ----------------------------------------------------------------------------------------
#   mirror_read
#   -----------
#
#   Read mode implementation - clone/fetch from source GitLab, create bundles
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
from concurrent.futures import ThreadPoolExecutor
from concurrent.futures import as_completed
from datetime import UTC
from datetime import datetime
from datetime import timedelta
from pathlib import Path
from .git_ops import clone_mirror
from .git_ops import create_bundle
from .git_ops import fetch_mirror
from .git_ops import is_git_repo
from .gitlab_api import GitLabClient
from .gitlab_api import ProjectInfo

# ----------------------------------------------------------------------------------------
#   Constants
# ----------------------------------------------------------------------------------------

DEFAULT_CACHE_DIR = ".mirror-cache"

# ----------------------------------------------------------------------------------------
#   Functions
# ----------------------------------------------------------------------------------------


# ----------------------------------------------------------------------------------------
def _is_recent(activity_str: str, cutoff: datetime) -> bool:
    """Check if activity timestamp is after cutoff date."""
    if not activity_str:
        return False
    try:
        # Parse ISO format timestamp (e.g., "2026-01-28T09:15:00.000Z")
        activity = datetime.fromisoformat(activity_str.replace("Z", "+00:00"))
        return activity >= cutoff
    except (ValueError, TypeError):
        # If we can't parse, include the project to be safe
        return True


# ----------------------------------------------------------------------------------------
def read_from_source(
    *,
    source_url: str,
    source_token: str,
    source_group: str,
    output_dir: str,
    cache_dir: str | None = None,
    since_days: int | None = None,
    full_mirror: bool = False,
    delete_first: bool = False,
    jobs: int = 1,
) -> int:
    """
    Clone or fetch repositories from source GitLab and create bundles.

    Creates bundle files in output_dir that can be transferred to another system.
    Uses a separate cache directory for bare repos to enable incremental bundles.

    Parameters:
        source_url: Source GitLab instance URL
        source_token: Personal access token for source
        source_group: Group/namespace to mirror
        output_dir: Local directory to store bundle files
        cache_dir: Directory for cached bare repos (default: .mirror-cache)
        since_days: Create incremental bundles with only commits from last N days
        full_mirror: Force full clone even if repo exists in cache
        delete_first: Delete the output directory before mirroring
        jobs: Number of parallel jobs

    Returns:
        Exit code (0 for success, non-zero for error)
    """
    import shutil

    output_path = Path(output_dir)
    cache_path = Path(cache_dir) if cache_dir else Path(DEFAULT_CACHE_DIR)

    # Delete output directory if requested
    if delete_first and output_path.exists():
        print(f"Deleting {output_dir}...")
        shutil.rmtree(output_path)

    print(f"Connecting to {source_url}...")
    client = GitLabClient(source_url, source_token)

    print(f"Listing projects in {source_group}...")
    try:
        projects = client.list_group_projects(source_group)
    except Exception as e:
        print(f"Error listing projects: {e}")
        return 1

    print(f"Found {len(projects)} projects")

    if not projects:
        print("No projects found in group")
        return 0

    # Filter by recent activity if --since is specified
    if since_days is not None:
        cutoff = datetime.now(UTC) - timedelta(days=since_days)
        original_count = len(projects)
        projects = [p for p in projects if _is_recent(p.last_activity_at, cutoff)]
        print(
            f"Filtered to {len(projects)} projects with activity in last {since_days}"
            " days"
        )
        if len(projects) < original_count:
            print(f"  (excluded {original_count - len(projects)} inactive projects)")

    # Ensure directories exist
    output_path.mkdir(parents=True, exist_ok=True)
    cache_path.mkdir(parents=True, exist_ok=True)

    # Filter out empty/archived repos first
    work_items: list[ProjectInfo] = []
    skipped = 0
    for project in projects:
        if project.empty_repo:
            print(f"Skipping {project.path_with_namespace} (empty repo)")
            skipped += 1
        elif project.archived:
            print(f"Skipping {project.path_with_namespace} (archived)")
            skipped += 1
        else:
            work_items.append(project)

    if not work_items:
        print("No projects to process")
        return 0

    errors: list[str] = []
    bundled = 0
    total = len(work_items)

    effective_jobs = min(jobs, total)
    if effective_jobs > 1:
        print(f"Processing {total} projects with {effective_jobs} parallel jobs...")
    else:
        print(f"Processing {total} projects...")

    if effective_jobs > 1:
        # Parallel processing
        with ThreadPoolExecutor(max_workers=effective_jobs) as executor:
            future_to_project = {
                executor.submit(
                    _bundle_single_project,
                    project=project,
                    output_dir=output_path,
                    cache_dir=cache_path,
                    source_group=source_group,
                    token=source_token,
                    full_mirror=full_mirror,
                    since_days=since_days,
                ): project
                for project in work_items
            }

            completed = 0
            for future in as_completed(future_to_project):
                project = future_to_project[future]
                completed += 1
                prefix = f"[{completed}/{total}]"
                try:
                    success = future.result()
                    if success:
                        print(f"{prefix} OK: {project.path_with_namespace}")
                        bundled += 1
                    else:
                        errors.append(f"{project.path_with_namespace}: bundle failed")
                        print(f"{prefix} FAILED: {project.path_with_namespace}")
                except Exception as e:
                    errors.append(f"{project.path_with_namespace}: {e}")
                    print(f"{prefix} ERROR: {project.path_with_namespace}: {e}")
                    logging.exception(f"Failed to bundle {project.path_with_namespace}")
    else:
        # Sequential processing
        for i, project in enumerate(work_items, 1):
            prefix = f"[{i}/{total}]"
            try:
                success = _bundle_single_project(
                    project=project,
                    output_dir=output_path,
                    cache_dir=cache_path,
                    source_group=source_group,
                    token=source_token,
                    full_mirror=full_mirror,
                    since_days=since_days,
                )
                if success:
                    print(f"{prefix} OK: {project.path_with_namespace}")
                    bundled += 1
                else:
                    errors.append(f"{project.path_with_namespace}: bundle failed")
                    print(f"{prefix} FAILED: {project.path_with_namespace}")
            except Exception as e:
                errors.append(f"{project.path_with_namespace}: {e}")
                print(f"{prefix} ERROR: {project.path_with_namespace}: {e}")
                logging.exception(f"Failed to bundle {project.path_with_namespace}")

    # Summary
    print()
    mode = f"incremental ({since_days} days)" if since_days else "full"
    print(f"Bundled ({mode}): {bundled}, Skipped: {skipped}, Errors: {len(errors)}")

    if errors:
        print("\nErrors:")
        for err in errors:
            print(f"  - {err}")
        return 1

    return 0


# ----------------------------------------------------------------------------------------
def _bundle_single_project(
    *,
    project: ProjectInfo,
    output_dir: Path,
    cache_dir: Path,
    source_group: str,
    token: str,
    full_mirror: bool,
    since_days: int | None,
) -> bool:
    """
    Clone/fetch a project and create a bundle file.

    Parameters:
        project: Project info from GitLab
        output_dir: Base directory for bundle files
        cache_dir: Directory for cached bare repos
        source_group: Source group prefix to strip from paths
        token: GitLab token for authentication
        full_mirror: Force full clone
        since_days: If set, create incremental bundle

    Returns:
        True on success, False on failure
    """
    import shutil

    # Strip source group prefix from path
    relative_path = project.path_with_namespace
    if relative_path.startswith(source_group + "/"):
        relative_path = relative_path[len(source_group) + 1 :]

    # Paths
    cache_repo_path = cache_dir / f"{relative_path}.git"
    bundle_path = output_dir / f"{relative_path}.bundle"

    # Ensure parent directories exist
    cache_repo_path.parent.mkdir(parents=True, exist_ok=True)
    bundle_path.parent.mkdir(parents=True, exist_ok=True)

    # Clone or fetch to cache
    if is_git_repo(str(cache_repo_path)) and not full_mirror:
        # Repo exists in cache, fetch updates
        logging.info(f"Fetching updates for {project.path_with_namespace}")
        success = fetch_mirror(str(cache_repo_path), token=token)
    else:
        # Clone new repo to cache
        if cache_repo_path.exists():
            shutil.rmtree(cache_repo_path)

        logging.info(f"Cloning {project.path_with_namespace}")
        success = clone_mirror(
            project.http_url_to_repo,
            str(cache_repo_path),
            token=token,
        )

    if not success:
        return False

    # Create bundle
    logging.info(f"Creating bundle for {project.path_with_namespace}")
    return create_bundle(
        str(cache_repo_path),
        str(bundle_path),
        since_days=since_days,
    )
