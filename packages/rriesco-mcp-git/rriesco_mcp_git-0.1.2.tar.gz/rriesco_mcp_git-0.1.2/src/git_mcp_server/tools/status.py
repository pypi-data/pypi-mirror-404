"""Git repository status tool."""

import logging
from typing import Any

from git import Repo

from .. import mcp
from ..utils import get_repo

logger = logging.getLogger(__name__)


def _get_tracking_info(repo: Repo) -> tuple[str | None, int, int]:
    """Get tracking branch information including ahead/behind counts.

    Args:
        repo: Git repository instance

    Returns:
        Tuple of (tracking_branch_name, ahead_count, behind_count)
    """
    tracking_branch = None
    ahead = 0
    behind = 0

    try:
        tracking = repo.active_branch.tracking_branch()
        if tracking:
            tracking_branch = tracking.name

            # Calculate ahead/behind commits
            # Commits in local but not in tracking (ahead)
            ahead_commits = list(repo.iter_commits(f"{tracking_branch}..{repo.active_branch.name}"))
            ahead = len(ahead_commits)

            # Commits in tracking but not in local (behind)
            behind_commits = list(
                repo.iter_commits(f"{repo.active_branch.name}..{tracking_branch}")
            )
            behind = len(behind_commits)
    except Exception:
        # No tracking branch configured or error calculating
        pass

    return tracking_branch, ahead, behind


def _get_staged_files(repo: Repo) -> list[str]:
    """Get list of staged files.

    Args:
        repo: Git repository instance

    Returns:
        List of staged file paths relative to repo root
    """
    staged = []
    try:
        # Staged files from index compared to HEAD
        diff_index = repo.index.diff("HEAD")
        for diff in diff_index:
            # Use a_path for deleted files, b_path for added/modified
            path = diff.b_path or diff.a_path
            if path:
                staged.append(path)
    except Exception:
        # Handle empty repo (no HEAD) or other issues
        pass

    return staged


def _get_modified_files(repo: Repo) -> list[str]:
    """Get list of modified (unstaged) files.

    Args:
        repo: Git repository instance

    Returns:
        List of modified file paths relative to repo root
    """
    modified = []
    try:
        # Modified files from working directory compared to index
        diff_working = repo.index.diff(None)
        for diff in diff_working:
            path = diff.b_path or diff.a_path
            if path:
                modified.append(path)
    except Exception:
        pass

    return modified


@mcp.tool()
def git_status() -> dict[str, Any]:
    """Get repository status: branch, tracking info, and file changes.

    Returns: {branch, tracking, ahead, behind, staged, modified, untracked, clean}

    clean=True means no staged, modified, or untracked files.
    """
    repo = get_repo()

    # Check for detached HEAD
    if repo.head.is_detached:
        raise ValueError("Repository is in detached HEAD state")

    # Get branch name
    branch_name = repo.active_branch.name

    # Get tracking branch info
    tracking_branch, ahead, behind = _get_tracking_info(repo)

    # Get staged files
    staged = _get_staged_files(repo)

    # Get modified files (unstaged)
    modified = _get_modified_files(repo)

    # Get untracked files
    untracked = list(repo.untracked_files) if repo.untracked_files else []

    # Check if repository is clean
    clean = len(staged) == 0 and len(modified) == 0 and len(untracked) == 0

    logger.info(
        f"Status: branch={branch_name}, clean={clean}, "
        f"staged={len(staged)}, modified={len(modified)}, untracked={len(untracked)}"
    )

    return {
        "branch": branch_name,
        "tracking": tracking_branch,
        "ahead": ahead,
        "behind": behind,
        "staged": staged,
        "modified": modified,
        "untracked": untracked,
        "clean": clean,
    }
