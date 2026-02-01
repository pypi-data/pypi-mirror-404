# Client Configuration

Different AI clients have varying configuration formats for MCP servers. This page documents the configuration specifics for each supported client.

## Standard Configuration Pattern

Most AI clients follow this basic pattern:

```json
{
  "mcpServers": {
    "stata-mcp": {
      "command": "uvx",
      "args": ["stata-mcp"]
    }
  }
}
```

However, each client may have slight variations in file location, format, or supported features.

## Client-Specific Configurations

### Claude Code

**Configuration Method**: CLI command or `.mcp.json`

**Global Installation**:
```bash
claude mcp add stata-mcp -- uvx stata-mcp
```

**Project-based Installation** (Recommended):
```bash
cd ~/Documents/MyResearch
claude mcp add stata-mcp \
  --env STATA_MCP_CWD=$(pwd) \
  --scope project \
  -- uvx --directory $(pwd) stata-mcp
```

**Configuration File**: `.mcp.json` (created in project directory)

**Format**: JSON
```json
{
  "mcpServers": {
    "stata-mcp": {
      "command": "uvx",
      "args": ["stata-mcp"],
      "env": {
        "STATA_MCP_CWD": "/absolute/path/to/project"
      }
    }
  }
}
```

**Unique Features**:
- ✅ Project-scoped configuration (`--scope project`)
- ✅ Environment variable injection (`--env`)
- ✅ Directory specification (`--directory`)
- ✅ Version pinning support (`stata-mcp==1.13.0`)

### Claude Desktop

**Configuration File**: `~/Library/Application Support/Claude/claude_desktop_config.json` (macOS)

**Format**: JSON
```json
{
  "mcpServers": {
    "stata-mcp": {
      "command": "uvx",
      "args": ["stata-mcp"],
      "env": {
        "STATA_MCP_CWD": "/path/to/project",
        "STATA_CLI": "/Applications/Stata/StataMP"
      }
    }
  }
}
```

**Unique Features**:
- ✅ Environment variable support via `env` object
- ✅ Manual configuration file editing required

### Codex (VS Code Extension)

**Configuration File**: `~/.codex/config.toml`

**Format**: TOML
```toml
[mcp_servers.stata-mcp]
command = "uvx"
args = ["stata-mcp"]
```

**With environment variables**:
```toml
[mcp_servers.stata-mcp]
command = "uvx"
args = ["stata-mcp"]
env = { STATA_MCP_CWD = "/path/to/project" }
```

**Unique Features**:
- ⚠️ Uses TOML format instead of JSON
- ✅ Environment variables via `env` table

### Cline

**Configuration File**: `~/Library/Application Support/Code/User/globalStorage/saoudrizwan.claude-dev/setting/cline_mcp_settings.json`

**Format**: JSON
```json
{
  "mcpServers": {
    "stata-mcp": {
      "command": "uvx",
      "args": [
        "stata-mcp"
      ]
    }
  }
}
```

**Unique Features**:
- ⚠️ Standard JSON format
- ⚠️ No special features or extensions

### Cursor

**Configuration File**: Cursor settings (location varies by OS)

**Format**: JSON
```json
{
  "mcpServers": {
    "stata-mcp": {
      "command": "uvx",
      "args": [
        "--directory",
        "/absolute/path/to/project",
        "stata-mcp"
      ],
      "env": {
        "STATA_MCP_CWD": "/absolute/path/to/project"
      }
    }
  }
}
```

**Known Issues**:
- ⚠️ File system access limitations (may not access `Documents` directory)
- ⚠️ **Requires both** `--directory` in args **and** `STATA_MCP_CWD` environment variable (both must point to same path)
- ⚠️ Must use absolute paths (relative paths not supported)
- ✅ Environment variables supported

### Cherry Studio

**Configuration File**: Cherry Studio settings

**Format**: JSON (same as Claude Desktop)

```json
{
  "mcpServers": {
    "stata-mcp": {
      "command": "uvx",
      "args": ["stata-mcp"]
    }
  }
}
```

**Unique Features**:
- ✅ Standard MCP configuration
- ✅ Compatible with Claude Desktop format

## Configuration Options

### Command Variations

**Standard** (uses latest version):
```json
"command": "uvx",
"args": ["stata-mcp"]
```

**Pinned Version**:
```json
"command": "uvx",
"args": ["stata-mcp==1.13.0"]
```

**With Custom Directory**:
```json
"command": "uvx",
"args": [
  "--directory",
  "/path/to/project",
  "stata-mcp"
]
```

### Environment Variables

#### Core Variables

| Variable                 | Purpose                                | Example                         |
|--------------------------|----------------------------------------|---------------------------------|
| `STATA_MCP_CWD`          | Working directory for Stata operations | `"/Users/user/research"`        |
| `STATA_CLI`              | Path to specific Stata executable      | `"/Applications/Stata/StataMP"` |
| `STATA_MCP_MODEL`        | LLM model for agent mode               | `"gpt-4"`                       |
| `STATA_MCP_API_KEY`      | API key for LLM provider               | `"sk-..."`                      |
| `STATA_MCP_API_BASE_URL` | Custom API endpoint                    | `"https://api.openai.com/v1"`   |

#### Security Variables

| Variable              | Purpose                          | Default | Example               |
|-----------------------|----------------------------------|---------|-----------------------|
| `STATA_MCP__IS_GUARD` | Enable security guard validation | `true`  | `"true"` or `"false"` |

#### Monitoring Variables

| Variable                | Purpose               | Default         | Example               |
|-------------------------|-----------------------|-----------------|-----------------------|
| `STATA_MCP__IS_MONITOR` | Enable RAM monitoring | `false`         | `"true"` or `"false"` |
| `STATA_MCP__RAM_LIMIT`  | Maximum RAM in MB     | `-1` (no limit) | `"8192"` for 8GB      |

#### Debug Variables

| Variable                                | Purpose                | Default                           | Example                          |
|-----------------------------------------|------------------------|-----------------------------------|----------------------------------|
| `STATA_MCP__IS_DEBUG`                   | Enable debug mode      | `false`                           | `"true"` or `"false"`            |
| `STATA_MCP__LOGGING_ON`                 | Enable logging         | `true`                            | `"true"` or `"false"`            |
| `STATA_MCP__LOGGING_CONSOLE_HANDLER_ON` | Enable console logging | `false`                           | `"true"` or `"false"`            |
| `STATA_MCP__LOGGING_FILE_HANDLER_ON`    | Enable file logging    | `true`                            | `"true"` or `"false"`            |
| `STATA_MCP__LOG_FILE`                   | Custom log file path   | `~/.statamcp/stata_mcp_debug.log` | `"/var/log/stata-mcp/debug.log"` |

**JSON Format**:
```json
"env": {
  "STATA_MCP_CWD": "/path/to/project",
  "STATA_CLI": "/path/to/stata"
}
```

**With Security and Monitoring**:
```json
"env": {
  "STATA_MCP_CWD": "/path/to/project",
  "STATA_MCP__IS_GUARD": "true",
  "STATA_MCP__IS_MONITOR": "true",
  "STATA_MCP__RAM_LIMIT": "8192"
}
```

**TOML Format** (Codex):
```toml
env = { STATA_MCP_CWD = "/path/to/project" }
```

**With All Features**:
```toml
env.STATA_MCP_CWD = "/path/to/project"
env.STATA_MCP__IS_GUARD = "true"
env.STATA_MCP__IS_MONITOR = "true"
env.STATA_MCP__RAM_LIMIT = "8192"
env.STATA_MCP__LOGGING_CONSOLE_HANDLER_ON = "true"
```

## Configuration File Locations

| Client         | Config File Location                                                                                           | Format |
|----------------|----------------------------------------------------------------------------------------------------------------|--------|
| Claude Code    | `.mcp.json` (project) or global config                                                                         | JSON   |
| Claude Desktop | `~/Library/Application Support/Claude/claude_desktop_config.json`                                              | JSON   |
| Codex          | `~/.codex/config.toml`                                                                                         | TOML   |
| Cline          | `~/Library/Application Support/Code/User/globalStorage/saoudrizwan.claude-dev/setting/cline_mcp_settings.json` | JSON   |
| Cursor         | Cursor settings directory                                                                                      | JSON   |
| Cherry Studio  | Cherry Studio settings directory                                                                               | JSON   |

## Troubleshooting

### Configuration Not Detected

1. **Verify file path**: Check if configuration file exists in the correct location
2. **Validate JSON/TOML syntax**: Use online validators to check for syntax errors
3. **Restart client**: Most clients require restart after configuration changes
4. **Check logs**: Look for MCP server connection errors in client logs

### Path Issues

**Problem**: Stata-MCP cannot access project files

**Solution**:
- Use absolute paths for `STATA_MCP_CWD`
- Ensure paths are within client's allowed directories
- Check client's file system access permissions

### Version Conflicts

**Problem**: Wrong Stata-MCP version loaded

**Solution**:
- Clear Python package cache: `pip cache purge stata-mcp`
- Pin specific version: `uvx stata-mcp==1.13.0`
- Use `uvx --refresh stata-mcp` to force refresh

## Best Practices

1. **Use project-scoped configuration** when available (Claude Code)
2. **Pin versions** in production environments
3. **Set absolute paths** for working directories
4. **Test configuration** with `uvx stata-mcp --usable` before adding to client
5. **Document custom configurations** for team collaboration

## Additional Resources

- [Usage Guide](usage.md) - Comprehensive usage examples
- [Overview](overview.md) - Architecture and design
- [MCP Tools](mcp/tools.md) - Available tools reference
