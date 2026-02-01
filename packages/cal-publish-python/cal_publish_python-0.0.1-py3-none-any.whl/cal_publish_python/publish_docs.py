# ────────────────────────────────────────────────────────────────────────────────────────
#   publish_docs.py
#   ────────────────
#
#   Documentation publishing functionality.
#
#   Supports two modes:
#   - GitLab Pages: Uses gitlab-pages-upload to publish to GitLab Pages
#   - SSH: Uses rsync/scp to upload to a remote server via SSH
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

import os
import subprocess
import tempfile
import zipfile
from dataclasses import dataclass
from pathlib import Path
from .config import DocsConfig
from .config import GitLabPagesConfig
from .config import SSHDocsConfig

# ────────────────────────────────────────────────────────────────────────────────────────
#   Data Classes
# ────────────────────────────────────────────────────────────────────────────────────────


# ────────────────────────────────────────────────────────────────────────────────────────
@dataclass
class DocsPublishResult:
    """Result of a documentation publish operation."""

    success: bool
    """Whether the operation succeeded."""

    message: str
    """Human-readable result message."""

    url: str | None = None
    """URL where the documentation was published (if available)."""


# ────────────────────────────────────────────────────────────────────────────────────────
#   Main Entry Point
# ────────────────────────────────────────────────────────────────────────────────────────


# ────────────────────────────────────────────────────────────────────────────────────────
def publish_docs(
    docs_path: Path,
    project_name: str,
    version: str,
    config: DocsConfig,
    *,
    set_latest: bool = False,
    force: bool = False,
    verbose: bool = False,
) -> DocsPublishResult:
    """
    Publish documentation using the configured mode.

    Parameters:
        docs_path: Path to the documentation (directory or .zip file).
        project_name: Name of the project.
        version: Version string for the documentation.
        config: Documentation publishing configuration.
        set_latest: If True, also set this version as 'latest'.
        force: If True, overwrite existing version.
        verbose: If True, print detailed output.

    Returns:
        DocsPublishResult indicating success or failure.
    """
    if config.mode == "gitlab-pages":
        return _publish_to_gitlab_pages(
            docs_path=docs_path,
            project_name=project_name,
            version=version,
            config=config.gitlab_pages,
            set_latest=set_latest,
            force=force,
            verbose=verbose,
        )
    elif config.mode == "ssh":
        return _publish_via_ssh(
            docs_path=docs_path,
            project_name=project_name,
            version=version,
            config=config.ssh,
            verbose=verbose,
        )
    else:
        return DocsPublishResult(
            success=False,
            message=f"Unknown documentation publishing mode: {config.mode}",
        )


# ────────────────────────────────────────────────────────────────────────────────────────
#   GitLab Pages Publishing
# ────────────────────────────────────────────────────────────────────────────────────────


# ────────────────────────────────────────────────────────────────────────────────────────
def _publish_to_gitlab_pages(
    docs_path: Path,
    project_name: str,
    version: str,
    config: GitLabPagesConfig,
    *,
    set_latest: bool = False,
    force: bool = False,
    verbose: bool = False,
) -> DocsPublishResult:
    """Publish documentation to GitLab Pages using gitlab-pages-upload."""
    try:
        # gitlab-pages-upload is a dev dependency
        from gitlab_pages_upload.cli import (  # pyright: ignore[reportMissingImports]
            main as gitlab_upload_main,  # pyright: ignore[reportUnknownVariableType]
        )
    except ImportError:
        return DocsPublishResult(
            success=False,
            message=(
                "gitlab-pages-upload not installed. "
                "Install it with: pip install gitlab-pages-upload"
            ),
        )

    if not config.token:
        return DocsPublishResult(
            success=False,
            message=(
                "GitLab token not configured. "
                "Set CAL_PUBLISH_GITLAB_TOKEN or configure in JSON."
            ),
        )

    if not docs_path.exists():
        return DocsPublishResult(
            success=False,
            message=f"Documentation path not found: {docs_path}",
        )

    if verbose:
        print(f"Publishing {project_name} v{version} to GitLab Pages")
        print(f"  GitLab URL: {config.url}")
        print(f"  Group: {config.group}")

    # Set the token in the environment for gitlab-pages-upload
    env_backup = os.environ.get("GITLAB_TOKEN")
    os.environ["GITLAB_TOKEN"] = config.token

    try:
        # Build arguments for gitlab-pages-upload
        args = [
            "--project",
            project_name,
            "--doc-version",
            version,
            "--html",
            str(docs_path),
            "--gitlab-url",
            config.url,
            "--group",
            config.group,
        ]

        if set_latest:
            args.append("--set-latest")

        if force:
            args.append("--force")

        if verbose:
            args.extend(["-v", "-v"])

        # Call gitlab-pages-upload
        exit_code: int = gitlab_upload_main(args)  # pyright: ignore[reportUnknownVariableType]

        if exit_code == 0:
            # Construct the URL
            group_path = config.group.replace("/", "-")
            base_url = config.url.replace("https://", "").replace("http://", "")
            docs_url = f"https://{group_path}.{base_url}/{project_name}/{version}/"

            return DocsPublishResult(
                success=True,
                message=(
                    f"Successfully published documentation for {project_name}"
                    f" v{version}"
                ),
                url=docs_url,
            )
        else:
            return DocsPublishResult(
                success=False,
                message=f"gitlab-pages-upload failed with exit code {exit_code}",
            )

    finally:
        # Restore original environment
        if env_backup is not None:
            os.environ["GITLAB_TOKEN"] = env_backup
        elif "GITLAB_TOKEN" in os.environ:
            del os.environ["GITLAB_TOKEN"]


# ────────────────────────────────────────────────────────────────────────────────────────
#   SSH Publishing
# ────────────────────────────────────────────────────────────────────────────────────────


# ────────────────────────────────────────────────────────────────────────────────────────
def _publish_via_ssh(
    docs_path: Path,
    project_name: str,
    version: str,
    config: SSHDocsConfig,
    *,
    verbose: bool = False,
) -> DocsPublishResult:
    """Publish documentation to a remote server via SSH using rsync."""
    # Validate configuration
    if not config.host:
        return DocsPublishResult(
            success=False,
            message=(
                "SSH host not configured. Set CAL_PUBLISH_SSH_HOST or configure in"
                " JSON."
            ),
        )

    if not config.base_path:
        return DocsPublishResult(
            success=False,
            message=(
                "SSH base path not configured. "
                "Set CAL_PUBLISH_SSH_BASE_PATH or configure in JSON."
            ),
        )

    if not config.ssh_key:
        return DocsPublishResult(
            success=False,
            message=(
                "SSH key not configured. Set CAL_PUBLISH_SSH_KEY or configure in JSON."
            ),
        )

    if not docs_path.exists():
        return DocsPublishResult(
            success=False,
            message=f"Documentation path not found: {docs_path}",
        )

    ssh_key_path = Path(config.ssh_key).expanduser()
    if not ssh_key_path.exists():
        return DocsPublishResult(
            success=False,
            message=f"SSH key file not found: {ssh_key_path}",
        )

    # Determine source directory (extract zip if needed)
    if docs_path.suffix == ".zip":
        return _publish_zip_via_ssh(
            zip_path=docs_path,
            project_name=project_name,
            version=version,
            config=config,
            ssh_key_path=ssh_key_path,
            verbose=verbose,
        )
    else:
        return _rsync_to_remote(
            source_dir=docs_path,
            project_name=project_name,
            version=version,
            config=config,
            ssh_key_path=ssh_key_path,
            verbose=verbose,
        )


# ────────────────────────────────────────────────────────────────────────────────────────
def _publish_zip_via_ssh(
    zip_path: Path,
    project_name: str,
    version: str,
    config: SSHDocsConfig,
    ssh_key_path: Path,
    *,
    verbose: bool = False,
) -> DocsPublishResult:
    """Extract a zip file and publish via SSH."""
    with tempfile.TemporaryDirectory() as temp_dir:
        extract_path = Path(temp_dir) / "docs"
        extract_path.mkdir()

        if verbose:
            print(f"Extracting {zip_path} to {extract_path}")

        try:
            with zipfile.ZipFile(zip_path, "r") as zf:
                zf.extractall(extract_path)
        except zipfile.BadZipFile:
            return DocsPublishResult(
                success=False,
                message=f"Invalid zip file: {zip_path}",
            )

        return _rsync_to_remote(
            source_dir=extract_path,
            project_name=project_name,
            version=version,
            config=config,
            ssh_key_path=ssh_key_path,
            verbose=verbose,
        )


# ────────────────────────────────────────────────────────────────────────────────────────
def _rsync_to_remote(
    source_dir: Path,
    project_name: str,
    version: str,
    config: SSHDocsConfig,
    ssh_key_path: Path,
    *,
    verbose: bool = False,
) -> DocsPublishResult:
    """Use rsync to upload documentation to the remote server."""
    # These are validated before this function is called
    assert config.base_path is not None
    assert config.host is not None

    # Build remote path: base_path/project_name-version/
    remote_path = f"{config.base_path.rstrip('/')}/{project_name}-{version}/"

    # Build SSH destination
    if config.user:
        destination = f"{config.user}@{config.host}:{remote_path}"
    else:
        destination = f"{config.host}:{remote_path}"

    if verbose:
        print(f"Uploading to {destination}")

    # Build rsync command
    cmd = [
        "rsync",
        "-avz",
        "--delete",
        "-e",
        (
            f"ssh -i {ssh_key_path} -p {config.port} "
            "-o StrictHostKeyChecking=no -o UserKnownHostsFile=/dev/null"
        ),
        f"{source_dir}/",
        destination,
    ]

    if verbose:
        cmd.append("--progress")

    try:
        result = subprocess.run(
            cmd,
            capture_output=not verbose,
            text=True,
            check=False,
        )

        if result.returncode == 0:
            return DocsPublishResult(
                success=True,
                message=(
                    "Successfully uploaded documentation for "
                    f"{project_name} v{version} to {config.host}"
                ),
            )
        else:
            error_msg = result.stderr if result.stderr else "Unknown error"
            return DocsPublishResult(
                success=False,
                message=f"rsync failed: {error_msg}",
            )

    except FileNotFoundError:
        return DocsPublishResult(
            success=False,
            message="rsync not found. Please install rsync.",
        )
    except Exception as e:
        return DocsPublishResult(
            success=False,
            message=f"Unexpected error: {e}",
        )
