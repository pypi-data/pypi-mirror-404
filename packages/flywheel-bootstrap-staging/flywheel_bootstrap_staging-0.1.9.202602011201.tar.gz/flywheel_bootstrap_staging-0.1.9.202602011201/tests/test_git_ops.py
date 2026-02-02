"""Tests for git operations module."""

from __future__ import annotations

from unittest.mock import MagicMock, patch

import pytest

from bootstrap.git_ops import (
    GitConfig,
    _run_git,
    clone_repository,
    commit_changes,
    get_head_sha,
    initialize_repo,
    push_changes,
    setup_branch,
    setup_git_credentials,
)
from bootstrap.payload import RepoContext


@pytest.fixture
def repo_context():
    """Create a test RepoContext."""
    return RepoContext(
        repo_url="https://github.com/testuser/testrepo",
        repo_owner="testuser",
        repo_name="testrepo",
        branch_name="flywheel/experiment-1",
        base_branch="main",
        is_fork=False,
    )


@pytest.fixture
def git_config(tmp_path, repo_context):
    """Create a test GitConfig."""
    workspace = tmp_path / "workspace"
    workspace.mkdir()
    return GitConfig(
        workspace=workspace,
        repo_context=repo_context,
        github_token="test-token-12345",
        log_fn=lambda level, msg: None,  # Silent logging
    )


class TestRunGit:
    """Tests for _run_git helper."""

    def test_run_git_success(self, tmp_path):
        """Test running a simple git command."""
        result = _run_git(["--version"], cwd=tmp_path)
        assert result.returncode == 0
        assert "git version" in result.stdout

    def test_run_git_failure(self, tmp_path):
        """Test running an invalid git command."""
        result = _run_git(["invalid-command"], cwd=tmp_path)
        assert result.returncode != 0


class TestSetupGitCredentials:
    """Tests for setup_git_credentials."""

    def test_setup_credentials_creates_file(self, git_config):
        """Test that credentials file is created."""
        # Initialize git repo first
        _run_git(["init"], cwd=git_config.workspace)

        result = setup_git_credentials(git_config)
        assert result is True

        credential_file = git_config.workspace / ".git-credentials"
        assert credential_file.exists()
        content = credential_file.read_text()
        assert "x-access-token:test-token-12345@github.com" in content

    def test_setup_credentials_configures_git(self, git_config):
        """Test that git is configured with user info."""
        _run_git(["init"], cwd=git_config.workspace)
        setup_git_credentials(git_config)

        result = _run_git(["config", "user.email"], cwd=git_config.workspace)
        assert result.returncode == 0
        assert "flywheel" in result.stdout.lower()


class TestCommitChanges:
    """Tests for commit_changes."""

    def test_commit_no_changes(self, git_config):
        """Test commit when there are no changes."""
        _run_git(["init"], cwd=git_config.workspace)
        setup_git_credentials(git_config)

        result = commit_changes(git_config, "Test commit")
        assert result is True  # No error even with no changes

    def test_commit_with_changes(self, git_config):
        """Test commit with actual changes."""
        _run_git(["init"], cwd=git_config.workspace)
        setup_git_credentials(git_config)

        # Create a file
        test_file = git_config.workspace / "test.txt"
        test_file.write_text("Hello, world!")

        result = commit_changes(git_config, "Add test file")
        assert result is True

        # Verify commit was created
        log_result = _run_git(["log", "--oneline", "-1"], cwd=git_config.workspace)
        assert "Add test file" in log_result.stdout


class TestGetHeadSha:
    """Tests for get_head_sha."""

    def test_get_head_sha_valid_repo(self, git_config):
        """Test getting HEAD SHA from a valid repo."""
        _run_git(["init"], cwd=git_config.workspace)
        setup_git_credentials(git_config)

        # Create initial commit
        test_file = git_config.workspace / "test.txt"
        test_file.write_text("Hello")
        _run_git(["add", "-A"], cwd=git_config.workspace)
        _run_git(["commit", "-m", "Initial"], cwd=git_config.workspace)

        sha = get_head_sha(git_config.workspace)
        assert sha is not None
        assert len(sha) == 40  # SHA-1 hash length

    def test_get_head_sha_no_repo(self, tmp_path):
        """Test getting HEAD SHA from a non-repo directory."""
        sha = get_head_sha(tmp_path)
        assert sha is None


class TestRepoContext:
    """Tests for RepoContext model."""

    def test_from_dict(self):
        """Test creating RepoContext from dict."""
        data = {
            "repo_url": "https://github.com/user/repo",
            "repo_owner": "user",
            "repo_name": "repo",
            "branch_name": "flywheel/test",
            "base_branch": "main",
            "is_fork": True,
            "fork_source_url": "https://github.com/other/repo",
        }
        ctx = RepoContext.from_dict(data)
        assert ctx.repo_url == "https://github.com/user/repo"
        assert ctx.repo_owner == "user"
        assert ctx.is_fork is True
        assert ctx.fork_source_url == "https://github.com/other/repo"


class TestCloneRepository:
    """Tests for clone_repository (mocked)."""

    @patch("bootstrap.git_ops._run_git")
    def test_clone_success(self, mock_run_git, git_config):
        """Test successful clone."""
        mock_run_git.return_value = MagicMock(returncode=0, stdout="", stderr="")

        result = clone_repository(git_config)
        assert result is True
        mock_run_git.assert_called_once()

        # Verify the clone command was constructed correctly
        call_args = mock_run_git.call_args[0][0]
        assert "clone" in call_args
        assert "--depth=1" in call_args
        assert "-b" in call_args
        assert "main" in call_args  # base_branch

    @patch("bootstrap.git_ops._run_git")
    def test_clone_failure(self, mock_run_git, git_config):
        """Test failed clone."""
        mock_run_git.return_value = MagicMock(
            returncode=1, stdout="", stderr="fatal: repository not found"
        )

        result = clone_repository(git_config)
        assert result is False


class TestSetupBranch:
    """Tests for setup_branch (mocked)."""

    @patch("bootstrap.git_ops._run_git")
    def test_setup_new_branch(self, mock_run_git, git_config):
        """Test creating a new branch."""
        # Mock responses: fetch succeeds, branch doesn't exist, checkout succeeds
        mock_run_git.side_effect = [
            MagicMock(returncode=0),  # fetch
            MagicMock(returncode=0, stdout=""),  # ls-remote (no branch found)
            MagicMock(returncode=0),  # checkout -b
        ]

        result = setup_branch(git_config)
        assert result is True

    @patch("bootstrap.git_ops._run_git")
    def test_setup_existing_branch(self, mock_run_git, git_config):
        """Test checking out an existing branch."""
        branch = git_config.repo_context.branch_name
        mock_run_git.side_effect = [
            MagicMock(returncode=0),  # fetch
            MagicMock(returncode=0, stdout=branch),  # ls-remote (branch exists)
            MagicMock(returncode=0),  # checkout -B
        ]

        result = setup_branch(git_config)
        assert result is True


class TestInitializeRepo:
    """Tests for initialize_repo (integration)."""

    @patch("bootstrap.git_ops.clone_repository")
    @patch("bootstrap.git_ops.setup_git_credentials")
    @patch("bootstrap.git_ops.setup_branch")
    def test_initialize_all_steps(
        self, mock_branch, mock_creds, mock_clone, git_config
    ):
        """Test that initialize_repo calls all steps."""
        mock_clone.return_value = True
        mock_creds.return_value = True
        mock_branch.return_value = True

        result = initialize_repo(git_config)
        assert result is True

        mock_clone.assert_called_once_with(git_config)
        mock_creds.assert_called_once_with(git_config)
        mock_branch.assert_called_once_with(git_config)

    @patch("bootstrap.git_ops.clone_repository")
    def test_initialize_fails_on_clone(self, mock_clone, git_config):
        """Test that initialize_repo fails if clone fails."""
        mock_clone.return_value = False

        result = initialize_repo(git_config)
        assert result is False


class TestPushChanges:
    """Tests for push_changes (mocked)."""

    @patch("bootstrap.git_ops._run_git")
    def test_push_success(self, mock_run_git, git_config):
        """Test successful push."""
        mock_run_git.return_value = MagicMock(returncode=0)

        result = push_changes(git_config)
        assert result is True

        call_args = mock_run_git.call_args[0][0]
        assert "push" in call_args
        assert "-u" in call_args
        assert "origin" in call_args

    @patch("bootstrap.git_ops._run_git")
    def test_push_failure(self, mock_run_git, git_config):
        """Test failed push."""
        mock_run_git.return_value = MagicMock(
            returncode=1, stderr="error: failed to push"
        )

        result = push_changes(git_config)
        assert result is False
