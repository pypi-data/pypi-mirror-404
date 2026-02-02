import subprocess
from typing import NamedTuple


class CommandResult(NamedTuple):
    """Result of a shell command execution."""

    success: bool
    stdout: str
    stderr: str


def _run_command_with_output(command: str, timeout: int = 300) -> CommandResult:
    """
    Internal helper function to run shell commands and capture output.

    Args:
        command: The shell command to execute
        timeout: Command timeout in seconds (default: 300)

    Returns:
        CommandResult with success status, stdout, and stderr
    """
    try:
        result = subprocess.run(
            command,
            shell=True,
            capture_output=True,
            text=True,
            timeout=timeout,
            check=False,
        )
        return CommandResult(
            success=result.returncode == 0, stdout=result.stdout, stderr=result.stderr
        )
    except subprocess.TimeoutExpired:
        return CommandResult(
            success=False,
            stdout="",
            stderr=f"Command timed out after {timeout} seconds",
        )
    except Exception as e:
        return CommandResult(success=False, stdout="", stderr=str(e))


def install_linux_package(package_name: str) -> CommandResult:
    """
    Install a Linux package using apt package manager.

    Args:
        package_name: Name of the package to install

    Returns:
        CommandResult with success status, stdout, and stderr
    """

    if not package_name or not package_name.strip():
        return CommandResult(
            success=False, stdout="", stderr="Package name cannot be empty"
        )
    package_name = package_name.strip()
    return _run_command_with_output(f"apt-get install -y {package_name}", timeout=600)


def run_bash_command(command: str, timeout: int = 300) -> CommandResult:
    """
    Execute a bash command and return the result.

    Args:
        command: The bash command to execute
        timeout: Command timeout in seconds (default: 300)

    Returns:
        CommandResult with success status, stdout, and stderr
    """
    if not command or not command.strip():
        return CommandResult(success=False, stdout="", stderr="Command cannot be empty")

    command = command.strip()
    return _run_command_with_output(command, timeout=timeout)
