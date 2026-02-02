"""Git sync with main branch tool."""

import logging
from typing import Any

from git.exc import GitCommandError

from .. import mcp
from ..utils import get_current_branch, get_remote_url_with_auth, get_repo

logger = logging.getLogger(__name__)


@mcp.tool()
def git_sync_with_main(
    main_branch: str = "main",
    strategy: str = "merge",
) -> dict[str, Any]:
    """Sync current branch with main. Fetches latest and merges/rebases.

    Options:
    - main_branch: branch to sync from (default: "main")
    - strategy: "merge" (default) or "rebase"

    Fails if on main branch or has uncommitted changes.

    Returns: {branch, main_branch, strategy, sha_before, sha_after,
              commits_added, up_to_date, files_changed}
    """
    # Validate strategy
    if strategy not in ("merge", "rebase"):
        raise ValueError(f"Invalid strategy '{strategy}'. Must be 'merge' or 'rebase'.")

    repo = get_repo()

    # Get current branch
    current_branch = get_current_branch(repo)

    # Check if on main branch
    if current_branch == main_branch:
        raise ValueError(
            f"Already on '{main_branch}' branch. "
            f"Use git_pull() instead, or checkout a feature branch first."
        )

    # Check for uncommitted changes
    if repo.is_dirty(untracked_files=True):
        raise ValueError("Cannot sync with uncommitted changes. Commit or stash changes first.")

    # Get SHA before sync
    sha_before = repo.head.commit.hexsha

    # Fetch latest from remote
    try:
        auth_url = get_remote_url_with_auth(repo)
        if auth_url:
            repo.git.fetch(auth_url, main_branch)
        else:
            repo.git.fetch("origin", main_branch)
    except GitCommandError as e:
        raise ValueError(f"Failed to fetch from origin: {e}") from e

    # Check if already up to date
    try:
        # Get commits in origin/main that are not in current branch
        commits_to_add = list(repo.iter_commits(f"{current_branch}..origin/{main_branch}"))
        commits_added = len(commits_to_add)

        if commits_added == 0:
            return {
                "branch": current_branch,
                "main_branch": main_branch,
                "strategy": strategy,
                "sha_before": sha_before,
                "sha_after": sha_before,
                "commits_added": 0,
                "up_to_date": True,
                "files_changed": [],
            }
    except Exception:
        # If we can't count commits, proceed with sync anyway
        commits_added = 0

    # Perform sync based on strategy
    try:
        if strategy == "merge":
            repo.git.merge(f"origin/{main_branch}", "--no-edit")
        else:  # rebase
            repo.git.rebase(f"origin/{main_branch}")

        # Get SHA after sync
        sha_after = repo.head.commit.hexsha

        # Get changed files
        if sha_before != sha_after:
            try:
                diff = repo.commit(sha_before).diff(repo.commit(sha_after))
                files_changed = [
                    path for d in diff if (path := d.a_path or d.b_path) is not None
                ]
            except Exception:
                files_changed = []

            # Recount commits if not already counted
            if commits_added == 0:
                try:
                    commits_added = len(list(repo.iter_commits(f"{sha_before}..{sha_after}")))
                except Exception:
                    commits_added = 1  # At least one commit was added
        else:
            files_changed = []

        logger.info(f"Synced {current_branch} with {main_branch} using {strategy}")

        return {
            "branch": current_branch,
            "main_branch": main_branch,
            "strategy": strategy,
            "sha_before": sha_before,
            "sha_after": sha_after,
            "commits_added": commits_added,
            "up_to_date": sha_before == sha_after,
            "files_changed": files_changed,
        }

    except GitCommandError as e:
        error_str = str(e).lower()

        if "conflict" in error_str or "merge" in error_str:
            # Abort the failed merge/rebase
            try:
                if strategy == "merge":
                    repo.git.merge("--abort")
                else:
                    repo.git.rebase("--abort")
            except Exception:
                pass  # Ignore abort errors

            raise ValueError(
                f"{'Merge' if strategy == 'merge' else 'Rebase'} conflict detected. "
                f"Resolve conflicts manually, then stage and commit the resolution."
            ) from e

        raise ValueError(f"Sync failed: {e}") from e
