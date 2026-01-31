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
def clone_repo(url: str, dest_path: str, *, token: str | None = None) -> bool:
    """
    Clone a repository.

    Parameters:
        url: Repository URL
        dest_path: Destination path
        token: Optional token to inject into URL

    Returns:
        True on success, False on failure
    """
    if token:
        url = inject_token_to_url(url, token)

    result = run_command(["git", "clone", url, dest_path])

    if not result.success:
        logging.error(f"Clone failed: {redact_secrets(result.stderr)}")
        return False

    return True


# ----------------------------------------------------------------------------------------
def init_repo(dest_path: str, remote_url: str, *, token: str | None = None) -> bool:
    """
    Initialize a new git repository with remote.

    Parameters:
        dest_path: Path to create repo
        remote_url: Remote URL to set as origin
        token: Optional token to inject into URL

    Returns:
        True on success, False on failure
    """
    path = Path(dest_path)
    path.mkdir(parents=True, exist_ok=True)

    # Initialize repo
    result = run_command(["git", "init"], cwd=dest_path)
    if not result.success:
        logging.error(f"Git init failed: {result.stderr}")
        return False

    # Set default branch to main
    result = run_command(["git", "checkout", "-b", "main"], cwd=dest_path)
    if not result.success:
        logging.error(f"Failed to create main branch: {result.stderr}")
        return False

    # Add remote
    if token:
        remote_url = inject_token_to_url(remote_url, token)

    result = run_command(["git", "remote", "add", "origin", remote_url], cwd=dest_path)
    if not result.success:
        logging.error(f"Failed to add remote: {redact_secrets(result.stderr)}")
        return False

    return True


# ----------------------------------------------------------------------------------------
def configure_git_user(repo_path: str, name: str, email: str) -> bool:
    """
    Configure git user for a repository.

    Parameters:
        repo_path: Path to git repo
        name: User name
        email: User email

    Returns:
        True on success, False on failure
    """
    result = run_command(["git", "config", "user.name", name], cwd=repo_path)
    if not result.success:
        logging.error(f"Failed to set git user.name: {result.stderr}")
        return False

    result = run_command(["git", "config", "user.email", email], cwd=repo_path)
    if not result.success:
        logging.error(f"Failed to set git user.email: {result.stderr}")
        return False

    return True


# ----------------------------------------------------------------------------------------
def add_files(repo_path: str, *paths: str) -> bool:
    """
    Stage files for commit.

    Parameters:
        repo_path: Path to git repo
        *paths: Paths to add (relative to repo)

    Returns:
        True on success, False on failure
    """
    result = run_command(["git", "add", *paths], cwd=repo_path)
    if not result.success:
        logging.error(f"Git add failed: {result.stderr}")
        return False
    return True


# ----------------------------------------------------------------------------------------
def has_changes(repo_path: str) -> bool:
    """
    Check if there are any staged or unstaged changes.

    Parameters:
        repo_path: Path to git repo

    Returns:
        True if there are changes, False otherwise
    """
    result = run_command(["git", "status", "--porcelain"], cwd=repo_path)
    return bool(result.stdout.strip())


# ----------------------------------------------------------------------------------------
def commit(repo_path: str, message: str) -> bool:
    """
    Create a commit with the staged changes.

    Parameters:
        repo_path: Path to git repo
        message: Commit message

    Returns:
        True on success, False on failure (including no changes)
    """
    result = run_command(["git", "commit", "-m", message], cwd=repo_path)
    if not result.success:
        # "nothing to commit" is not an error for our purposes
        if "nothing to commit" in result.stdout or "nothing to commit" in result.stderr:
            logging.info("No changes to commit")
            return True
        logging.error(f"Git commit failed: {result.stderr}")
        return False
    return True


# ----------------------------------------------------------------------------------------
def push(
    repo_path: str,
    *,
    remote: str = "origin",
    branch: str = "main",
    set_upstream: bool = False,
) -> bool:
    """
    Push commits to remote.

    Parameters:
        repo_path: Path to git repo
        remote: Remote name
        branch: Branch name
        set_upstream: Whether to set upstream tracking

    Returns:
        True on success, False on failure
    """
    args = ["git", "push"]
    if set_upstream:
        args.extend(["-u", remote, branch])
    else:
        args.extend([remote, branch])

    result = run_command(args, cwd=repo_path)
    if not result.success:
        logging.error(f"Git push failed: {redact_secrets(result.stderr)}")
        return False
    return True


# ----------------------------------------------------------------------------------------
def is_git_repo(path: str) -> bool:
    """Check if path is a git repository."""
    git_dir = Path(path)
    # Check for bare repo (has HEAD directly) or regular repo (has .git)
    return (git_dir / "HEAD").exists() or (git_dir / ".git").exists()


# ----------------------------------------------------------------------------------------
def get_default_branch(repo_path: str) -> str | None:
    """Get the default branch name of a repo."""
    result = run_command(
        ["git", "symbolic-ref", "--short", "HEAD"],
        cwd=repo_path,
    )
    if result.success:
        return result.stdout.strip()
    return None


# ----------------------------------------------------------------------------------------
def set_remote_url(repo_path: str, url: str, *, remote: str = "origin") -> bool:
    """
    Set the remote URL (with token for push).

    Parameters:
        repo_path: Path to git repo
        url: New remote URL
        remote: Remote name

    Returns:
        True on success, False on failure
    """
    result = run_command(["git", "remote", "set-url", remote, url], cwd=repo_path)
    if not result.success:
        logging.error(f"Failed to set remote URL: {redact_secrets(result.stderr)}")
        return False
    return True
