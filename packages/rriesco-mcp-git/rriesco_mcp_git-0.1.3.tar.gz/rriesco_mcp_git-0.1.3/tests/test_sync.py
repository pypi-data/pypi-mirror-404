"""Unit tests for git sync with main branch tool.

Tests the git_sync_with_main functionality with merge and rebase strategies,
error handling, and edge cases following TDD approach.
"""

import os
from pathlib import Path
from unittest.mock import MagicMock, patch

import pytest
from git.exc import GitCommandError

from git_mcp_server.tools.sync import git_sync_with_main


def _create_mock_ref(name: str) -> MagicMock:
    """Create a mock git reference object."""
    ref = MagicMock()
    ref.name = name
    return ref


class TestGitSyncWithMainMergeStrategy:
    """Test git_sync_with_main using merge strategy."""

    def test_sync_with_merge_returns_correct_structure(self, git_repo_with_files: Path) -> None:
        """Test merge sync returns dict with all required fields."""
        original_dir = os.getcwd()
        os.chdir(git_repo_with_files)

        try:
            with patch("git_mcp_server.tools.sync.get_repo") as mock_get_repo:
                mock_repo = MagicMock()
                mock_get_repo.return_value = mock_repo
                mock_repo.head.is_detached = False
                mock_repo.active_branch.name = "feature-branch"
                sha_before = "aaa111bbb222aaa111bbb222aaa111bbb222aaa1"
                sha_after = "ccc333ddd444ccc333ddd444ccc333ddd444ccc3"
                mock_repo.head.commit.hexsha = sha_before
                mock_repo.is_dirty.return_value = False
                mock_repo.git.fetch.return_value = ""
                mock_repo.git.merge.return_value = ""

                # Mock commit objects for diff
                mock_diff_item1 = MagicMock()
                mock_diff_item1.a_path = "file1.py"
                mock_diff_item2 = MagicMock()
                mock_diff_item2.a_path = "file2.py"
                mock_commit_before = MagicMock()
                mock_commit_before.diff.return_value = [mock_diff_item1, mock_diff_item2]

                # Simulate SHA change after merge
                def merge_side_effect(*args, **kwargs):
                    mock_repo.head.commit.hexsha = sha_after
                    return ""

                mock_repo.git.merge.side_effect = merge_side_effect
                mock_repo.iter_commits.return_value = ["commit1", "commit2"]
                mock_repo.commit.return_value = mock_commit_before

                # Act
                result = git_sync_with_main(main_branch="main", strategy="merge")

                # Assert
                assert isinstance(result, dict)
                assert "branch" in result
                assert "main_branch" in result
                assert "strategy" in result
                assert "sha_before" in result
                assert "sha_after" in result
                assert "commits_added" in result
                assert "up_to_date" in result
                assert "files_changed" in result

                assert result["branch"] == "feature-branch"
                assert result["main_branch"] == "main"
                assert result["strategy"] == "merge"
                assert result["sha_before"] == sha_before
                assert result["sha_after"] == sha_after
                assert isinstance(result["commits_added"], int)
                assert isinstance(result["up_to_date"], bool)
                assert isinstance(result["files_changed"], list)

        finally:
            os.chdir(original_dir)

    def test_sync_with_merge_calls_fetch_before_merge(self, git_repo_with_files: Path) -> None:
        """Test merge sync fetches from origin before merging."""
        original_dir = os.getcwd()
        os.chdir(git_repo_with_files)

        try:
            with patch("git_mcp_server.tools.sync.get_repo") as mock_get_repo:
                mock_repo = MagicMock()
                mock_get_repo.return_value = mock_repo
                mock_repo.head.is_detached = False
                mock_repo.active_branch.name = "feature"
                sha1 = "aaa111bbb222aaa111bbb222aaa111bbb222aaa1"
                mock_repo.head.commit.hexsha = sha1
                mock_repo.is_dirty.return_value = False
                mock_repo.git.fetch.return_value = ""
                mock_repo.git.merge.return_value = ""
                mock_repo.iter_commits.return_value = []
                mock_repo.commit.return_value = MagicMock()

                # Act
                git_sync_with_main(main_branch="main", strategy="merge")

                # Assert: fetch should be called
                assert mock_repo.git.fetch.called

        finally:
            os.chdir(original_dir)

    def test_sync_with_merge_successful_adds_commits(self, git_repo_with_files: Path) -> None:
        """Test merge sync correctly counts commits added from main."""
        original_dir = os.getcwd()
        os.chdir(git_repo_with_files)

        try:
            with patch("git_mcp_server.tools.sync.get_repo") as mock_get_repo:
                mock_repo = MagicMock()
                mock_get_repo.return_value = mock_repo
                mock_repo.head.is_detached = False
                mock_repo.active_branch.name = "feature"
                sha1 = "aaa111bbb222aaa111bbb222aaa111bbb222aaa1"
                sha2 = "ddd444eee555ddd444eee555ddd444eee555ddd4"
                mock_repo.head.commit.hexsha = sha1
                mock_repo.is_dirty.return_value = False
                mock_repo.git.fetch.return_value = ""

                # Simulate SHA change after merge
                def merge_side_effect(*args, **kwargs):
                    mock_repo.head.commit.hexsha = sha2
                    return ""

                mock_repo.git.merge.side_effect = merge_side_effect
                # Simulate 3 commits added
                mock_repo.iter_commits.return_value = ["c1", "c2", "c3"]
                mock_repo.commit.return_value = MagicMock()

                # Act
                result = git_sync_with_main(main_branch="main", strategy="merge")

                # Assert
                assert result["commits_added"] == 3

        finally:
            os.chdir(original_dir)

    def test_sync_with_merge_tracks_files_changed(self, git_repo_with_files: Path) -> None:
        """Test merge sync tracks files changed from main."""
        original_dir = os.getcwd()
        os.chdir(git_repo_with_files)

        try:
            with patch("git_mcp_server.tools.sync.get_repo") as mock_get_repo:
                mock_repo = MagicMock()
                mock_get_repo.return_value = mock_repo
                mock_repo.head.is_detached = False
                mock_repo.active_branch.name = "feature"
                sha1 = "aaa111bbb222aaa111bbb222aaa111bbb222aaa1"
                sha2 = "ddd444eee555ddd444eee555ddd444eee555ddd4"
                mock_repo.head.commit.hexsha = sha1
                mock_repo.is_dirty.return_value = False
                mock_repo.git.fetch.return_value = ""

                def merge_side_effect(*args, **kwargs):
                    mock_repo.head.commit.hexsha = sha2
                    return ""

                mock_repo.git.merge.side_effect = merge_side_effect
                mock_repo.iter_commits.return_value = ["c1"]

                # Mock diff results
                mock_diff1 = MagicMock()
                mock_diff1.a_path = "file1.py"
                mock_diff2 = MagicMock()
                mock_diff2.a_path = "file2.py"
                mock_diff3 = MagicMock()
                mock_diff3.a_path = "file3.md"
                mock_commit = MagicMock()
                mock_commit.diff.return_value = [mock_diff1, mock_diff2, mock_diff3]
                mock_repo.commit.return_value = mock_commit

                # Act
                result = git_sync_with_main(main_branch="main", strategy="merge")

                # Assert - use set comparison since order is not guaranteed
                assert set(result["files_changed"]) == {"file1.py", "file2.py", "file3.md"}

        finally:
            os.chdir(original_dir)


class TestGitSyncWithMainRebaseStrategy:
    """Test git_sync_with_main using rebase strategy."""

    def test_sync_with_rebase_returns_correct_structure(self, git_repo_with_files: Path) -> None:
        """Test rebase sync returns dict with all required fields."""
        original_dir = os.getcwd()
        os.chdir(git_repo_with_files)

        try:
            with patch("git_mcp_server.tools.sync.get_repo") as mock_get_repo:
                mock_repo = MagicMock()
                mock_get_repo.return_value = mock_repo
                mock_repo.head.is_detached = False
                mock_repo.active_branch.name = "feature-branch"
                sha_before = "bbb222ccc333bbb222ccc333bbb222ccc333bbb2"
                sha_after = "ddd444eee555ddd444eee555ddd444eee555ddd4"
                mock_repo.head.commit.hexsha = sha_before
                mock_repo.is_dirty.return_value = False
                mock_repo.git.fetch.return_value = ""
                mock_repo.git.rebase.return_value = ""

                # Mock commit objects for diff
                mock_diff_item = MagicMock()
                mock_diff_item.a_path = "feature.py"
                mock_commit_before = MagicMock()
                mock_commit_before.diff.return_value = [mock_diff_item]

                def rebase_side_effect(*args, **kwargs):
                    mock_repo.head.commit.hexsha = sha_after
                    return ""

                mock_repo.git.rebase.side_effect = rebase_side_effect
                mock_repo.iter_commits.return_value = ["commit1"]
                mock_repo.commit.return_value = mock_commit_before

                # Act
                result = git_sync_with_main(main_branch="main", strategy="rebase")

                # Assert
                assert isinstance(result, dict)
                assert result["strategy"] == "rebase"
                assert result["branch"] == "feature-branch"
                assert result["main_branch"] == "main"
                assert result["sha_before"] == sha_before
                assert result["sha_after"] == sha_after

        finally:
            os.chdir(original_dir)

    def test_sync_with_rebase_calls_rebase_command(self, git_repo_with_files: Path) -> None:
        """Test rebase sync uses git rebase command."""
        original_dir = os.getcwd()
        os.chdir(git_repo_with_files)

        try:
            with patch("git_mcp_server.tools.sync.get_repo") as mock_get_repo:
                mock_repo = MagicMock()
                mock_get_repo.return_value = mock_repo
                mock_repo.head.is_detached = False
                mock_repo.active_branch.name = "feature"
                sha1 = "eee555fff666eee555fff666eee555fff666eee5"
                sha2 = "fff666ggg777fff666ggg777fff666ggg777fff6"
                mock_repo.head.commit.hexsha = sha1
                mock_repo.is_dirty.return_value = False
                mock_repo.git.fetch.return_value = ""

                def rebase_side_effect(*args, **kwargs):
                    mock_repo.head.commit.hexsha = sha2
                    return ""

                mock_repo.git.rebase.side_effect = rebase_side_effect
                # Must have commits to add for rebase to be called
                mock_repo.iter_commits.return_value = ["commit1"]
                mock_repo.commit.return_value = MagicMock()

                # Act
                git_sync_with_main(main_branch="main", strategy="rebase")

                # Assert: rebase should be called with origin/main
                assert mock_repo.git.rebase.called

        finally:
            os.chdir(original_dir)

    def test_sync_with_rebase_updates_sha(self, git_repo_with_files: Path) -> None:
        """Test rebase sync updates SHA after successful rebase."""
        original_dir = os.getcwd()
        os.chdir(git_repo_with_files)

        try:
            with patch("git_mcp_server.tools.sync.get_repo") as mock_get_repo:
                mock_repo = MagicMock()
                mock_get_repo.return_value = mock_repo
                mock_repo.head.is_detached = False
                mock_repo.active_branch.name = "feature"
                sha1 = "fff666ggg777fff666ggg777fff666ggg777fff6"
                sha2 = "hhh888iii999hhh888iii999hhh888iii999hhh8"
                mock_repo.head.commit.hexsha = sha1
                mock_repo.is_dirty.return_value = False
                mock_repo.git.fetch.return_value = ""

                def rebase_side_effect(*args, **kwargs):
                    mock_repo.head.commit.hexsha = sha2
                    return ""

                mock_repo.git.rebase.side_effect = rebase_side_effect
                # Must have commits to add for rebase to be called
                mock_repo.iter_commits.return_value = ["commit1", "commit2"]
                mock_repo.commit.return_value = MagicMock()

                # Act
                result = git_sync_with_main(main_branch="main", strategy="rebase")

                # Assert
                assert result["sha_before"] == sha1
                assert result["sha_after"] == sha2
                assert result["sha_before"] != result["sha_after"]

        finally:
            os.chdir(original_dir)


class TestGitSyncWithMainAlreadyUpToDate:
    """Test git_sync_with_main when already up-to-date with main."""

    def test_sync_already_up_to_date_returns_true(self, git_repo_with_files: Path) -> None:
        """Test sync detects when branch is already up-to-date with main."""
        original_dir = os.getcwd()
        os.chdir(git_repo_with_files)

        try:
            with patch("git_mcp_server.tools.sync.get_repo") as mock_get_repo:
                mock_repo = MagicMock()
                mock_get_repo.return_value = mock_repo
                mock_repo.head.is_detached = False
                mock_repo.active_branch.name = "feature"
                # Same SHA before and after means no commits were added
                same_sha = "jjj000kkk111jjj000kkk111jjj000kkk111jjj0"
                mock_repo.head.commit.hexsha = same_sha
                mock_repo.is_dirty.return_value = False
                mock_repo.git.fetch.return_value = ""
                mock_repo.git.merge.return_value = ""
                # No new commits when already up-to-date
                mock_repo.iter_commits.return_value = []

                def merge_side_effect(*args, **kwargs):
                    # SHA doesn't change
                    mock_repo.head.commit.hexsha = same_sha
                    return ""

                mock_repo.git.merge.side_effect = merge_side_effect
                mock_repo.commit.return_value = MagicMock()

                # Act
                result = git_sync_with_main(main_branch="main", strategy="merge")

                # Assert
                assert result["up_to_date"] is True
                assert result["commits_added"] == 0
                assert result["sha_before"] == result["sha_after"]

        finally:
            os.chdir(original_dir)

    def test_sync_not_up_to_date_returns_false_when_commits_added(
        self, git_repo_with_files: Path
    ) -> None:
        """Test sync returns up_to_date=False when commits were added."""
        original_dir = os.getcwd()
        os.chdir(git_repo_with_files)

        try:
            with patch("git_mcp_server.tools.sync.get_repo") as mock_get_repo:
                mock_repo = MagicMock()
                mock_get_repo.return_value = mock_repo
                mock_repo.head.is_detached = False
                mock_repo.active_branch.name = "feature"
                sha1 = "lll222mmm333lll222mmm333lll222mmm333lll2"
                sha2 = "nnn444ooo555nnn444ooo555nnn444ooo555nnn4"
                mock_repo.head.commit.hexsha = sha1
                mock_repo.is_dirty.return_value = False
                mock_repo.git.fetch.return_value = ""

                def merge_side_effect(*args, **kwargs):
                    mock_repo.head.commit.hexsha = sha2
                    return ""

                mock_repo.git.merge.side_effect = merge_side_effect
                # Multiple new commits
                mock_repo.iter_commits.return_value = ["c1", "c2", "c3", "c4"]
                mock_repo.commit.return_value = MagicMock()

                # Act
                result = git_sync_with_main(main_branch="main", strategy="merge")

                # Assert
                assert result["up_to_date"] is False
                assert result["commits_added"] == 4

        finally:
            os.chdir(original_dir)


class TestGitSyncWithMainErrorHandling:
    """Test git_sync_with_main error handling."""

    def test_sync_merge_conflict_raises_error(self, git_repo_with_files: Path) -> None:
        """Test merge conflict during sync raises ValueError."""
        original_dir = os.getcwd()
        os.chdir(git_repo_with_files)

        try:
            with patch("git_mcp_server.tools.sync.get_repo") as mock_get_repo:
                mock_repo = MagicMock()
                mock_get_repo.return_value = mock_repo
                mock_repo.head.is_detached = False
                mock_repo.active_branch.name = "feature"
                mock_repo.head.commit.hexsha = "ppp666qqq777ppp666qqq777ppp666qqq777ppp6"
                mock_repo.is_dirty.return_value = False
                mock_repo.git.fetch.return_value = ""
                # Must have commits to add for merge to be called
                mock_repo.iter_commits.return_value = ["commit1"]
                # Simulate merge conflict
                error = GitCommandError(
                    "merge",
                    "Merge conflict",
                    stderr="Automatic merge failed; fix conflicts and then commit",
                )
                mock_repo.git.merge.side_effect = error

                # Act & Assert
                with pytest.raises(ValueError, match="Merge conflict|conflict"):
                    git_sync_with_main(main_branch="main", strategy="merge")

        finally:
            os.chdir(original_dir)

    def test_sync_rebase_conflict_raises_error(self, git_repo_with_files: Path) -> None:
        """Test rebase conflict during sync raises ValueError."""
        original_dir = os.getcwd()
        os.chdir(git_repo_with_files)

        try:
            with patch("git_mcp_server.tools.sync.get_repo") as mock_get_repo:
                mock_repo = MagicMock()
                mock_get_repo.return_value = mock_repo
                mock_repo.head.is_detached = False
                mock_repo.active_branch.name = "feature"
                mock_repo.head.commit.hexsha = "rrr888sss999rrr888sss999rrr888sss999rrr8"
                mock_repo.is_dirty.return_value = False
                mock_repo.git.fetch.return_value = ""
                # Must have commits to add for rebase to be called
                mock_repo.iter_commits.return_value = ["commit1"]
                # Simulate rebase conflict
                error = GitCommandError(
                    "rebase",
                    "Rebase conflict",
                    stderr="CONFLICT (content): Merge conflict in file.py",
                )
                mock_repo.git.rebase.side_effect = error

                # Act & Assert
                with pytest.raises(ValueError, match="Rebase conflict|conflict"):
                    git_sync_with_main(main_branch="main", strategy="rebase")

        finally:
            os.chdir(original_dir)

    def test_sync_on_main_branch_raises_error(self, git_repo_with_files: Path) -> None:
        """Test syncing while on main branch raises ValueError."""
        original_dir = os.getcwd()
        os.chdir(git_repo_with_files)

        try:
            with patch("git_mcp_server.tools.sync.get_repo") as mock_get_repo:
                mock_repo = MagicMock()
                mock_get_repo.return_value = mock_repo
                mock_repo.head.is_detached = False
                # Already on main branch
                mock_repo.active_branch.name = "main"

                # Act & Assert
                with pytest.raises(ValueError, match="on main|feature branch"):
                    git_sync_with_main(main_branch="main", strategy="merge")

        finally:
            os.chdir(original_dir)

    def test_sync_with_uncommitted_changes_raises_error(self, git_repo_with_files: Path) -> None:
        """Test sync with uncommitted changes raises ValueError."""
        original_dir = os.getcwd()
        os.chdir(git_repo_with_files)

        try:
            with patch("git_mcp_server.tools.sync.get_repo") as mock_get_repo:
                mock_repo = MagicMock()
                mock_get_repo.return_value = mock_repo
                mock_repo.head.is_detached = False
                mock_repo.active_branch.name = "feature"
                # Dirty working directory
                mock_repo.is_dirty.return_value = True

                # Act & Assert
                with pytest.raises(ValueError, match="uncommitted changes"):
                    git_sync_with_main(main_branch="main", strategy="merge")

        finally:
            os.chdir(original_dir)

    def test_sync_in_detached_head_raises_error(self, git_repo_with_files: Path) -> None:
        """Test syncing in detached HEAD state raises ValueError."""
        original_dir = os.getcwd()
        os.chdir(git_repo_with_files)

        try:
            with patch("git_mcp_server.tools.sync.get_repo") as mock_get_repo:
                mock_repo = MagicMock()
                mock_get_repo.return_value = mock_repo
                mock_repo.head.is_detached = True
                mock_repo.active_branch = None

                # Act & Assert
                with pytest.raises(ValueError, match="detached HEAD"):
                    git_sync_with_main(main_branch="main", strategy="merge")

        finally:
            os.chdir(original_dir)

    def test_sync_invalid_strategy_raises_error(self, git_repo_with_files: Path) -> None:
        """Test invalid strategy parameter raises ValueError."""
        original_dir = os.getcwd()
        os.chdir(git_repo_with_files)

        try:
            with patch("git_mcp_server.tools.sync.get_repo") as mock_get_repo:
                mock_repo = MagicMock()
                mock_get_repo.return_value = mock_repo
                mock_repo.head.is_detached = False
                mock_repo.active_branch.name = "feature"

                # Act & Assert
                with pytest.raises(ValueError, match="strategy|invalid"):
                    git_sync_with_main(main_branch="main", strategy="cherry-pick")

        finally:
            os.chdir(original_dir)

    def test_sync_fetch_failure_raises_error(self, git_repo_with_files: Path) -> None:
        """Test fetch failure during sync raises ValueError."""
        original_dir = os.getcwd()
        os.chdir(git_repo_with_files)

        try:
            with patch("git_mcp_server.tools.sync.get_repo") as mock_get_repo:
                mock_repo = MagicMock()
                mock_get_repo.return_value = mock_repo
                mock_repo.head.is_detached = False
                mock_repo.active_branch.name = "feature"
                mock_repo.is_dirty.return_value = False
                # Simulate fetch failure (no remote connection)
                error = GitCommandError(
                    "fetch",
                    "Connection failed",
                    stderr="fatal: Could not read from remote repository",
                )
                mock_repo.git.fetch.side_effect = error

                # Act & Assert
                with pytest.raises(ValueError, match="Fetch failed|remote"):
                    git_sync_with_main(main_branch="main", strategy="merge")

        finally:
            os.chdir(original_dir)

    def test_sync_not_a_git_repo_raises_error(self, git_repo_with_files: Path) -> None:
        """Test syncing outside git repository raises ValueError."""
        original_dir = os.getcwd()
        os.chdir(git_repo_with_files)

        try:
            with patch("git_mcp_server.tools.sync.get_repo") as mock_get_repo:
                # Simulate repo creation failure
                mock_get_repo.side_effect = ValueError("Not a git repository")

                # Act & Assert
                with pytest.raises(ValueError, match="Not a git repository"):
                    git_sync_with_main(main_branch="main", strategy="merge")

        finally:
            os.chdir(original_dir)


class TestGitSyncWithMainDefaultParameters:
    """Test git_sync_with_main with default parameters."""

    def test_sync_default_main_branch_parameter(self, git_repo_with_files: Path) -> None:
        """Test default main_branch parameter is 'main'."""
        original_dir = os.getcwd()
        os.chdir(git_repo_with_files)

        try:
            with patch("git_mcp_server.tools.sync.get_repo") as mock_get_repo:
                mock_repo = MagicMock()
                mock_get_repo.return_value = mock_repo
                mock_repo.head.is_detached = False
                mock_repo.active_branch.name = "feature"
                sha1 = "ttt000uuu111ttt000uuu111ttt000uuu111ttt0"
                mock_repo.head.commit.hexsha = sha1
                mock_repo.is_dirty.return_value = False
                mock_repo.git.fetch.return_value = ""
                mock_repo.git.merge.return_value = ""
                mock_repo.iter_commits.return_value = []
                mock_repo.commit.return_value = MagicMock()

                # Act - call without main_branch parameter
                result = git_sync_with_main(strategy="merge")

                # Assert - should default to "main"
                assert result["main_branch"] == "main"

        finally:
            os.chdir(original_dir)

    def test_sync_default_strategy_parameter(self, git_repo_with_files: Path) -> None:
        """Test default strategy parameter is 'merge'."""
        original_dir = os.getcwd()
        os.chdir(git_repo_with_files)

        try:
            with patch("git_mcp_server.tools.sync.get_repo") as mock_get_repo:
                mock_repo = MagicMock()
                mock_get_repo.return_value = mock_repo
                mock_repo.head.is_detached = False
                mock_repo.active_branch.name = "feature"
                sha1 = "vvv222www333vvv222www333vvv222www333vvv2"
                sha2 = "www333xxx444www333xxx444www333xxx444www3"
                mock_repo.head.commit.hexsha = sha1
                mock_repo.is_dirty.return_value = False
                mock_repo.git.fetch.return_value = ""

                def merge_side_effect(*args, **kwargs):
                    mock_repo.head.commit.hexsha = sha2
                    return ""

                mock_repo.git.merge.side_effect = merge_side_effect
                # Must have commits to add for merge to be called
                mock_repo.iter_commits.return_value = ["commit1"]
                mock_repo.commit.return_value = MagicMock()

                # Act - call without strategy parameter
                result = git_sync_with_main()

                # Assert - should default to "merge"
                assert result["strategy"] == "merge"
                assert mock_repo.git.merge.called

        finally:
            os.chdir(original_dir)

    def test_sync_with_no_parameters_uses_defaults(self, git_repo_with_files: Path) -> None:
        """Test sync with no parameters uses both defaults."""
        original_dir = os.getcwd()
        os.chdir(git_repo_with_files)

        try:
            with patch("git_mcp_server.tools.sync.get_repo") as mock_get_repo:
                mock_repo = MagicMock()
                mock_get_repo.return_value = mock_repo
                mock_repo.head.is_detached = False
                mock_repo.active_branch.name = "feature"
                sha1 = "xxx444yyy555xxx444yyy555xxx444yyy555xxx4"
                mock_repo.head.commit.hexsha = sha1
                mock_repo.is_dirty.return_value = False
                mock_repo.git.fetch.return_value = ""
                mock_repo.git.merge.return_value = ""
                mock_repo.iter_commits.return_value = []
                mock_repo.commit.return_value = MagicMock()

                # Act - call with no parameters
                result = git_sync_with_main()

                # Assert - both defaults applied
                assert result["main_branch"] == "main"
                assert result["strategy"] == "merge"

        finally:
            os.chdir(original_dir)


class TestGitSyncWithMainCustomMainBranch:
    """Test git_sync_with_main with custom main branch names."""

    def test_sync_with_custom_main_branch_develop(self, git_repo_with_files: Path) -> None:
        """Test sync with custom main_branch parameter 'develop'."""
        original_dir = os.getcwd()
        os.chdir(git_repo_with_files)

        try:
            with patch("git_mcp_server.tools.sync.get_repo") as mock_get_repo:
                mock_repo = MagicMock()
                mock_get_repo.return_value = mock_repo
                mock_repo.head.is_detached = False
                mock_repo.active_branch.name = "feature"
                sha1 = "zzz666aaa777zzz666aaa777zzz666aaa777zzz6"
                mock_repo.head.commit.hexsha = sha1
                mock_repo.is_dirty.return_value = False
                mock_repo.git.fetch.return_value = ""
                mock_repo.git.merge.return_value = ""
                mock_repo.iter_commits.return_value = []
                mock_repo.commit.return_value = MagicMock()

                # Act
                result = git_sync_with_main(main_branch="develop", strategy="merge")

                # Assert
                assert result["main_branch"] == "develop"

        finally:
            os.chdir(original_dir)

    def test_sync_with_custom_main_branch_master(self, git_repo_with_files: Path) -> None:
        """Test sync with custom main_branch parameter 'master'."""
        original_dir = os.getcwd()
        os.chdir(git_repo_with_files)

        try:
            with patch("git_mcp_server.tools.sync.get_repo") as mock_get_repo:
                mock_repo = MagicMock()
                mock_get_repo.return_value = mock_repo
                mock_repo.head.is_detached = False
                mock_repo.active_branch.name = "feature"
                sha1 = "bbb888ccc999bbb888ccc999bbb888ccc999bbb8"
                mock_repo.head.commit.hexsha = sha1
                mock_repo.is_dirty.return_value = False
                mock_repo.git.fetch.return_value = ""
                mock_repo.git.merge.return_value = ""
                mock_repo.iter_commits.return_value = []
                mock_repo.commit.return_value = MagicMock()

                # Act
                result = git_sync_with_main(main_branch="master", strategy="merge")

                # Assert
                assert result["main_branch"] == "master"

        finally:
            os.chdir(original_dir)


class TestGitSyncWithMainEdgeCases:
    """Test edge cases in git_sync_with_main."""

    def test_sync_with_no_files_changed(self, git_repo_with_files: Path) -> None:
        """Test sync when main has no file changes."""
        original_dir = os.getcwd()
        os.chdir(git_repo_with_files)

        try:
            with patch("git_mcp_server.tools.sync.get_repo") as mock_get_repo:
                mock_repo = MagicMock()
                mock_get_repo.return_value = mock_repo
                mock_repo.head.is_detached = False
                mock_repo.active_branch.name = "feature"
                sha1 = "ddd000eee111ddd000eee111ddd000eee111ddd0"
                sha2 = "fff222ggg333fff222ggg333fff222ggg333fff2"
                mock_repo.head.commit.hexsha = sha1
                mock_repo.is_dirty.return_value = False
                mock_repo.git.fetch.return_value = ""

                def merge_side_effect(*args, **kwargs):
                    mock_repo.head.commit.hexsha = sha2
                    return ""

                mock_repo.git.merge.side_effect = merge_side_effect
                mock_repo.iter_commits.return_value = ["c1"]
                # No files changed in diff
                mock_commit = MagicMock()
                mock_commit.diff.return_value = []
                mock_repo.commit.return_value = mock_commit

                # Act
                result = git_sync_with_main(main_branch="main", strategy="merge")

                # Assert
                assert result["files_changed"] == []
                assert len(result["files_changed"]) == 0

        finally:
            os.chdir(original_dir)

    def test_sync_with_many_files_changed(self, git_repo_with_files: Path) -> None:
        """Test sync tracks many file changes correctly."""
        original_dir = os.getcwd()
        os.chdir(git_repo_with_files)

        try:
            with patch("git_mcp_server.tools.sync.get_repo") as mock_get_repo:
                mock_repo = MagicMock()
                mock_get_repo.return_value = mock_repo
                mock_repo.head.is_detached = False
                mock_repo.active_branch.name = "feature"
                sha1 = "hhh444iii555hhh444iii555hhh444iii555hhh4"
                sha2 = "jjj666kkk777jjj666kkk777jjj666kkk777jjj6"
                mock_repo.head.commit.hexsha = sha1
                mock_repo.is_dirty.return_value = False
                mock_repo.git.fetch.return_value = ""

                def merge_side_effect(*args, **kwargs):
                    mock_repo.head.commit.hexsha = sha2
                    return ""

                mock_repo.git.merge.side_effect = merge_side_effect
                mock_repo.iter_commits.return_value = ["c1"]

                # Create many file diffs
                diffs = []
                for i in range(10):
                    diff = MagicMock()
                    diff.a_path = f"file{i}.py"
                    diffs.append(diff)

                mock_commit = MagicMock()
                mock_commit.diff.return_value = diffs
                mock_repo.commit.return_value = mock_commit

                # Act
                result = git_sync_with_main(main_branch="main", strategy="merge")

                # Assert
                assert len(result["files_changed"]) == 10
                assert all(f"file{i}.py" in result["files_changed"] for i in range(10))

        finally:
            os.chdir(original_dir)

    def test_sync_with_single_commit_from_main(self, git_repo_with_files: Path) -> None:
        """Test sync with exactly one commit from main."""
        original_dir = os.getcwd()
        os.chdir(git_repo_with_files)

        try:
            with patch("git_mcp_server.tools.sync.get_repo") as mock_get_repo:
                mock_repo = MagicMock()
                mock_get_repo.return_value = mock_repo
                mock_repo.head.is_detached = False
                mock_repo.active_branch.name = "feature"
                sha1 = "lll888mmm999lll888mmm999lll888mmm999lll8"
                sha2 = "nnn000ooo111nnn000ooo111nnn000ooo111nnn0"
                mock_repo.head.commit.hexsha = sha1
                mock_repo.is_dirty.return_value = False
                mock_repo.git.fetch.return_value = ""

                def merge_side_effect(*args, **kwargs):
                    mock_repo.head.commit.hexsha = sha2
                    return ""

                mock_repo.git.merge.side_effect = merge_side_effect
                # Exactly 1 commit
                mock_repo.iter_commits.return_value = ["c1"]
                mock_repo.commit.return_value = MagicMock()

                # Act
                result = git_sync_with_main(main_branch="main", strategy="merge")

                # Assert
                assert result["commits_added"] == 1
                assert result["up_to_date"] is False

        finally:
            os.chdir(original_dir)

    def test_sync_preserves_branch_state_on_error(self, git_repo_with_files: Path) -> None:
        """Test sync doesn't leave repo in bad state on error."""
        original_dir = os.getcwd()
        os.chdir(git_repo_with_files)

        try:
            with patch("git_mcp_server.tools.sync.get_repo") as mock_get_repo:
                mock_repo = MagicMock()
                mock_get_repo.return_value = mock_repo
                mock_repo.head.is_detached = False
                mock_repo.active_branch.name = "feature"
                original_sha = "ppp222qqq333ppp222qqq333ppp222qqq333ppp2"
                mock_repo.head.commit.hexsha = original_sha
                mock_repo.is_dirty.return_value = False
                mock_repo.git.fetch.return_value = ""
                # Must have commits to add for merge to be called
                mock_repo.iter_commits.return_value = ["commit1"]
                # Merge fails with conflict
                error = GitCommandError(
                    "merge",
                    "Merge conflict",
                    stderr="CONFLICT",
                )
                mock_repo.git.merge.side_effect = error

                # Act & Assert
                with pytest.raises(ValueError, match="conflict"):
                    git_sync_with_main(main_branch="main", strategy="merge")

                # Verify SHA wasn't updated before error
                assert mock_repo.head.commit.hexsha == original_sha

        finally:
            os.chdir(original_dir)


class TestGitSyncWithMainSHAGeneration:
    """Test SHA handling in git_sync_with_main."""

    def test_sync_returns_40_char_sha_before(self, git_repo_with_files: Path) -> None:
        """Test sync returns 40-character SHA before sync."""
        original_dir = os.getcwd()
        os.chdir(git_repo_with_files)

        try:
            test_sha = "rrr444sss555rrr444sss555rrr444sss555rrr4"
            with patch("git_mcp_server.tools.sync.get_repo") as mock_get_repo:
                mock_repo = MagicMock()
                mock_get_repo.return_value = mock_repo
                mock_repo.head.is_detached = False
                mock_repo.active_branch.name = "feature"
                mock_repo.head.commit.hexsha = test_sha
                mock_repo.is_dirty.return_value = False
                mock_repo.git.fetch.return_value = ""
                mock_repo.git.merge.return_value = ""
                mock_repo.iter_commits.return_value = []
                mock_repo.commit.return_value = MagicMock()

                # Act
                result = git_sync_with_main(main_branch="main", strategy="merge")

                # Assert
                assert result["sha_before"] == test_sha
                assert len(result["sha_before"]) == 40

        finally:
            os.chdir(original_dir)

    def test_sync_returns_40_char_sha_after(self, git_repo_with_files: Path) -> None:
        """Test sync returns 40-character SHA after sync."""
        original_dir = os.getcwd()
        os.chdir(git_repo_with_files)

        try:
            sha_before = "ttt666uuu777ttt666uuu777ttt666uuu777ttt6"
            sha_after = "vvv888www999vvv888www999vvv888www999vvv8"
            with patch("git_mcp_server.tools.sync.get_repo") as mock_get_repo:
                mock_repo = MagicMock()
                mock_get_repo.return_value = mock_repo
                mock_repo.head.is_detached = False
                mock_repo.active_branch.name = "feature"
                mock_repo.head.commit.hexsha = sha_before
                mock_repo.is_dirty.return_value = False
                mock_repo.git.fetch.return_value = ""

                def merge_side_effect(*args, **kwargs):
                    mock_repo.head.commit.hexsha = sha_after
                    return ""

                mock_repo.git.merge.side_effect = merge_side_effect
                mock_repo.iter_commits.return_value = ["c1"]
                mock_repo.commit.return_value = MagicMock()

                # Act
                result = git_sync_with_main(main_branch="main", strategy="merge")

                # Assert
                assert result["sha_after"] == sha_after
                assert len(result["sha_after"]) == 40

        finally:
            os.chdir(original_dir)
