"""Structured error handling for git operations.

This module provides structured error types and conversion functions for
common git errors. All errors include:
- Error type classification
- Human-readable message
- Actionable suggestion for fixing
- Optional command to run

This enables tools to provide helpful, actionable feedback to users.
"""

import logging
from dataclasses import dataclass

from git.exc import (
    GitCommandError,
    InvalidGitRepositoryError,
)

logger = logging.getLogger(__name__)


@dataclass(frozen=True)
class GitError:
    """Structured git error with actionable suggestions.

    Attributes:
        error_type: Classification of the error (e.g., "not_a_repo", "merge_conflict")
        message: Human-readable error message
        suggestion: Actionable suggestion for fixing the error
        command: Optional command to run to fix the issue
    """

    error_type: str
    message: str
    suggestion: str
    command: str | None = None


def handle_git_error(e: Exception) -> GitError:
    """Convert git exceptions to structured errors.

    Args:
        e: Exception raised by git operation

    Returns:
        GitError with error type, message, suggestion, and optional command

    Example:
        >>> try:
        ...     repo.git.push()
        ... except GitCommandError as e:
        ...     error = handle_git_error(e)
        ...     print(error.message)
        ...     print(error.suggestion)
    """
    # Invalid git repository
    if isinstance(e, InvalidGitRepositoryError):
        logger.error(f"Not a git repository: {e}")
        return GitError(
            error_type="not_a_repo",
            message=str(e),
            suggestion="Navigate to a git repository before running git commands.",
            command="git status",
        )

    # Git command failed
    if isinstance(e, GitCommandError):
        logger.error(f"Git command failed: {e}")

        # Authentication failures
        if "authentication failed" in str(e).lower() or "permission denied" in str(e).lower():
            return GitError(
                error_type="auth_failed",
                message="Git authentication failed",
                suggestion=(
                    "Check your git credentials. For HTTPS, verify your personal access token. "
                    "For SSH, ensure your SSH key is configured correctly."
                ),
                command="git config --list | grep credential",
            )

        # Merge conflicts
        if "conflict" in str(e).lower() or "merge" in str(e).lower():
            return GitError(
                error_type="merge_conflict",
                message="Merge conflict detected",
                suggestion=(
                    "Resolve merge conflicts in affected files, "
                    "then stage and commit the resolution."
                ),
                command="git status",
            )

        # Detached HEAD
        if "detached head" in str(e).lower():
            return GitError(
                error_type="detached_head",
                message="Repository is in detached HEAD state",
                suggestion="Create a new branch or checkout an existing branch to continue.",
                command="git checkout -b new-branch-name",
            )

        # Nothing to commit
        if "nothing to commit" in str(e).lower():
            return GitError(
                error_type="nothing_to_commit",
                message="No changes to commit",
                suggestion=(
                    "Make changes to files before committing, "
                    "or use 'git status' to see current state."
                ),
                command="git status",
            )

        # No remote configured
        if (
            "no configured push destination" in str(e).lower()
            or "no upstream branch" in str(e).lower()
        ):
            return GitError(
                error_type="no_remote",
                message="No remote repository configured",
                suggestion=(
                    "Set up a remote repository or specify the remote branch when pushing. "
                    "Use 'git remote add origin <url>' to add a remote."
                ),
                command="git remote -v",
            )

        # Generic git command error
        return GitError(
            error_type="git_command_failed",
            message=f"Git command failed: {e}",
            suggestion=(
                "Check the error message above for details. "
                "Run 'git status' to see repository state."
            ),
            command="git status",
        )

    # ValueError (e.g., from get_repo())
    if isinstance(e, ValueError):
        logger.error(f"Validation error: {e}")
        return GitError(
            error_type="validation_error",
            message=str(e),
            suggestion="Check the error message and verify your input parameters.",
            command=None,
        )

    # Unknown error
    logger.error(f"Unknown error: {e}")
    return GitError(
        error_type="unknown_error",
        message=f"Unexpected error: {e}",
        suggestion="Check the error message above. If the issue persists, please report it.",
        command="git status",
    )
