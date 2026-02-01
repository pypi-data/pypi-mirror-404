"""HTTP transport for host-terminal-mcp.

Wraps the existing HostTerminalServer logic in a FastAPI app,
allowing external services (e.g. Annie's MCP server running in Docker)
to call host-terminal-mcp via HTTP instead of stdio.
"""

import json
from typing import Optional

from fastapi import FastAPI
from pydantic import BaseModel

from .config import Config, load_config
from .executor import CommandExecutor


class ExecuteRequest(BaseModel):
    """Request body for /execute endpoint."""

    command: str
    working_directory: Optional[str] = None


class CdRequest(BaseModel):
    """Request body for /cd endpoint."""

    path: str


def create_app(config: Config) -> FastAPI:
    """Create a FastAPI app that delegates to existing command execution logic.

    Args:
        config: The loaded host-terminal-mcp Config.

    Returns:
        A FastAPI application instance.
    """
    app = FastAPI(title="host-terminal-mcp", version="0.1.0")
    executor = CommandExecutor(config)

    @app.get("/health")
    async def health() -> dict:
        return {
            "status": "ok",
            "service": "host-terminal-mcp",
            "permission_mode": config.permission_mode.value,
        }

    @app.post("/execute")
    async def execute(req: ExecuteRequest) -> dict:
        command = req.command.strip()
        if not command:
            return {"status": "error", "error": "No command provided"}

        # Permission check (reuses existing config logic)
        is_allowed, reason = config.is_command_allowed(command)

        if reason == "NEEDS_APPROVAL":
            return {
                "status": "needs_approval",
                "command": command,
                "message": (
                    f"Command '{command}' is not in the allow list. "
                    "Approve it via the MCP stdio interface or add it to config."
                ),
            }

        if not is_allowed:
            return {
                "status": "error",
                "error": f"Command not allowed: {reason}",
            }

        result = await executor.execute(command, req.working_directory)

        return {
            "status": "success",
            "stdout": result.stdout,
            "stderr": result.stderr,
            "exit_code": result.return_code,
            "return_code": result.return_code,
            "timed_out": result.timed_out,
            "truncated": result.truncated,
            "working_directory": result.working_directory,
        }

    @app.post("/cd")
    async def change_directory(req: CdRequest) -> dict:
        path = req.path.strip()
        if not path:
            return {"status": "error", "error": "No path provided"}

        success, message = executor.change_directory(path)
        return {
            "status": "success" if success else "error",
            "message": message,
            "current_directory": executor.current_directory,
        }

    @app.get("/cwd")
    async def get_current_directory() -> dict:
        return {
            "status": "success",
            "current_directory": executor.current_directory,
        }

    @app.get("/permissions")
    async def get_permissions() -> dict:
        return {
            "status": "success",
            "permission_mode": config.permission_mode.value,
            "num_allowed_patterns": len(config.allowed_commands),
            "num_blocked_patterns": len(config.blocked_commands),
            "allowed_directories": config.allowed_directories,
            "timeout_seconds": config.timeout_seconds,
        }

    return app
