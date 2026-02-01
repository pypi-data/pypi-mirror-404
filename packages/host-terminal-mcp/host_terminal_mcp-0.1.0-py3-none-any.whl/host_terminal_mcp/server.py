"""MCP Server for host terminal access."""

import argparse
import asyncio
import json
import logging
import sys
from pathlib import Path
from typing import Any, Optional

from mcp.server import Server
from mcp.server.stdio import stdio_server
from mcp.types import (
    CallToolResult,
    TextContent,
    Tool,
)

from .config import (
    Config,
    PermissionMode,
    create_default_config_file,
    get_default_config_path,
    load_config,
    save_config,
)
from .executor import CommandExecutor

# Set up logging
logging.basicConfig(level=logging.INFO, stream=sys.stderr)
logger = logging.getLogger("host-terminal-mcp")


class HostTerminalServer:
    """MCP Server for executing terminal commands on the host machine."""

    def __init__(self, config: Config):
        self.config = config
        self.executor = CommandExecutor(config)
        self.server = Server("host-terminal-mcp")
        self._pending_approvals: dict[str, asyncio.Event] = {}
        self._approval_results: dict[str, bool] = {}

        # Register handlers
        self._setup_handlers()

    def _setup_handlers(self):
        """Set up MCP request handlers."""

        @self.server.list_tools()
        async def list_tools() -> list[Tool]:
            """List available tools."""
            return [
                Tool(
                    name="execute_command",
                    description=(
                        "Execute a terminal command on the host machine. "
                        "Commands are subject to permission controls based on configuration. "
                        "Read-only commands like ls, cat, git status are generally allowed by default. "
                        "Use 'cd' as a separate command or specify working_directory parameter."
                    ),
                    inputSchema={
                        "type": "object",
                        "properties": {
                            "command": {
                                "type": "string",
                                "description": "The command to execute",
                            },
                            "working_directory": {
                                "type": "string",
                                "description": "Optional working directory for the command (defaults to current directory)",
                            },
                        },
                        "required": ["command"],
                    },
                ),
                Tool(
                    name="change_directory",
                    description="Change the current working directory for subsequent commands.",
                    inputSchema={
                        "type": "object",
                        "properties": {
                            "path": {
                                "type": "string",
                                "description": "The directory path to change to (absolute or relative)",
                            },
                        },
                        "required": ["path"],
                    },
                ),
                Tool(
                    name="get_current_directory",
                    description="Get the current working directory.",
                    inputSchema={
                        "type": "object",
                        "properties": {},
                    },
                ),
                Tool(
                    name="approve_command",
                    description=(
                        "Approve a command that requires permission. "
                        "This is used when permission_mode is 'ask' and a command is not in the allow list. "
                        "The command will be approved for this session only."
                    ),
                    inputSchema={
                        "type": "object",
                        "properties": {
                            "command": {
                                "type": "string",
                                "description": "The exact command to approve",
                            },
                            "approve": {
                                "type": "boolean",
                                "description": "Whether to approve (true) or deny (false) the command",
                            },
                        },
                        "required": ["command", "approve"],
                    },
                ),
                Tool(
                    name="get_permission_status",
                    description="Get information about the current permission mode and allowed commands.",
                    inputSchema={
                        "type": "object",
                        "properties": {
                            "show_all_allowed": {
                                "type": "boolean",
                                "description": "Whether to show all allowed command patterns (default: false for brevity)",
                                "default": False,
                            },
                        },
                    },
                ),
                Tool(
                    name="set_permission_mode",
                    description=(
                        "Change the permission mode. Modes: "
                        "'allowlist' (only allow listed commands), "
                        "'ask' (prompt for unlisted commands), "
                        "'allow_all' (allow all commands - use with caution!)"
                    ),
                    inputSchema={
                        "type": "object",
                        "properties": {
                            "mode": {
                                "type": "string",
                                "enum": ["allowlist", "ask", "allow_all"],
                                "description": "The permission mode to set",
                            },
                            "persist": {
                                "type": "boolean",
                                "description": "Whether to save this mode to config file (default: false, session only)",
                                "default": False,
                            },
                        },
                        "required": ["mode"],
                    },
                ),
            ]

        @self.server.call_tool()
        async def call_tool(name: str, arguments: dict[str, Any]) -> CallToolResult:
            """Handle tool calls."""
            try:
                if name == "execute_command":
                    return await self._handle_execute_command(arguments)
                elif name == "change_directory":
                    return await self._handle_change_directory(arguments)
                elif name == "get_current_directory":
                    return await self._handle_get_current_directory()
                elif name == "approve_command":
                    return await self._handle_approve_command(arguments)
                elif name == "get_permission_status":
                    return await self._handle_get_permission_status(arguments)
                elif name == "set_permission_mode":
                    return await self._handle_set_permission_mode(arguments)
                else:
                    return CallToolResult(
                        content=[TextContent(type="text", text=f"Unknown tool: {name}")],
                        isError=True,
                    )
            except Exception as e:
                logger.exception(f"Error handling tool {name}")
                return CallToolResult(
                    content=[TextContent(type="text", text=f"Error: {str(e)}")],
                    isError=True,
                )

    async def _handle_execute_command(self, arguments: dict[str, Any]) -> CallToolResult:
        """Handle execute_command tool call."""
        command = arguments.get("command", "").strip()
        working_directory = arguments.get("working_directory")

        if not command:
            return CallToolResult(
                content=[TextContent(type="text", text="Error: No command provided")],
                isError=True,
            )

        # Check if command is allowed
        is_allowed, reason = self.config.is_command_allowed(command)

        if reason == "NEEDS_APPROVAL":
            # In ask mode, return a message indicating approval is needed
            return CallToolResult(
                content=[
                    TextContent(
                        type="text",
                        text=json.dumps({
                            "status": "needs_approval",
                            "command": command,
                            "message": (
                                f"Command '{command}' is not in the allow list. "
                                "Use the 'approve_command' tool to approve or deny this command, "
                                "or change the permission mode."
                            ),
                        }, indent=2),
                    )
                ],
            )

        if not is_allowed:
            return CallToolResult(
                content=[
                    TextContent(
                        type="text",
                        text=f"Command not allowed: {reason}\n\n"
                        f"To allow this command:\n"
                        f"1. Use 'set_permission_mode' to change to 'ask' mode and then approve it\n"
                        f"2. Or add the command pattern to your config file",
                    )
                ],
                isError=True,
            )

        # Execute the command
        result = await self.executor.execute(command, working_directory)

        # Format the response
        response_parts = []

        if result.timed_out:
            response_parts.append(f"⏱️ Command timed out after {self.config.timeout_seconds}s")

        if result.stdout:
            response_parts.append(f"stdout:\n{result.stdout}")

        if result.stderr:
            response_parts.append(f"stderr:\n{result.stderr}")

        if result.truncated:
            response_parts.append("⚠️ Output was truncated")

        response_parts.append(f"\nExit code: {result.return_code}")
        response_parts.append(f"Working directory: {result.working_directory}")

        return CallToolResult(
            content=[TextContent(type="text", text="\n".join(response_parts))],
            isError=result.return_code != 0,
        )

    async def _handle_change_directory(self, arguments: dict[str, Any]) -> CallToolResult:
        """Handle change_directory tool call."""
        path = arguments.get("path", "").strip()

        if not path:
            return CallToolResult(
                content=[TextContent(type="text", text="Error: No path provided")],
                isError=True,
            )

        success, message = self.executor.change_directory(path)

        return CallToolResult(
            content=[TextContent(type="text", text=message)],
            isError=not success,
        )

    async def _handle_get_current_directory(self) -> CallToolResult:
        """Handle get_current_directory tool call."""
        return CallToolResult(
            content=[
                TextContent(
                    type="text",
                    text=f"Current directory: {self.executor.current_directory}",
                )
            ],
        )

    async def _handle_approve_command(self, arguments: dict[str, Any]) -> CallToolResult:
        """Handle approve_command tool call."""
        command = arguments.get("command", "").strip()
        approve = arguments.get("approve", False)

        if not command:
            return CallToolResult(
                content=[TextContent(type="text", text="Error: No command provided")],
                isError=True,
            )

        if approve:
            self.config.approve_command_for_session(command)
            return CallToolResult(
                content=[
                    TextContent(
                        type="text",
                        text=f"✅ Command approved for this session: {command}\n"
                        "You can now execute it with execute_command.",
                    )
                ],
            )
        else:
            return CallToolResult(
                content=[
                    TextContent(
                        type="text",
                        text=f"❌ Command denied: {command}",
                    )
                ],
            )

    async def _handle_get_permission_status(self, arguments: dict[str, Any]) -> CallToolResult:
        """Handle get_permission_status tool call."""
        show_all = arguments.get("show_all_allowed", False)

        status = {
            "permission_mode": self.config.permission_mode.value,
            "allowed_directories": self.config.allowed_directories,
            "timeout_seconds": self.config.timeout_seconds,
            "session_approved_commands": self.config.session_approved_commands,
            "num_allowed_patterns": len(self.config.allowed_commands),
            "num_blocked_patterns": len(self.config.blocked_commands),
        }

        if show_all:
            status["allowed_commands"] = [
                {"pattern": cmd.pattern, "description": cmd.description, "is_regex": cmd.is_regex}
                for cmd in self.config.allowed_commands
            ]
            status["blocked_commands"] = [
                {"pattern": cmd.pattern, "description": cmd.description, "is_regex": cmd.is_regex}
                for cmd in self.config.blocked_commands
            ]

        return CallToolResult(
            content=[TextContent(type="text", text=json.dumps(status, indent=2))],
        )

    async def _handle_set_permission_mode(self, arguments: dict[str, Any]) -> CallToolResult:
        """Handle set_permission_mode tool call."""
        mode_str = arguments.get("mode", "").strip()
        persist = arguments.get("persist", False)

        try:
            mode = PermissionMode(mode_str)
        except ValueError:
            return CallToolResult(
                content=[
                    TextContent(
                        type="text",
                        text=f"Invalid mode: {mode_str}. Valid modes: allowlist, ask, allow_all",
                    )
                ],
                isError=True,
            )

        old_mode = self.config.permission_mode
        self.config.permission_mode = mode

        message = f"Permission mode changed: {old_mode.value} → {mode.value}"

        if mode == PermissionMode.ALLOW_ALL:
            message += "\n\n⚠️ WARNING: All commands are now allowed. Use with extreme caution!"

        if persist:
            save_config(self.config)
            message += "\n\n💾 Mode saved to config file."
        else:
            message += "\n\n(Change is for this session only. Use persist=true to save.)"

        return CallToolResult(
            content=[TextContent(type="text", text=message)],
        )

    async def run(self):
        """Run the MCP server."""
        async with stdio_server() as (read_stream, write_stream):
            await self.server.run(
                read_stream,
                write_stream,
                self.server.create_initialization_options(),
            )


def main():
    """Main entry point."""
    parser = argparse.ArgumentParser(
        description="Host Terminal MCP Server - Execute terminal commands with configurable permissions"
    )
    parser.add_argument(
        "--config",
        "-c",
        type=Path,
        default=None,
        help="Path to configuration file (default: ~/.config/host-terminal-mcp/config.yaml)",
    )
    parser.add_argument(
        "--init-config",
        action="store_true",
        help="Create a default configuration file and exit",
    )
    parser.add_argument(
        "--mode",
        choices=["allowlist", "ask", "allow_all"],
        default=None,
        help="Override permission mode for this session",
    )
    parser.add_argument(
        "--allow-dir",
        action="append",
        dest="allowed_dirs",
        help="Add allowed directory (can be specified multiple times)",
    )

    args = parser.parse_args()

    # Handle init-config
    if args.init_config:
        config_path = create_default_config_file(args.config)
        print(f"Created default configuration at: {config_path}", file=sys.stderr)
        sys.exit(0)

    # Load configuration
    config = load_config(args.config)

    # Apply command-line overrides
    if args.mode:
        config.permission_mode = PermissionMode(args.mode)
        logger.info(f"Permission mode overridden to: {args.mode}")

    if args.allowed_dirs:
        config.allowed_directories.extend(args.allowed_dirs)
        logger.info(f"Added allowed directories: {args.allowed_dirs}")

    # Create and run server
    server = HostTerminalServer(config)
    logger.info("Starting Host Terminal MCP Server")
    logger.info(f"Permission mode: {config.permission_mode.value}")
    logger.info(f"Allowed directories: {config.allowed_directories}")

    asyncio.run(server.run())


if __name__ == "__main__":
    main()
