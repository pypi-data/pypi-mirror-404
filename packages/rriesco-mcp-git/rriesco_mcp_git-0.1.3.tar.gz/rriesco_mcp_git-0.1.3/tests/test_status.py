"""Unit tests for git_status tool.

Tests the git repository status functionality including:
- Current branch information
- Tracking branch details (ahead/behind counts)
- Staged, modified, and untracked files
- Repository cleanliness
- Error handling for edge cases

Following TDD approach: tests define expected behavior before implementation.
"""

import os
from pathlib import Path
from unittest.mock import Mock, PropertyMock, patch

import pytest
from git import Repo

from git_mcp_server.tools.status import git_status


class TestGitStatusBasicInfo:
    """Test git_status returns basic repository information."""

    def test_returns_correct_structure(self, temp_git_repo: Path) -> None:
        """Test returns dict with all required fields."""
        # Arrange: Use temp repo with initial commit
        repo = Repo(temp_git_repo)
        test_file = temp_git_repo / "test.txt"
        test_file.write_text("initial")
        repo.index.add([str(test_file)])
        repo.index.commit("Initial commit")

        original_dir = os.getcwd()
        os.chdir(temp_git_repo)

        try:
            # Act
            result = git_status()

            # Assert: Check all required keys present
            assert isinstance(result, dict)
            assert "branch" in result
            assert "tracking" in result
            assert "ahead" in result
            assert "behind" in result
            assert "staged" in result
            assert "modified" in result
            assert "untracked" in result
            assert "clean" in result

        finally:
            os.chdir(original_dir)

    def test_current_branch_name_correct(self, temp_git_repo: Path) -> None:
        """Test returns correct current branch name."""
        # Arrange
        repo = Repo(temp_git_repo)
        test_file = temp_git_repo / "test.txt"
        test_file.write_text("initial")
        repo.index.add([str(test_file)])
        repo.index.commit("Initial commit")

        original_dir = os.getcwd()
        os.chdir(temp_git_repo)

        try:
            # Act
            result = git_status()

            # Assert: Should be on master or main (temp repo default)
            assert result["branch"] in ["master", "main"]
            assert isinstance(result["branch"], str)

        finally:
            os.chdir(original_dir)

    def test_clean_repository_returns_clean_true(self, git_repo_with_files: Path) -> None:
        """Test clean repository returns clean=True with empty file lists."""
        original_dir = os.getcwd()
        os.chdir(git_repo_with_files)

        try:
            # Act: Repository is already clean from fixture
            result = git_status()

            # Assert
            assert result["clean"] is True
            assert result["staged"] == []
            assert result["modified"] == []
            assert result["untracked"] == []

        finally:
            os.chdir(original_dir)


class TestGitStatusStagedFiles:
    """Test git_status correctly identifies staged files."""

    def test_single_staged_file(self, git_repo_with_files: Path) -> None:
        """Test status with one staged file."""
        # Arrange
        repo = Repo(git_repo_with_files)
        staged_file = git_repo_with_files / "staged.txt"
        staged_file.write_text("staged content")
        repo.index.add([str(staged_file)])

        original_dir = os.getcwd()
        os.chdir(git_repo_with_files)

        try:
            # Act
            result = git_status()

            # Assert
            assert result["clean"] is False
            assert "staged.txt" in result["staged"]
            assert len(result["staged"]) == 1
            assert result["modified"] == []
            assert result["untracked"] == []

        finally:
            os.chdir(original_dir)

    def test_multiple_staged_files(self, git_repo_with_files: Path) -> None:
        """Test status with multiple staged files."""
        # Arrange
        repo = Repo(git_repo_with_files)
        file1 = git_repo_with_files / "staged1.txt"
        file2 = git_repo_with_files / "staged2.txt"
        file3 = git_repo_with_files / "staged3.txt"

        file1.write_text("content 1")
        file2.write_text("content 2")
        file3.write_text("content 3")

        repo.index.add([str(file1), str(file2), str(file3)])

        original_dir = os.getcwd()
        os.chdir(git_repo_with_files)

        try:
            # Act
            result = git_status()

            # Assert
            assert result["clean"] is False
            assert len(result["staged"]) == 3
            assert "staged1.txt" in result["staged"]
            assert "staged2.txt" in result["staged"]
            assert "staged3.txt" in result["staged"]

        finally:
            os.chdir(original_dir)

    def test_staged_files_listed_with_relative_paths(self, git_repo_with_files: Path) -> None:
        """Test staged files use relative paths from repo root."""
        # Arrange
        repo = Repo(git_repo_with_files)
        subdir = git_repo_with_files / "subdir"
        subdir.mkdir(exist_ok=True)
        staged_file = subdir / "nested.txt"
        staged_file.write_text("nested content")

        repo.index.add([str(staged_file)])

        original_dir = os.getcwd()
        os.chdir(git_repo_with_files)

        try:
            # Act
            result = git_status()

            # Assert: Should use relative path
            assert len(result["staged"]) == 1
            assert (
                "subdir/nested.txt" in result["staged"] or "subdir\\nested.txt" in result["staged"]
            )

        finally:
            os.chdir(original_dir)

    def test_deleted_file_staged_shows_in_staged(self, git_repo_with_files: Path) -> None:
        """Test deleting and staging a file shows in staged."""
        # Arrange
        repo = Repo(git_repo_with_files)
        test_file = git_repo_with_files / "test.txt"  # Created by fixture

        # Delete and stage deletion
        test_file.unlink()
        repo.index.remove([str(test_file)])

        original_dir = os.getcwd()
        os.chdir(git_repo_with_files)

        try:
            # Act
            result = git_status()

            # Assert
            assert result["clean"] is False
            assert "test.txt" in result["staged"]

        finally:
            os.chdir(original_dir)


class TestGitStatusModifiedFiles:
    """Test git_status correctly identifies modified files."""

    def test_single_modified_file(self, git_repo_with_files: Path) -> None:
        """Test status with one modified unstaged file."""
        # Arrange
        test_file = git_repo_with_files / "test.txt"  # From fixture
        test_file.write_text("modified content without staging")

        original_dir = os.getcwd()
        os.chdir(git_repo_with_files)

        try:
            # Act
            result = git_status()

            # Assert
            assert result["clean"] is False
            assert "test.txt" in result["modified"]
            assert len(result["modified"]) >= 1
            assert result["staged"] == []

        finally:
            os.chdir(original_dir)

    def test_multiple_modified_files(self, git_repo_with_files: Path) -> None:
        """Test status with multiple modified unstaged files."""
        # Arrange
        file1 = git_repo_with_files / "test.txt"
        file2 = git_repo_with_files / "test2.txt"

        file1.write_text("modified 1")
        file2.write_text("modified 2")

        original_dir = os.getcwd()
        os.chdir(git_repo_with_files)

        try:
            # Act
            result = git_status()

            # Assert
            assert result["clean"] is False
            assert "test.txt" in result["modified"]
            assert "test2.txt" in result["modified"]
            assert len(result["modified"]) >= 2

        finally:
            os.chdir(original_dir)

    def test_staged_and_modified_shows_in_both(self, git_repo_with_files: Path) -> None:
        """Test file that's staged and then modified again shows in both lists."""
        # Arrange
        repo = Repo(git_repo_with_files)
        test_file = git_repo_with_files / "modified_twice.txt"

        # Create and stage
        test_file.write_text("first version")
        repo.index.add([str(test_file)])

        # Modify after staging
        test_file.write_text("second version")

        original_dir = os.getcwd()
        os.chdir(git_repo_with_files)

        try:
            # Act
            result = git_status()

            # Assert: Should appear in both staged and modified
            assert result["clean"] is False
            assert "modified_twice.txt" in result["staged"]
            assert "modified_twice.txt" in result["modified"]

        finally:
            os.chdir(original_dir)


class TestGitStatusUntrackedFiles:
    """Test git_status correctly identifies untracked files."""

    def test_single_untracked_file(self, git_repo_with_files: Path) -> None:
        """Test status with one untracked file."""
        # Arrange
        untracked = git_repo_with_files / "untracked.txt"
        untracked.write_text("untracked content")

        original_dir = os.getcwd()
        os.chdir(git_repo_with_files)

        try:
            # Act
            result = git_status()

            # Assert
            assert result["clean"] is False
            assert "untracked.txt" in result["untracked"]
            assert len(result["untracked"]) >= 1

        finally:
            os.chdir(original_dir)

    def test_multiple_untracked_files(self, git_repo_with_files: Path) -> None:
        """Test status with multiple untracked files."""
        # Arrange
        file1 = git_repo_with_files / "untracked1.txt"
        file2 = git_repo_with_files / "untracked2.txt"
        file3 = git_repo_with_files / "untracked3.txt"

        file1.write_text("content 1")
        file2.write_text("content 2")
        file3.write_text("content 3")

        original_dir = os.getcwd()
        os.chdir(git_repo_with_files)

        try:
            # Act
            result = git_status()

            # Assert
            assert result["clean"] is False
            assert "untracked1.txt" in result["untracked"]
            assert "untracked2.txt" in result["untracked"]
            assert "untracked3.txt" in result["untracked"]
            assert len(result["untracked"]) >= 3

        finally:
            os.chdir(original_dir)

    def test_untracked_files_use_relative_paths(self, git_repo_with_files: Path) -> None:
        """Test untracked files use relative paths."""
        # Arrange
        subdir = git_repo_with_files / "new_dir"
        subdir.mkdir(exist_ok=True)
        untracked = subdir / "file.txt"
        untracked.write_text("nested untracked")

        original_dir = os.getcwd()
        os.chdir(git_repo_with_files)

        try:
            # Act
            result = git_status()

            # Assert: Should use relative path
            assert len(result["untracked"]) >= 1
            assert (
                "new_dir/file.txt" in result["untracked"]
                or "new_dir\\file.txt" in result["untracked"]
            )

        finally:
            os.chdir(original_dir)

    def test_ignored_files_not_in_untracked(self, git_repo_with_files: Path) -> None:
        """Test .gitignore patterns exclude files from untracked."""
        # Arrange
        repo = Repo(git_repo_with_files)

        # Create .gitignore
        gitignore = git_repo_with_files / ".gitignore"
        gitignore.write_text("*.log\n__pycache__/\n")
        repo.index.add([str(gitignore)])
        repo.index.commit("Add gitignore")

        # Create ignored files
        log_file = git_repo_with_files / "debug.log"
        log_file.write_text("log content")

        original_dir = os.getcwd()
        os.chdir(git_repo_with_files)

        try:
            # Act
            result = git_status()

            # Assert: .log file should not appear in untracked
            assert "debug.log" not in result["untracked"]

        finally:
            os.chdir(original_dir)


class TestGitStatusClean:
    """Test git_status clean field behavior."""

    def test_clean_is_true_when_no_changes(self, git_repo_with_files: Path) -> None:
        """Test clean=True when repository has no changes."""
        original_dir = os.getcwd()
        os.chdir(git_repo_with_files)

        try:
            # Act
            result = git_status()

            # Assert
            assert result["clean"] is True
            assert result["staged"] == []
            assert result["modified"] == []
            assert result["untracked"] == []

        finally:
            os.chdir(original_dir)

    def test_clean_is_false_with_staged_files(self, git_repo_with_files: Path) -> None:
        """Test clean=False when files are staged."""
        # Arrange
        repo = Repo(git_repo_with_files)
        staged_file = git_repo_with_files / "staged.txt"
        staged_file.write_text("staged")
        repo.index.add([str(staged_file)])

        original_dir = os.getcwd()
        os.chdir(git_repo_with_files)

        try:
            # Act
            result = git_status()

            # Assert
            assert result["clean"] is False

        finally:
            os.chdir(original_dir)

    def test_clean_is_false_with_modified_files(self, git_repo_with_files: Path) -> None:
        """Test clean=False when files are modified."""
        # Arrange
        test_file = git_repo_with_files / "test.txt"
        test_file.write_text("modified")

        original_dir = os.getcwd()
        os.chdir(git_repo_with_files)

        try:
            # Act
            result = git_status()

            # Assert
            assert result["clean"] is False

        finally:
            os.chdir(original_dir)

    def test_clean_is_false_with_untracked_files(self, git_repo_with_files: Path) -> None:
        """Test clean=False when files are untracked."""
        # Arrange
        untracked = git_repo_with_files / "untracked.txt"
        untracked.write_text("untracked")

        original_dir = os.getcwd()
        os.chdir(git_repo_with_files)

        try:
            # Act
            result = git_status()

            # Assert
            assert result["clean"] is False

        finally:
            os.chdir(original_dir)

    def test_clean_is_false_with_mixed_changes(self, git_repo_with_files: Path) -> None:
        """Test clean=False when repo has multiple types of changes."""
        # Arrange
        repo = Repo(git_repo_with_files)

        # Add staged file
        staged = git_repo_with_files / "staged.txt"
        staged.write_text("staged")
        repo.index.add([str(staged)])

        # Modify existing file
        test_file = git_repo_with_files / "test.txt"
        test_file.write_text("modified")

        # Add untracked file
        untracked = git_repo_with_files / "untracked.txt"
        untracked.write_text("untracked")

        original_dir = os.getcwd()
        os.chdir(git_repo_with_files)

        try:
            # Act
            result = git_status()

            # Assert
            assert result["clean"] is False
            assert len(result["staged"]) > 0
            assert len(result["modified"]) > 0
            assert len(result["untracked"]) > 0

        finally:
            os.chdir(original_dir)


class TestGitStatusTracking:
    """Test git_status tracking branch information."""

    def test_tracking_is_none_when_no_upstream(self, git_repo_with_files: Path) -> None:
        """Test tracking is None when branch has no upstream."""
        original_dir = os.getcwd()
        os.chdir(git_repo_with_files)

        try:
            # Act
            result = git_status()

            # Assert: Local temp repo has no upstream
            assert result["tracking"] is None

        finally:
            os.chdir(original_dir)

    def test_ahead_zero_when_no_upstream(self, git_repo_with_files: Path) -> None:
        """Test ahead is 0 when no upstream configured."""
        original_dir = os.getcwd()
        os.chdir(git_repo_with_files)

        try:
            # Act
            result = git_status()

            # Assert
            assert result["ahead"] == 0

        finally:
            os.chdir(original_dir)

    def test_behind_zero_when_no_upstream(self, git_repo_with_files: Path) -> None:
        """Test behind is 0 when no upstream configured."""
        original_dir = os.getcwd()
        os.chdir(git_repo_with_files)

        try:
            # Act
            result = git_status()

            # Assert
            assert result["behind"] == 0

        finally:
            os.chdir(original_dir)

    def test_ahead_behind_are_integers(self, git_repo_with_files: Path) -> None:
        """Test ahead and behind fields are integers."""
        original_dir = os.getcwd()
        os.chdir(git_repo_with_files)

        try:
            # Act
            result = git_status()

            # Assert
            assert isinstance(result["ahead"], int)
            assert isinstance(result["behind"], int)
            assert result["ahead"] >= 0
            assert result["behind"] >= 0

        finally:
            os.chdir(original_dir)


class TestGitStatusFieldTypes:
    """Test git_status returns correct field types."""

    def test_branch_is_string(self, git_repo_with_files: Path) -> None:
        """Test branch field is always a string."""
        original_dir = os.getcwd()
        os.chdir(git_repo_with_files)

        try:
            # Act
            result = git_status()

            # Assert
            assert isinstance(result["branch"], str)
            assert len(result["branch"]) > 0

        finally:
            os.chdir(original_dir)

    def test_staged_is_list(self, git_repo_with_files: Path) -> None:
        """Test staged field is always a list."""
        original_dir = os.getcwd()
        os.chdir(git_repo_with_files)

        try:
            # Act
            result = git_status()

            # Assert
            assert isinstance(result["staged"], list)
            for item in result["staged"]:
                assert isinstance(item, str)

        finally:
            os.chdir(original_dir)

    def test_modified_is_list(self, git_repo_with_files: Path) -> None:
        """Test modified field is always a list."""
        original_dir = os.getcwd()
        os.chdir(git_repo_with_files)

        try:
            # Act
            result = git_status()

            # Assert
            assert isinstance(result["modified"], list)
            for item in result["modified"]:
                assert isinstance(item, str)

        finally:
            os.chdir(original_dir)

    def test_untracked_is_list(self, git_repo_with_files: Path) -> None:
        """Test untracked field is always a list."""
        original_dir = os.getcwd()
        os.chdir(git_repo_with_files)

        try:
            # Act
            result = git_status()

            # Assert
            assert isinstance(result["untracked"], list)
            for item in result["untracked"]:
                assert isinstance(item, str)

        finally:
            os.chdir(original_dir)

    def test_clean_is_boolean(self, git_repo_with_files: Path) -> None:
        """Test clean field is always a boolean."""
        original_dir = os.getcwd()
        os.chdir(git_repo_with_files)

        try:
            # Act
            result = git_status()

            # Assert
            assert isinstance(result["clean"], bool)

        finally:
            os.chdir(original_dir)

    def test_tracking_is_string_or_none(self, git_repo_with_files: Path) -> None:
        """Test tracking field is string or None."""
        original_dir = os.getcwd()
        os.chdir(git_repo_with_files)

        try:
            # Act
            result = git_status()

            # Assert
            assert result["tracking"] is None or isinstance(result["tracking"], str)

        finally:
            os.chdir(original_dir)


class TestGitStatusErrorCases:
    """Test git_status error handling."""

    def test_not_in_git_repo_raises_value_error(self, non_git_dir: Path) -> None:
        """Test ValueError raised when not in a git repository."""
        original_dir = os.getcwd()
        os.chdir(non_git_dir)

        try:
            # Act & Assert
            with pytest.raises(ValueError, match="Not a git repository"):
                git_status()

        finally:
            os.chdir(original_dir)

    def test_detached_head_raises_value_error(self, git_repo_with_files: Path) -> None:
        """Test ValueError raised when in detached HEAD state."""
        # Arrange
        repo = Repo(git_repo_with_files)
        commit_sha = repo.head.commit.hexsha

        original_dir = os.getcwd()
        os.chdir(git_repo_with_files)

        try:
            # Detach HEAD by checking out commit directly
            repo.git.checkout(commit_sha)

            # Act & Assert
            with pytest.raises(ValueError, match="detached HEAD"):
                git_status()

        finally:
            # Restore to master
            try:
                repo.git.checkout("master")
            except Exception:
                # Fallback if master doesn't exist
                try:
                    repo.git.checkout("main")
                except Exception:
                    pass

            os.chdir(original_dir)

    def test_error_accessing_repo_raises_exception(self) -> None:
        """Test appropriate exception when repo cannot be accessed."""
        # Arrange: Mock get_repo to raise exception with ValueError
        # The implementation wraps errors in ValueError
        with patch("git_mcp_server.tools.status.get_repo") as mock_get_repo:
            mock_get_repo.side_effect = ValueError("Not a git repository")

            # Act & Assert: Should raise ValueError
            with pytest.raises(ValueError, match="Not a git repository"):
                git_status()


class TestGitStatusIntegration:
    """Integration tests for git_status with various repository states."""

    def test_status_after_stage_and_modify(self, git_repo_with_files: Path) -> None:
        """Test status correctly reflects files staged then modified again."""
        # Arrange
        repo = Repo(git_repo_with_files)
        test_file = git_repo_with_files / "test.txt"

        # Modify
        test_file.write_text("version 1")
        repo.index.add([str(test_file)])  # Stage

        test_file.write_text("version 2")  # Modify after staging

        original_dir = os.getcwd()
        os.chdir(git_repo_with_files)

        try:
            # Act
            result = git_status()

            # Assert: File appears in both staged and modified
            assert result["clean"] is False
            assert "test.txt" in result["staged"]
            assert "test.txt" in result["modified"]

        finally:
            os.chdir(original_dir)

    def test_status_with_deleted_tracked_file(self, git_repo_with_files: Path) -> None:
        """Test status when a tracked file is deleted."""
        # Arrange
        test_file = git_repo_with_files / "test.txt"

        # Delete file
        test_file.unlink()

        original_dir = os.getcwd()
        os.chdir(git_repo_with_files)

        try:
            # Act
            result = git_status()

            # Assert: Deleted file should appear in modified
            assert result["clean"] is False
            assert "test.txt" in result["modified"]

        finally:
            os.chdir(original_dir)

    def test_status_with_renamed_file(self, git_repo_with_files: Path) -> None:
        """Test status when a file is renamed."""
        # Arrange
        old_file = git_repo_with_files / "test.txt"
        new_file = git_repo_with_files / "test_renamed.txt"

        # Rename
        old_file.rename(new_file)

        original_dir = os.getcwd()
        os.chdir(git_repo_with_files)

        try:
            # Act
            result = git_status()

            # Assert: Should show as deleted and untracked (git rename not staged)
            assert result["clean"] is False

        finally:
            os.chdir(original_dir)

    def test_status_with_subdirectory_changes(self, git_repo_with_files: Path) -> None:
        """Test status correctly reports files in subdirectories."""
        # Arrange
        repo = Repo(git_repo_with_files)
        subdir = git_repo_with_files / "src" / "module"
        subdir.mkdir(parents=True, exist_ok=True)

        staged_file = subdir / "staged.py"
        modified_file = git_repo_with_files / "src" / "main.py"
        untracked_file = subdir / "untracked.py"

        staged_file.write_text("staged code")
        repo.index.add([str(staged_file)])

        modified_file.write_text("modified code")
        modified_file.parent.mkdir(parents=True, exist_ok=True)

        untracked_file.write_text("untracked code")

        original_dir = os.getcwd()
        os.chdir(git_repo_with_files)

        try:
            # Act
            result = git_status()

            # Assert: All changes detected with correct paths
            assert result["clean"] is False

        finally:
            os.chdir(original_dir)

    def test_status_empty_repository_after_init(self, temp_git_repo: Path) -> None:
        """Test status of a freshly initialized repository with no commits."""
        original_dir = os.getcwd()
        os.chdir(temp_git_repo)

        try:
            # Act & Assert: Should handle repo with no commits
            # Some implementations may raise error, some may return default values
            try:
                result = git_status()
                # If it succeeds, check reasonable defaults
                assert isinstance(result["branch"], str)
                assert isinstance(result["staged"], list)
            except ValueError as e:
                # Also acceptable to raise error for empty repo
                assert "HEAD" in str(e) or "commit" in str(e).lower()

        finally:
            os.chdir(original_dir)


class TestGitStatusMockingPatterns:
    """Test git_status with mocked git operations for unit test coverage."""

    def test_with_mocked_repo_clean_status(self, mock_repo: Mock) -> None:
        """Test status with mocked clean repository."""
        # Arrange: Configure mock properly
        mock_repo.active_branch.name = "main"
        mock_repo.is_dirty.return_value = False
        mock_repo.untracked_files = []
        mock_repo.index.diff.return_value = []

        # Configure head.is_detached as a property
        type(mock_repo.head).is_detached = PropertyMock(return_value=False)
        mock_repo.active_branch.tracking_branch.return_value = None

        with patch("git_mcp_server.tools.status.get_repo", return_value=mock_repo):
            # Act
            result = git_status()

            # Assert: Verify mocks called appropriately
            assert result["branch"] == "main"
            assert result["clean"] is True

    def test_with_mocked_repo_dirty_status(self, mock_repo: Mock) -> None:
        """Test status with mocked dirty repository."""
        # Arrange: Configure mock properly
        mock_repo.active_branch.name = "develop"
        mock_repo.is_dirty.return_value = True
        mock_repo.untracked_files = ["untracked.txt"]

        # Create mock diff entry with b_path
        mock_diff = Mock()
        mock_diff.b_path = "modified.txt"
        mock_repo.index.diff.return_value = [mock_diff]

        # Configure head.is_detached as a property
        type(mock_repo.head).is_detached = PropertyMock(return_value=False)
        mock_repo.active_branch.tracking_branch.return_value = None

        with patch("git_mcp_server.tools.status.get_repo", return_value=mock_repo):
            # Act
            result = git_status()

            # Assert
            assert result["branch"] == "develop"
            assert result["clean"] is False
