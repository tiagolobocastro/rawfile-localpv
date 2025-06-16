import os
import logging
import subprocess
from pathlib import Path
import sys

logger = logging.getLogger(__name__)


def root_dir():
    current_file_path = Path(__file__).resolve()
    return current_file_path.parents[3]


def env_cleanup():
    clean = os.getenv("CLEAN")
    if clean is not None and clean.lower() in ("no", "false", "f", "0"):
        return False
    return True


def fixture_cleanup():
    if hasattr(sys, "last_traceback"):
        return False
    return True


def run(
    command: str,
    args: list[str] = None,
    capture_output=True,
    log_run=True,
    **kwargs,
):
    command = [command]
    if args is not None:
        command.extend(args)

    if log_run:
        logger.info(f"Running '{command}'")
    else:
        logger.debug(f"Running '{command}'")
    try:
        result = subprocess.run(
            command, capture_output=capture_output, check=True, text=True, **kwargs
        )
        logger.debug(
            f"Command '{command}' completed with:\nStdErr Output: {result.stderr}\nStdOut Output: {result.stdout}"
        )
        return result.stdout.strip()

    except subprocess.CalledProcessError as e:
        logger.error(
            f"Command '{command}' failed with exit code {e.returncode}\nStdErr Output: {e.stderr}\nStdOut Output: {e.stdout}"
        )
        raise e

    except Exception as e:
        logger.error(f"An unexpected error occurred: {e}")
        raise e
