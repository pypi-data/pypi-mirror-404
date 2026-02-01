# Host Terminal MCP

[![PyPI](https://img.shields.io/pypi/v/host-terminal-mcp)](https://pypi.org/project/host-terminal-mcp/)
[![License](https://img.shields.io/badge/License-Apache_2.0-blue.svg)](https://opensource.org/licenses/Apache-2.0)

Run terminal commands on your computer through Claude.

Two transports:
- **Stdio** — for Claude Desktop and MCP Inspector (default)
- **HTTP** — for external services calling in over the network (e.g. a chatbot running in Docker)

## Quick Start

### MCP Server (Claude Desktop / Cowork)

```bash
# Install
uv tool install host-terminal-mcp

# Add to Claude Desktop config and restart
```

Claude Desktop config (`~/Library/Application Support/Claude/claude_desktop_config.json` on Mac):

```json
{
  "mcpServers": {
    "host-terminal": {
      "command": "host-terminal-mcp"
    }
  }
}
```

### HTTP Server (External Services)

For services running in Docker or on other machines that need to execute host commands via REST API:

```bash
# Install with HTTP extras
uv tool install 'host-terminal-mcp[http]'

# Start in background
nohup host-terminal-mcp --http --port 8099 > /tmp/host-terminal-mcp.log 2>&1 &

# With a specific permission mode
nohup host-terminal-mcp --http --port 8099 --mode ask > /tmp/host-terminal-mcp.log 2>&1 &

# Verify
curl http://localhost:8099/health
```

Services call `POST http://localhost:8099/execute` with a JSON body.

### From Source

```bash
git clone https://github.com/ankitag-in/host-terminal-mcp.git
cd host-terminal-mcp
make install

# MCP stdio server (foreground, for Claude Desktop)
make run

# HTTP server (background daemon)
make start                        # port 8099, allowlist mode
make start HTTP_PORT=9000         # custom port
make start MODE=ask               # ask permission mode
make stop                         # stop
make status                       # status + recent logs
make restart                      # stop + start
```

#### HTTP Endpoints

| Endpoint | Method | Purpose |
|----------|--------|---------|
| `/health` | GET | Health check |
| `/execute` | POST | Run a command |
| `/cd` | POST | Change working directory |
| `/cwd` | GET | Get current directory |
| `/permissions` | GET | Get permission config |

#### Example

```bash
# Health check
curl http://localhost:8099/health

# Execute a command
curl -X POST http://localhost:8099/execute \
  -H "Content-Type: application/json" \
  -d '{"command": "docker compose ps", "working_directory": "/path/to/project"}'

# Response
{
  "status": "success",
  "stdout": "NAME    IMAGE    ...",
  "stderr": "",
  "exit_code": 0,
  "return_code": 0,
  "timed_out": false,
  "truncated": false,
  "working_directory": "/path/to/project"
}
```

## Use

Ask Claude:
- "List files in my home directory"
- "Show git status"
- "What's running on port 3000?"

## Permission Modes

| Mode | Description | Safety |
|------|-------------|--------|
| `allowlist` | Only pre-approved commands run (default) | **Recommended** |
| `ask` | Prompts for unknown commands, can be approved per-session | Use with caution |
| `allow_all` | Allows everything except blocked commands | **Dangerous** |

Permission check order: **blocked** (always wins) > **allowed** > **session-approved** > **mode decision**

### Default Allowed Commands

These commands (and their arguments) are allowed out of the box:

**File listing & navigation:**
`ls`, `ll`, `la`, `pwd`, `tree`, `find`, `locate`, `which`, `whereis`, `file`

**File viewing:**
`cat`, `head`, `tail`, `less`, `more`, `bat`, `wc`

**Search:**
`grep`, `rg`, `ag`, `ack`, `fzf`

**Git (read-only):**
`git status`, `git log`, `git diff`, `git show`, `git branch`, `git remote`, `git tag`, `git stash list`, `git rev-parse`, `git config --get`, `git config --list`, `git blame`, `git shortlog`, `git describe`

**System info:**
`uname`, `hostname`, `whoami`, `id`, `date`, `uptime`, `df`, `du`, `free`, `top -l 1`, `ps`, `env`, `printenv`, `echo $`

**Network (read-only):**
`ping -c`, `curl -I`, `curl --head`, `dig`, `nslookup`, `host`, `ifconfig`, `ip addr`, `netstat`, `ss`

**Package managers (info only):**
`npm list`, `npm ls`, `npm view`, `npm show`, `npm outdated`, `pip list`, `pip show`, `pip freeze`, `brew list`, `brew info`, `apt list`, `dpkg -l`

**Dev tool versions:**
`python --version`, `python3 --version`, `node --version`, `npm --version`, `cargo --version`, `rustc --version`, `go version`, `java --version`, `javac --version`, `ruby --version`, `docker --version`

**Docker (read-only):**
`docker ps`, `docker images`, `docker logs`

**Data processing:**
`jq`, `yq`

**Misc:**
`man`, `help`, `type`, `stat`, `md5sum`, `sha256sum`, `shasum`

### Always Blocked Commands

These are blocked regardless of permission mode:

| Pattern | Reason |
|---------|--------|
| `rm -rf /` | Recursive delete root |
| `rm -rf ~` | Recursive delete home |
| `rm -rf *` | Recursive delete all |
| `mkfs` | Format filesystem |
| `dd if=` | Disk destroyer |
| `:(){` | Fork bomb |
| `> /dev/sd` | Overwrite disk |
| `chmod -R 777 /` | Dangerous permissions |
| `chown -R` | Recursive ownership change |
| `sudo`, `su`, `doas` | Privilege escalation |
| `nc -l` | Netcat listener |
| `nmap` | Port scanner |
| `cat /etc/shadow` | Password file |
| `cat /etc/passwd` | User file |
| `history -c` | Clear history |
| `shred` | Secure delete |

## Config

Config file: `~/.config/host-terminal-mcp/config.yaml`

```bash
# Generate default config
host-terminal-mcp --init-config
```

Add custom allowed commands:

```yaml
allowed_commands:
  # Append your own patterns to the defaults
  - pattern: "docker compose logs"
    description: "Docker Compose service logs"
  - pattern: "docker compose ps"
    description: "Docker Compose service status"
  - pattern: "docker stats --no-stream"
    description: "Docker container resource usage"
  - pattern: "redis-cli"
    description: "Redis CLI commands"

  # Use regex for more flexible matching
  - pattern: "^kubectl get "
    description: "Kubernetes get resources"
    is_regex: true
```

Other config options:

```yaml
permission_mode: allowlist          # allowlist | ask | allow_all
timeout_seconds: 300                # Max command execution time
max_output_size: 100000             # Max output chars (truncated beyond this)
shell: /bin/bash                    # Shell to use
allowed_directories:                # Commands restricted to these dirs
  - /Users/me
environment_passthrough:            # Env vars passed to commands
  - PATH
  - HOME
  - USER
  - LANG
  - LC_ALL
```

## Development

```bash
make install        # Install all deps (venv auto-created)
make test           # Run tests
make lint           # Run linters
make format         # Format code
make help           # Show all targets
```

## License

Apache-2.0
