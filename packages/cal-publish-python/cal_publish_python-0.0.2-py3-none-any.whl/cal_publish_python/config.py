# ────────────────────────────────────────────────────────────────────────────────────────
#   config.py
#   ─────────
#
#   Configuration handling for cal-publish-python.
#
#   Loads configuration from a JSON file (path from CAL_PUBLISH_CONFIG env var) and
#   allows all values to be overridden by environment variables.
#
#   (c) 2026 Cyber Assessment Labs — MIT License; see LICENSE in the project root.
#
#   Authors
#   ───────
#   bena (via Claude)
#
#   Version History
#   ───────────────
#   Feb 2026 - Created
# ────────────────────────────────────────────────────────────────────────────────────────

# ────────────────────────────────────────────────────────────────────────────────────────
#   Imports
# ────────────────────────────────────────────────────────────────────────────────────────

import json
import os
from dataclasses import dataclass
from dataclasses import field
from pathlib import Path
from typing import TYPE_CHECKING

if TYPE_CHECKING:
    from typing import Any

# ────────────────────────────────────────────────────────────────────────────────────────
#   Constants
# ────────────────────────────────────────────────────────────────────────────────────────

# Environment variable for config file path
CONFIG_PATH_ENV = "CAL_PUBLISH_CONFIG"

# Environment variable prefix for overrides
ENV_PREFIX = "CAL_PUBLISH_"

# Default PyPI registry URL
DEFAULT_PYPI_URL = "https://upload.pypi.org/legacy/"

# Default GitLab URL
DEFAULT_GITLAB_URL = "https://gitlab.com"

# Default GitLab group for docs
DEFAULT_GITLAB_GROUP = "docs"


# ────────────────────────────────────────────────────────────────────────────────────────
#   Data Classes
# ────────────────────────────────────────────────────────────────────────────────────────


# ────────────────────────────────────────────────────────────────────────────────────────
@dataclass
class PyPIConfig:
    """Configuration for PyPI publishing."""

    token: str | None = None
    """PyPI API token for authentication."""

    repository_url: str = DEFAULT_PYPI_URL
    """PyPI repository URL (default: https://upload.pypi.org/legacy/)."""


# ────────────────────────────────────────────────────────────────────────────────────────
@dataclass
class GitLabPagesConfig:
    """Configuration for GitLab Pages documentation publishing."""

    token: str | None = None
    """GitLab personal access token with api and write_repository scopes."""

    url: str = DEFAULT_GITLAB_URL
    """GitLab instance URL (default: https://gitlab.com)."""

    group: str = DEFAULT_GITLAB_GROUP
    """GitLab group for documentation projects (default: docs)."""


# ────────────────────────────────────────────────────────────────────────────────────────
@dataclass
class SSHDocsConfig:
    """Configuration for SSH-based documentation publishing."""

    host: str | None = None
    """SSH host to upload to."""

    base_path: str | None = None
    """Base path on the remote server for documentation."""

    ssh_key: str | None = None
    """Path to SSH private key file."""

    user: str | None = None
    """SSH user (optional, defaults to current user)."""

    port: int = 22
    """SSH port (default: 22)."""


# ────────────────────────────────────────────────────────────────────────────────────────
@dataclass
class DocsConfig:
    """Configuration for documentation publishing."""

    mode: str = "gitlab-pages"
    """Documentation publishing mode: 'gitlab-pages' or 'ssh'."""

    gitlab_pages: GitLabPagesConfig = field(default_factory=GitLabPagesConfig)
    """GitLab Pages specific configuration."""

    ssh: SSHDocsConfig = field(default_factory=SSHDocsConfig)
    """SSH specific configuration."""


# ────────────────────────────────────────────────────────────────────────────────────────
@dataclass
class Config:
    """Top-level configuration for cal-publish-python."""

    pypi: PyPIConfig = field(default_factory=PyPIConfig)
    """PyPI publishing configuration."""

    docs: DocsConfig = field(default_factory=DocsConfig)
    """Documentation publishing configuration."""


# ────────────────────────────────────────────────────────────────────────────────────────
#   Configuration Loading
# ────────────────────────────────────────────────────────────────────────────────────────


# ────────────────────────────────────────────────────────────────────────────────────────
def _get_env(key: str, default: str | None = None) -> str | None:
    """Get an environment variable with the CAL_PUBLISH_ prefix."""
    return os.environ.get(f"{ENV_PREFIX}{key}", default)


# ────────────────────────────────────────────────────────────────────────────────────────
def _get_env_int(key: str, default: int) -> int:
    """Get an integer environment variable with the CAL_PUBLISH_ prefix."""
    value = _get_env(key)
    if value is None:
        return default
    try:
        return int(value)
    except ValueError:
        return default


# ────────────────────────────────────────────────────────────────────────────────────────
def load_config(config_path: Path | None = None, *, verbose: bool = False) -> Config:
    """
    Load configuration from JSON file and environment variables.

    Configuration is loaded in the following order (later sources override earlier):
    1. Default values
    2. JSON config file (if provided or CAL_PUBLISH_CONFIG env var is set)
    3. Environment variables (CAL_PUBLISH_* prefix)

    Parameters:
        config_path: Optional path to JSON config file. If not provided, uses
                     the CAL_PUBLISH_CONFIG environment variable.
        verbose: If True, print configuration loading details.

    Returns:
        Loaded configuration.

    Environment Variables:
        CAL_PUBLISH_CONFIG: Path to JSON config file
        CAL_PUBLISH_PYPI_TOKEN: PyPI API token
        CAL_PUBLISH_PYPI_REPOSITORY_URL: PyPI repository URL
        CAL_PUBLISH_DOCS_MODE: Documentation mode ('gitlab-pages' or 'ssh')
        CAL_PUBLISH_GITLAB_TOKEN: GitLab personal access token
        CAL_PUBLISH_GITLAB_URL: GitLab instance URL
        CAL_PUBLISH_GITLAB_GROUP: GitLab group for docs
        CAL_PUBLISH_SSH_HOST: SSH host
        CAL_PUBLISH_SSH_BASE_PATH: Base path on remote server
        CAL_PUBLISH_SSH_KEY: Path to SSH private key
        CAL_PUBLISH_SSH_USER: SSH user
        CAL_PUBLISH_SSH_PORT: SSH port
    """
    config = Config()

    # Determine config file path
    if config_path is None:
        env_path = os.environ.get(CONFIG_PATH_ENV)
        if env_path:
            config_path = Path(env_path)

    # Load from JSON file if available
    if config_path is not None:
        config = _load_from_json(config_path, verbose=verbose)

    # Apply environment variable overrides
    config = _apply_env_overrides(config, verbose=verbose)

    return config


# ────────────────────────────────────────────────────────────────────────────────────────
def _load_from_json(config_path: Path, *, verbose: bool = False) -> Config:
    """Load configuration from a JSON file."""
    if not config_path.exists():
        raise FileNotFoundError(f"Configuration file not found: {config_path}")

    if verbose:
        print(f"Loading configuration from: {config_path}")

    with config_path.open() as f:
        data: dict[str, Any] = json.load(f)

    config = Config()

    # Load PyPI config
    if "pypi" in data:
        pypi_data = data["pypi"]
        config.pypi.token = pypi_data.get("token")
        config.pypi.repository_url = pypi_data.get("repository_url", DEFAULT_PYPI_URL)

    # Load docs config
    if "docs" in data:
        docs_data = data["docs"]
        config.docs.mode = docs_data.get("mode", "gitlab-pages")

        # GitLab Pages config
        if "gitlab_pages" in docs_data:
            gl_data = docs_data["gitlab_pages"]
            config.docs.gitlab_pages.token = gl_data.get("token")
            config.docs.gitlab_pages.url = gl_data.get("url", DEFAULT_GITLAB_URL)
            config.docs.gitlab_pages.group = gl_data.get("group", DEFAULT_GITLAB_GROUP)

        # SSH config
        if "ssh" in docs_data:
            ssh_data = docs_data["ssh"]
            config.docs.ssh.host = ssh_data.get("host")
            config.docs.ssh.base_path = ssh_data.get("base_path")
            config.docs.ssh.ssh_key = ssh_data.get("ssh_key")
            config.docs.ssh.user = ssh_data.get("user")
            config.docs.ssh.port = ssh_data.get("port", 22)

    return config


# ────────────────────────────────────────────────────────────────────────────────────────
def _apply_env_overrides(config: Config, *, verbose: bool = False) -> Config:
    """Apply environment variable overrides to the configuration."""
    # PyPI overrides
    pypi_token = _get_env("PYPI_TOKEN")
    if pypi_token:
        if verbose:
            print("Overriding pypi.token from CAL_PUBLISH_PYPI_TOKEN")
        config.pypi.token = pypi_token

    pypi_url = _get_env("PYPI_REPOSITORY_URL")
    if pypi_url:
        if verbose:
            print("Overriding pypi.repository_url from CAL_PUBLISH_PYPI_REPOSITORY_URL")
        config.pypi.repository_url = pypi_url

    # Docs mode override
    docs_mode = _get_env("DOCS_MODE")
    if docs_mode:
        if verbose:
            print("Overriding docs.mode from CAL_PUBLISH_DOCS_MODE")
        config.docs.mode = docs_mode

    # GitLab Pages overrides
    gitlab_token = _get_env("GITLAB_TOKEN")
    if gitlab_token:
        if verbose:
            print("Overriding docs.gitlab_pages.token from CAL_PUBLISH_GITLAB_TOKEN")
        config.docs.gitlab_pages.token = gitlab_token

    gitlab_url = _get_env("GITLAB_URL")
    if gitlab_url:
        if verbose:
            print("Overriding docs.gitlab_pages.url from CAL_PUBLISH_GITLAB_URL")
        config.docs.gitlab_pages.url = gitlab_url

    gitlab_group = _get_env("GITLAB_GROUP")
    if gitlab_group:
        if verbose:
            print("Overriding docs.gitlab_pages.group from CAL_PUBLISH_GITLAB_GROUP")
        config.docs.gitlab_pages.group = gitlab_group

    # SSH overrides
    ssh_host = _get_env("SSH_HOST")
    if ssh_host:
        if verbose:
            print("Overriding docs.ssh.host from CAL_PUBLISH_SSH_HOST")
        config.docs.ssh.host = ssh_host

    ssh_base_path = _get_env("SSH_BASE_PATH")
    if ssh_base_path:
        if verbose:
            print("Overriding docs.ssh.base_path from CAL_PUBLISH_SSH_BASE_PATH")
        config.docs.ssh.base_path = ssh_base_path

    ssh_key = _get_env("SSH_KEY")
    if ssh_key:
        if verbose:
            print("Overriding docs.ssh.ssh_key from CAL_PUBLISH_SSH_KEY")
        config.docs.ssh.ssh_key = ssh_key

    ssh_user = _get_env("SSH_USER")
    if ssh_user:
        if verbose:
            print("Overriding docs.ssh.user from CAL_PUBLISH_SSH_USER")
        config.docs.ssh.user = ssh_user

    ssh_port = _get_env_int("SSH_PORT", config.docs.ssh.port)
    if _get_env("SSH_PORT"):
        if verbose:
            print("Overriding docs.ssh.port from CAL_PUBLISH_SSH_PORT")
        config.docs.ssh.port = ssh_port

    return config
