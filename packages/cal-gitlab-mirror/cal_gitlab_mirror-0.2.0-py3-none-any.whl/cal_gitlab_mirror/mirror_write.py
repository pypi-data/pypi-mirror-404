# ----------------------------------------------------------------------------------------
#   mirror_write
#   ------------
#
#   Write mode implementation - push bundles to destination GitLab
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
import tempfile
import threading
from concurrent.futures import ThreadPoolExecutor
from concurrent.futures import as_completed
from pathlib import Path
from .git_ops import clone_from_bundle
from .git_ops import clone_mirror
from .git_ops import fetch_from_bundle
from .git_ops import push_mirror
from .gitlab_api import GitLabClient
from .gitlab_api import GroupInfo

# ----------------------------------------------------------------------------------------
#   Module-level lock for GitLab API operations that modify state
# ----------------------------------------------------------------------------------------

_gitlab_api_lock = threading.Lock()

# ----------------------------------------------------------------------------------------
#   Functions
# ----------------------------------------------------------------------------------------


# ----------------------------------------------------------------------------------------
def _find_bundles(base_dir: Path) -> list[Path]:
    """
    Find all bundle files in a directory.

    Parameters:
        base_dir: Directory to search

    Returns:
        List of paths to .bundle files
    """
    bundles: list[Path] = []
    for path in base_dir.rglob("*.bundle"):
        if path.is_file():
            bundles.append(path)
    return sorted(bundles)


# ----------------------------------------------------------------------------------------
def write_to_dest(
    *,
    dest_url: str,
    dest_token: str,
    dest_group: str,
    input_dir: str,
    jobs: int = 1,
) -> int:
    """
    Push bundle files to destination GitLab.

    Scans input directory for .bundle files and pushes them to destination.

    Parameters:
        dest_url: Destination GitLab instance URL
        dest_token: Personal access token for destination
        dest_group: Target group/namespace
        input_dir: Local directory containing bundle files
        jobs: Number of parallel jobs

    Returns:
        Exit code (0 for success, non-zero for error)
    """
    input_path = Path(input_dir)

    if not input_path.exists():
        print(f"Error: Input directory does not exist: {input_dir}")
        return 1

    # Find all bundles (skip .cache directory)
    print(f"Scanning {input_dir} for bundles...")
    all_bundles = _find_bundles(input_path)
    # Filter out bundles in .cache directory
    bundles = [b for b in all_bundles if ".cache" not in b.parts]

    if not bundles:
        print("No bundle files found")
        return 0

    print(f"Found {len(bundles)} bundles")

    print(f"Connecting to {dest_url}...")
    client = GitLabClient(dest_url, dest_token)

    # Verify/create base destination group
    print(f"Verifying destination group: {dest_group}")
    base_group = _ensure_group_hierarchy(client, dest_group)
    if base_group is None:
        print(f"Error: Could not create/access group {dest_group}")
        return 1

    # Build work items
    work_items: list[tuple[str, Path]] = []
    for bundle_path in bundles:
        relative_path = bundle_path.relative_to(input_path)
        relative_str = str(relative_path)
        if relative_str.endswith(".bundle"):
            relative_str = relative_str[:-7]
        work_items.append((relative_str, bundle_path))

    errors: list[str] = []
    pushed = 0
    total = len(work_items)

    effective_jobs = min(jobs, total)
    if effective_jobs > 1:
        print(f"Processing {total} bundles with {effective_jobs} parallel jobs...")
    else:
        print(f"Processing {total} bundles...")

    if effective_jobs > 1:
        # Parallel processing
        with ThreadPoolExecutor(max_workers=effective_jobs) as executor:
            future_to_item = {
                executor.submit(
                    _push_single_bundle,
                    relative_path=relative_str,
                    bundle_path=bundle_path,
                    client=client,
                    dest_group=dest_group,
                    dest_token=dest_token,
                ): relative_str
                for relative_str, bundle_path in work_items
            }

            completed = 0
            for future in as_completed(future_to_item):
                relative_str = future_to_item[future]
                completed += 1
                prefix = f"[{completed}/{total}]"
                try:
                    success = future.result()
                    if success:
                        print(f"{prefix} OK: {relative_str}")
                        pushed += 1
                    else:
                        errors.append(f"{relative_str}: push failed")
                        print(f"{prefix} FAILED: {relative_str}")
                except Exception as e:
                    errors.append(f"{relative_str}: {e}")
                    print(f"{prefix} ERROR: {relative_str}: {e}")
                    logging.exception(f"Failed to push {relative_str}")
    else:
        # Sequential processing
        for i, (relative_str, bundle_path) in enumerate(work_items, 1):
            prefix = f"[{i}/{total}]"
            try:
                success = _push_single_bundle(
                    relative_path=relative_str,
                    bundle_path=bundle_path,
                    client=client,
                    dest_group=dest_group,
                    dest_token=dest_token,
                )
                if success:
                    print(f"{prefix} OK: {relative_str}")
                    pushed += 1
                else:
                    errors.append(f"{relative_str}: push failed")
                    print(f"{prefix} FAILED: {relative_str}")
            except Exception as e:
                errors.append(f"{relative_str}: {e}")
                print(f"{prefix} ERROR: {relative_str}: {e}")
                logging.exception(f"Failed to push {relative_str}")

    # Summary
    print()
    print(f"Pushed: {pushed}, Errors: {len(errors)}")

    if errors:
        print("\nErrors:")
        for err in errors:
            print(f"  - {err}")
        return 1

    return 0


# ----------------------------------------------------------------------------------------
def _ensure_group_hierarchy(client: GitLabClient, group_path: str) -> GroupInfo | None:
    """
    Ensure all groups in a path exist, creating them if needed.

    Thread-safe: uses a lock to prevent race conditions when creating groups.

    Parameters:
        client: GitLab client
        group_path: Full group path (e.g., cal/mirror/subgroup)

    Returns:
        Final group info, or None on failure
    """
    with _gitlab_api_lock:
        parts = group_path.split("/")
        current_path = ""
        parent_id: int | None = None

        for part in parts:
            current_path = f"{current_path}/{part}" if current_path else part

            group = client.get_group(current_path)
            if group is None:
                # Create the group
                logging.info(f"Creating group: {current_path}")
                try:
                    group = client.create_group(part, part, parent_id)
                    print(f"  Created group: {current_path}")
                except Exception as e:
                    logging.error(f"Failed to create group {current_path}: {e}")
                    return None

            parent_id = group.id

        # Return the final group
        return client.get_group(group_path)


# ----------------------------------------------------------------------------------------
def _push_single_bundle(
    *,
    relative_path: str,
    bundle_path: Path,
    client: GitLabClient,
    dest_group: str,
    dest_token: str,
) -> bool:
    """
    Push a single bundle to destination.

    Handles both full bundles (for new repos) and incremental bundles
    (for existing repos). For incremental bundles, clones from destination
    first, then fetches from bundle, then pushes updates.

    Parameters:
        relative_path: Relative path of repo (e.g., subgroup/project)
        bundle_path: Path to bundle file
        client: GitLab client for destination
        dest_group: Base destination group
        dest_token: Token for authentication

    Returns:
        True on success, False on failure
    """
    dest_project_path = f"{dest_group}/{relative_path}"

    # Ensure parent groups exist (thread-safe)
    dest_namespace = "/".join(dest_project_path.split("/")[:-1])

    namespace_info = _ensure_group_hierarchy(client, dest_namespace)
    if namespace_info is None:
        logging.error(f"Could not ensure namespace: {dest_namespace}")
        return False

    # Check if project exists, create if not (thread-safe)
    with _gitlab_api_lock:
        existing = client.get_project(dest_project_path)
        project_exists = existing is not None

        if not project_exists:
            project_name = dest_project_path.split("/")[-1]
            logging.info(f"Creating project: {dest_project_path}")
            try:
                client.create_project(project_name, namespace_info.id)
                print(f"  Created project: {dest_project_path}")
            except Exception as e:
                logging.error(f"Failed to create project: {e}")
                return False

        # Get destination project URL
        dest_project = client.get_project(dest_project_path)
        if dest_project is None:
            logging.error(f"Could not get project after creation: {dest_project_path}")
            return False
        dest_url = dest_project.http_url_to_repo

    # Git operations can run in parallel (outside the lock)
    with tempfile.TemporaryDirectory() as temp_dir:
        temp_repo = Path(temp_dir) / "repo.git"

        if project_exists:
            # Project exists - this might be an incremental bundle
            # Clone from destination first, then fetch from bundle
            logging.info(f"Cloning existing repo from {dest_url}")
            if not clone_mirror(dest_url, str(temp_repo), token=dest_token):
                logging.warning("Could not clone from destination, trying bundle only")
                # Fall back to bundle-only approach
                if not clone_from_bundle(str(bundle_path), str(temp_repo)):
                    return False
            else:
                # Fetch updates from bundle
                logging.info(f"Fetching updates from bundle {bundle_path}")
                if not fetch_from_bundle(str(temp_repo), str(bundle_path)):
                    logging.error("Failed to fetch from bundle")
                    return False
        else:
            # New project - clone directly from bundle (must be full bundle)
            if not clone_from_bundle(str(bundle_path), str(temp_repo)):
                logging.error(
                    "Failed to clone from bundle. "
                    "For new projects, a full bundle is required."
                )
                return False

        # Temporarily unprotect branches for push
        protected_branches: list[str] = []
        if project_exists:
            protected_branches = client.list_protected_branches(dest_project.id)
            for branch in protected_branches:
                logging.info(f"Temporarily unprotecting branch: {branch}")
                client.unprotect_branch(dest_project.id, branch)

        # Push to destination
        logging.info(f"Pushing to {dest_url}")
        push_success = push_mirror(
            str(temp_repo),
            dest_url,
            token=dest_token,
        )

        # Re-protect branches
        for branch in protected_branches:
            logging.info(f"Re-protecting branch: {branch}")
            client.protect_branch(dest_project.id, branch)

        return push_success
