import subprocess
from .logs import logger
from typing import Any
from datetime import datetime


def run(cmd: str, executable: str | None = None, check=True, capture_output=True):
    start = datetime.now()
    kwargs: dict[str, Any] = {
        "check": check,
        "capture_output": capture_output,
        "shell": True,
    }
    log_ctx: dict[str, Any] = {
        "check": check,
        "capture_output": capture_output,
        "command": cmd,
        "start": start,
    }
    if executable is not None:
        kwargs["executable"] = executable
        log_ctx["executable"] = executable

    output = subprocess.run(cmd, **kwargs)
    end = datetime.now()
    log_ctx.update(
        {
            "returncode": output.returncode,
            "end": end,
            "latency": end - start,
        }
    )
    if capture_output:
        log_ctx.update(
            {
                "stderr": output.stderr.decode(),
                "stdout": output.stdout.decode(),
            }
        )
    logger.debug("Shell command execution", **log_ctx)
    return output
