"""Unit tests for git_commit tool.

Tests the git commit functionality with conventional commit format and
Claude Code attribution following TDD approach.
"""

import os
from pathlib import Path

import pytest
from git import Repo

from git_mcp_server.tools.commit import git_commit


class TestGitCommit:
    """Test git_commit tool behavior."""

    def test_commit_all_changes_returns_correct_structure(self, temp_git_repo: Path) -> None:
        """Test commit all changes returns dict with SHA, stats, and message."""
        # Arrange: Create some changes
        test_file = temp_git_repo / "new_file.txt"
        test_file.write_text("test content")

        # Change to temp repo directory
        original_dir = os.getcwd()
        os.chdir(temp_git_repo)

        try:
            # Act
            result = git_commit(
                type="feat",
                message="add new feature",
                files=None,  # All changes
                skip_hooks=True,  # Skip hooks for testing
            )

            # Assert
            assert isinstance(result, dict)
            assert "sha" in result
            assert "stats" in result
            assert "message" in result
            assert isinstance(result["sha"], str)
            assert len(result["sha"]) == 40  # Full SHA is 40 chars
            assert isinstance(result["stats"], dict)
            assert "files_changed" in result["stats"]
            assert "insertions" in result["stats"]
            assert "deletions" in result["stats"]

        finally:
            os.chdir(original_dir)

    def test_commit_specific_files_only_stages_those_files(self, temp_git_repo: Path) -> None:
        """Test commit specific files only includes those files."""
        # Arrange: Create multiple files
        file1 = temp_git_repo / "file1.txt"
        file2 = temp_git_repo / "file2.txt"
        file1.write_text("content 1")
        file2.write_text("content 2")

        original_dir = os.getcwd()
        os.chdir(temp_git_repo)

        try:
            # Act: Only commit file1
            result = git_commit(
                type="feat",
                message="add file1",
                files=["file1.txt"],
                skip_hooks=True,
            )

            # Assert: Verify commit succeeded
            assert result["sha"]
            assert result["stats"]["files_changed"] == 1

            # Verify file2 is still untracked
            repo = Repo(temp_git_repo)
            assert "file2.txt" in repo.untracked_files

        finally:
            os.chdir(original_dir)

    def test_commit_with_skip_hooks_uses_no_verify(self, temp_git_repo: Path) -> None:
        """Test skip_hooks=True successfully commits without hooks."""
        # Arrange
        test_file = temp_git_repo / "test.txt"
        test_file.write_text("test")

        original_dir = os.getcwd()
        os.chdir(temp_git_repo)

        try:
            # Act: Commit with skip_hooks (should succeed even if hooks would fail)
            result = git_commit(
                type="feat",
                message="test commit",
                skip_hooks=True,
            )

            # Assert: Commit succeeded
            assert "sha" in result
            assert isinstance(result["sha"], str)
            assert len(result["sha"]) == 40

        finally:
            os.chdir(original_dir)

    def test_conventional_commit_format_in_message(self, temp_git_repo: Path) -> None:
        """Test commit message follows conventional commit format."""
        # Arrange
        test_file = temp_git_repo / "test.txt"
        test_file.write_text("test")

        original_dir = os.getcwd()
        os.chdir(temp_git_repo)

        try:
            # Act
            result = git_commit(
                type="fix",
                message="resolve bug in parser",
                skip_hooks=True,
            )

            # Assert: Message starts with type:
            assert result["message"].startswith("fix:")
            assert "resolve bug in parser" in result["message"]

        finally:
            os.chdir(original_dir)

    def test_claude_attribution_added_to_commit(self, temp_git_repo: Path) -> None:
        """Test Claude Code attribution is included in commit message."""
        # Arrange
        test_file = temp_git_repo / "test.txt"
        test_file.write_text("test")

        original_dir = os.getcwd()
        os.chdir(temp_git_repo)

        try:
            # Act
            result = git_commit(
                type="docs",
                message="update documentation",
                skip_hooks=True,
            )

            # Assert: Attribution present
            assert "Claude Code" in result["message"]
            assert "Co-Authored-By: Claude" in result["message"]

        finally:
            os.chdir(original_dir)

    def test_invalid_commit_type_raises_value_error(self, temp_git_repo: Path) -> None:
        """Test invalid commit type raises ValueError."""
        # Arrange
        test_file = temp_git_repo / "test.txt"
        test_file.write_text("test")

        original_dir = os.getcwd()
        os.chdir(temp_git_repo)

        try:
            # Act & Assert
            with pytest.raises(ValueError, match="Invalid commit type"):
                git_commit(
                    type="invalid_type",
                    message="test",
                    skip_hooks=True,
                )

        finally:
            os.chdir(original_dir)

    def test_empty_message_raises_value_error(self, temp_git_repo: Path) -> None:
        """Test empty message raises ValueError."""
        # Arrange
        test_file = temp_git_repo / "test.txt"
        test_file.write_text("test")

        original_dir = os.getcwd()
        os.chdir(temp_git_repo)

        try:
            # Act & Assert
            with pytest.raises(ValueError, match="message cannot be empty"):
                git_commit(
                    type="feat",
                    message="",
                    skip_hooks=True,
                )

        finally:
            os.chdir(original_dir)

    def test_no_changes_to_commit_raises_error(self, temp_git_repo: Path) -> None:
        """Test committing with no changes raises ValueError."""
        # Arrange: temp_git_repo starts clean after initial setup
        # Create initial commit to have a clean state
        test_file = temp_git_repo / "initial.txt"
        test_file.write_text("initial")

        repo = Repo(temp_git_repo)
        repo.index.add([str(test_file)])
        repo.index.commit("Initial commit")

        original_dir = os.getcwd()
        os.chdir(temp_git_repo)

        try:
            # Act & Assert: Try to commit with no changes
            with pytest.raises(ValueError, match="No changes to commit"):
                git_commit(
                    type="feat",
                    message="test",
                    skip_hooks=True,
                )

        finally:
            os.chdir(original_dir)

    def test_commit_stats_accurate(self, temp_git_repo: Path) -> None:
        """Test commit stats reflect actual changes."""
        # Arrange: Create file with known content
        test_file = temp_git_repo / "test.txt"
        test_file.write_text("line 1\nline 2\nline 3\n")  # 3 lines

        original_dir = os.getcwd()
        os.chdir(temp_git_repo)

        try:
            # Act
            result = git_commit(
                type="feat",
                message="add test file",
                skip_hooks=True,
            )

            # Assert: Verify stats
            assert result["stats"]["files_changed"] == 1
            assert result["stats"]["insertions"] >= 3  # At least 3 lines added

        finally:
            os.chdir(original_dir)

    def test_all_conventional_commit_types_accepted(self, temp_git_repo: Path) -> None:
        """Test all valid conventional commit types are accepted."""
        # Arrange
        valid_types = [
            "feat",
            "fix",
            "docs",
            "style",
            "refactor",
            "perf",
            "test",
            "build",
            "ci",
            "chore",
        ]

        original_dir = os.getcwd()
        os.chdir(temp_git_repo)

        try:
            # Act & Assert: Each type should work
            for idx, commit_type in enumerate(valid_types):
                test_file = temp_git_repo / f"file_{idx}.txt"
                test_file.write_text(f"content {idx}")

                result = git_commit(
                    type=commit_type,
                    message=f"test {commit_type}",
                    skip_hooks=True,
                )

                assert result["message"].startswith(f"{commit_type}:")

        finally:
            os.chdir(original_dir)

    def test_nonexistent_file_in_files_raises_error(self, temp_git_repo: Path) -> None:
        """Test specifying nonexistent file raises ValueError."""
        # Arrange
        original_dir = os.getcwd()
        os.chdir(temp_git_repo)

        try:
            # Act & Assert
            with pytest.raises(ValueError, match="File not found"):
                git_commit(
                    type="feat",
                    message="test",
                    files=["nonexistent.txt"],
                    skip_hooks=True,
                )

        finally:
            os.chdir(original_dir)

    def test_commit_creates_retrievable_commit_object(self, temp_git_repo: Path) -> None:
        """Test commit creates a valid commit that can be retrieved."""
        # Arrange
        test_file = temp_git_repo / "test.txt"
        test_file.write_text("test content")

        original_dir = os.getcwd()
        os.chdir(temp_git_repo)

        try:
            # Act
            result = git_commit(
                type="feat",
                message="add feature",
                skip_hooks=True,
            )

            # Assert: Can retrieve the commit
            repo = Repo(temp_git_repo)
            commit = repo.commit(result["sha"])
            assert commit.hexsha == result["sha"]
            assert "feat: add feature" in commit.message
            assert "Claude Code" in commit.message

        finally:
            os.chdir(original_dir)
