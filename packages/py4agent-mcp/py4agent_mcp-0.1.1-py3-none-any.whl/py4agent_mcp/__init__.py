"""
py4agent-mcp: MCP (Model Context Protocol) Server for py4agent

Provides code execution capabilities through Jupyter kernels via MCP.
"""

from py4agent_mcp.mcp_server import create_app, create_mcp_app, main

__version__ = "0.1.0"

__all__ = ["create_app", "create_mcp_app", "main"]
