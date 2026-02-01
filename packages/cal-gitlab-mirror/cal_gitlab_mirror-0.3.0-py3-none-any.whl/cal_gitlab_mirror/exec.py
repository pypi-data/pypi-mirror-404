# ----------------------------------------------------------------------------------------
#   exec
#   ----
#
#   Subprocess execution helpers with logging
#
#   License
#   -------
#   MIT License - Copyright 2026 Cyber Assessment Labs
#
#   Authors
#   -------
#   bena (via claude)
#
#   Version History
#   ---------------
#   Jan 2026 - Created
# ----------------------------------------------------------------------------------------

# ----------------------------------------------------------------------------------------
#   Imports
# ----------------------------------------------------------------------------------------

import logging
import re
import subprocess
from dataclasses import dataclass

# ----------------------------------------------------------------------------------------
#   Types
# ----------------------------------------------------------------------------------------


@dataclass
class ExecResult:
    """Result of a subprocess execution."""

    returncode: int
    stdout: str
    stderr: str

    @property
    def success(self) -> bool:
        return self.returncode == 0


# ----------------------------------------------------------------------------------------
#   Functions
# ----------------------------------------------------------------------------------------


# ----------------------------------------------------------------------------------------
_URL_AUTH_RE = re.compile(r"(://[^:/@]+:)([^@/]+)(@)")
_GITLAB_PAT_RE = re.compile(r"(glpat-)[0-9A-Za-z_-]{6,}")


def redact_secrets(text: str) -> str:
    """Redact common credentials patterns from text intended for logs."""
    text = _URL_AUTH_RE.sub(r"\1***\3", text)
    text = _GITLAB_PAT_RE.sub(r"\1***", text)
    return text


# ----------------------------------------------------------------------------------------
def run_command(
    args: list[str],
    *,
    cwd: str | None = None,
    env: dict[str, str] | None = None,
    capture_output: bool = True,
) -> ExecResult:
    """
    Execute a command and return the result.

    Parameters:
        args: Command and arguments to execute
        cwd: Working directory for the command
        env: Environment variables (added to current env)
        capture_output: Whether to capture stdout/stderr

    Returns:
        ExecResult with returncode, stdout, and stderr
    """
    logging.debug("Running: %s", " ".join(redact_secrets(a) for a in args))

    try:
        result = subprocess.run(
            args,
            cwd=cwd,
            env=env,
            capture_output=capture_output,
            text=True,
        )
        return ExecResult(
            returncode=result.returncode,
            stdout=result.stdout if capture_output else "",
            stderr=result.stderr if capture_output else "",
        )
    except FileNotFoundError as e:
        logging.error(f"Command not found: {args[0]}")
        return ExecResult(returncode=-1, stdout="", stderr=str(e))
    except Exception as e:
        logging.error(f"Command failed: {e}")
        return ExecResult(returncode=-1, stdout="", stderr=str(e))
