# py4agent-mcp

MCP (Model Context Protocol) Server for py4agent - Provides code execution capabilities through Jupyter kernels.

## Features

- **Isolated Python Runtimes**: Create and manage independent Python execution environments
- **MCP Protocol Integration**: Seamless integration with Model Context Protocol
- **Jupyter Kernel Backend**: Powered by Jupyter Server's kernel management
- **Multi-modal Output**: Support for text, tables, plots, and images
- **Background Execution**: Async code execution for long-running operations
- **Runtime Persistence**: Automatic save/restore of runtime configurations

## Installation

This project is part of a monorepo. Install dependencies:

```bash
# Install py4agent (required dependency)
pip install py4agent

# Install py4agent-mcp
cd py4agent-mcp
pip install -e .
```

For development setup, see [INSTALL.md](INSTALL.md).

## Usage

### Start the MCP Server

```bash
# Start with default settings (127.0.0.1:8889)
py4agent-mcp

# Custom host and port
py4agent-mcp --host 0.0.0.0 --port 9000

# Enable debug logging
py4agent-mcp --debug

# Save logs to file
py4agent-mcp --log-dir ./logs
```

### Command Line Options

- `--host`: Host to bind (default: 127.0.0.1)
- `--port`: Port to bind (default: 8889)
- `--debug`: Enable debug logging
- `--workers`: Number of worker processes (must be 1 for MCP)
- `--log-dir`: Directory to store logs (optional)

### Python API

```python
from py4agent_mcp import create_app, create_mcp_app, main
from py4agent_mcp.mcp_server import JupyterKernelManager

# Create FastAPI app with MCP mounted
app = create_app()

# Create MCP server app
mcp_app = create_mcp_app()

# Run the server
main()
```

## MCP Tools

The server exposes the following MCP tools:

1. **create_runtime**: Create a new isolated Python runtime
2. **list_runtimes**: List all active runtimes
3. **delete_runtime**: Delete a runtime and free resources
4. **restart_runtime**: Restart a runtime (clears state)
5. **interrupt_runtime**: Interrupt running code (Ctrl+C)
6. **get_runtime_status**: Get runtime status information
7. **execute_code**: Execute Python code in a runtime

## Project Structure

```
py4agent-mcp/
├── py4agent_mcp/           # Package directory
│   ├── __init__.py         # Package exports
│   └── mcp_server.py       # Main MCP server implementation
├── pyproject.toml          # Project configuration
├── README.md
├── INSTALL.md
├── CHANGES.md
└── test_install.sh
```

## Architecture

- Built on FastAPI and FastMCP
- Uses Jupyter Server's AsyncMappingKernelManager
- Runtime configurations persist across server restarts
- Single-worker mode required for MCP SSE (Server-Sent Events)
- Depends on py4agent for code execution parsing
- Organized as a proper Python package for clean imports

## Requirements

- Python >= 3.9
- py4agent >= 0.0.3
- FastAPI
- FastMCP
- Jupyter Server >= 2.0.0
- Jupyter Client >= 8.0.0

## License

MIT
