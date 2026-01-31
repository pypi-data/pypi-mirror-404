# Installation

Multiple installation methods are available for FPL MCP Server. Choose the one that best fits your needs.

## uvx (Recommended)

[uvx](https://docs.astral.sh/uv/guides/tools/) provides the simplest installation experience. It automatically downloads and caches the package on first use.

```bash
# Run directly (downloads on first use, cached for subsequent run
uvx fpl-mcp-server
```

Or install it globally:
```bash
uv tool install fpl-mcp-server
```

### IDE Configuration with uvx

**Claude Desktop** (`~/Library/Application Support/Claude/claude_desktop_config.json`):

```json
{
  "mcpServers": {
    "fpl": {
      "command": "uvx",
      "args": ["fpl-mcp-server"]
    }
  }
}
```

**Cline** (VS Code settings):

```json
{
  "mcp.servers": {
    "fpl": {
      "command": "uvx",
      "args": ["fpl-mcp-server"],
      "type": "stdio"
    }
  }
}
```

---

## Docker

Use the pre-built Docker image from GitHub Container Registry for isolated, reproducible environments.

```bash
# Pull the latest image
docker pull ghcr.io/nguyenanhducs/fpl-mcp:latest

# Run the server
docker run --rm -i ghcr.io/nguyenanhducs/fpl-mcp:latest
```

### IDE Configuration with Docker

**Claude Desktop**:

```json
{
  "mcpServers": {
    "fpl": {
      "command": "docker",
      "args": [
        "run",
        "--rm",
        "-i",
        "ghcr.io/nguyenanhducs/fpl-mcp:latest"
      ]
    }
  }
}
```

**Cline**:

```json
{
  "mcp.servers": {
    "fpl": {
      "command": "docker",
      "args": [
        "run",
        "--rm",
        "-i",
        "ghcr.io/nguyenanhducs/fpl-mcp:latest"
      ],
      "type": "stdio"
    }
  }
}
```

---

## pip

Traditional installation using pip:

```bash
pip install fpl-mcp-server
```

Then configure Claude Desktop to use it:

```json
{
  "mcpServers": {
    "fpl": {
      "command": "fpl-mcp-server"
    }
  }
}
```

---

### Using `uv` (Recommended)

```bash
uv add fpl-mcp-server
```

---

## From Source

For development or contributing:

```bash
# Clone the repository
git clone https://github.com/nguyenanhducs/fpl-mcp.git
cd fpl-mcp

# Install with uv
uv sync

# Run the server
uv run python -m src.main
```

### IDE Configuration for Development

```json
{
  "mcpServers": {
    "fpl": {
      "command": "uv",
      "args": [
        "--directory",
        "/absolute/path/to/fpl-mcp",
        "run",
        "python",
        "-m",
        "src.main"
      ]
    }
  }
}
```

Replace `/absolute/path/to/fpl-mcp` with your actual installation path.

---

## Configuration

The FPL MCP Server works out-of-the-box with sensible defaults. For advanced configuration options, see the [Configuration Guide](./configuration.md).

## Verification

To verify your installation, ask your AI assistant:

```
List available FPL tools
```

You should see all 17 FPL tools, including player search, fixture analysis, and transfer tracking capabilities.
