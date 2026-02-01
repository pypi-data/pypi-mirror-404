"""Unit tests for git_mcp_server.utils.errors.

Tests structured error handling and GitError dataclass.
"""

from dataclasses import fields

import git
import pytest

from git_mcp_server.utils import GitError, handle_git_error


class TestGitError:
    """Test GitError dataclass."""

    def test_creates_git_error_with_all_fields(self) -> None:
        """Test that GitError can be created with all required fields."""
        # Arrange
        error = GitError(
            error_type="test_error",
            message="Test message",
            suggestion="Test suggestion",
            command="test command",
        )

        # Assert
        assert error.error_type == "test_error"
        assert error.message == "Test message"
        assert error.suggestion == "Test suggestion"
        assert error.command == "test command"

    def test_creates_git_error_without_command(self) -> None:
        """Test that GitError can be created without optional command field."""
        # Arrange
        error = GitError(
            error_type="test_error",
            message="Test message",
            suggestion="Test suggestion",
        )

        # Assert
        assert error.error_type == "test_error"
        assert error.message == "Test message"
        assert error.suggestion == "Test suggestion"
        assert error.command is None

    def test_git_error_is_frozen_dataclass(self) -> None:
        """Test that GitError is frozen and cannot be modified."""
        # Arrange
        error = GitError(
            error_type="test",
            message="msg",
            suggestion="sug",
        )

        # Act & Assert
        with pytest.raises(AttributeError):
            error.message = "modified"  # type: ignore

    def test_git_error_has_required_fields(self) -> None:
        """Test that GitError has all required fields."""
        # Arrange
        error_fields = {f.name for f in fields(GitError)}

        # Assert
        expected_fields = {"error_type", "message", "suggestion", "command"}
        assert error_fields == expected_fields

    def test_git_error_is_dataclass(self) -> None:
        """Test that GitError is a dataclass."""
        # Arrange
        error = GitError(
            error_type="test",
            message="msg",
            suggestion="sug",
        )

        # Assert: Dataclasses have __dataclass_fields__
        assert hasattr(GitError, "__dataclass_fields__")
        assert len(fields(error)) == 4

    def test_git_error_command_field_is_optional(self) -> None:
        """Test that command field is Optional[str]."""
        # Arrange
        error1 = GitError(
            error_type="test",
            message="msg",
            suggestion="sug",
            command=None,
        )
        error2 = GitError(
            error_type="test",
            message="msg",
            suggestion="sug",
            command="git status",
        )

        # Assert
        assert error1.command is None
        assert error2.command == "git status"


class TestHandleGitErrorInvalidRepository:
    """Test handle_git_error with InvalidGitRepositoryError."""

    def test_invalid_repository_error_returns_not_a_repo_type(self) -> None:
        """Test that InvalidGitRepositoryError returns not_a_repo error type."""
        # Arrange
        original_error = git.InvalidGitRepositoryError("Not a git repo")

        # Act
        result = handle_git_error(original_error)

        # Assert
        assert result.error_type == "not_a_repo"
        assert isinstance(result, GitError)

    def test_invalid_repository_error_includes_message(self) -> None:
        """Test that error message is preserved from original error."""
        # Arrange
        original_error = git.InvalidGitRepositoryError("Not a git repo")

        # Act
        result = handle_git_error(original_error)

        # Assert
        assert result.message is not None
        assert len(result.message) > 0

    def test_invalid_repository_error_includes_helpful_suggestion(self) -> None:
        """Test that suggestion includes guidance to navigate to git repo."""
        # Arrange
        original_error = git.InvalidGitRepositoryError("Not a git repo")

        # Act
        result = handle_git_error(original_error)

        # Assert
        assert "git repository" in result.suggestion.lower()
        assert result.suggestion is not None

    def test_invalid_repository_error_includes_diagnostic_command(self) -> None:
        """Test that command suggests git status for diagnosis."""
        # Arrange
        original_error = git.InvalidGitRepositoryError("Not a git repo")

        # Act
        result = handle_git_error(original_error)

        # Assert
        assert result.command == "git status"

    def test_invalid_repository_different_error_messages(self) -> None:
        """Test handling of InvalidGitRepositoryError with different messages."""
        # Test multiple error message variations
        messages = [
            "Not a git repository",
            "Error: not a repo",
            "/path/to/dir",
        ]

        for msg in messages:
            error = git.InvalidGitRepositoryError(msg)
            result = handle_git_error(error)

            assert result.error_type == "not_a_repo"
            assert result.command == "git status"


class TestHandleGitErrorAuthenticationFailure:
    """Test handle_git_error with authentication failures."""

    def test_authentication_failed_message_returns_auth_failed_type(self) -> None:
        """Test that 'authentication failed' message returns auth_failed error type."""
        # Arrange
        error = git.GitCommandError("push", "everything up-to-date", stderr="authentication failed")

        # Act
        result = handle_git_error(error)

        # Assert
        assert result.error_type == "auth_failed"

    def test_permission_denied_message_returns_auth_failed_type(self) -> None:
        """Test that 'permission denied' message returns auth_failed error type."""
        # Arrange
        error = git.GitCommandError(
            "pull", "fatal: could not read from repository", stderr="Permission denied"
        )

        # Act
        result = handle_git_error(error)

        # Assert
        assert result.error_type == "auth_failed"

    def test_auth_failed_includes_helpful_suggestion(self) -> None:
        """Test that auth error includes guidance on fixing credentials."""
        # Arrange
        error = git.GitCommandError("push", "everything up-to-date", stderr="authentication failed")

        # Act
        result = handle_git_error(error)

        # Assert
        assert "credential" in result.suggestion.lower()
        assert "ssh" in result.suggestion.lower()

    def test_auth_failed_includes_diagnostic_command(self) -> None:
        """Test that auth error includes command to check git config."""
        # Arrange
        error = git.GitCommandError("push", "everything up-to-date", stderr="authentication failed")

        # Act
        result = handle_git_error(error)

        # Assert
        assert "git config" in result.command.lower()

    def test_case_insensitive_authentication_detection(self) -> None:
        """Test that auth detection is case-insensitive."""
        # Arrange
        errors = [
            git.GitCommandError("cmd", "msg", stderr="AUTHENTICATION FAILED"),
            git.GitCommandError("cmd", "msg", stderr="Authentication Failed"),
            git.GitCommandError("cmd", "msg", stderr="PERMISSION DENIED"),
            git.GitCommandError("cmd", "msg", stderr="Permission Denied"),
        ]

        # Act & Assert
        for error in errors:
            result = handle_git_error(error)
            assert result.error_type == "auth_failed"


class TestHandleGitErrorMergeConflict:
    """Test handle_git_error with merge conflicts."""

    def test_conflict_message_returns_merge_conflict_type(self) -> None:
        """Test that 'conflict' message returns merge_conflict error type."""
        # Arrange
        error = git.GitCommandError("merge", "CONFLICT (content): ", stderr="conflict")

        # Act
        result = handle_git_error(error)

        # Assert
        assert result.error_type == "merge_conflict"

    def test_merge_message_returns_merge_conflict_type(self) -> None:
        """Test that 'merge' message returns merge_conflict error type."""
        # Arrange
        error = git.GitCommandError("pull", "Merge in progress", stderr="merge error")

        # Act
        result = handle_git_error(error)

        # Assert
        assert result.error_type == "merge_conflict"

    def test_merge_conflict_includes_resolution_suggestion(self) -> None:
        """Test that merge conflict includes resolution steps."""
        # Arrange
        error = git.GitCommandError("merge", "CONFLICT", stderr="conflict")

        # Act
        result = handle_git_error(error)

        # Assert
        assert "merge conflict" in result.suggestion.lower()
        assert "stage" in result.suggestion.lower() or "resolve" in result.suggestion.lower()

    def test_merge_conflict_includes_diagnostic_command(self) -> None:
        """Test that merge conflict includes git status command."""
        # Arrange
        error = git.GitCommandError("merge", "CONFLICT", stderr="conflict")

        # Act
        result = handle_git_error(error)

        # Assert
        assert result.command == "git status"

    def test_case_insensitive_conflict_detection(self) -> None:
        """Test that conflict detection is case-insensitive."""
        # Arrange
        errors = [
            git.GitCommandError("cmd", "msg", stderr="CONFLICT"),
            git.GitCommandError("cmd", "msg", stderr="Conflict"),
            git.GitCommandError("cmd", "msg", stderr="MERGE"),
            git.GitCommandError("cmd", "msg", stderr="Merge"),
        ]

        # Act & Assert
        for error in errors:
            result = handle_git_error(error)
            assert result.error_type == "merge_conflict"


class TestHandleGitErrorDetachedHead:
    """Test handle_git_error with detached HEAD state."""

    def test_detached_head_message_returns_detached_head_type(self) -> None:
        """Test that 'detached head' message returns detached_head error type."""
        # Arrange
        error = git.GitCommandError(
            "checkout", "You are in detached HEAD state", stderr="detached head"
        )

        # Act
        result = handle_git_error(error)

        # Assert
        assert result.error_type == "detached_head"

    def test_detached_head_includes_branch_creation_suggestion(self) -> None:
        """Test that detached head suggests creating a new branch."""
        # Arrange
        error = git.GitCommandError("cmd", "msg", stderr="detached head")

        # Act
        result = handle_git_error(error)

        # Assert
        assert "branch" in result.suggestion.lower()
        assert "checkout" in result.suggestion.lower()

    def test_detached_head_includes_branch_creation_command(self) -> None:
        """Test that detached head includes example branch creation command."""
        # Arrange
        error = git.GitCommandError("cmd", "msg", stderr="detached head")

        # Act
        result = handle_git_error(error)

        # Assert
        assert "git checkout" in result.command.lower()
        assert "-b" in result.command.lower()

    def test_case_insensitive_detached_head_detection(self) -> None:
        """Test that detached head detection is case-insensitive."""
        # Arrange
        errors = [
            git.GitCommandError("cmd", "msg", stderr="DETACHED HEAD"),
            git.GitCommandError("cmd", "msg", stderr="Detached Head"),
        ]

        # Act & Assert
        for error in errors:
            result = handle_git_error(error)
            assert result.error_type == "detached_head"


class TestHandleGitErrorNothingToCommit:
    """Test handle_git_error with nothing to commit."""

    def test_nothing_to_commit_returns_nothing_to_commit_type(self) -> None:
        """Test that 'nothing to commit' message returns nothing_to_commit error type."""
        # Arrange
        error = git.GitCommandError("commit", "nothing to commit", stderr="nothing to commit")

        # Act
        result = handle_git_error(error)

        # Assert
        assert result.error_type == "nothing_to_commit"

    def test_nothing_to_commit_includes_helpful_suggestion(self) -> None:
        """Test that nothing to commit suggests making changes or checking status."""
        # Arrange
        error = git.GitCommandError("commit", "nothing to commit", stderr="nothing to commit")

        # Act
        result = handle_git_error(error)

        # Assert
        assert "changes" in result.suggestion.lower()
        assert "status" in result.suggestion.lower()

    def test_nothing_to_commit_includes_diagnostic_command(self) -> None:
        """Test that nothing to commit includes git status command."""
        # Arrange
        error = git.GitCommandError("commit", "nothing to commit", stderr="nothing to commit")

        # Act
        result = handle_git_error(error)

        # Assert
        assert result.command == "git status"

    def test_case_insensitive_nothing_to_commit_detection(self) -> None:
        """Test that nothing to commit detection is case-insensitive."""
        # Arrange
        errors = [
            git.GitCommandError("cmd", "msg", stderr="NOTHING TO COMMIT"),
            git.GitCommandError("cmd", "msg", stderr="Nothing To Commit"),
        ]

        # Act & Assert
        for error in errors:
            result = handle_git_error(error)
            assert result.error_type == "nothing_to_commit"


class TestHandleGitErrorNoRemote:
    """Test handle_git_error with no remote configured."""

    def test_no_configured_push_destination_returns_no_remote_type(self) -> None:
        """Test that 'no configured push destination' returns no_remote error type."""
        # Arrange
        error = git.GitCommandError(
            "push", "fatal: No configured push destination", stderr="no configured push destination"
        )

        # Act
        result = handle_git_error(error)

        # Assert
        assert result.error_type == "no_remote"

    def test_no_upstream_branch_returns_no_remote_type(self) -> None:
        """Test that 'no upstream branch' returns no_remote error type."""
        # Arrange
        error = git.GitCommandError(
            "push", "fatal: The current branch has no upstream branch", stderr="no upstream branch"
        )

        # Act
        result = handle_git_error(error)

        # Assert
        assert result.error_type == "no_remote"

    def test_no_remote_includes_setup_suggestion(self) -> None:
        """Test that no remote error includes guidance on setting up remote."""
        # Arrange
        error = git.GitCommandError("push", "fatal: No configured push destination", stderr="no")

        # Act
        result = handle_git_error(error)

        # Assert
        assert "remote" in result.suggestion.lower()
        assert "add" in result.suggestion.lower() or "set" in result.suggestion.lower()

    def test_no_remote_includes_diagnostic_command(self) -> None:
        """Test that no remote error includes git remote command."""
        # Arrange
        error = git.GitCommandError("push", "fatal: No configured push destination", stderr="no")

        # Act
        result = handle_git_error(error)

        # Assert
        assert "git remote" in result.command.lower()

    def test_case_insensitive_no_remote_detection(self) -> None:
        """Test that no remote detection is case-insensitive."""
        # Arrange
        errors = [
            git.GitCommandError("cmd", "msg", stderr="NO CONFIGURED PUSH DESTINATION"),
            git.GitCommandError("cmd", "msg", stderr="No Upstream Branch"),
        ]

        # Act & Assert
        for error in errors:
            result = handle_git_error(error)
            assert result.error_type == "no_remote"


class TestHandleGitErrorGenericCommandFailure:
    """Test handle_git_error with generic git command failures."""

    def test_unrecognized_git_command_error_returns_git_command_failed_type(self) -> None:
        """Test that unrecognized GitCommandError returns git_command_failed type."""
        # Arrange
        error = git.GitCommandError("unknown", "some unknown error", stderr="")

        # Act
        result = handle_git_error(error)

        # Assert
        assert result.error_type == "git_command_failed"

    def test_generic_git_error_includes_original_message(self) -> None:
        """Test that generic error includes original error message."""
        # Arrange
        error = git.GitCommandError("cmd", "some unknown error", stderr="")

        # Act
        result = handle_git_error(error)

        # Assert
        assert "Git command failed" in result.message

    def test_generic_git_error_includes_diagnostic_suggestion(self) -> None:
        """Test that generic error suggests checking git status."""
        # Arrange
        error = git.GitCommandError("cmd", "error", stderr="")

        # Act
        result = handle_git_error(error)

        # Assert
        assert "status" in result.suggestion.lower()

    def test_generic_git_error_includes_diagnostic_command(self) -> None:
        """Test that generic error includes git status command."""
        # Arrange
        error = git.GitCommandError("cmd", "error", stderr="")

        # Act
        result = handle_git_error(error)

        # Assert
        assert result.command == "git status"


class TestHandleGitErrorValueError:
    """Test handle_git_error with ValueError."""

    def test_value_error_returns_validation_error_type(self) -> None:
        """Test that ValueError returns validation_error error type."""
        # Arrange
        error = ValueError("Invalid input")

        # Act
        result = handle_git_error(error)

        # Assert
        assert result.error_type == "validation_error"

    def test_value_error_includes_message(self) -> None:
        """Test that ValueError message is preserved."""
        # Arrange
        error = ValueError("Invalid input data")

        # Act
        result = handle_git_error(error)

        # Assert
        assert "Invalid input" in result.message

    def test_value_error_includes_helpful_suggestion(self) -> None:
        """Test that ValueError includes suggestion to check parameters."""
        # Arrange
        error = ValueError("Invalid input")

        # Act
        result = handle_git_error(error)

        # Assert
        assert "error" in result.suggestion.lower()
        assert "input" in result.suggestion.lower() or "parameter" in result.suggestion.lower()

    def test_value_error_has_no_command(self) -> None:
        """Test that ValueError has no suggested command."""
        # Arrange
        error = ValueError("Invalid input")

        # Act
        result = handle_git_error(error)

        # Assert
        assert result.command is None


class TestHandleGitErrorUnknownException:
    """Test handle_git_error with unexpected exception types."""

    def test_runtime_error_returns_unknown_error_type(self) -> None:
        """Test that unexpected RuntimeError returns unknown_error type."""
        # Arrange
        error = RuntimeError("Something unexpected")

        # Act
        result = handle_git_error(error)

        # Assert
        assert result.error_type == "unknown_error"

    def test_unknown_error_includes_original_message(self) -> None:
        """Test that unknown error message is preserved."""
        # Arrange
        error = RuntimeError("Unexpected error message")

        # Act
        result = handle_git_error(error)

        # Assert
        assert "Unexpected" in result.message

    def test_unknown_error_includes_helpful_suggestion(self) -> None:
        """Test that unknown error includes suggestion to report if persistent."""
        # Arrange
        error = RuntimeError("Unknown")

        # Act
        result = handle_git_error(error)

        # Assert
        assert "error" in result.suggestion.lower() or "report" in result.suggestion.lower()

    def test_unknown_error_includes_diagnostic_command(self) -> None:
        """Test that unknown error includes git status command."""
        # Arrange
        error = RuntimeError("Unknown")

        # Act
        result = handle_git_error(error)

        # Assert
        assert result.command == "git status"

    def test_exception_returns_valid_git_error(self) -> None:
        """Test that any exception returns a valid GitError."""
        # Arrange
        error = Exception("Generic exception")

        # Act
        result = handle_git_error(error)

        # Assert
        assert isinstance(result, GitError)
        assert result.error_type is not None
        assert result.message is not None
        assert result.suggestion is not None


class TestHandleGitErrorEdgeCases:
    """Test handle_git_error edge cases."""

    def test_error_priority_authentication_before_merge(self) -> None:
        """Test that authentication error takes priority over merge error keywords."""
        # Arrange: Error with both auth and merge keywords
        error = git.GitCommandError(
            "cmd",
            "authentication failed during merge",
            stderr="authentication failed during merge",
        )

        # Act
        result = handle_git_error(error)

        # Assert: Should detect auth first (appears first in if-elif chain)
        assert result.error_type == "auth_failed"

    def test_error_message_with_multiple_error_indicators(self) -> None:
        """Test error with multiple conflicting error type indicators."""
        # Arrange: Error with multiple keywords
        error = git.GitCommandError(
            "cmd",
            "nothing to commit, detached HEAD state",
            stderr="nothing to commit detached",
        )

        # Act
        result = handle_git_error(error)

        # Assert: Should match first pattern (merge/conflict before nothing)
        assert result.error_type in ["merge_conflict", "nothing_to_commit", "detached_head"]

    def test_error_with_empty_message(self) -> None:
        """Test error with empty message string."""
        # Arrange
        error = git.GitCommandError("cmd", "", stderr="")

        # Act
        result = handle_git_error(error)

        # Assert
        assert isinstance(result, GitError)
        assert result.error_type == "git_command_failed"

    def test_error_none_message_handled_gracefully(self) -> None:
        """Test that None-like error messages are handled."""
        # Arrange
        error = RuntimeError(None)  # type: ignore

        # Act
        result = handle_git_error(error)

        # Assert
        assert isinstance(result, GitError)
        assert result.error_type == "unknown_error"
