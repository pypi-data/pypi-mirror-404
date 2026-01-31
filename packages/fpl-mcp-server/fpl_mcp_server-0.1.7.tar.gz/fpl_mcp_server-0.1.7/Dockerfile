# ============================================
# Builder Stage: Install dependencies with uv
# ============================================
FROM ghcr.io/astral-sh/uv:python3.13-alpine AS builder

WORKDIR /app

# Enable bytecode compilation
ENV UV_COMPILE_BYTECODE=1

# Copy from cache instead of linking
ENV UV_LINK_MODE=copy

# Copy dependency files
COPY pyproject.toml uv.lock README.md ./

# Install dependencies to /app/.venv
RUN --mount=type=cache,target=/root/.cache/uv \
    uv sync --frozen --no-dev

# Copy application code
COPY src ./src

# ============================================
# Runtime Stage: Minimal Python runtime
# ============================================
FROM python:3.13-alpine AS runtime

# Metadata labels
LABEL maintainer="nguyenanhducs"
LABEL description="Fantasy Premier League MCP Server"
LABEL org.opencontainers.image.source="https://github.com/nguyenanhducs/fpl-mcp"
LABEL org.opencontainers.image.title="FPL MCP Server"
LABEL org.opencontainers.image.description="A comprehensive Model Context Protocol (MCP) server for Fantasy Premier League analysis and strategy. Provides AI assistants with powerful tools, resources, and prompts for data-driven FPL insights."
LABEL org.opencontainers.image.licenses="MIT"

WORKDIR /app

# Create non-root user for security
RUN addgroup -g 1000 fplmcp && \
    adduser -D -u 1000 -G fplmcp fplmcp

# Copy virtual environment and source code from builder
COPY --from=builder --chown=fplmcp:fplmcp /app/.venv /app/.venv
COPY --from=builder --chown=fplmcp:fplmcp /app/src /app/src

# Switch to non-root user
USER fplmcp

# Set Python to unbuffered mode for proper stdio
ENV PYTHONUNBUFFERED=1

# Add .venv/bin to PATH
ENV PATH="/app/.venv/bin:$PATH"

# Run with stdio transport (default)
CMD ["python", "-m", "src.main"]
