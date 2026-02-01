# ────────────────────────────────────────────────────────────────────────────────────────
#   cli.py
#   ──────
#
#   Command-line interface for cal-publish-python.
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
import sys
import traceback
from pathlib import Path
from .argbuilder import ArgsParser
from .argbuilder import Namespace
from .config import Config
from .config import load_config
from .publish_docs import publish_docs
from .publish_pypi import find_wheel
from .publish_pypi import publish_to_pypi
from .version import VERSION_STR

# ────────────────────────────────────────────────────────────────────────────────────────
#   Constants
# ────────────────────────────────────────────────────────────────────────────────────────

CONFIG_ENV_VAR = "CAL_PUBLISH_CONFIG"
DEFAULT_CONFIG_PATH = Path.home() / ".config" / "cal-publish-python" / "config.json"

# ────────────────────────────────────────────────────────────────────────────────────────
#   Argument Parsing
# ────────────────────────────────────────────────────────────────────────────────────────


# ────────────────────────────────────────────────────────────────────────────────────────
def create_parser() -> ArgsParser:
    """Create the argument parser."""
    epilog = """\
Environment Variables:
  CAL_PUBLISH_CONFIG           Path to configuration file

  PyPI:
    CAL_PUBLISH_PYPI_TOKEN           PyPI API token
    CAL_PUBLISH_PYPI_REPOSITORY_URL  PyPI repository URL

  GitLab Pages:
    CAL_PUBLISH_GITLAB_TOKEN   GitLab personal access token
    CAL_PUBLISH_GITLAB_URL     GitLab instance URL
    CAL_PUBLISH_GITLAB_GROUP   GitLab group path

  SSH:
    CAL_PUBLISH_SSH_HOST       Remote server hostname
    CAL_PUBLISH_SSH_USER       SSH username
    CAL_PUBLISH_SSH_PORT       SSH port
    CAL_PUBLISH_SSH_BASE_PATH  Base directory on remote server
    CAL_PUBLISH_SSH_KEY        Path to SSH private key

Configuration File Format (JSON):
  {
      "pypi": {
          "token": "pypi-xxxxxxxxxxxx",
          "repository_url": "https://upload.pypi.org/legacy/"
      },
      "docs": {
          "mode": "gitlab-pages",
          "gitlab_pages": {
              "token": "glpat-xxxxxxxxxxxx",
              "url": "https://gitlab.com",
              "group": "mygroup/public/docs"
          }
      }
  }

Configuration File Location (in order of priority):
  1. --config FILE
  2. $CAL_PUBLISH_CONFIG
  3. ~/.config/cal-publish-python/config.json

Documentation Zip Filename Format:
  project-name-VERSION-docs.zip
  Examples: myproject-1.0.0-docs.zip, my-lib-2.3.4.post5+gabcdef-docs.zip
"""

    parser = ArgsParser(
        prog="cal-publish-python",
        description=(
            "Publish Python packages and documentation with external configuration.\n\n"
            "By default, publishes both PyPI package and documentation based on what\n"
            "is configured. Use --pypi-only or --docs-only to limit."
        ),
        epilog=epilog,
        version=f"cal-publish-python {VERSION_STR}",
    )

    # Required positional argument(s)
    parser.add_argument(
        "artifacts",
        metavar="ARTIFACT",
        nargs="+",
        help="Directory or file(s) to publish (.whl and/or docs .zip)",
    )

    # Config options
    parser.add_argument(
        "-c",
        "--config",
        metavar="FILE",
        help=(
            "Path to JSON configuration file "
            f"(default: ${CONFIG_ENV_VAR} or {DEFAULT_CONFIG_PATH})"
        ),
    )

    # What to publish
    mode_group = parser.add_mutex_group()
    mode_group.add_argument(
        "--pypi-only",
        action="store_true",
        help="Only publish to PyPI (skip documentation)",
    )
    mode_group.add_argument(
        "--docs-only",
        action="store_true",
        help="Only publish documentation (skip PyPI)",
    )

    # Documentation options
    docs_group = parser.add_group("Documentation Options")
    docs_group.add_argument(
        "-l",
        "--set-latest",
        action="store_true",
        help="Also set this version as 'latest' (GitLab Pages mode only)",
    )
    docs_group.add_argument(
        "-f",
        "--force",
        action="store_true",
        help="Overwrite existing documentation version if it exists",
    )

    # General options
    parser.add_argument(
        "-v",
        "--verbose",
        action="store_true",
        help="Verbose output",
    )

    return parser


# ────────────────────────────────────────────────────────────────────────────────────────
#   Main Entry Point
# ────────────────────────────────────────────────────────────────────────────────────────


# ────────────────────────────────────────────────────────────────────────────────────────
def main(argv: list[str] | None = None) -> int:
    """
    Main entry point for cal-publish-python CLI.

    Parameters:
        argv: Command line arguments (without program name). If None, uses sys.argv[1:].

    Returns:
        Exit code (0 for success, non-zero for error)
    """
    if argv is None:
        argv = sys.argv[1:]

    try:
        return _main_inner(argv)
    except KeyboardInterrupt:
        print()
        print("---- Manually Terminated ----")
        print()
        return 1
    except SystemExit as e:
        if isinstance(e.code, int):
            return e.code
        return 1
    except BaseException as e:
        t = "-----------------------------------------------------------------------------\n"
        t += "UNHANDLED EXCEPTION OCCURRED!!\n"
        t += "\n"
        t += traceback.format_exc()
        t += "\n"
        t += f"EXCEPTION: {type(e)} {e}\n"
        t += "-----------------------------------------------------------------------------\n"
        t += "\n"
        print(t, file=sys.stderr)
        return 1


# ────────────────────────────────────────────────────────────────────────────────────────
def _resolve_config_path(cli_arg: str | None) -> Path:
    """
    Resolve the configuration file path.

    Priority:
    1. Command-line argument (--config)
    2. Environment variable (CAL_PUBLISH_CONFIG)
    3. Default path (~/.config/cal-publish-python/config.json)
    """
    if cli_arg is not None:
        return Path(cli_arg)

    env_path = os.environ.get(CONFIG_ENV_VAR)
    if env_path:
        return Path(env_path)

    return DEFAULT_CONFIG_PATH


# ────────────────────────────────────────────────────────────────────────────────────────
def _print_config_not_found_error(config_path: Path, cli_arg: str | None) -> None:
    """Print a helpful error message when config file is not found."""
    # Use ~ for home directory in display
    display_path = str(config_path).replace(str(Path.home()), "~")
    default_display = str(DEFAULT_CONFIG_PATH).replace(str(Path.home()), "~")

    print("Error: No configuration file found.", file=sys.stderr)
    print(file=sys.stderr)
    print("Checked:", file=sys.stderr)
    print(f"  {display_path}", file=sys.stderr)
    print(file=sys.stderr)
    if cli_arg is not None:
        print("The specified path does not exist.", file=sys.stderr)
    else:
        print("To fix, do one of the following:", file=sys.stderr)
        print("  - Use --config to specify a config file", file=sys.stderr)
        print(
            f"  - Set {CONFIG_ENV_VAR} to the path of a config file",
            file=sys.stderr,
        )
        print(f"  - Create a config file at {default_display}", file=sys.stderr)


# ────────────────────────────────────────────────────────────────────────────────────────
def _main_inner(argv: list[str]) -> int:
    """Inner main function that does the actual work."""
    parser = create_parser()
    args: Namespace = parser.parse(argv)

    verbose: bool = getattr(args, "verbose", False)

    # Resolve configuration path
    cli_config_arg = getattr(args, "config", None)
    config_path = _resolve_config_path(cli_config_arg)

    # Load configuration
    try:
        config = load_config(config_path, verbose=verbose)
    except FileNotFoundError:
        _print_config_not_found_error(config_path, cli_config_arg)
        return 2
    except Exception as e:
        print(f"Error loading configuration: {e}", file=sys.stderr)
        return 1

    # Determine what to publish
    pypi_only: bool = getattr(args, "pypi_only", False)
    docs_only: bool = getattr(args, "docs_only", False)

    # Check what's configured
    has_pypi_config = config.pypi.token is not None
    has_docs_config = (
        config.docs.mode == "gitlab-pages"
        and config.docs.gitlab_pages.token is not None
    ) or (config.docs.mode == "ssh" and config.docs.ssh.host is not None)

    do_pypi = not docs_only and has_pypi_config
    do_docs = not pypi_only and has_docs_config

    if not do_pypi and not do_docs:
        if pypi_only and not has_pypi_config:
            print(
                "Error: --pypi-only specified but PyPI is not configured",
                file=sys.stderr,
            )
        elif docs_only and not has_docs_config:
            print(
                "Error: --docs-only specified but docs are not configured",
                file=sys.stderr,
            )
        else:
            print(
                "Error: Nothing to publish - configure PyPI or docs in config file",
                file=sys.stderr,
            )
        return 1

    # Parse artifacts to find wheel and docs zip
    wheel_path, docs_zip = _find_artifacts(args.artifacts, do_pypi, do_docs)

    if do_pypi and wheel_path is None:
        print("Error: No .whl file found in artifacts", file=sys.stderr)
        return 1

    if do_docs and docs_zip is None:
        print("Error: No docs .zip file found in artifacts", file=sys.stderr)
        return 1

    pypi_success = True
    docs_success = True

    # Publish to PyPI
    if do_pypi and wheel_path is not None:
        pypi_success = _publish_pypi(wheel_path, config, verbose=verbose)

    # Publish documentation
    if do_docs and docs_zip is not None:
        set_latest: bool = getattr(args, "set_latest", False)
        force: bool = getattr(args, "force", False)
        docs_success = _publish_docs_file(
            docs_zip, config, set_latest=set_latest, force=force, verbose=verbose
        )

    if pypi_success and docs_success:
        return 0
    else:
        return 1


# ────────────────────────────────────────────────────────────────────────────────────────
def _find_artifacts(
    paths: list[str], need_wheel: bool, need_docs: bool
) -> tuple[Path | None, Path | None]:
    """
    Find wheel and docs zip from the provided paths.

    If a single directory is provided, search within it.
    If files are provided, use them directly.

    Returns:
        Tuple of (wheel_path, docs_zip_path), either may be None.
    """
    wheel_path: Path | None = None
    docs_zip: Path | None = None

    for path_str in paths:
        path = Path(path_str)
        if not path.exists():
            print(f"Warning: Path not found: {path}", file=sys.stderr)
            continue

        if path.is_dir():
            # Search directory for artifacts
            if need_wheel and wheel_path is None:
                wheel_path = find_wheel(path)
            if need_docs and docs_zip is None:
                docs_zip = _find_docs_zip(path)
        else:
            # Direct file
            if path.suffix == ".whl":
                wheel_path = path
            elif path.suffix == ".zip":
                docs_zip = path

    return wheel_path, docs_zip


# ────────────────────────────────────────────────────────────────────────────────────────
def _find_docs_zip(directory: Path) -> Path | None:
    """Find docs zip file in directory."""
    zip_files = list(directory.glob("*-docs.zip"))
    if not zip_files:
        zip_files = list(directory.glob("*.zip"))
    if not zip_files:
        return None
    # Use most recent
    zip_files.sort(key=lambda p: p.stat().st_mtime, reverse=True)
    return zip_files[0]


# ────────────────────────────────────────────────────────────────────────────────────────
#   Publishing Functions
# ────────────────────────────────────────────────────────────────────────────────────────


# ────────────────────────────────────────────────────────────────────────────────────────
def _publish_pypi(wheel_path: Path, config: Config, *, verbose: bool = False) -> bool:
    """Publish wheel to PyPI. Returns True on success."""
    print(f"Publishing to PyPI: {wheel_path.name}")
    if verbose:
        print(f"  Repository: {config.pypi.repository_url}")

    result = publish_to_pypi(wheel_path, config.pypi, verbose=verbose)

    if result.success:
        print(f"  {result.message}")
        return True
    else:
        print(f"  Error: {result.message}", file=sys.stderr)
        return False


# ────────────────────────────────────────────────────────────────────────────────────────
def _publish_docs_file(
    docs_zip: Path,
    config: Config,
    *,
    set_latest: bool = False,
    force: bool = False,
    verbose: bool = False,
) -> bool:
    """Publish documentation. Returns True on success."""
    # Extract project name and version from filename
    # Expected format: project-name-1.2.3-docs.zip or project-name-1.2.3.zip
    project_name, doc_version = _parse_docs_filename(docs_zip.name)
    if project_name is None or doc_version is None:
        print(
            f"Error: Could not parse project/version from: {docs_zip.name}",
            file=sys.stderr,
        )
        print("  Expected format: project-name-VERSION-docs.zip", file=sys.stderr)
        return False

    print(f"Publishing documentation: {docs_zip.name}")
    print(f"  Project: {project_name}")
    print(f"  Version: {doc_version}")
    if verbose:
        print(f"  Mode: {config.docs.mode}")

    result = publish_docs(
        docs_path=docs_zip,
        project_name=project_name,
        version=doc_version,
        config=config.docs,
        set_latest=set_latest,
        force=force,
        verbose=verbose,
    )

    if result.success:
        print(f"  {result.message}")
        if result.url:
            print(f"  URL: {result.url}")
        return True
    else:
        print(f"  Error: {result.message}", file=sys.stderr)
        return False


# ────────────────────────────────────────────────────────────────────────────────────────
def _parse_docs_filename(filename: str) -> tuple[str | None, str | None]:
    """
    Parse project name and version from docs zip filename.

    Expected formats:
    - project-name-1.2.3-docs.zip
    - project-name-1.2.3.zip
    - project_name-1.2.3-docs.zip

    Returns:
        Tuple of (project_name, version) or (None, None) if parsing fails.
    """
    # Remove .zip extension
    if filename.endswith(".zip"):
        filename = filename[:-4]

    # Remove -docs suffix if present
    if filename.endswith("-docs"):
        filename = filename[:-5]

    # Find the version part (starts with a digit or 'v')
    # Split on '-' and find where version starts
    parts = filename.split("-")
    if len(parts) < 2:
        return None, None

    # Find the first part that looks like a version
    version_idx = None
    for i, part in enumerate(parts):
        if part and (part[0].isdigit() or (part[0] == "v" and len(part) > 1)):
            version_idx = i
            break

    if version_idx is None or version_idx == 0:
        return None, None

    project_name = "-".join(parts[:version_idx])
    version = "-".join(parts[version_idx:])

    return project_name, version
