"""Git operations for code persistence.

This module handles:
- Cloning repositories with authentication
- Branch creation and checkout
- Committing and pushing changes

IMPORTANT: The GitHub token is used for git operations via HTTPS.
It should never be exposed to the AI model - only the harness uses it.
"""

from __future__ import annotations

import subprocess
import sys
from dataclasses import dataclass
from pathlib import Path
from typing import Callable

from bootstrap.payload import RepoContext


@dataclass
class GitConfig:
    """Configuration for git operations."""

    workspace: Path
    repo_context: RepoContext
    github_token: str
    log_fn: Callable[[str, str], None] | None = None

    def log(self, level: str, message: str) -> None:
        """Log a message using the provided log function."""
        if self.log_fn:
            self.log_fn(level, message)
        else:
            print(f"[git:{level}] {message}", file=sys.stderr)


def _run_git(
    args: list[str],
    cwd: Path,
    env: dict[str, str] | None = None,
    capture_output: bool = True,
) -> subprocess.CompletedProcess:
    """Run a git command and return the result."""
    import os

    full_env = os.environ.copy()
    if env:
        full_env.update(env)

    return subprocess.run(
        ["git"] + args,
        cwd=cwd,
        capture_output=capture_output,
        text=True,
        env=full_env,
    )


def setup_git_credentials(config: GitConfig) -> bool:
    """Configure git to use the GitHub token for authentication.

    Uses the credential helper to store the token temporarily.
    The token is only valid for 1 hour.

    Returns:
        True if setup succeeded, False otherwise.
    """
    workspace = config.workspace
    token = config.github_token

    # Configure git to use the token via credential helper
    # We use a simple approach: configure the remote URL with the token embedded
    # This is safe because the workspace is ephemeral and the token is short-lived

    # First, configure git user for commits
    result = _run_git(
        ["config", "user.email", "flywheel@example.com"],
        cwd=workspace,
    )
    if result.returncode != 0:
        config.log("warning", f"Failed to set git email: {result.stderr}")

    result = _run_git(
        ["config", "user.name", "Flywheel"],
        cwd=workspace,
    )
    if result.returncode != 0:
        config.log("warning", f"Failed to set git name: {result.stderr}")

    # Configure credential helper to cache the token
    # We use the 'store' helper with a file in the workspace
    credential_file = workspace / ".git-credentials"
    repo_url = config.repo_context.repo_url

    # Write credentials in the format expected by git-credential-store
    # https://x-access-token:TOKEN@github.com
    if "github.com" in repo_url:
        credential_line = f"https://x-access-token:{token}@github.com\n"
        try:
            credential_file.write_text(credential_line)
            credential_file.chmod(0o600)  # Restrict permissions

            result = _run_git(
                ["config", "credential.helper", f"store --file={credential_file}"],
                cwd=workspace,
            )
            if result.returncode != 0:
                config.log(
                    "warning", f"Failed to set credential helper: {result.stderr}"
                )
                return False

            config.log("info", "Git credentials configured")
            return True
        except Exception as e:
            config.log("error", f"Failed to write credentials: {e}")
            return False

    return False


def clone_repository(config: GitConfig) -> bool:
    """Clone the repository to the workspace.

    Returns:
        True if clone succeeded, False otherwise.
    """
    repo = config.repo_context
    workspace = config.workspace
    token = config.github_token

    # Build authenticated URL
    # Format: https://x-access-token:TOKEN@github.com/owner/repo.git
    auth_url = repo.repo_url.replace(
        "https://github.com", f"https://x-access-token:{token}@github.com"
    )

    config.log("info", f"Cloning repository {repo.repo_owner}/{repo.repo_name}")

    # Clone to a temp directory first, then move contents to workspace
    # This handles the case where workspace might have existing content
    result = _run_git(
        ["clone", "--depth=1", "-b", repo.base_branch, auth_url, "."],
        cwd=workspace,
    )

    if result.returncode != 0:
        config.log("error", f"Failed to clone repository: {result.stderr}")
        return False

    config.log("info", "Repository cloned successfully")
    return True


def setup_branch(config: GitConfig) -> bool:
    """Create or checkout the experiment branch.

    If the branch already exists on remote, we check it out.
    Otherwise, we create it from the base branch.

    Returns:
        True if branch setup succeeded, False otherwise.
    """
    repo = config.repo_context
    workspace = config.workspace

    branch_name = repo.branch_name
    base_branch = repo.base_branch

    # Fetch all branches
    result = _run_git(["fetch", "--all"], cwd=workspace)
    if result.returncode != 0:
        config.log("warning", f"Failed to fetch: {result.stderr}")

    # Check if branch exists on remote
    result = _run_git(
        ["ls-remote", "--heads", "origin", branch_name],
        cwd=workspace,
    )

    if result.returncode == 0 and branch_name in result.stdout:
        # Branch exists, check it out
        config.log("info", f"Checking out existing branch: {branch_name}")
        result = _run_git(
            ["checkout", "-B", branch_name, f"origin/{branch_name}"],
            cwd=workspace,
        )
    else:
        # Branch doesn't exist, create from base
        config.log("info", f"Creating new branch: {branch_name} from {base_branch}")
        result = _run_git(
            ["checkout", "-b", branch_name],
            cwd=workspace,
        )

    if result.returncode != 0:
        config.log("error", f"Failed to setup branch: {result.stderr}")
        return False

    config.log("info", f"Branch {branch_name} is ready")
    return True


def commit_changes(config: GitConfig, message: str) -> bool:
    """Commit any changes in the workspace.

    Returns:
        True if commit succeeded (or no changes to commit), False on error.
    """
    workspace = config.workspace

    # Check if there are any changes
    result = _run_git(["status", "--porcelain"], cwd=workspace)
    if result.returncode != 0:
        config.log("error", f"Failed to check status: {result.stderr}")
        return False

    if not result.stdout.strip():
        config.log("info", "No changes to commit")
        return True

    # Stage all changes
    result = _run_git(["add", "-A"], cwd=workspace)
    if result.returncode != 0:
        config.log("error", f"Failed to stage changes: {result.stderr}")
        return False

    # Commit
    result = _run_git(
        ["commit", "-m", message],
        cwd=workspace,
    )
    if result.returncode != 0:
        config.log("error", f"Failed to commit: {result.stderr}")
        return False

    config.log("info", f"Changes committed: {message}")
    return True


def push_changes(config: GitConfig) -> bool:
    """Push committed changes to the remote.

    Returns:
        True if push succeeded, False otherwise.
    """
    workspace = config.workspace
    branch_name = config.repo_context.branch_name

    config.log("info", f"Pushing to origin/{branch_name}")

    result = _run_git(
        ["push", "-u", "origin", branch_name],
        cwd=workspace,
    )

    if result.returncode != 0:
        config.log("error", f"Failed to push: {result.stderr}")
        return False

    config.log("info", "Push successful")
    return True


def get_head_sha(workspace: Path) -> str | None:
    """Get the SHA of the current HEAD commit.

    Returns:
        The commit SHA or None if not a git repo.
    """
    result = _run_git(["rev-parse", "HEAD"], cwd=workspace)
    if result.returncode == 0:
        return result.stdout.strip()
    return None


def initialize_repo(config: GitConfig) -> bool:
    """Initialize a fresh repository for the experiment.

    This is the main entry point for setting up code persistence.
    It handles:
    1. Cloning the repository
    2. Setting up git credentials
    3. Creating/checking out the branch

    Returns:
        True if initialization succeeded, False otherwise.
    """
    if not clone_repository(config):
        return False

    if not setup_git_credentials(config):
        return False

    if not setup_branch(config):
        return False

    return True


def finalize_repo(config: GitConfig, run_id: str) -> bool:
    """Finalize the repository after the experiment completes.

    This commits and pushes any changes made during the run.

    Args:
        config: Git configuration
        run_id: The run ID for the commit message

    Returns:
        True if finalization succeeded, False otherwise.
    """
    commit_message = f"Flywheel experiment run: {run_id}"

    if not commit_changes(config, commit_message):
        return False

    if not push_changes(config):
        return False

    return True
