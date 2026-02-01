# ────────────────────────────────────────────────────────────────────────────────────────
#   publish_pypi.py
#   ────────────────
#
#   PyPI package publishing functionality.
#
#   Uses twine to upload wheel files to a PyPI repository.
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

import subprocess
import sys
from dataclasses import dataclass
from pathlib import Path
from .config import PyPIConfig

# ────────────────────────────────────────────────────────────────────────────────────────
#   Data Classes
# ────────────────────────────────────────────────────────────────────────────────────────


# ────────────────────────────────────────────────────────────────────────────────────────
@dataclass
class PublishResult:
    """Result of a publish operation."""

    success: bool
    """Whether the operation succeeded."""

    message: str
    """Human-readable result message."""

    wheel_path: Path | None = None
    """Path to the uploaded wheel file."""


# ────────────────────────────────────────────────────────────────────────────────────────
#   Functions
# ────────────────────────────────────────────────────────────────────────────────────────


# ────────────────────────────────────────────────────────────────────────────────────────
def find_wheel(output_dir: Path) -> Path | None:
    """
    Find the wheel file in the output directory.

    Parameters:
        output_dir: Directory to search for wheel files.

    Returns:
        Path to the wheel file, or None if not found.
    """
    wheels = list(output_dir.glob("*.whl"))
    if len(wheels) == 0:
        return None
    if len(wheels) > 1:
        # Return the most recently modified one
        wheels.sort(key=lambda p: p.stat().st_mtime, reverse=True)
    return wheels[0]


# ────────────────────────────────────────────────────────────────────────────────────────
def publish_to_pypi(
    wheel_path: Path,
    config: PyPIConfig,
    *,
    verbose: bool = False,
) -> PublishResult:
    """
    Publish a wheel file to PyPI using twine.

    Parameters:
        wheel_path: Path to the .whl file to upload.
        config: PyPI configuration (token and repository URL).
        verbose: If True, print detailed output.

    Returns:
        PublishResult indicating success or failure.
    """
    if not wheel_path.exists():
        return PublishResult(
            success=False,
            message=f"Wheel file not found: {wheel_path}",
        )

    if not wheel_path.suffix == ".whl":
        return PublishResult(
            success=False,
            message=f"Not a wheel file: {wheel_path}",
        )

    if not config.token:
        return PublishResult(
            success=False,
            message=(
                "PyPI token not configured. Set CAL_PUBLISH_PYPI_TOKEN or configure in"
                " JSON."
            ),
        )

    if verbose:
        print(f"Uploading {wheel_path.name} to {config.repository_url}")

    # Build twine command
    cmd = [
        sys.executable,
        "-m",
        "twine",
        "upload",
        "--repository-url",
        config.repository_url,
        "--username",
        "__token__",
        "--password",
        config.token,
        "--non-interactive",
        str(wheel_path),
    ]

    if verbose:
        cmd.append("--verbose")

    try:
        result = subprocess.run(
            cmd,
            capture_output=not verbose,
            text=True,
            check=False,
        )

        if result.returncode == 0:
            return PublishResult(
                success=True,
                message=f"Successfully uploaded {wheel_path.name}",
                wheel_path=wheel_path,
            )
        else:
            error_msg = result.stderr if result.stderr else "Unknown error"
            # Redact token from error messages
            error_msg = error_msg.replace(config.token, "[REDACTED]")
            return PublishResult(
                success=False,
                message=f"Failed to upload: {error_msg}",
                wheel_path=wheel_path,
            )

    except FileNotFoundError:
        return PublishResult(
            success=False,
            message="twine not found. Please install it with: pip install twine",
        )
    except Exception as e:
        return PublishResult(
            success=False,
            message=f"Unexpected error: {e}",
        )
