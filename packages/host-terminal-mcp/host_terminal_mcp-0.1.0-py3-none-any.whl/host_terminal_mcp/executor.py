"""Command execution with safety controls."""

import asyncio
import os
import shlex
from dataclasses import dataclass
from pathlib import Path
from typing import Optional

from .config import Config


@dataclass
class ExecutionResult:
    """Result of command execution."""

    command: str
    stdout: str
    stderr: str
    return_code: int
    timed_out: bool = False
    truncated: bool = False
    working_directory: str = ""


class CommandExecutor:
    """Execute commands with safety controls."""

    def __init__(self, config: Config):
        self.config = config
        self._current_directory = str(Path.home())

    @property
    def current_directory(self) -> str:
        """Get current working directory."""
        return self._current_directory

    def change_directory(self, path: str) -> tuple[bool, str]:
        """
        Change the current working directory.

        Returns:
            Tuple of (success, message)
        """
        # Expand user home directory
        expanded_path = os.path.expanduser(path)

        # Make absolute if relative
        if not os.path.isabs(expanded_path):
            expanded_path = os.path.join(self._current_directory, expanded_path)

        # Normalize the path
        normalized_path = os.path.normpath(expanded_path)

        # Check if path exists and is a directory
        if not os.path.exists(normalized_path):
            return False, f"Directory does not exist: {normalized_path}"

        if not os.path.isdir(normalized_path):
            return False, f"Not a directory: {normalized_path}"

        # Check if path is in allowed directories
        is_allowed = False
        for allowed_dir in self.config.allowed_directories:
            allowed_expanded = os.path.expanduser(allowed_dir)
            if normalized_path.startswith(os.path.normpath(allowed_expanded)):
                is_allowed = True
                break

        if not is_allowed:
            return False, f"Directory not in allowed paths: {normalized_path}"

        self._current_directory = normalized_path
        return True, f"Changed directory to: {normalized_path}"

    def _build_environment(self) -> dict[str, str]:
        """Build environment variables for command execution."""
        env = {}
        for var in self.config.environment_passthrough:
            if var in os.environ:
                env[var] = os.environ[var]
        return env

    async def execute(
        self,
        command: str,
        working_directory: Optional[str] = None,
    ) -> ExecutionResult:
        """
        Execute a command.

        Args:
            command: The command to execute
            working_directory: Optional working directory (uses current if not specified)

        Returns:
            ExecutionResult with stdout, stderr, return code, etc.
        """
        # Use provided directory or current directory
        cwd = working_directory or self._current_directory

        # Expand and normalize the working directory
        cwd = os.path.normpath(os.path.expanduser(cwd))

        # Verify working directory is allowed
        is_allowed = False
        for allowed_dir in self.config.allowed_directories:
            allowed_expanded = os.path.normpath(os.path.expanduser(allowed_dir))
            if cwd.startswith(allowed_expanded):
                is_allowed = True
                break

        if not is_allowed:
            return ExecutionResult(
                command=command,
                stdout="",
                stderr=f"Working directory not allowed: {cwd}",
                return_code=1,
                working_directory=cwd,
            )

        # Build environment
        env = self._build_environment()

        # Execute the command
        try:
            process = await asyncio.create_subprocess_shell(
                command,
                stdout=asyncio.subprocess.PIPE,
                stderr=asyncio.subprocess.PIPE,
                cwd=cwd,
                env=env,
                shell=True,
                executable=self.config.shell,
            )

            try:
                stdout_bytes, stderr_bytes = await asyncio.wait_for(
                    process.communicate(),
                    timeout=self.config.timeout_seconds,
                )
                timed_out = False
            except asyncio.TimeoutError:
                process.kill()
                await process.wait()
                return ExecutionResult(
                    command=command,
                    stdout="",
                    stderr=f"Command timed out after {self.config.timeout_seconds} seconds",
                    return_code=-1,
                    timed_out=True,
                    working_directory=cwd,
                )

            # Decode output
            stdout = stdout_bytes.decode("utf-8", errors="replace")
            stderr = stderr_bytes.decode("utf-8", errors="replace")

            # Truncate if too large
            truncated = False
            if len(stdout) > self.config.max_output_size:
                stdout = stdout[: self.config.max_output_size]
                stdout += f"\n\n[Output truncated at {self.config.max_output_size} characters]"
                truncated = True

            if len(stderr) > self.config.max_output_size:
                stderr = stderr[: self.config.max_output_size]
                stderr += f"\n\n[Output truncated at {self.config.max_output_size} characters]"
                truncated = True

            return ExecutionResult(
                command=command,
                stdout=stdout,
                stderr=stderr,
                return_code=process.returncode or 0,
                truncated=truncated,
                working_directory=cwd,
            )

        except Exception as e:
            return ExecutionResult(
                command=command,
                stdout="",
                stderr=f"Execution error: {str(e)}",
                return_code=1,
                working_directory=cwd,
            )
