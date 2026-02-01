"""Configuration management for Host Terminal MCP."""

import os
import re
from enum import Enum
from pathlib import Path
from typing import Optional

import yaml
from pydantic import BaseModel, Field


class PermissionMode(str, Enum):
    """Permission modes for command execution."""

    ALLOWLIST = "allowlist"  # Only allow commands in the allow list
    ASK = "ask"  # Ask for permission if command not in allow list
    ALLOW_ALL = "allow_all"  # Allow all commands (dangerous!)


class CommandPattern(BaseModel):
    """A pattern for matching commands."""

    pattern: str = Field(description="Regex pattern or exact command prefix")
    description: str = Field(default="", description="Human-readable description")
    is_regex: bool = Field(default=False, description="Whether pattern is a regex")

    def matches(self, command: str) -> bool:
        """Check if a command matches this pattern."""
        if self.is_regex:
            try:
                return bool(re.match(self.pattern, command))
            except re.error:
                return False
        else:
            if command == self.pattern:
                return True
            # Patterns ending with whitespace (e.g. "echo ", "sudo ") already
            # encode the word boundary, so plain startswith is correct.
            if self.pattern.endswith((" ", "\t")):
                return command.startswith(self.pattern)
            # Otherwise require a separator after the match so that
            # "ls" matches "ls -la" but not "lsof".
            return command.startswith(self.pattern + " ") or command.startswith(self.pattern + "\t")


class Config(BaseModel):
    """Configuration for Host Terminal MCP."""

    permission_mode: PermissionMode = Field(
        default=PermissionMode.ALLOWLIST,
        description="How to handle commands not in the allow list"
    )

    allowed_commands: list[CommandPattern] = Field(
        default_factory=list,
        description="List of allowed command patterns"
    )

    blocked_commands: list[CommandPattern] = Field(
        default_factory=list,
        description="List of blocked command patterns (takes precedence over allowed)"
    )

    allowed_directories: list[str] = Field(
        default_factory=lambda: [str(Path.home())],
        description="Directories where commands can be executed"
    )

    timeout_seconds: int = Field(
        default=300,
        description="Maximum execution time for commands (seconds)"
    )

    max_output_size: int = Field(
        default=100000,
        description="Maximum output size in characters"
    )

    shell: str = Field(
        default="/bin/bash",
        description="Shell to use for command execution"
    )

    environment_passthrough: list[str] = Field(
        default_factory=lambda: ["PATH", "HOME", "USER", "LANG", "LC_ALL"],
        description="Environment variables to pass through to commands"
    )

    # Commands that have been dynamically approved during the session
    session_approved_commands: list[str] = Field(
        default_factory=list,
        description="Commands approved during this session (not persisted)"
    )

    def is_command_allowed(self, command: str) -> tuple[bool, str]:
        """
        Check if a command is allowed.

        Returns:
            Tuple of (is_allowed, reason)
        """
        # First check blocked commands - they always take precedence
        for blocked in self.blocked_commands:
            if blocked.matches(command):
                return False, f"Command matches blocked pattern: {blocked.description or blocked.pattern}"

        # Check if in allowed commands
        for allowed in self.allowed_commands:
            if allowed.matches(command):
                return True, f"Command matches allowed pattern: {allowed.description or allowed.pattern}"

        # Check session-approved commands
        if command in self.session_approved_commands:
            return True, "Command was approved during this session"

        # Handle based on permission mode
        if self.permission_mode == PermissionMode.ALLOW_ALL:
            return True, "allow_all mode is enabled"
        elif self.permission_mode == PermissionMode.ASK:
            return False, "NEEDS_APPROVAL"
        else:  # ALLOWLIST
            return False, "Command not in allow list"

    def approve_command_for_session(self, command: str) -> None:
        """Approve a command for the current session."""
        if command not in self.session_approved_commands:
            self.session_approved_commands.append(command)


def get_default_config_path() -> Path:
    """Get the default configuration file path."""
    # Check XDG config directory first
    xdg_config = os.environ.get("XDG_CONFIG_HOME")
    if xdg_config:
        config_dir = Path(xdg_config) / "host-terminal-mcp"
    else:
        config_dir = Path.home() / ".config" / "host-terminal-mcp"

    return config_dir / "config.yaml"


def get_default_allowed_commands() -> list[CommandPattern]:
    """Get the default list of allowed developer commands."""
    return [
        # File listing and navigation
        CommandPattern(pattern="ls", description="List directory contents"),
        CommandPattern(pattern="ll", description="List directory contents (long format alias)"),
        CommandPattern(pattern="la", description="List all files including hidden"),
        CommandPattern(pattern="pwd", description="Print working directory"),
        CommandPattern(pattern="tree", description="Display directory tree"),
        CommandPattern(pattern="find ", description="Find files", is_regex=False),
        CommandPattern(pattern="locate ", description="Locate files"),
        CommandPattern(pattern="which ", description="Locate a command"),
        CommandPattern(pattern="whereis ", description="Locate binary, source, and manual"),
        CommandPattern(pattern="file ", description="Determine file type"),

        # File content viewing
        CommandPattern(pattern="cat ", description="Display file contents"),
        CommandPattern(pattern="head ", description="Display first lines of file"),
        CommandPattern(pattern="tail ", description="Display last lines of file"),
        CommandPattern(pattern="less ", description="View file with pagination"),
        CommandPattern(pattern="more ", description="View file with pagination"),
        CommandPattern(pattern="bat ", description="Cat with syntax highlighting"),
        CommandPattern(pattern="wc ", description="Word, line, character count"),

        # Search and grep
        CommandPattern(pattern="grep ", description="Search text patterns"),
        CommandPattern(pattern="rg ", description="Ripgrep - fast search"),
        CommandPattern(pattern="ag ", description="Silver searcher"),
        CommandPattern(pattern="ack ", description="Ack search tool"),
        CommandPattern(pattern="fzf", description="Fuzzy finder"),

        # Git read operations
        CommandPattern(pattern="git status", description="Git status"),
        CommandPattern(pattern="git log", description="Git log"),
        CommandPattern(pattern="git diff", description="Git diff"),
        CommandPattern(pattern="git show", description="Git show"),
        CommandPattern(pattern="git branch", description="Git branches"),
        CommandPattern(pattern="git remote", description="Git remotes"),
        CommandPattern(pattern="git tag", description="Git tags"),
        CommandPattern(pattern="git stash list", description="Git stash list"),
        CommandPattern(pattern="git rev-parse", description="Git rev-parse"),
        CommandPattern(pattern="git config --get", description="Git config read"),
        CommandPattern(pattern="git config --list", description="Git config list"),
        CommandPattern(pattern="git blame", description="Git blame"),
        CommandPattern(pattern="git shortlog", description="Git shortlog"),
        CommandPattern(pattern="git describe", description="Git describe"),

        # System info
        CommandPattern(pattern="uname", description="System info"),
        CommandPattern(pattern="hostname", description="System hostname"),
        CommandPattern(pattern="whoami", description="Current user"),
        CommandPattern(pattern="id", description="User/group IDs"),
        CommandPattern(pattern="date", description="Current date/time"),
        CommandPattern(pattern="uptime", description="System uptime"),
        CommandPattern(pattern="df", description="Disk space usage"),
        CommandPattern(pattern="du ", description="Directory space usage"),
        CommandPattern(pattern="free", description="Memory usage"),
        CommandPattern(pattern="top -l 1", description="Process info (macOS)"),
        CommandPattern(pattern="ps", description="Process status"),

        # Network info (read-only)
        CommandPattern(pattern="ping -c", description="Ping with count"),
        CommandPattern(pattern="curl -I", description="HTTP headers only"),
        CommandPattern(pattern="curl --head", description="HTTP headers only"),
        CommandPattern(pattern="dig ", description="DNS lookup"),
        CommandPattern(pattern="nslookup ", description="DNS lookup"),
        CommandPattern(pattern="host ", description="DNS lookup"),
        CommandPattern(pattern="ifconfig", description="Network interfaces"),
        CommandPattern(pattern="ip addr", description="IP addresses"),
        CommandPattern(pattern="netstat", description="Network stats"),
        CommandPattern(pattern="ss ", description="Socket stats"),

        # Package managers (info only)
        CommandPattern(pattern="npm list", description="NPM list packages"),
        CommandPattern(pattern="npm ls", description="NPM list packages"),
        CommandPattern(pattern="npm view", description="NPM view package"),
        CommandPattern(pattern="npm show", description="NPM show package"),
        CommandPattern(pattern="npm outdated", description="NPM outdated packages"),
        CommandPattern(pattern="pip list", description="Pip list packages"),
        CommandPattern(pattern="pip show", description="Pip show package"),
        CommandPattern(pattern="pip freeze", description="Pip freeze"),
        CommandPattern(pattern="brew list", description="Homebrew list"),
        CommandPattern(pattern="brew info", description="Homebrew info"),
        CommandPattern(pattern="apt list", description="APT list packages"),
        CommandPattern(pattern="dpkg -l", description="DPKG list packages"),

        # Development tools (read operations)
        CommandPattern(pattern="python --version", description="Python version"),
        CommandPattern(pattern="python3 --version", description="Python3 version"),
        CommandPattern(pattern="node --version", description="Node version"),
        CommandPattern(pattern="npm --version", description="NPM version"),
        CommandPattern(pattern="cargo --version", description="Cargo version"),
        CommandPattern(pattern="rustc --version", description="Rust version"),
        CommandPattern(pattern="go version", description="Go version"),
        CommandPattern(pattern="java --version", description="Java version"),
        CommandPattern(pattern="javac --version", description="Javac version"),
        CommandPattern(pattern="ruby --version", description="Ruby version"),
        CommandPattern(pattern="docker --version", description="Docker version"),
        CommandPattern(pattern="docker ps", description="Docker containers"),
        CommandPattern(pattern="docker images", description="Docker images"),
        CommandPattern(pattern="docker logs", description="Docker logs"),

        # JSON/YAML processing
        CommandPattern(pattern="jq ", description="JSON processor"),
        CommandPattern(pattern="yq ", description="YAML processor"),

        # Misc read operations
        CommandPattern(pattern="man ", description="Manual pages"),
        CommandPattern(pattern="help ", description="Help for commands"),
        CommandPattern(pattern="type ", description="Command type"),
        CommandPattern(pattern="stat ", description="File statistics"),
        CommandPattern(pattern="md5sum ", description="MD5 checksum"),
        CommandPattern(pattern="sha256sum ", description="SHA256 checksum"),
        CommandPattern(pattern="shasum ", description="SHA checksum"),
    ]


def get_default_blocked_commands() -> list[CommandPattern]:
    """Get the default list of blocked commands."""
    return [
        # --- Destructive file operations ---
        CommandPattern(
            pattern=r"^rm\s+-rf\s+/",
            description="Recursive force-delete from root. Blocked regex: ^rm\\s+-rf\\s+/",
            is_regex=True,
        ),
        CommandPattern(
            pattern=r"^rm\s+-rf\s+~",
            description="Recursive force-delete home directory. Blocked regex: ^rm\\s+-rf\\s+~",
            is_regex=True,
        ),
        CommandPattern(
            pattern=r"^rm\s+-rf\s+\*",
            description="Recursive force-delete wildcard. Blocked regex: ^rm\\s+-rf\\s+\\*",
            is_regex=True,
        ),
        CommandPattern(
            pattern=r"^rm\s+-rf\s+\.",
            description="Recursive force-delete current/parent directory. Blocked regex: ^rm\\s+-rf\\s+\\.",
            is_regex=True,
        ),
        CommandPattern(
            pattern=r"^rm\s+-fr\s+/",
            description="Recursive force-delete root (reversed flags). Blocked regex: ^rm\\s+-fr\\s+/",
            is_regex=True,
        ),
        CommandPattern(
            pattern=r"^rm\s+--recursive",
            description="Recursive delete using long flag. Blocked regex: ^rm\\s+--recursive",
            is_regex=True,
        ),
        CommandPattern(pattern="mkfs", description="Format filesystem"),
        CommandPattern(pattern="dd", description="Disk duplicator — can overwrite drives and partitions"),

        # --- Arbitrary command execution via find ---
        CommandPattern(
            pattern=r"^find\s+.*-exec",
            description=(
                "find with -exec/-execdir can run arbitrary commands "
                "(e.g. find / -exec rm -rf {} \\;). "
                "Use find without -exec, or pipe to xargs. "
                "Blocked regex: ^find\\s+.*-exec"
            ),
            is_regex=True,
        ),

        # --- Fork bomb / device overwrite ---
        CommandPattern(pattern=":(){", description="Fork bomb"),
        CommandPattern(
            pattern=r".*>\s*/dev/(sd|nvme|disk|vd|hd)",
            description=(
                "Redirect output to raw disk device. "
                "Blocked regex: .*>\\s*/dev/(sd|nvme|disk|vd|hd)"
            ),
            is_regex=True,
        ),

        # --- Dangerous permission changes ---
        CommandPattern(pattern="chmod -R 777 /", description="Recursive world-writable permissions on root"),
        CommandPattern(pattern="chmod 777 /", description="World-writable permissions on root"),
        CommandPattern(pattern="chmod -R 777 ~", description="Recursive world-writable permissions on home"),
        CommandPattern(pattern="chown -R ", description="Recursive ownership change"),

        # --- Privilege escalation ---
        CommandPattern(pattern="sudo ", description="Superuser commands"),
        CommandPattern(pattern="su ", description="Switch user"),
        CommandPattern(pattern="doas ", description="OpenBSD sudo alternative"),

        # --- System shutdown / process control ---
        CommandPattern(pattern="reboot", description="System reboot"),
        CommandPattern(pattern="shutdown", description="System shutdown"),
        CommandPattern(pattern="halt", description="System halt"),
        CommandPattern(pattern="poweroff", description="System power off"),
        CommandPattern(pattern="kill", description="Kill process"),
        CommandPattern(pattern="killall", description="Kill processes by name"),
        CommandPattern(pattern="pkill", description="Kill processes by pattern"),

        # --- Network attacks ---
        CommandPattern(pattern="nc -l", description="Netcat listener"),
        CommandPattern(pattern="nmap ", description="Port scanner"),

        # --- Sensitive file access (blocked regardless of reader command) ---
        CommandPattern(
            pattern=r".*/etc/shadow",
            description="Access to shadow password file. Blocked regex: .*/etc/shadow",
            is_regex=True,
        ),
        CommandPattern(
            pattern=r".*/etc/passwd",
            description="Access to system user file. Blocked regex: .*/etc/passwd",
            is_regex=True,
        ),
        CommandPattern(
            pattern=r".*\.ssh/",
            description="Access to SSH keys and configuration (~/.ssh/). Blocked regex: .*\\.ssh/",
            is_regex=True,
        ),
        CommandPattern(
            pattern=r".*\.aws/",
            description="Access to AWS credentials (~/.aws/). Blocked regex: .*\\.aws/",
            is_regex=True,
        ),
        CommandPattern(
            pattern=r".*\.gnupg/",
            description="Access to GPG keys (~/.gnupg/). Blocked regex: .*\\.gnupg/",
            is_regex=True,
        ),

        # --- History/credential wiping ---
        CommandPattern(pattern="history -c", description="Clear history"),
        CommandPattern(pattern="shred ", description="Secure delete"),
    ]


def load_config(config_path: Optional[Path] = None) -> Config:
    """Load configuration from file or create default."""
    if config_path is None:
        config_path = get_default_config_path()

    if config_path.exists():
        with open(config_path) as f:
            data = yaml.safe_load(f) or {}

        # Convert command patterns
        if "allowed_commands" in data:
            data["allowed_commands"] = [
                CommandPattern(**cmd) if isinstance(cmd, dict) else CommandPattern(pattern=cmd)
                for cmd in data["allowed_commands"]
            ]

        if "blocked_commands" in data:
            data["blocked_commands"] = [
                CommandPattern(**cmd) if isinstance(cmd, dict) else CommandPattern(pattern=cmd)
                for cmd in data["blocked_commands"]
            ]

        return Config(**data)

    # Return default config
    return Config(
        allowed_commands=get_default_allowed_commands(),
        blocked_commands=get_default_blocked_commands(),
    )


def save_config(config: Config, config_path: Optional[Path] = None) -> None:
    """Save configuration to file."""
    if config_path is None:
        config_path = get_default_config_path()

    # Ensure directory exists
    config_path.parent.mkdir(parents=True, exist_ok=True)

    # Convert to dict, excluding session-only fields
    data = config.model_dump(exclude={"session_approved_commands"})

    # Convert permission_mode enum to string value
    data["permission_mode"] = config.permission_mode.value

    # Convert CommandPattern objects to dicts
    data["allowed_commands"] = [
        {"pattern": cmd["pattern"], "description": cmd["description"], "is_regex": cmd["is_regex"]}
        for cmd in data["allowed_commands"]
    ]
    data["blocked_commands"] = [
        {"pattern": cmd["pattern"], "description": cmd["description"], "is_regex": cmd["is_regex"]}
        for cmd in data["blocked_commands"]
    ]

    with open(config_path, "w") as f:
        yaml.safe_dump(data, f, default_flow_style=False, sort_keys=False)


def create_default_config_file(config_path: Optional[Path] = None) -> Path:
    """Create a default configuration file."""
    if config_path is None:
        config_path = get_default_config_path()

    config = Config(
        allowed_commands=get_default_allowed_commands(),
        blocked_commands=get_default_blocked_commands(),
    )

    save_config(config, config_path)
    return config_path
