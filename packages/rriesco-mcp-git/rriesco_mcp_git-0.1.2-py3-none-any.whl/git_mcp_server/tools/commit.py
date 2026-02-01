"""Git commit tool with conventional commit format."""

import logging
from pathlib import Path
from typing import Any

from git import Repo
from git.exc import GitCommandError

from .. import mcp

logger = logging.getLogger(__name__)

# Valid conventional commit types
VALID_COMMIT_TYPES = [
    "feat",  # New feature
    "fix",  # Bug fix
    "docs",  # Documentation changes
    "style",  # Code style changes (formatting, etc.)
    "refactor",  # Code refactoring
    "perf",  # Performance improvements
    "test",  # Adding or updating tests
    "build",  # Build system changes
    "ci",  # CI/CD changes
    "chore",  # Maintenance tasks
    "revert",  # Revert previous commit
    "merge",  # Merge commits
]


def _validate_commit_type(commit_type: str) -> None:
    """Validate commit type follows conventional commits.

    Args:
        commit_type: Type of commit

    Raises:
        ValueError: If commit type is invalid
    """
    if commit_type not in VALID_COMMIT_TYPES:
        raise ValueError(
            f"Invalid commit type: {commit_type}. " f"Valid types: {', '.join(VALID_COMMIT_TYPES)}"
        )


def _validate_message(message: str) -> None:
    """Validate commit message is not empty.

    Args:
        message: Commit message

    Raises:
        ValueError: If message is empty or whitespace only
    """
    if not message or not message.strip():
        raise ValueError("Commit message cannot be empty")


def _build_commit_message(commit_type: str, message: str) -> str:
    """Build complete commit message with attribution.

    Args:
        commit_type: Type of commit (feat, fix, etc.)
        message: Short commit message

    Returns:
        Complete formatted commit message with Claude Code attribution
    """
    # Build subject line
    subject = f"{commit_type}: {message}"

    # Build full message with attribution
    parts = [
        subject,
        "",
        "🤖 Generated with [Claude Code](https://claude.com/claude-code)",
        "",
        "Co-Authored-By: Claude <noreply@anthropic.com>",
    ]

    return "\n".join(parts)


def _validate_files_exist(repo: Repo, files: list[str]) -> None:
    """Validate that all specified files exist in working directory.

    Args:
        repo: Git repository instance
        files: List of file paths to validate

    Raises:
        ValueError: If any file doesn't exist
    """
    repo_path = Path(repo.working_dir)

    for file_path in files:
        full_path = repo_path / file_path
        if not full_path.exists():
            raise ValueError(f"File not found: {file_path}")


def _get_commit_stats(repo: Repo, commit_sha: str) -> dict[str, int]:
    """Get statistics for a commit.

    Args:
        repo: Git repository instance
        commit_sha: SHA of the commit

    Returns:
        Dict with files_changed, insertions, deletions
    """
    commit = repo.commit(commit_sha)

    # Get stats from commit
    stats = commit.stats.total

    return {
        "files_changed": stats.get("files", 0),
        "insertions": stats.get("insertions", 0),
        "deletions": stats.get("deletions", 0),
    }


@mcp.tool()
def git_commit(
    type: str,
    message: str,
    files: list[str] | None = None,
    skip_hooks: bool = False,
) -> dict[str, Any]:
    """Create conventional commit (type: message) with Claude attribution.

    Types: feat, fix, docs, style, refactor, perf, test, build, ci, chore, revert

    Options:
    - files: commit specific files only (default: all changes)
    - skip_hooks: bypass pre-commit hooks via --no-verify

    Returns: {sha, stats: {files_changed, insertions, deletions}, message}
    """
    # Validate inputs
    _validate_commit_type(type)
    _validate_message(message)

    # Get repository (use Repo directly to avoid singleton caching issues)
    from pathlib import Path as P

    repo = Repo(P.cwd(), search_parent_directories=True)

    # Validate files exist before checking for changes
    if files:
        _validate_files_exist(repo, files)

    # Check for changes
    if not repo.is_dirty(untracked_files=True):
        raise ValueError("No changes to commit")

    # Build commit message
    commit_message = _build_commit_message(type, message)

    try:
        # Stage files
        if files:
            # Stage specific files
            repo.index.add(files)
        else:
            # Stage all changes (tracked and untracked)
            # Add all modified tracked files
            repo.git.add(A=True)

            # Add all untracked files
            if repo.untracked_files:
                repo.index.add(repo.untracked_files)

        # Create commit
        if skip_hooks:
            # Use --no-verify to skip hooks
            commit = repo.index.commit(commit_message, skip_hooks=True)
        else:
            commit = repo.index.commit(commit_message)

        # Get commit SHA
        commit_sha = commit.hexsha

        # Get commit stats
        stats = _get_commit_stats(repo, commit_sha)

        logger.info(f"Created commit {commit_sha[:8]} with {stats['files_changed']} file(s)")

        return {
            "sha": commit_sha,
            "stats": stats,
            "message": commit_message,
        }

    except GitCommandError as e:
        logger.error(f"Commit failed: {e}")
        raise ValueError(f"Failed to create commit: {e}") from e
