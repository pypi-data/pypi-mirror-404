# ----------------------------------------------------------------------------------------
#   upload
#   ------
#
#   Core upload logic - orchestrates the documentation upload process
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

import re
import shutil
import tempfile
import zipfile
from dataclasses import dataclass
from pathlib import Path
from typing import TYPE_CHECKING
from .constants import GITLAB_CI_YAML

if TYPE_CHECKING:
    from .config import Config
from .git_ops import add_files
from .git_ops import clone_repo
from .git_ops import commit
from .git_ops import configure_git_user
from .git_ops import has_changes
from .git_ops import init_repo
from .git_ops import inject_token_to_url
from .git_ops import push
from .git_ops import set_remote_url
from .gitlab_api import GitLabClient

# ----------------------------------------------------------------------------------------
#   Types
# ----------------------------------------------------------------------------------------


@dataclass
class UploadResult:
    """Result of the upload operation."""

    success: bool
    pages_url: str | None = None
    version_url: str | None = None
    latest_url: str | None = None
    error_message: str | None = None


# ----------------------------------------------------------------------------------------
#   Constants
# ----------------------------------------------------------------------------------------

# Version format: allow semver-like versions, dates, etc.
# Valid: 1.2.3, v1.2.3, 1.2.3-beta, 2024.01.15
# Invalid: ../escape, paths, special chars
VERSION_PATTERN = re.compile(r"^v?[0-9][0-9a-zA-Z._-]*$")

# ----------------------------------------------------------------------------------------
#   Functions
# ----------------------------------------------------------------------------------------


# ----------------------------------------------------------------------------------------
def validate_version(version: str) -> str | None:
    """
    Validate version string is safe for use as directory name.

    Parameters:
        version: Version string to validate

    Returns:
        Error message if invalid, None if valid
    """
    if not version:
        return "Version cannot be empty"

    if len(version) > 100:
        return "Version string too long (max 100 characters)"

    if ".." in version or "/" in version or "\\" in version:
        return "Version cannot contain path separators or '..'"

    if not VERSION_PATTERN.match(version):
        return (
            "Version must start with a digit (optionally prefixed with 'v') "
            "and contain only alphanumeric characters, dots, dashes, and underscores"
        )

    return None


# ----------------------------------------------------------------------------------------
def validate_html_source(html_path: Path) -> str | None:
    """
    Validate HTML source exists (directory or .zip file).

    Parameters:
        html_path: Path to HTML directory or .zip file

    Returns:
        Error message if invalid, None if valid
    """
    if not html_path.exists():
        return f"HTML source does not exist: {html_path}"

    if html_path.is_file():
        if not html_path.suffix.lower() == ".zip":
            return f"HTML source must be a directory or .zip file: {html_path}"
        # Validate it's a valid zip
        if not zipfile.is_zipfile(html_path):
            return f"Invalid zip file: {html_path}"
    elif not html_path.is_dir():
        return f"HTML source must be a directory or .zip file: {html_path}"

    return None


# ----------------------------------------------------------------------------------------
def validate_html_dir(html_dir: Path) -> str | None:
    """
    Validate HTML directory contains an index.html.

    Parameters:
        html_dir: Path to HTML directory

    Returns:
        Error message if invalid, None if valid
    """
    # Check for index.html
    if not (html_dir / "index.html").exists():
        return f"HTML directory must contain an index.html: {html_dir}"

    return None


# ----------------------------------------------------------------------------------------
def extract_zip(zip_path: Path, dest_dir: Path) -> Path:
    """
    Extract a zip file to a destination directory.

    Parameters:
        zip_path: Path to the zip file
        dest_dir: Directory to extract into

    Returns:
        Path to the extracted contents (handles single root dir case)
    """
    with zipfile.ZipFile(zip_path, "r") as zf:
        zf.extractall(dest_dir)

    # Check if zip contains a single root directory
    # If so, return that directory instead of dest_dir
    contents = list(dest_dir.iterdir())
    if len(contents) == 1 and contents[0].is_dir():
        return contents[0]

    return dest_dir


# ----------------------------------------------------------------------------------------
def count_files(directory: Path) -> int:
    """Count the number of files in a directory recursively."""
    return sum(1 for _ in directory.rglob("*") if _.is_file())


# ----------------------------------------------------------------------------------------
def upload_docs(config: Config, *, verbose: bool = False) -> UploadResult:
    """
    Upload documentation to GitLab Pages.

    Parameters:
        config: Upload configuration
        verbose: Whether to print verbose output

    Returns:
        UploadResult with success status and URLs
    """
    # Validate inputs
    version_error = validate_version(config.version)
    if version_error:
        return UploadResult(
            success=False, error_message=f"Invalid version: {version_error}"
        )

    source_error = validate_html_source(config.html_dir)
    if source_error:
        return UploadResult(success=False, error_message=source_error)

    if not config.token:
        return UploadResult(
            success=False,
            error_message=(
                "GITLAB_TOKEN environment variable not set.\n"
                "Hint: Create a Personal Access Token at "
                f"{config.gitlab_url}/-/user_settings/personal_access_tokens\n"
                "with 'api' and 'write_repository' scopes, then:\n"
                "  export GITLAB_TOKEN=glpat-xxxxxxxxxxxxxxxxxxxx"
            ),
        )

    # Handle zip file extraction
    zip_temp_dir: tempfile.TemporaryDirectory[str] | None = None
    html_dir = config.html_dir

    if config.html_dir.is_file() and config.html_dir.suffix.lower() == ".zip":
        if verbose:
            print(f"Extracting {config.html_dir.name}...", end=" ", flush=True)
        zip_temp_dir = tempfile.TemporaryDirectory()
        html_dir = extract_zip(config.html_dir, Path(zip_temp_dir.name))
        if verbose:
            print("done")

    # Validate extracted/provided directory has index.html
    html_error = validate_html_dir(html_dir)
    if html_error:
        if zip_temp_dir:
            zip_temp_dir.cleanup()
        return UploadResult(success=False, error_message=html_error)

    file_count = count_files(html_dir)
    if verbose:
        print(f"  Project: {config.project}")
        print(f"  Version: {config.version}")
        print(f"  HTML source: {config.html_dir} ({file_count} files)")
        print()

    # Create GitLab client
    client = GitLabClient(config.gitlab_url, config.token)

    # Ensure project exists
    if verbose:
        print(f"Checking GitLab group '{config.group}'...", end=" ", flush=True)

    try:
        project = client.ensure_project(config.group, config.project)
    except Exception as e:
        if zip_temp_dir:
            zip_temp_dir.cleanup()
        return UploadResult(
            success=False,
            error_message=f"Failed to create/access GitLab project: {e}",
        )

    if verbose:
        if project.empty_repo:
            print("created (new project)")
        else:
            print("exists")

    # Work in a temporary directory
    with tempfile.TemporaryDirectory() as temp_dir:
        repo_path = Path(temp_dir) / "repo"

        # Clone or init repo
        if verbose:
            print("Cloning repository...", end=" ", flush=True)

        if project.empty_repo:
            # New empty project - initialize
            success = init_repo(
                str(repo_path),
                project.http_url_to_repo,
                token=config.token,
            )
        else:
            # Existing project - clone
            success = clone_repo(
                project.http_url_to_repo,
                str(repo_path),
                token=config.token,
            )

        if not success:
            if zip_temp_dir:
                zip_temp_dir.cleanup()
            return UploadResult(
                success=False,
                error_message="Failed to clone/initialize repository",
            )

        if verbose:
            print("done")

        # Configure git user for commits
        configure_git_user(
            str(repo_path),
            "GitLab Pages Upload",
            "pages-upload@gitlab.local",
        )

        # Ensure public directory exists
        public_dir = repo_path / "public"
        public_dir.mkdir(exist_ok=True)

        # Check if version already exists
        version_dir = public_dir / config.version
        if version_dir.exists():
            if not config.force:
                if zip_temp_dir:
                    zip_temp_dir.cleanup()
                return UploadResult(
                    success=False,
                    error_message=(
                        f"Version {config.version} already exists. "
                        "Use --force to overwrite."
                    ),
                )
            shutil.rmtree(version_dir)

        if verbose:
            print(
                f"Copying documentation to public/{config.version}/...",
                end=" ",
                flush=True,
            )

        shutil.copytree(html_dir, version_dir)

        if verbose:
            print("done")

        # Optionally copy to public/latest/
        if config.set_latest:
            latest_dir = public_dir / "latest"
            if latest_dir.exists():
                shutil.rmtree(latest_dir)

            if verbose:
                print("Copying documentation to public/latest/...", end=" ", flush=True)

            shutil.copytree(html_dir, latest_dir)

            if verbose:
                print("done")

        # Write root index.html with redirect to latest (only if --set-latest)
        if config.set_latest:
            root_index = public_dir / "index.html"
            root_index.write_text("""\
<!DOCTYPE html>
<html>
<head>
    <meta charset="utf-8">
    <meta http-equiv="refresh" content="0; url=latest/">
    <title>Redirecting...</title>
</head>
<body>
    <p>Redirecting to <a href="latest/">latest/</a></p>
</body>
</html>
""")

            if verbose:
                print(
                    "Writing root index.html (redirects to latest/)...",
                    end=" ",
                    flush=True,
                )
                print("done")

        # Write .gitlab-ci.yml
        ci_file = repo_path / ".gitlab-ci.yml"
        ci_file.write_text(GITLAB_CI_YAML)

        if verbose:
            print("Writing .gitlab-ci.yml...", end=" ", flush=True)
            print("done")

        # Stage files
        add_files(str(repo_path), "public/", ".gitlab-ci.yml")

        # Commit if there are changes
        if has_changes(str(repo_path)):
            if verbose:
                print("Committing changes...", end=" ", flush=True)

            commit_msg = f"Upload docs v{config.version}"
            if config.set_latest:
                commit_msg += " (set as latest)"

            success = commit(str(repo_path), commit_msg)
            if not success:
                if zip_temp_dir:
                    zip_temp_dir.cleanup()
                return UploadResult(
                    success=False,
                    error_message="Failed to commit changes",
                )

            if verbose:
                print("done")
        else:
            if verbose:
                print("No changes to commit (docs already up to date)")

        # Set remote URL with token for push
        set_remote_url(
            str(repo_path),
            inject_token_to_url(project.http_url_to_repo, config.token),
        )

        # Push
        if verbose:
            print("Pushing to GitLab...", end=" ", flush=True)

        success = push(str(repo_path), set_upstream=project.empty_repo)
        if not success:
            if zip_temp_dir:
                zip_temp_dir.cleanup()
            return UploadResult(
                success=False,
                error_message="Failed to push to GitLab",
            )

        if verbose:
            print("done")

    # Clean up zip temp directory if used
    if zip_temp_dir:
        zip_temp_dir.cleanup()

    # Build result URLs
    pages_url = client.get_pages_url(config.group, config.project)
    version_url = f"{pages_url}{config.version}/"
    latest_url = f"{pages_url}latest/" if config.set_latest else None

    return UploadResult(
        success=True,
        pages_url=pages_url,
        version_url=version_url,
        latest_url=latest_url,
    )
