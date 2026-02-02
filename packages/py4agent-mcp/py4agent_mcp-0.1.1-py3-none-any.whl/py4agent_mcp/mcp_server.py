"""
MCP (Model Context Protocol) Server for py4agent

Provides code execution capabilities through Jupyter kernels via MCP.
Uses jupyter_server's kernel management API directly in-process.
"""
import asyncio
import json
import os
import random
import string
import sys
import time
import traceback
import uuid
from pathlib import Path
from typing import Literal, Optional

import uvicorn
from contextlib import asynccontextmanager
from fastapi import FastAPI
from fastmcp import FastMCP
from loguru import logger
from pydantic import BaseModel, Field
from jupyter_server.services.kernels.kernelmanager import AsyncMappingKernelManager

from py4agent.injection.jupyter_parse import parse_msg_list_to_tool_response


def _generate_short_id(length: int = 8) -> str:
    """Generate a short random alphanumeric ID"""
    chars = string.ascii_lowercase + string.digits
    return ''.join(random.choice(chars) for _ in range(length))


class RuntimeConfig(BaseModel):
    """Runtime configuration binding runtime_id to kernel_id"""
    runtime_id: str = Field(..., description="Unique runtime identifier (user-facing)")
    kernel_id: str = Field(..., description="Jupyter kernel ID (internal)")
    created_at: float = Field(default_factory=time.time, description="Creation timestamp")
    last_used: float = Field(default_factory=time.time, description="Last used timestamp")


# Input Models for MCP Tools
class RuntimeIdInput(BaseModel):
    """Input model for tools that only need runtime_id"""
    runtime_id: str = Field(
        ...,
        description="The 8-character runtime identifier (e.g., 'a8x3k9z2')",
        min_length=8,
        max_length=8,
        pattern=r'^[a-z0-9]{8}$',
    )


class ExecuteCodeInput(BaseModel):
    """Input model for execute_code tool"""
    runtime_id: Optional[str] = Field(
        None,
        description="The 8-character runtime identifier (e.g., 'a8x3k9z2'). If not provided or null, a new runtime will be automatically created.",
        min_length=8,
        max_length=8,
        pattern=r'^[a-z0-9]{8}$',
    )
    code: str = Field(
        ...,
        description="Python code to execute. Can be multi-line. Examples: 'x = 42', 'import pandas as pd\\ndf = pd.DataFrame()', 'print(\"Hello\")'",
        min_length=1,
    )
    description: str = Field(
        ...,
        description="Human-readable description of what the code does. Used for logging and tracking. Examples: 'Load dataset', 'Train model', 'Generate plot'",
        min_length=1,
    )
    background: bool = Field(
        False,
        description="If True, execute code asynchronously without waiting for results. Use for long-running operations.",
    )


class JupyterKernelManager:
    """Manages Jupyter kernels using jupyter_server's AsyncMappingKernelManager"""

    def __init__(self):
        # Use jupyter_server's kernel manager
        self.kernel_manager: AsyncMappingKernelManager = AsyncMappingKernelManager()
        self._running = False
        logger.info("Initialized Jupyter Server kernel manager")

    async def start(self):
        """Initialize the kernel manager"""
        if self._running:
            logger.warning("Kernel manager is already running")
            return

        self._running = True
        logger.info("Kernel manager started and ready")

    async def stop(self):
        """Stop all kernels and clean up"""
        if self._running:
            logger.info("Stopping all kernels...")
            await self.kernel_manager.shutdown_all()
            self._running = False
            logger.info("Kernel manager stopped")

    async def create_kernel(self, kernel_name: str = "python3") -> str:
        """Create a new kernel"""
        kernel_id = await self.kernel_manager.start_kernel(kernel_name=kernel_name)
        logger.info(f"Created kernel: {kernel_id} (type: {kernel_name})")
        return kernel_id

    async def delete_kernel(self, kernel_id: str):
        """Delete a kernel"""
        if kernel_id not in self.kernel_manager:
            raise Exception(f"Kernel {kernel_id} not found")

        await self.kernel_manager.shutdown_kernel(kernel_id)
        logger.info(f"Deleted kernel: {kernel_id}")
        return True

    async def list_kernels(self) -> list:
        """List all active kernels"""
        kernels = []
        for kernel_id in self.kernel_manager.list_kernel_ids():
            kernel = self.kernel_manager.get_kernel(kernel_id)
            kernels.append({
                "id": kernel_id,
                "name": getattr(kernel, 'kernel_name', 'python3'),
                "last_activity": time.time(),
                "execution_state": "unknown",
            })
        return kernels

    async def interrupt_kernel(self, kernel_id: str):
        """Interrupt a kernel"""
        if kernel_id not in self.kernel_manager:
            raise Exception(f"Kernel {kernel_id} not found")

        kernel = self.kernel_manager.get_kernel(kernel_id)
        await kernel.interrupt_kernel()
        logger.info(f"Interrupted kernel: {kernel_id}")
        return True

    async def restart_kernel(self, kernel_id: str):
        """Restart a kernel"""
        if kernel_id not in self.kernel_manager:
            raise Exception(f"Kernel {kernel_id} not found")

        await self.kernel_manager.restart_kernel(kernel_id)
        logger.info(f"Restarted kernel: {kernel_id}")
        return True

    def get_kernel(self, kernel_id: str):
        """Get a kernel instance"""
        if kernel_id not in self.kernel_manager:
            raise Exception(f"Kernel {kernel_id} not found")
        return self.kernel_manager.get_kernel(kernel_id)


# Global kernel manager (using jupyter_server)
kernel_manager: Optional[JupyterKernelManager] = None

# Store runtime configurations (runtime_id -> RuntimeConfig)
_runtimes: dict[str, RuntimeConfig] = {}


def get_runtime_config_path() -> str:
    """Get the runtime configuration file path for this worker process.

    In multi-worker mode, each worker gets its own config file to avoid conflicts.
    The worker ID is determined by the process ID.
    """
    base_path = os.getenv(
        "PY4AGENT_RUNTIME_CONFIG",
        os.path.join(os.path.expanduser("~"), ".py4agent", "runtimes.json")
    )

    # In multi-worker mode, uvicorn creates child processes
    # We can detect if we're in a worker by checking if our PID differs from the parent
    # For simplicity, we use PID-based file naming
    pid = os.getpid()

    # Check if we should use per-worker config files
    # This is enabled by setting PY4AGENT_MULTIWORKER=1
    if os.getenv("PY4AGENT_MULTIWORKER", "0") == "1":
        # Use PID-based config file for each worker
        base_dir = os.path.dirname(base_path)
        base_name = os.path.basename(base_path)
        name, ext = os.path.splitext(base_name)
        return os.path.join(base_dir, f"{name}.{pid}{ext}")

    return base_path


# Runtime persistence file path
RUNTIME_CONFIG_PATH = get_runtime_config_path()


def _load_runtimes():
    """Load runtime configurations from persistent storage"""
    global _runtimes
    config_path = Path(RUNTIME_CONFIG_PATH)

    if config_path.exists():
        try:
            with open(config_path, "r", encoding="utf-8") as f:
                data = json.load(f)
                _runtimes = {
                    runtime_id: RuntimeConfig(**config)
                    for runtime_id, config in data.items()
                }
            logger.info(f"Loaded {len(_runtimes)} runtime configurations from {config_path}")
        except Exception as e:
            logger.error(f"Failed to load runtime configurations: {e}")
            _runtimes = {}
    else:
        _runtimes = {}
        logger.info("No existing runtime configurations found")


def _save_runtimes():
    """Save runtime configurations to persistent storage"""
    config_path = Path(RUNTIME_CONFIG_PATH)
    config_path.parent.mkdir(parents=True, exist_ok=True)

    try:
        data = {
            runtime_id: config.model_dump()
            for runtime_id, config in _runtimes.items()
        }
        with open(config_path, "w", encoding="utf-8") as f:
            json.dump(data, f, indent=2, ensure_ascii=False)
        logger.debug(f"Saved {len(_runtimes)} runtime configurations to {config_path}")
    except Exception as e:
        logger.error(f"Failed to save runtime configurations: {e}")


async def _create_runtime_impl() -> dict:
    """Internal implementation to create a runtime"""
    if not kernel_manager:
        return {"error": "Kernel manager not initialized"}

    try:
        # Create kernel
        kernel_id = await kernel_manager.create_kernel()

        # Generate short runtime_id (8 characters, alphanumeric)
        # Ensure uniqueness by checking existing runtimes
        while True:
            runtime_id = _generate_short_id(8)
            if runtime_id not in _runtimes:
                break

        # Create runtime configuration
        config = RuntimeConfig(
            runtime_id=runtime_id,
            kernel_id=kernel_id,
        )

        _runtimes[runtime_id] = config
        _save_runtimes()

        logger.info(f"Created runtime {runtime_id} backed by kernel {kernel_id}")
        return {
            "runtime_id": runtime_id,
            "created_at": config.created_at,
        }

    except Exception as e:
        logger.error(f"Failed to create runtime: {e}\n{traceback.format_exc()}")
        return {"error": str(e), "traceback": traceback.format_exc()}


async def _list_runtimes_impl() -> dict:
    """Internal implementation of list_runtimes with automatic cleanup"""
    if not kernel_manager:
        return {}

    # Check each runtime and remove those with dead kernels
    dead_runtimes = []
    for runtime_id, config in list(_runtimes.items()):  # Use list() to avoid dict size change during iteration
        kernel_id = config.kernel_id
        # Check if kernel exists in kernel manager
        if kernel_id not in kernel_manager.kernel_manager:
            logger.warning(f"Runtime {runtime_id} has dead kernel {kernel_id}, removing from registry")
            dead_runtimes.append(runtime_id)

    # Remove dead runtimes
    if dead_runtimes:
        for runtime_id in dead_runtimes:
            del _runtimes[runtime_id]
        _save_runtimes()
        logger.info(f"Cleaned up {len(dead_runtimes)} dead runtime(s): {dead_runtimes}")

    # Return active runtimes
    return {
        runtime_id: {
            "created_at": config.created_at,
            "last_used": config.last_used,
        }
        for runtime_id, config in _runtimes.items()
    }


async def _delete_runtime_impl(runtime_id: str) -> dict:
    """Internal implementation of delete_runtime"""
    if not kernel_manager:
        return {"error": "Kernel manager not initialized"}

    if runtime_id not in _runtimes:
        return {"error": f"Runtime {runtime_id} not found"}

    try:
        config = _runtimes[runtime_id]
        kernel_id = config.kernel_id

        # Delete kernel
        await kernel_manager.delete_kernel(kernel_id)

        # Remove from runtime registry
        del _runtimes[runtime_id]
        _save_runtimes()

        logger.info(f"Deleted runtime {runtime_id} (kernel {kernel_id})")
        return {"success": f"Runtime {runtime_id} deleted successfully"}

    except Exception as e:
        logger.error(f"Failed to delete runtime: {e}\n{traceback.format_exc()}")
        return {"error": str(e), "traceback": traceback.format_exc()}


async def _restart_runtime_impl(runtime_id: str) -> dict:
    """Internal implementation of restart_runtime"""
    if not kernel_manager:
        return {"error": "Kernel manager not initialized"}

    if runtime_id not in _runtimes:
        return {"error": f"Runtime {runtime_id} not found"}

    try:
        config = _runtimes[runtime_id]
        kernel_id = config.kernel_id

        # Restart kernel
        await kernel_manager.restart_kernel(kernel_id)

        logger.info(f"Restarted runtime {runtime_id} (kernel {kernel_id})")
        return {"success": f"Runtime {runtime_id} restarted successfully"}

    except Exception as e:
        logger.error(f"Failed to restart runtime: {e}\n{traceback.format_exc()}")
        return {"error": str(e), "traceback": traceback.format_exc()}

async def _interrupt_runtime_impl(runtime_id: str) -> dict:
    """Internal implementation of interrupt_runtime"""
    if not kernel_manager:
        return {"error": "Kernel manager not initialized"}

    if runtime_id not in _runtimes:
        return {"error": f"Runtime {runtime_id} not found"}

    try:
        config = _runtimes[runtime_id]
        kernel_id = config.kernel_id

        # Interrupt kernel
        await kernel_manager.interrupt_kernel(kernel_id)

        logger.info(f"Interrupted runtime {runtime_id} (kernel {kernel_id})")
        return {"success": f"Runtime {runtime_id} interrupted successfully"}

    except Exception as e:
        logger.error(f"Failed to interrupt runtime: {e}\n{traceback.format_exc()}")
        return {"error": str(e), "traceback": traceback.format_exc()}


async def _get_runtime_status_impl(runtime_id: str) -> dict:
    """Internal implementation of get_runtime_status"""
    if runtime_id not in _runtimes:
        return {"error": f"Runtime {runtime_id} not found"}

    config = _runtimes[runtime_id]
    kernel_id = config.kernel_id

    # Check if kernel is alive
    kernel_alive = False
    if kernel_manager:
        try:
            km = kernel_manager.get_kernel(kernel_id)
            # Try to check if kernel is responsive
            kernel_alive = await kernel_manager.kernel_manager.is_alive(kernel_id)
        except Exception as e:
            logger.warning(f"Failed to check kernel status: {e}")

    return {
        "runtime_id": runtime_id,
        "kernel_id": kernel_id,
        "kernel_alive": kernel_alive,
        "created_at": config.created_at,
        "last_used": config.last_used,
    }


async def _execute_code_impl(
    runtime_id: str,
    code: str,
    mode: Literal["simple", "full", "debug"] = "full",
    timeout: int = 60,
) -> dict:
    """
    Internal implementation of code execution.

    Args:
        runtime_id: Runtime configuration identifier
        code: Python code to execute
        mode: Output mode (simple, full, debug)
        timeout: Execution timeout in seconds

    Returns:
        Execution result dictionary
    """
    # Get runtime configuration
    if runtime_id not in _runtimes:
        return {
            "status": "error",
            "error": f"Runtime {runtime_id} not found. Please create a runtime first using create_runtime.",
        }

    config = _runtimes[runtime_id]
    kernel_id = config.kernel_id

    if not kernel_manager:
        return {
            "status": "error",
            "error": "Kernel manager not initialized",
        }

    # Generate unique identifier for message tracking
    msg_id = str(uuid.uuid4())

    results = []
    start_time = time.time()
    kc = None

    logger.debug(f"Executing code in kernel {kernel_id} (timeout: {timeout}s)")

    try:
        # Get kernel from manager
        km = kernel_manager.get_kernel(kernel_id)
        logger.debug(f"Got kernel manager for kernel_id: {kernel_id}")

        # Create a client for this kernel
        kc = km.client()
        kc.start_channels()
        logger.debug("Kernel client created and channels started")

        # Wait for kernel to be ready by checking kernel_info
        logger.debug("Waiting for kernel to be ready...")
        try:
            # Wait up to 10 seconds for kernel_info_reply
            # This is CRITICAL - ensures kernel is ready before executing code
            # Note: wait_for_ready may have incorrect type hints in some versions
            await kc.wait_for_ready(timeout=10)  # type: ignore[misc]
            logger.debug("Kernel is ready")
        except Exception as e:
            logger.error(f"Kernel failed to become ready: {e}")
            kc.stop_channels()
            return {
                "status": "error",
                "error": f"Kernel failed to become ready: {e}",
            }

        # Execute code
        logger.debug(f"Executing code (length: {len(code)} chars)")
        msg_id = kc.execute(code, silent=False, store_history=True)
        logger.debug(f"Code execution submitted with msg_id: {msg_id}")

        # Collect results
        results = []
        while True:
            try:
                # Get messages from iopub channel with timeout
                # AsyncKernelClient.get_iopub_msg() is async and needs await
                # Note: jupyter_client has incorrect type hints (says Dict but is actually async)
                msg = await kc.get_iopub_msg(timeout=1)  # type: ignore[misc]

                # Only collect messages for this execution
                if msg.get("parent_header", {}).get("msg_id") != msg_id:
                    logger.debug(f"Skipping message with different msg_id")
                    continue

                results.append(msg)
                logger.debug(f"Received message: {msg['msg_type']}")

                # Check if execution is complete
                if msg["msg_type"] == "status" and msg["content"].get("execution_state") == "idle":
                    logger.debug("Execution completed, kernel is idle")
                    break

            except asyncio.TimeoutError:
                # Handle timeout from get_iopub_msg (no message available)
                # This is normal - just continue waiting
                elapsed = time.time() - start_time
                if elapsed > timeout:
                    logger.error(f"Execution timeout after {timeout} seconds")
                    kc.stop_channels()
                    return {
                        "status": "error",
                        "error": f"Execution timeout after {timeout} seconds",
                        "execution_time": elapsed,
                    }
                continue
            except Exception as e:
                # Handle Empty exception from queue (when no message available)
                # AsyncKernelClient may raise queue.Empty instead of asyncio.TimeoutError
                elapsed = time.time() - start_time

                if type(e).__name__ == 'Empty':
                    # No message available, check for overall timeout
                    if elapsed > timeout:
                        logger.error(f"Execution timeout after {timeout} seconds")
                        kc.stop_channels()
                        return {
                            "status": "error",
                            "error": f"Execution timeout after {timeout} seconds",
                            "execution_time": elapsed,
                        }
                    continue
                else:
                    # Unexpected error - stop execution
                    logger.error(f"Unexpected error during execution: {type(e).__name__}: {e}")
                    logger.error(traceback.format_exc())
                    kc.stop_channels()
                    return {
                        "status": "error",
                        "error": f"Execution failed: {e}",
                        "execution_time": elapsed,
                        "traceback": traceback.format_exc(),
                    }

        # Stop channels
        kc.stop_channels()

        # Update last_used timestamp
        config.last_used = time.time()
        _save_runtimes()

        # Parse results
        logger.debug(f"Parsing {len(results)} execution results")
        response = parse_msg_list_to_tool_response(results, mode)

        return {
            "status": "success",
            "execution_time": time.time() - start_time,
            **response,
        }

    except Exception as e:
        logger.error(f"Execution error: {str(e)}\n{traceback.format_exc()}")
        try:
            if kc is not None:
                kc.stop_channels()
        except:
            pass
        return {
            "status": "error",
            "error": f"Execution failed: {str(e)}",
            "traceback": traceback.format_exc(),
        }


async def _execute_code_tool_impl(
    runtime_id: Optional[str],
    code: str,
    description: str,
    background: bool
) -> dict:
    """Internal implementation of execute_code tool with auto-create and background support"""
    # Auto-create runtime if not provided
    runtime_created = False
    actual_runtime_id: str  # Will be set below

    if runtime_id is None:
        logger.info("No runtime_id provided, creating a new runtime automatically")
        create_result = await _create_runtime_impl()
        if "error" in create_result:
            return create_result  # Return error if creation failed
        actual_runtime_id = create_result["runtime_id"]
        runtime_created = True
        logger.info(f"Auto-created runtime: {actual_runtime_id}")
    else:
        actual_runtime_id = runtime_id

    # Log execution description if provided
    if description:
        logger.info(f"Executing in runtime {actual_runtime_id}: {description}")
    else:
        logger.info(f"Executing code in runtime {actual_runtime_id}")

    if background:
        # For background execution, start task and return immediately
        asyncio.create_task(_execute_code_impl(actual_runtime_id, code))
        return {
            "status": "background",
            "message": "Code execution started in background",
            "runtime_id": actual_runtime_id,
            "runtime_created": runtime_created,
            "description": description,
        }
    else:
        # Synchronous execution
        result = await _execute_code_impl(actual_runtime_id, code)
        result["runtime_id"] = actual_runtime_id
        result["runtime_created"] = runtime_created
        if description:
            result["description"] = description
        return result

def create_mcp_app() -> FastMCP:
    # Initialize MCP server
    mcp_server = FastMCP(
        name="py4agent"
    )

    @mcp_server.tool(
        name="create_runtime",
        description="Create a new isolated Python runtime environment with unique 8-char ID. Returns runtime_id and created_at timestamp."
    )
    async def create_runtime() -> dict:
        """Create a new isolated Python runtime environment."""
        return await _create_runtime_impl()


    @mcp_server.tool(
        name="list_runtimes",
        description="List all active runtimes with their created_at and last_used timestamps. Auto-cleans up dead kernels."
    )
    async def list_runtimes() -> dict:
        """List all active runtime environments and their status."""
        return await _list_runtimes_impl()

    @mcp_server.tool(
        name="delete_runtime",
        description="Permanently delete a runtime and free its resources. All variables and state will be lost."
    )
    async def delete_runtime(input: RuntimeIdInput) -> dict:
        """Permanently delete a runtime and free its resources."""
        return await _delete_runtime_impl(input.runtime_id)



    @mcp_server.tool(
        name="restart_runtime",
        description="Restart a runtime to clear all variables and state. Runtime ID remains the same."
    )
    async def restart_runtime(input: RuntimeIdInput) -> dict:
        """Restart a runtime to clear all variables and state."""
        return await _restart_runtime_impl(input.runtime_id)


    @mcp_server.tool(
        name="interrupt_runtime",
        description="Send interrupt signal (Ctrl+C) to stop currently running code. Runtime stays active and variables are preserved."
    )
    async def interrupt_runtime(input: RuntimeIdInput) -> dict:
        """Stop currently running code execution in a runtime."""
        return await _interrupt_runtime_impl(input.runtime_id)


    @mcp_server.tool(
        name="get_runtime_status",
        description="Get runtime status including kernel_alive, created_at, and last_used timestamps."
    )
    async def get_runtime_status(input: RuntimeIdInput) -> dict:
        """Get detailed status information about a specific runtime."""
        return await _get_runtime_status_impl(input.runtime_id)


    @mcp_server.tool(
        name="execute_code",
        description="Execute Python code in isolated runtime. Auto-creates runtime if not provided. Returns multimodal output: text, tables, plots, images. Set background=true for async execution."
    )
    async def execute_code(input: ExecuteCodeInput) -> dict:
        """Execute Python code in an isolated runtime environment."""
        return await _execute_code_tool_impl(
            input.runtime_id,
            input.code,
            input.description,
            input.background
        )

    return mcp_server


def create_app() -> FastAPI:
    """Create and configure the FastAPI application.

    This function is called by uvicorn in each worker process.
    Each worker will have its own kernel_manager instance and runtime registry.
    """
    global kernel_manager

    # Load persisted runtime configurations
    # Note: In multi-worker mode, each worker loads its own copy
    logger.info(f"Loading runtime configurations from: {RUNTIME_CONFIG_PATH}")
    _load_runtimes()
    logger.info(f"Loaded {len(_runtimes)} runtime(s)")

    # Get MCP app first (we need its lifespan)
    mcp_server = create_mcp_app()
    mcp_app = mcp_server.http_app()
    logger.info("✓ MCP app created")

    # Define combined lifespan that includes both kernel_manager and MCP app's lifespan
    @asynccontextmanager
    async def lifespan(app: FastAPI):
        # Startup Phase
        # 1. Initialize kernel manager first
        global kernel_manager
        logger.info("Initializing Jupyter kernel manager...")
        kernel_manager = JupyterKernelManager()
        await kernel_manager.start()
        logger.info("✓ Jupyter kernel manager started")

        # 2. Enter MCP app's lifespan context
        # FastMCP requires its lifespan to be explicitly managed
        logger.info("Entering MCP app lifespan context...")
        async with mcp_app.lifespan(mcp_app):
            logger.info("✓ MCP app lifespan started")

            yield  # App is running

            logger.info("Exiting MCP app lifespan context...")

        logger.info("✓ MCP app lifespan stopped")

        # 3. Shutdown: Stop kernel manager last
        if kernel_manager:
            logger.info("Stopping Jupyter kernel manager...")
            await kernel_manager.stop()
            logger.info("✓ Jupyter kernel manager stopped")

    # Create FastAPI app with combined lifespan
    app = FastAPI(
        title="py4agent MCP Server",
        description="MCP server with Python code execution capabilities",
        version="0.0.1",
        lifespan=lifespan
    )

    # Mount MCP app at root
    app.mount("/", mcp_app)
    logger.info("✓ MCP app mounted at root")

    return app


# Module-level app instance for uvicorn to import
# Use lazy initialization to avoid creating app during module import
_app_instance: Optional[FastAPI] = None


def _get_or_create_app() -> FastAPI:
    """Get or create the FastAPI application instance (lazy initialization)."""
    global _app_instance
    if _app_instance is None:
        _app_instance = create_app()
    return _app_instance


# Module __getattr__ to provide lazy app initialization
def __getattr__(name: str):
    """Lazy initialization of module-level app for uvicorn workers."""
    if name == "app":
        return _get_or_create_app()
    raise AttributeError(f"module {__name__!r} has no attribute {name!r}")


def main():
    """Main entry point for the MCP server"""
    import argparse
    import os

    # Parse command line arguments
    parser = argparse.ArgumentParser(description="Run the py4agent MCP server")
    parser.add_argument("--host", type=str, default="127.0.0.1", help="Host to bind (default: 127.0.0.1)")
    parser.add_argument("--port", type=int, default=8889, help="Port to bind (default: 8889)")
    parser.add_argument("--debug", action="store_true", help="Enable debug logging")
    parser.add_argument("--workers", type=int, default=1, help="Number of worker processes (default: 1)")
    parser.add_argument("--log-dir", type=str, default=None, help="Directory to store logs (optional)")
    args = parser.parse_args()

    # Configure logging (this affects the main process and will be inherited by workers)
    logger.remove()
    log_level = "DEBUG" if args.debug else "INFO"

    # Add stderr logging
    logger.add(
        sys.stderr,
        format="<green>{time:YYYY-MM-DD HH:mm:ss}</green> | <level>{level: <8}</level> | <cyan>{name}</cyan>:<cyan>{function}</cyan> - <level>{message}</level>",
        level=log_level,
    )

    # Add file logging if log-dir is specified
    if args.log_dir:
        os.makedirs(args.log_dir, exist_ok=True)
        log_file = os.path.join(args.log_dir, "mcp_server.log")
        logger.add(
            log_file,
            format="<green>{time:YYYY-MM-DD HH:mm:ss}</green> | <level>{level: <8}</level> | <cyan>{name}</cyan>:<cyan>{function}</cyan> - <level>{message}</level>",
            level=log_level,
            rotation="100 MB",
            retention="7 days",
        )
        logger.info(f"File logging enabled: {log_file}")

    logger.info("=" * 60)
    logger.info("Starting py4agent MCP server")
    logger.info("=" * 60)

    logger.info("")
    logger.info("Available MCP tools:")
    logger.info("  - create_runtime: Create a new runtime")
    logger.info("  - list_runtimes: List all active runtimes")
    logger.info("  - delete_runtime: Delete a runtime")
    logger.info("  - restart_runtime: Restart a runtime")
    logger.info("  - interrupt_runtime: Interrupt runtime execution")
    logger.info("  - get_runtime_status: Get runtime status")
    logger.info("  - execute_code: Execute Python code in a runtime")
    logger.info("=" * 60)

    # Use command line arguments for host and port
    host = args.host
    port = args.port

    logger.info(f"Starting MCP server on {host}:{port}")
    logger.info(f"  - MCP Protocol: http://{host}:{port}/")

    # MCP protocol limitation: Cannot use multi-worker mode
    if args.workers > 1:
        logger.error("=" * 60)
        logger.error("ERROR: Multi-worker mode (--workers > 1) is NOT supported for MCP server")
        logger.error("")
        logger.error("Reason:")
        logger.error("  MCP protocol uses Server-Sent Events (SSE) for streaming")
        logger.error("  SSE requires stateful long-lived connections")
        logger.error("  Multi-worker mode breaks session continuity")
        logger.error("")
        logger.error("Error symptoms:")
        logger.error("  - 'No valid session ID provided'")
        logger.error("  - Requests routed to different workers")
        logger.error("  - Connection lost during streaming")
        logger.error("")
        logger.error("Solution:")
        logger.error("  Use --workers 1 (single worker mode)")
        logger.error("")
        logger.error("For high concurrency, consider:")
        logger.error("  - Using async I/O (already enabled)")
        logger.error("  - Deploying multiple instances with separate ports")
        logger.error("  - Using a reverse proxy (Nginx) for load balancing")
        logger.error("=" * 60)
        logger.error("")
        logger.error("Forcing single worker mode to avoid session errors...")
        args.workers = 1

    logger.info(f"  - Workers: {args.workers}")
    logger.info("=" * 60)

    # Set uvicorn log level based on debug flag
    uvicorn_log_level = "debug" if args.debug else "info"

    try:
        # Always use single worker mode for MCP server
        app_instance = _get_or_create_app()
        uvicorn.run(
            app_instance,
            host=host,
            port=port,
            log_level=uvicorn_log_level,
        )
    except KeyboardInterrupt:
        logger.info("Shutting down...")
    finally:
        logger.info("py4agent MCP server stopped")


if __name__ == "__main__":
    main()
