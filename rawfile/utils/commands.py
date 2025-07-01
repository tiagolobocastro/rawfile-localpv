import subprocess
from typing import Any


def run(cmd: str, executable: str | None = None, check=True, capture_output=True):
    kwargs: dict[str, Any] = {
        "check": check,
        "capture_output": capture_output,
        "shell": True,
    }
    if executable is not None:
        kwargs["executable"] = executable

    return subprocess.run(cmd, **kwargs)
