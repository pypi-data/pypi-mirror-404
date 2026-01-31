# Configuration Guide

The FPL MCP Server supports configuration through environment variables. This guide covers how to customize settings for both Docker and uv deployment methods.

## Configuration Options

| Variable                           | Description                             | Default                             | Type    |
| ---------------------------------- | --------------------------------------- | ----------------------------------- | ------- |
| `FPL_MCP_FPL_BASE_URL`             | FPL API base URL                        | `https://fantasy.premierleague.com` | string  |
| `FPL_MCP_FPL_API_TIMEOUT`          | API request timeout (seconds)           | `30`                                | integer |
| `FPL_MCP_BOOTSTRAP_CACHE_TTL`      | Bootstrap data cache duration (seconds) | `14400` (4 hours)                   | integer |
| `FPL_MCP_FIXTURES_CACHE_TTL`       | Fixtures cache duration (seconds)       | `14400` (4 hours)                   | integer |
| `FPL_MCP_PLAYER_SUMMARY_CACHE_TTL` | Player summary cache duration (seconds) | `300` (5 minutes)                   | integer |
| `FPL_MCP_LOG_LEVEL`                | Logging level                           | `INFO`                              | string  |

### Log Levels

Available log levels (from least to most verbose):

- `CRITICAL` - Only critical errors
- `ERROR` - Errors and critical issues
- `WARNING` - Warnings, errors, and critical issues
- `INFO` - General information (recommended)
- `DEBUG` - Detailed debugging information

## Docker

When running the FPL MCP server with Docker, you can pass environment variables using the `-e` flag

```json
{
  "mcpServers": {
    "fpl": {
      "command": "docker",
      "args": [
        "run",
        "--rm",
        "-i",
        "-e",
        "FPL_MCP_LOG_LEVEL=INFO",
        "-e",
        "FPL_MCP_BOOTSTRAP_CACHE_TTL=7200",
        "-e",
        "FPL_MCP_FIXTURES_CACHE_TTL=7200",
        "nguyenanhducs/fpl-mcp:latest"
      ],
      "type": "stdio"
    }
  }
}
```

## UV

When running with `uv`, the server automatically loads environment variables from a `.env` file in the project root.

### Step 1: Create Environment File

Create a `.env` file in the project root directory:

```bash
cd /path/to/fpl-mcp
cp .env.example .env
```

### Step 2: Edit Configuration

Edit the `.env` file with your preferred settings:

```bash
# FPL API Configuration
FPL_MCP_FPL_BASE_URL=https://fantasy.premierleague.com
FPL_MCP_FPL_API_TIMEOUT=30

# Cache Configuration (in seconds)
FPL_MCP_BOOTSTRAP_CACHE_TTL=14400  # 4 hours
FPL_MCP_FIXTURES_CACHE_TTL=14400   # 4 hours
FPL_MCP_PLAYER_SUMMARY_CACHE_TTL=300  # 5 minutes

# Logging Configuration
FPL_MCP_LOG_LEVEL=INFO
```

### Step 3: Run the Server

The server will automatically load the `.env` file:

```bash
uv run python -m src.main
```

> [!TIP]
> The `.env` file is ignored by git, so your configuration won't be committed to version control.

## Common Configuration Scenarios

### Scenario 1: Development/Debugging

For debugging issues, increase logging verbosity:

```bash
FPL_MCP_LOG_LEVEL=DEBUG
```

### Scenario 2: Reduce API Load

Increase cache durations to reduce API calls:

```bash
FPL_MCP_BOOTSTRAP_CACHE_TTL=28800  # 8 hours
FPL_MCP_FIXTURES_CACHE_TTL=28800   # 8 hours
FPL_MCP_PLAYER_SUMMARY_CACHE_TTL=600  # 10 minutes
```

### Scenario 3: Fresh Data Priority

Reduce cache durations for more up-to-date data (may increase API load):

```bash
FPL_MCP_BOOTSTRAP_CACHE_TTL=1800   # 30 minutes
FPL_MCP_FIXTURES_CACHE_TTL=1800    # 30 minutes
FPL_MCP_PLAYER_SUMMARY_CACHE_TTL=60  # 1 minute
```

### Scenario 4: Slow Network

Increase timeout for slower connections:

```bash
FPL_MCP_FPL_API_TIMEOUT=60  # 60 seconds
```

## Verifying Configuration

To verify your configuration is loaded correctly, check the server logs when it starts. With `FPL_MCP_LOG_LEVEL=DEBUG`, you'll see the loaded settings.

## Default Behavior

If no environment variables are set, the server uses sensible defaults:

- **4-hour cache** for bootstrap data and fixtures
- **5-minute cache** for player summaries
- **30-second timeout** for API requests
- **INFO-level logging** for general operation information

These defaults work well for most use cases and balance data freshness with API load.
