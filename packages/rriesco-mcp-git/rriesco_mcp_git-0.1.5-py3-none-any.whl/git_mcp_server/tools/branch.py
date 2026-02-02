"""Git branch creation tools."""

import logging
from typing import Any

from git.exc import GitCommandError

from .. import mcp
from ..utils import (
    branch_exists,
    get_main_branch_name,
    get_repo,
    validate_branch_name,
    validate_description,
)

logger = logging.getLogger(__name__)


@mcp.tool()
def git_create_branch(
    branch_name: str | None = None,
    issue_number: int | None = None,
    description: str | None = None,
    from_branch: str | None = None,
    pull_latest: bool = False,
) -> dict[str, Any]:
    """Create and checkout a git branch.

    Naming: branch_name (explicit) OR issue_number/description (auto: issue-N-desc or feature-desc).
    Options: from_branch (default: HEAD or main if auto-naming), pull_latest (default: False).

    Returns: {branch_name, previous_branch, sha, based_on}
    """
    repo = get_repo()
    previous_branch = repo.active_branch.name

    # Determine branch name
    if branch_name is not None:
        # Explicit branch name mode
        validate_branch_name(branch_name)
        target_branch = branch_name
        base_branch = from_branch  # Can be None (uses current HEAD)
    elif issue_number is not None or description is not None:
        # Auto-naming mode
        if description is not None:
            validate_description(description)

        if issue_number is not None:
            target_branch = (
                f"issue-{issue_number}-{description}" if description else f"issue-{issue_number}"
            )
        else:
            target_branch = f"feature-{description}"

        # Auto-naming defaults to main branch
        base_branch = from_branch if from_branch else get_main_branch_name(repo)
        # Auto-naming implies pull_latest unless explicitly from_branch
        if from_branch is None:
            pull_latest = True
    else:
        raise ValueError("Provide branch_name OR issue_number/description for auto-naming")

    # Check if branch already exists
    if branch_exists(repo, target_branch):
        raise ValueError(f"Branch '{target_branch}' already exists")

    # Validate from_branch if specified
    if base_branch is not None and not branch_exists(repo, base_branch):
        raise ValueError(f"Branch '{base_branch}' does not exist")

    try:
        # Switch to base branch if specified
        if base_branch is not None:
            repo.git.checkout(base_branch)

            # Pull latest if requested
            if pull_latest and repo.remotes:
                try:
                    repo.git.pull("origin", base_branch)
                    logger.info(f"Pulled latest from origin/{base_branch}")
                except GitCommandError:
                    logger.debug("Pull failed - continuing without pull")

        # Create new branch
        repo.git.checkout("-b", target_branch)
        sha = repo.head.commit.hexsha

        logger.info(f"Created branch '{target_branch}' at {sha[:8]}")

        return {
            "branch_name": target_branch,
            "previous_branch": previous_branch,
            "sha": sha,
            "based_on": base_branch,
        }

    except GitCommandError as e:
        logger.error(f"Failed to create branch: {e}")
        raise ValueError(f"Failed to create branch '{target_branch}': {e}") from e
