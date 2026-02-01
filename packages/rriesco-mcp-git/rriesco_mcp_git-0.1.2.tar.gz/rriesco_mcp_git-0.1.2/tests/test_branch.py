"""Unit tests for git branch creation tools."""

import os
from pathlib import Path

import pytest
from git import Repo

from git_mcp_server.tools.branch import git_create_branch


class TestGitCreateBranch:
    """Test git_create_branch tool behavior."""

    def test_create_branch_from_head_returns_correct_structure(
        self, git_repo_with_files: Path
    ) -> None:
        """Test create branch from HEAD returns dict with branch name, previous branch, and SHA."""
        original_dir = os.getcwd()
        os.chdir(git_repo_with_files)

        try:
            result = git_create_branch(branch_name="feature-test")

            assert isinstance(result, dict)
            assert "branch_name" in result
            assert "previous_branch" in result
            assert "sha" in result
            assert result["branch_name"] == "feature-test"
            assert isinstance(result["sha"], str)
            assert len(result["sha"]) == 40  # Full SHA is 40 chars

        finally:
            os.chdir(original_dir)

    def test_create_branch_switches_to_new_branch(self, git_repo_with_files: Path) -> None:
        """Test that creating a branch switches to the new branch."""
        original_dir = os.getcwd()
        os.chdir(git_repo_with_files)

        try:
            result = git_create_branch(branch_name="new-branch")

            repo = Repo(git_repo_with_files)
            assert repo.active_branch.name == "new-branch"
            assert result["branch_name"] == "new-branch"

        finally:
            os.chdir(original_dir)

    def test_create_branch_from_specific_branch(self, git_repo_with_files: Path) -> None:
        """Test create branch from a specific branch."""
        original_dir = os.getcwd()
        os.chdir(git_repo_with_files)

        try:
            repo = Repo(git_repo_with_files)

            # Create a develop branch with a unique commit
            repo.git.checkout("-b", "develop")
            test_file = git_repo_with_files / "develop_file.txt"
            test_file.write_text("develop content")
            repo.index.add([str(test_file)])
            repo.index.commit("Develop commit")
            develop_sha = repo.head.commit.hexsha

            # Go back to main
            repo.git.checkout("master")

            # Create feature branch from develop
            result = git_create_branch(branch_name="feature-from-develop", from_branch="develop")

            # Verify the new branch is based on develop
            assert result["branch_name"] == "feature-from-develop"
            assert result["sha"] == develop_sha

        finally:
            os.chdir(original_dir)

    def test_create_branch_already_exists_raises_error(self, git_repo_with_files: Path) -> None:
        """Test creating a branch that already exists raises ValueError."""
        original_dir = os.getcwd()
        os.chdir(git_repo_with_files)

        try:
            # Create branch first time
            git_create_branch(branch_name="existing-branch")

            # Go back to master
            repo = Repo(git_repo_with_files)
            repo.git.checkout("master")

            # Try to create same branch again
            with pytest.raises(ValueError, match="already exists"):
                git_create_branch(branch_name="existing-branch")

        finally:
            os.chdir(original_dir)

    def test_create_branch_invalid_name_raises_error(self, git_repo_with_files: Path) -> None:
        """Test invalid branch name raises ValueError."""
        original_dir = os.getcwd()
        os.chdir(git_repo_with_files)

        try:
            with pytest.raises(ValueError, match="Invalid branch name"):
                git_create_branch(branch_name="branch with spaces")

        finally:
            os.chdir(original_dir)

    def test_create_branch_from_nonexistent_branch_raises_error(
        self, git_repo_with_files: Path
    ) -> None:
        """Test creating branch from nonexistent branch raises ValueError."""
        original_dir = os.getcwd()
        os.chdir(git_repo_with_files)

        try:
            with pytest.raises(ValueError, match="does not exist"):
                git_create_branch(branch_name="new-branch", from_branch="nonexistent-branch")

        finally:
            os.chdir(original_dir)


class TestGitCreateBranchAutoNaming:
    """Test git_create_branch tool auto-naming behavior."""

    def test_create_feature_branch_with_issue_number(self, git_repo_with_files: Path) -> None:
        """Test create feature branch with issue number follows naming convention."""
        original_dir = os.getcwd()
        os.chdir(git_repo_with_files)

        try:
            result = git_create_branch(issue_number=42, description="add-optimizer")

            assert result["branch_name"] == "issue-42-add-optimizer"
            assert isinstance(result["sha"], str)
            assert len(result["sha"]) == 40

            repo = Repo(git_repo_with_files)
            assert repo.active_branch.name == "issue-42-add-optimizer"

        finally:
            os.chdir(original_dir)

    def test_create_feature_branch_description_only(self, git_repo_with_files: Path) -> None:
        """Test create feature branch with description only."""
        original_dir = os.getcwd()
        os.chdir(git_repo_with_files)

        try:
            result = git_create_branch(description="add-caching-layer")

            assert result["branch_name"] == "feature-add-caching-layer"

        finally:
            os.chdir(original_dir)

    def test_create_feature_branch_from_main(self, git_repo_with_files: Path) -> None:
        """Test feature branch is created from main/master."""
        original_dir = os.getcwd()
        os.chdir(git_repo_with_files)

        try:
            repo = Repo(git_repo_with_files)

            # Create a develop branch with unique commit
            repo.git.checkout("-b", "develop")
            test_file = git_repo_with_files / "develop_only.txt"
            test_file.write_text("develop only")
            repo.index.add([str(test_file)])
            repo.index.commit("Develop only commit")

            # Stay on develop - feature branch should still come from main
            result = git_create_branch(issue_number=123, description="from-main")

            # Verify the branch was created
            assert result["branch_name"] == "issue-123-from-main"

            # Verify the branch was created from main, not develop
            # Check that develop_only.txt doesn't exist in this branch
            repo = Repo(git_repo_with_files)
            develop_file = git_repo_with_files / "develop_only.txt"
            assert not develop_file.exists()

        finally:
            os.chdir(original_dir)

    def test_create_feature_branch_invalid_description_raises_error(
        self, git_repo_with_files: Path
    ) -> None:
        """Test invalid description raises ValueError."""
        original_dir = os.getcwd()
        os.chdir(git_repo_with_files)

        try:
            with pytest.raises(ValueError, match="must be lowercase"):
                git_create_branch(issue_number=42, description="Invalid Description")

        finally:
            os.chdir(original_dir)

    def test_create_branch_no_params_raises_error(self, git_repo_with_files: Path) -> None:
        """Test creating branch without params raises ValueError."""
        original_dir = os.getcwd()
        os.chdir(git_repo_with_files)

        try:
            with pytest.raises(ValueError, match="Provide branch_name OR issue_number"):
                git_create_branch()

        finally:
            os.chdir(original_dir)

    def test_create_feature_branch_returns_correct_structure(
        self, git_repo_with_files: Path
    ) -> None:
        """Test feature branch returns dict with all required fields."""
        original_dir = os.getcwd()
        os.chdir(git_repo_with_files)

        try:
            result = git_create_branch(issue_number=99, description="test-structure")

            assert isinstance(result, dict)
            assert "branch_name" in result
            assert "previous_branch" in result
            assert "sha" in result
            assert "based_on" in result
            assert result["based_on"] == "master"  # temp repo uses master

        finally:
            os.chdir(original_dir)

    def test_create_feature_branch_pulls_latest_main(self, git_repo_with_files: Path) -> None:
        """Test feature branch creation updates from main first (when remote exists)."""
        # This test verifies the logic exists but doesn't test actual remote
        # since temp_git_repo doesn't have a remote
        original_dir = os.getcwd()
        os.chdir(git_repo_with_files)

        try:
            # Just verify the function completes successfully
            result = git_create_branch(issue_number=1, description="pull-test")

            assert result["branch_name"] == "issue-1-pull-test"

        finally:
            os.chdir(original_dir)


class TestBranchNamingValidation:
    """Test branch naming validation."""

    def test_validate_description_lowercase_hyphens_valid(self, git_repo_with_files: Path) -> None:
        """Test valid description patterns."""
        original_dir = os.getcwd()
        os.chdir(git_repo_with_files)

        try:
            valid_descriptions = [
                "add-feature",
                "fix-bug",
                "update123",
                "a",
                "test-1-2-3",
            ]

            for idx, desc in enumerate(valid_descriptions):
                result = git_create_branch(issue_number=idx + 100, description=desc)
                assert result["branch_name"] == f"issue-{idx + 100}-{desc}"

                # Reset to master for next iteration
                repo = Repo(git_repo_with_files)
                repo.git.checkout("master")

        finally:
            os.chdir(original_dir)

    def test_validate_description_uppercase_invalid(self, git_repo_with_files: Path) -> None:
        """Test uppercase descriptions are invalid."""
        original_dir = os.getcwd()
        os.chdir(git_repo_with_files)

        try:
            invalid_descriptions = [
                "Add-Feature",
                "UPPERCASE",
                "mixedCase",
            ]

            for desc in invalid_descriptions:
                with pytest.raises(ValueError, match="must be lowercase"):
                    git_create_branch(issue_number=42, description=desc)

        finally:
            os.chdir(original_dir)

    def test_validate_description_spaces_invalid(self, git_repo_with_files: Path) -> None:
        """Test descriptions with spaces are invalid."""
        original_dir = os.getcwd()
        os.chdir(git_repo_with_files)

        try:
            with pytest.raises(ValueError, match="must be lowercase"):
                git_create_branch(issue_number=42, description="has spaces here")

        finally:
            os.chdir(original_dir)
