"""Git repository utilities."""

import os
import re
from pathlib import Path

from git import Repo
from git.exc import InvalidGitRepositoryError

# Module-level singleton instance
_repo_instance: Repo | None = None


def get_repo() -> Repo:
    """Get or create Git repository instance (singleton)."""
    global _repo_instance

    if _repo_instance is None:
        cwd = Path.cwd()
        try:
            _repo_instance = Repo(cwd, search_parent_directories=True)
        except InvalidGitRepositoryError as e:
            raise ValueError(
                f"Not a git repository: {cwd}\n"
                f"Please run this tool from within a git repository."
            ) from e

    return _repo_instance


def reset_repo() -> None:
    """Reset repository instance (for testing)."""
    global _repo_instance
    _repo_instance = None


def get_current_branch(repo: Repo) -> str:
    """Get current branch name. Raises ValueError if detached HEAD."""
    if repo.head.is_detached:
        raise ValueError("Cannot operate in detached HEAD state. Checkout a branch first.")
    return repo.active_branch.name


def get_remote_url_with_auth(repo: Repo, remote: str = "origin") -> str | None:
    """Get remote URL with GITHUB_TOKEN auth if available."""
    token = os.getenv("GITHUB_TOKEN")
    if not token:
        return None

    try:
        remote_obj = repo.remote(remote)
        url = remote_obj.url

        if "github.com" in url:
            if url.startswith("https://"):
                return url.replace("https://", f"https://{token}@")
            elif url.startswith("git@github.com:"):
                path = url.replace("git@github.com:", "")
                return f"https://{token}@github.com/{path}"
        return None
    except Exception:
        return None


def get_main_branch_name(repo: Repo) -> str:
    """Detect main branch name (main or master)."""
    branch_names = [branch.name for branch in repo.branches]
    if "main" in branch_names:
        return "main"
    if "master" in branch_names:
        return "master"
    return "master"


def branch_exists(repo: Repo, branch_name: str) -> bool:
    """Check if a branch exists."""
    return branch_name in [branch.name for branch in repo.branches]


def validate_branch_name(branch_name: str) -> None:
    """Validate branch name follows git conventions. Raises ValueError if invalid."""
    if not branch_name or not branch_name.strip():
        raise ValueError("Branch name cannot be empty")

    invalid_pattern = r"[\s~^:?*\[\]\\]|\.{2}"
    if re.search(invalid_pattern, branch_name):
        raise ValueError(
            f"Invalid branch name: {branch_name}. "
            "Cannot contain spaces or special characters (~, ^, :, ?, *, [, ], \\, ..)"
        )


def validate_description(description: str) -> None:
    """Validate branch description (lowercase with hyphens)."""
    pattern = r"^[a-z0-9]+(-[a-z0-9]+)*$"
    if not re.match(pattern, description):
        raise ValueError(
            f"Description must be lowercase with hyphens (e.g. 'add-feature'). Got: {description}"
        )
