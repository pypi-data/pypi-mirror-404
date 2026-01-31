# ----------------------------------------------------------------------------------------
#   git_ops
#   -------
#
#   Git operations using subprocess
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
from pathlib import Path
from urllib.parse import urlparse
from urllib.parse import urlunparse
from .exec import redact_secrets
from .exec import run_command

# ----------------------------------------------------------------------------------------
#   Functions
# ----------------------------------------------------------------------------------------


# ----------------------------------------------------------------------------------------
def inject_token_to_url(url: str, token: str) -> str:
    """
    Inject OAuth2 token into HTTPS URL for authentication.

    Parameters:
        url: Git remote URL (https://gitlab.com/group/project.git)
        token: Personal access token

    Returns:
        URL with token (https://oauth2:TOKEN@gitlab.com/group/project.git)
    """
    parsed = urlparse(url)
    if parsed.scheme != "https":
        return url

    # Add oauth2:token as username:password
    netloc = f"oauth2:{token}@{parsed.hostname}"
    if parsed.port:
        netloc = f"{netloc}:{parsed.port}"

    return urlunparse(
        (
            parsed.scheme,
            netloc,
            parsed.path,
            parsed.params,
            parsed.query,
            parsed.fragment,
        )
    )


# ----------------------------------------------------------------------------------------
def clone_mirror(url: str, dest_path: str, *, token: str | None = None) -> bool:
    """
    Clone a repository with --mirror flag for full clone.

    Parameters:
        url: Repository URL
        dest_path: Destination path for bare repo
        token: Optional token to inject into URL

    Returns:
        True on success, False on failure
    """
    if token:
        url = inject_token_to_url(url, token)

    result = run_command(["git", "clone", "--mirror", url, dest_path])

    if not result.success:
        logging.error(f"Clone failed: {redact_secrets(result.stderr)}")
        return False

    return True


# ----------------------------------------------------------------------------------------
def fetch_mirror(repo_path: str, *, token: str | None = None) -> bool:
    """
    Fetch all updates for a mirrored repo.

    Parameters:
        repo_path: Path to bare git repo
        token: Optional token (updates remote URL temporarily)

    Returns:
        True on success, False on failure
    """
    # If token provided, temporarily set remote URL with auth
    if token:
        # Get current remote URL
        result = run_command(
            ["git", "remote", "get-url", "origin"],
            cwd=repo_path,
        )
        if not result.success:
            logging.error(f"Failed to get remote URL: {redact_secrets(result.stderr)}")
            return False

        original_url = result.stdout.strip()
        auth_url = inject_token_to_url(original_url, token)

        # Set remote URL with auth
        run_command(["git", "remote", "set-url", "origin", auth_url], cwd=repo_path)

        # Fetch
        result = run_command(
            ["git", "fetch", "--all", "--prune"],
            cwd=repo_path,
        )

        # Restore original URL (without token)
        run_command(["git", "remote", "set-url", "origin", original_url], cwd=repo_path)
    else:
        result = run_command(
            ["git", "fetch", "--all", "--prune"],
            cwd=repo_path,
        )

    if not result.success:
        logging.error(f"Fetch failed: {redact_secrets(result.stderr)}")
        return False

    return True


# ----------------------------------------------------------------------------------------
def push_mirror(repo_path: str, remote_url: str, *, token: str | None = None) -> bool:
    """
    Push all branches and tags to remote.

    Note: We don't use --mirror because it tries to push refs/merge-requests/*
    which GitLab rejects. Instead we push branches and tags explicitly.

    Parameters:
        repo_path: Path to bare git repo
        remote_url: Remote URL to push to
        token: Optional token to inject into URL

    Returns:
        True on success, False on failure
    """
    if token:
        remote_url = inject_token_to_url(remote_url, token)

    # Push all branches
    result = run_command(
        ["git", "push", "--force", remote_url, "refs/heads/*:refs/heads/*"],
        cwd=repo_path,
    )

    if not result.success:
        logging.error(f"Push branches failed: {redact_secrets(result.stderr)}")
        return False

    # Push all tags
    result = run_command(
        ["git", "push", "--force", remote_url, "refs/tags/*:refs/tags/*"],
        cwd=repo_path,
    )

    if not result.success:
        logging.error(f"Push tags failed: {redact_secrets(result.stderr)}")
        return False

    return True


# ----------------------------------------------------------------------------------------
def create_bundle(
    repo_path: str,
    bundle_path: str,
    *,
    since_days: int | None = None,
) -> bool:
    """
    Create a git bundle file.

    Parameters:
        repo_path: Path to git repo
        bundle_path: Output path for bundle file
        since_days: If provided, only include commits from last N days

    Returns:
        True on success, False on failure
    """
    # Ensure parent directory exists and get absolute path
    bundle_path_obj = Path(bundle_path).resolve()
    bundle_path_obj.parent.mkdir(parents=True, exist_ok=True)
    bundle_path = str(bundle_path_obj)

    if since_days:
        # Incremental bundle - only recent commits
        result = run_command(
            [
                "git",
                "bundle",
                "create",
                bundle_path,
                "--all",
                f"--since={since_days} days ago",
            ],
            cwd=repo_path,
        )
    else:
        # Full bundle
        result = run_command(
            ["git", "bundle", "create", bundle_path, "--all"],
            cwd=repo_path,
        )

    if not result.success:
        # Bundle creation fails if there are no commits matching criteria
        if "empty bundle" in result.stderr.lower():
            logging.info("No new commits to bundle")
            return True
        logging.error(f"Bundle creation failed: {result.stderr}")
        return False

    return True


# ----------------------------------------------------------------------------------------
def clone_from_bundle(bundle_path: str, dest_path: str) -> bool:
    """
    Clone a repository from a bundle file.

    Parameters:
        bundle_path: Path to bundle file
        dest_path: Destination path for bare repo

    Returns:
        True on success, False on failure
    """
    # Ensure parent directory exists
    Path(dest_path).parent.mkdir(parents=True, exist_ok=True)

    # Clone from bundle as bare repo
    result = run_command(["git", "clone", "--bare", bundle_path, dest_path])

    if not result.success:
        logging.error(f"Clone from bundle failed: {redact_secrets(result.stderr)}")
        return False

    return True


# ----------------------------------------------------------------------------------------
def fetch_from_bundle(repo_path: str, bundle_path: str) -> bool:
    """
    Fetch updates from a bundle file into an existing repo.

    Parameters:
        repo_path: Path to existing git repo
        bundle_path: Path to bundle file

    Returns:
        True on success, False on failure
    """
    # Ensure absolute path for bundle
    bundle_path = str(Path(bundle_path).resolve())

    # Fetch all refs from bundle (+ prefix allows non-fast-forward updates)
    result = run_command(
        ["git", "fetch", bundle_path, "+*:*"],
        cwd=repo_path,
    )

    if not result.success:
        # Try alternative approach - fetch refs/heads and refs/tags separately
        result = run_command(
            ["git", "fetch", bundle_path, "+refs/heads/*:refs/heads/*"],
            cwd=repo_path,
        )
        if not result.success:
            logging.error(f"Fetch from bundle failed: {result.stderr}")
            return False

        # Also fetch tags
        run_command(
            ["git", "fetch", bundle_path, "refs/tags/*:refs/tags/*"],
            cwd=repo_path,
        )

    return True


# ----------------------------------------------------------------------------------------
def get_repo_refs(repo_path: str) -> dict[str, str]:
    """
    Get all refs and their commit hashes.

    Parameters:
        repo_path: Path to git repo

    Returns:
        Dict mapping ref names to commit hashes
    """
    result = run_command(
        ["git", "show-ref"],
        cwd=repo_path,
    )

    refs: dict[str, str] = {}
    if result.success:
        for line in result.stdout.strip().split("\n"):
            if line:
                parts = line.split(" ", 1)
                if len(parts) == 2:
                    commit_hash, ref_name = parts
                    refs[ref_name] = commit_hash

    return refs


# ----------------------------------------------------------------------------------------
def is_git_repo(path: str) -> bool:
    """Check if path is a git repository."""
    git_dir = Path(path)
    # Check for bare repo (has HEAD directly) or regular repo (has .git)
    return (git_dir / "HEAD").exists() or (git_dir / ".git").exists()


# ----------------------------------------------------------------------------------------
def get_remote_url(repo_path: str) -> str | None:
    """Get the origin remote URL of a repo."""
    result = run_command(
        ["git", "remote", "get-url", "origin"],
        cwd=repo_path,
    )
    if result.success:
        return result.stdout.strip()
    return None
