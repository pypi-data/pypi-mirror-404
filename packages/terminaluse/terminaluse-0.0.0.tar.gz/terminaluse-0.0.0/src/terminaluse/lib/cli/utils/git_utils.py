"""Git detection utilities for deployment flow.

Detects git information (branch, commit hash, dirty state) from the current directory
to support image tagging and deployment tracking.
"""

from __future__ import annotations

import subprocess
from datetime import datetime
from dataclasses import dataclass


@dataclass
class GitInfo:
    """Git repository information."""

    branch: str | None
    commit_hash: str | None
    commit_message: str | None
    is_dirty: bool
    is_git_repo: bool


def detect_git_info(repo_path: str = ".") -> GitInfo:
    """Detect git information from the specified directory.

    Args:
        repo_path: Path to the repository (default: current directory)

    Returns:
        GitInfo containing branch, commit hash, message, and dirty state
    """
    # Check if this is a git repository
    try:
        subprocess.run(
            ["git", "rev-parse", "--git-dir"],
            cwd=repo_path,
            capture_output=True,
            check=True,
        )
    except (subprocess.CalledProcessError, FileNotFoundError):
        return GitInfo(
            branch=None,
            commit_hash=None,
            commit_message=None,
            is_dirty=False,
            is_git_repo=False,
        )

    # Get current branch
    branch_result = subprocess.run(
        ["git", "rev-parse", "--abbrev-ref", "HEAD"],
        cwd=repo_path,
        capture_output=True,
        text=True,
    )
    branch = branch_result.stdout.strip() if branch_result.returncode == 0 else None

    # Handle detached HEAD state
    if branch == "HEAD":
        branch = None

    # Get full commit hash
    hash_result = subprocess.run(
        ["git", "rev-parse", "HEAD"],
        cwd=repo_path,
        capture_output=True,
        text=True,
    )
    commit_hash = hash_result.stdout.strip() if hash_result.returncode == 0 else None

    # Get commit message (first line only)
    msg_result = subprocess.run(
        ["git", "log", "-1", "--format=%s"],
        cwd=repo_path,
        capture_output=True,
        text=True,
    )
    commit_message = msg_result.stdout.strip() if msg_result.returncode == 0 else None

    # Check for uncommitted changes (dirty state)
    dirty_result = subprocess.run(
        ["git", "status", "--porcelain"],
        cwd=repo_path,
        capture_output=True,
        text=True,
    )
    is_dirty = bool(dirty_result.stdout.strip())

    return GitInfo(
        branch=branch,
        commit_hash=commit_hash,
        commit_message=commit_message,
        is_dirty=is_dirty,
        is_git_repo=True,
    )


def generate_image_tag(git_info: GitInfo) -> str:
    """Generate an image tag from git info or timestamp.

    Args:
        git_info: Git repository information

    Returns:
        Image tag string (commit hash prefix or nogit-timestamp)
    """
    if git_info.is_git_repo and git_info.commit_hash:
        # Use first 12 characters of commit hash
        return git_info.commit_hash[:12]
    else:
        # No git repo - use timestamp-based tag
        return f"nogit-{datetime.now().strftime('%Y%m%d%H%M%S')}"


def get_short_hash(git_info: GitInfo, length: int = 8) -> str | None:
    """Get a short version of the commit hash.

    Args:
        git_info: Git repository information
        length: Number of characters to include (default: 8)

    Returns:
        Short commit hash or None if not available
    """
    if git_info.commit_hash:
        return git_info.commit_hash[:length]
    return None


@dataclass
class GitAuthor:
    """Git author information."""

    name: str | None
    email: str | None


def detect_git_author(repo_path: str = ".") -> GitAuthor:
    """Detect git author information from git config.

    Args:
        repo_path: Path to the repository (default: current directory)

    Returns:
        GitAuthor with name and email from git config
    """
    name = None
    email = None

    # Get author name from git config
    try:
        name_result = subprocess.run(
            ["git", "config", "user.name"],
            cwd=repo_path,
            capture_output=True,
            text=True,
        )
        if name_result.returncode == 0:
            name = name_result.stdout.strip() or None
    except (subprocess.CalledProcessError, FileNotFoundError):
        pass

    # Get author email from git config
    try:
        email_result = subprocess.run(
            ["git", "config", "user.email"],
            cwd=repo_path,
            capture_output=True,
            text=True,
        )
        if email_result.returncode == 0:
            email = email_result.stdout.strip() or None
    except (subprocess.CalledProcessError, FileNotFoundError):
        pass

    return GitAuthor(name=name, email=email)
