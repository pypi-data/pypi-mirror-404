"""Git remote synchronization tools."""

import logging
from typing import Any

from git import Repo
from git.exc import GitCommandError

from .. import mcp
from ..utils import get_current_branch, get_remote_url_with_auth, get_repo

logger = logging.getLogger(__name__)


def _count_commits_ahead_behind(repo: Repo, branch: str, remote: str) -> tuple[int, int]:
    """Count commits ahead and behind remote.

    Args:
        repo: Git repository instance
        branch: Branch name
        remote: Remote name

    Returns:
        Tuple of (ahead, behind) commit counts
    """
    try:
        # Get local and remote refs
        local_ref = f"{branch}"
        remote_ref = f"{remote}/{branch}"

        # Count commits ahead (local has, remote doesn't)
        ahead = len(list(repo.iter_commits(f"{remote_ref}..{local_ref}")))

        # Count commits behind (remote has, local doesn't)
        behind = len(list(repo.iter_commits(f"{local_ref}..{remote_ref}")))

        return ahead, behind
    except Exception:
        # If remote branch doesn't exist, we're pushing a new branch
        return 0, 0


@mcp.tool()
def git_push(
    remote: str = "origin",
    branch: str | None = None,
    set_upstream: bool = True,
    force: bool = False,
) -> dict[str, Any]:
    """Push commits to remote. Uses GITHUB_TOKEN from env if available.

    Options:
    - branch: specific branch (default: current)
    - set_upstream: track new branches (default: True)
    - force: force push (use with caution!)

    Returns: {branch, remote, sha, commits_pushed, is_new_branch, force}
    """
    repo = get_repo()

    # Determine branch to push
    target_branch = branch if branch else get_current_branch(repo)

    # Check if remote exists
    try:
        remote_obj = repo.remote(remote)
    except ValueError as e:
        raise ValueError(f"Remote '{remote}' not found. Use 'git remote add' first.") from e

    # Check if this is a new branch
    remote_branches = [ref.name for ref in remote_obj.refs]
    is_new_branch = f"{remote}/{target_branch}" not in remote_branches

    # Get commits ahead before push
    commits_ahead, _ = _count_commits_ahead_behind(repo, target_branch, remote)

    # Get current SHA
    sha = repo.head.commit.hexsha

    try:
        # Try push with token auth if available
        auth_url = get_remote_url_with_auth(repo, remote)

        # Build push args
        push_args = []
        if set_upstream and is_new_branch:
            push_args.append("-u")
        if force:
            push_args.append("--force")

        if auth_url:
            # Push using authenticated URL
            push_args.extend([auth_url, target_branch])
            repo.git.push(*push_args)
        else:
            # Push using configured remote
            push_args.extend([remote, target_branch])
            repo.git.push(*push_args)

        logger.info(f"Pushed {target_branch} to {remote}")

        return {
            "branch": target_branch,
            "remote": remote,
            "sha": sha,
            "commits_pushed": commits_ahead if not is_new_branch else 1,
            "is_new_branch": is_new_branch,
            "force": force,
        }

    except GitCommandError as e:
        error_str = str(e).lower()

        if "authentication failed" in error_str or "permission denied" in error_str:
            raise ValueError(
                "Authentication failed. Ensure GITHUB_TOKEN is set in environment, "
                "or configure git credentials."
            ) from e

        if "rejected" in error_str and "non-fast-forward" in error_str:
            raise ValueError(
                "Push rejected: Remote has changes not in local branch. "
                "Pull first with 'git_pull()', or use force=True (caution!)."
            ) from e

        if "does not appear to be a git repository" in error_str:
            raise ValueError(f"Remote '{remote}' is not a valid git repository.") from e

        raise ValueError(f"Push failed: {e}") from e


@mcp.tool()
def git_pull(
    remote: str = "origin",
    branch: str | None = None,
) -> dict[str, Any]:
    """Pull commits from remote. Uses GITHUB_TOKEN from env if available.

    Fails if there are uncommitted changes (commit or stash first).

    Returns: {branch, remote, sha_before, sha_after, commits_pulled, files_changed, up_to_date}
    """
    repo = get_repo()

    # Determine branch to pull
    target_branch = branch if branch else get_current_branch(repo)

    # Check if remote exists
    try:
        repo.remote(remote)
    except ValueError as e:
        raise ValueError(f"Remote '{remote}' not found. Use 'git remote add' first.") from e

    # Get SHA before pull
    sha_before = repo.head.commit.hexsha

    # Check for uncommitted changes
    if repo.is_dirty(untracked_files=True):
        raise ValueError("Cannot pull with uncommitted changes. Commit or stash changes first.")

    try:
        # Try pull with token auth if available
        auth_url = get_remote_url_with_auth(repo, remote)

        if auth_url:
            # Pull using authenticated URL
            repo.git.pull(auth_url, target_branch, "--no-edit")
        else:
            # Pull using configured remote
            repo.git.pull(remote, target_branch, "--no-edit")

        # Get SHA after pull
        sha_after = repo.head.commit.hexsha

        # Calculate commits pulled
        if sha_before == sha_after:
            commits_pulled = 0
            files_changed: list[str] = []
            up_to_date = True
        else:
            # Count commits between old and new HEAD
            commits_pulled = len(list(repo.iter_commits(f"{sha_before}..{sha_after}")))
            # Get changed files
            diff = repo.commit(sha_before).diff(repo.commit(sha_after))
            files_changed = [
                path for d in diff if (path := d.a_path or d.b_path) is not None
            ]
            up_to_date = False

        logger.info(f"Pulled {target_branch} from {remote}: {commits_pulled} commits")

        return {
            "branch": target_branch,
            "remote": remote,
            "sha_before": sha_before,
            "sha_after": sha_after,
            "commits_pulled": commits_pulled,
            "files_changed": files_changed,
            "up_to_date": up_to_date,
        }

    except GitCommandError as e:
        error_str = str(e).lower()

        if "authentication failed" in error_str or "permission denied" in error_str:
            raise ValueError(
                "Authentication failed. Ensure GITHUB_TOKEN is set in environment, "
                "or configure git credentials."
            ) from e

        if "conflict" in error_str or "merge" in error_str:
            raise ValueError(
                "Merge conflict detected. Resolve conflicts manually, "
                "then stage and commit the resolution."
            ) from e

        if "does not appear to be a git repository" in error_str:
            raise ValueError(f"Remote '{remote}' is not a valid git repository.") from e

        if "couldn't find remote ref" in error_str:
            raise ValueError(
                f"Branch '{target_branch}' does not exist on remote '{remote}'."
            ) from e

        raise ValueError(f"Pull failed: {e}") from e
