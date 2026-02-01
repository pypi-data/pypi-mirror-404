# Host Terminal MCP

Run terminal commands on your computer through Claude.

**Why?** Claude Cowork runs inside a sandboxed VM and can't access your host machine's terminal. This MCP plugin bridges that gap, letting Claude run commands directly on your computer (with permission controls).

## Install

```bash
# Clone
git clone https://github.com/ankitag-in/host-terminal-mcp.git
cd host-terminal-mcp

# Install
uv tool install .
```

## Configure Claude Desktop

Add to `~/Library/Application Support/Claude/claude_desktop_config.json` (Mac) or `~/.config/claude/claude_desktop_config.json` (Linux):

```json
{
  "mcpServers": {
    "host-terminal": {
      "command": "host-terminal-mcp"
    }
  }
}
```

Restart Claude Desktop.

## Use

Ask Claude:
- "List files in my home directory"
- "Show git status"
- "What's running on port 3000?"

## Permission Modes

| Mode | Description |
|------|-------------|
| `allowlist` | Only pre-approved commands (default, safest) |
| `ask` | Prompts for unknown commands |
| `allow_all` | Allows everything (dangerous!) |

Common read commands are pre-approved: `ls`, `cat`, `grep`, `git status`, `ps`, etc.

Dangerous commands are always blocked: `sudo`, `rm -rf /`, etc.

## Commands

```bash
# Create config file
host-terminal-mcp --init-config

# Run in ask mode (approve commands on the fly)
host-terminal-mcp --mode ask

# Show help
host-terminal-mcp --help
```

## Config

Edit `~/.config/host-terminal-mcp/config.yaml` to customize allowed commands.

## License

Apache-2.0
