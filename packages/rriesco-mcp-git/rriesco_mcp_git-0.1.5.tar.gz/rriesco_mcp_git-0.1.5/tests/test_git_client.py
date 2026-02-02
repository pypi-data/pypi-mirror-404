"""Unit tests for git_mcp_server.utils.git_client.

Tests the Git repository singleton instance management.
"""

from pathlib import Path
from unittest.mock import Mock, patch

import git
import pytest

from git_mcp_server.utils import get_repo, reset_repo


class TestGetRepo:
    """Test get_repo() singleton function."""

    def test_returns_repo_instance(self) -> None:
        """Test that get_repo returns a valid Repo instance when in git directory."""
        # Arrange: Mock Repo to avoid requiring actual git directory
        with patch("git_mcp_server.utils.git_client.Repo") as mock_repo_class:
            mock_instance = Mock(spec=git.Repo)
            mock_repo_class.return_value = mock_instance
            reset_repo()  # Clear singleton

            # Act
            result = get_repo()

            # Assert
            assert isinstance(result, Mock)
            assert result == mock_instance

    def test_returns_same_instance_on_multiple_calls(self) -> None:
        """Test that get_repo returns singleton instance on subsequent calls."""
        # Arrange
        with patch("git_mcp_server.utils.git_client.Repo") as mock_repo_class:
            mock_instance = Mock(spec=git.Repo)
            mock_repo_class.return_value = mock_instance
            reset_repo()  # Clear singleton

            # Act
            result1 = get_repo()
            result2 = get_repo()

            # Assert
            assert result1 is result2
            # Repo constructor should only be called once
            mock_repo_class.assert_called_once()

    def test_searches_parent_directories_for_git_root(self) -> None:
        """Test that get_repo searches parent directories for .git."""
        # Arrange
        with patch("git_mcp_server.utils.git_client.Repo") as mock_repo_class:
            mock_instance = Mock(spec=git.Repo)
            mock_repo_class.return_value = mock_instance
            reset_repo()

            # Act
            get_repo()

            # Assert
            # Verify search_parent_directories=True is used
            mock_repo_class.assert_called_once()
            call_kwargs = mock_repo_class.call_args[1]
            assert call_kwargs.get("search_parent_directories") is True

    def test_uses_current_working_directory(self) -> None:
        """Test that get_repo uses current working directory."""
        # Arrange
        with patch("git_mcp_server.utils.git_client.Repo") as mock_repo_class:
            with patch("git_mcp_server.utils.git_client.Path.cwd") as mock_cwd:
                mock_cwd.return_value = Path("/current/dir")
                mock_instance = Mock(spec=git.Repo)
                mock_repo_class.return_value = mock_instance
                reset_repo()

                # Act
                get_repo()

                # Assert
                mock_repo_class.assert_called_once()
                call_args = mock_repo_class.call_args[0]
                assert call_args[0] == Path("/current/dir")

    def test_raises_value_error_when_not_in_git_repo(self) -> None:
        """Test that get_repo raises ValueError when not in git repository."""
        # Arrange
        with patch("git_mcp_server.utils.git_client.Repo") as mock_repo_class:
            mock_repo_class.side_effect = git.InvalidGitRepositoryError("Invalid git repository")
            reset_repo()

            # Act & Assert
            with pytest.raises(ValueError) as exc_info:
                get_repo()

            assert "Not a git repository" in str(exc_info.value)
            assert "git repository" in str(exc_info.value).lower()

    def test_error_message_includes_working_directory(self) -> None:
        """Test that ValueError includes the working directory path."""
        # Arrange
        test_path = Path("/some/non/git/path")
        with patch("git_mcp_server.utils.git_client.Repo") as mock_repo_class:
            with patch("git_mcp_server.utils.git_client.Path.cwd") as mock_cwd:
                mock_cwd.return_value = test_path
                mock_repo_class.side_effect = git.InvalidGitRepositoryError(
                    "Invalid git repository"
                )
                reset_repo()

                # Act & Assert
                with pytest.raises(ValueError) as exc_info:
                    get_repo()

                assert str(test_path) in str(exc_info.value)

    def test_error_includes_helpful_suggestion(self) -> None:
        """Test that error message includes suggestion to run from git repo."""
        # Arrange
        with patch("git_mcp_server.utils.git_client.Repo") as mock_repo_class:
            mock_repo_class.side_effect = git.InvalidGitRepositoryError("Invalid git repository")
            reset_repo()

            # Act & Assert
            with pytest.raises(ValueError) as exc_info:
                get_repo()

            error_msg = str(exc_info.value).lower()
            assert "git repository" in error_msg

    def test_preserves_git_error_cause(self) -> None:
        """Test that ValueError preserves the original git exception as cause."""
        # Arrange
        original_error = git.InvalidGitRepositoryError("Original error")
        with patch("git_mcp_server.utils.git_client.Repo") as mock_repo_class:
            mock_repo_class.side_effect = original_error
            reset_repo()

            # Act & Assert
            with pytest.raises(ValueError) as exc_info:
                get_repo()

            assert exc_info.value.__cause__ is original_error


class TestResetRepo:
    """Test reset_repo() singleton reset function."""

    def test_clears_singleton_instance(self) -> None:
        """Test that reset_repo clears the cached singleton instance."""
        # Arrange
        with patch("git_mcp_server.utils.git_client.Repo") as mock_repo_class:
            mock_instance1 = Mock(spec=git.Repo)
            mock_instance2 = Mock(spec=git.Repo)
            mock_repo_class.side_effect = [mock_instance1, mock_instance2]
            reset_repo()

            # Act: Get repo, reset, get repo again
            first_repo = get_repo()
            reset_repo()
            second_repo = get_repo()

            # Assert: Should be different instances
            assert first_repo is not second_repo
            assert first_repo == mock_instance1
            assert second_repo == mock_instance2

    def test_allows_new_instance_creation_after_reset(self) -> None:
        """Test that reset_repo allows creating new instance with different cwd."""
        # Arrange
        with patch("git_mcp_server.utils.git_client.Repo") as mock_repo_class:
            with patch("git_mcp_server.utils.git_client.Path.cwd") as mock_cwd:
                mock_instance1 = Mock(spec=git.Repo)
                mock_instance2 = Mock(spec=git.Repo)
                mock_repo_class.side_effect = [mock_instance1, mock_instance2]

                # First call from /dir1
                mock_cwd.return_value = Path("/dir1")
                reset_repo()
                first_repo = get_repo()

                # Reset and call from /dir2
                reset_repo()
                mock_cwd.return_value = Path("/dir2")
                second_repo = get_repo()

                # Assert
                assert first_repo is not second_repo
                assert mock_repo_class.call_count == 2

    def test_can_be_called_multiple_times_safely(self) -> None:
        """Test that reset_repo can be called multiple times without errors."""
        # Arrange & Act & Assert
        # Should not raise any errors
        reset_repo()
        reset_repo()
        reset_repo()

    def test_reset_before_first_get_does_not_raise(self) -> None:
        """Test that reset_repo can be called before get_repo is ever called."""
        # Arrange & Act & Assert
        reset_repo()
        # Should not raise any errors
        assert True

    def test_reset_state_is_truly_cleared(self) -> None:
        """Test that reset_repo completely clears the module state."""
        # Arrange
        with patch("git_mcp_server.utils.git_client.Repo") as mock_repo_class:
            mock_instance = Mock(spec=git.Repo)
            mock_repo_class.return_value = mock_instance
            reset_repo()

            # Act: Get repo, reset, get repo again
            get_repo()
            reset_repo()

            # Now verify by checking calls - should be called twice after reset
            # (once before reset, once after)
            get_repo()

            # Assert
            assert mock_repo_class.call_count == 2


class TestSingletonPatternIntegration:
    """Integration tests for singleton pattern behavior."""

    def test_singleton_survives_multiple_function_calls(self) -> None:
        """Test that singleton persists across multiple separate function calls."""
        # Arrange
        with patch("git_mcp_server.utils.git_client.Repo") as mock_repo_class:
            mock_instance = Mock(spec=git.Repo)
            mock_repo_class.return_value = mock_instance
            reset_repo()

            # Act
            repo1 = get_repo()
            repo2 = get_repo()
            repo3 = get_repo()

            # Assert
            assert repo1 is repo2 is repo3
            mock_repo_class.assert_called_once()

    def test_different_repo_after_reset_cycle(self) -> None:
        """Test that reset creates space for new repo on next get."""
        # Arrange
        with patch("git_mcp_server.utils.git_client.Repo") as mock_repo_class:
            instances = [Mock(spec=git.Repo), Mock(spec=git.Repo)]
            mock_repo_class.side_effect = instances
            reset_repo()

            # Act: Cycle 1
            repo1 = get_repo()
            repo1_again = get_repo()

            # Act: Reset and Cycle 2
            reset_repo()
            repo2 = get_repo()
            repo2_again = get_repo()

            # Assert: Same instance within cycles, different across cycles
            assert repo1 is repo1_again
            assert repo2 is repo2_again
            assert repo1 is not repo2

    def test_repo_passed_correct_parameters_to_constructor(self) -> None:
        """Test that Repo is initialized with correct parameters."""
        # Arrange
        with patch("git_mcp_server.utils.git_client.Repo") as mock_repo_class:
            with patch("git_mcp_server.utils.git_client.Path.cwd") as mock_cwd:
                current_path = Path("/current/working/dir")
                mock_cwd.return_value = current_path
                mock_instance = Mock(spec=git.Repo)
                mock_repo_class.return_value = mock_instance
                reset_repo()

                # Act
                get_repo()

                # Assert
                mock_repo_class.assert_called_once_with(
                    current_path, search_parent_directories=True
                )
