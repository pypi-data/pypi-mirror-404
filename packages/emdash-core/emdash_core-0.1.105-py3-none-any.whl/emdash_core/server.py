"""FastAPI server entry point for emdash-core."""

import argparse
import os
import signal
import sys
from contextlib import asynccontextmanager
from pathlib import Path
from typing import Optional

import uvicorn
from dotenv import load_dotenv
from fastapi import FastAPI
from fastapi.middleware.cors import CORSMiddleware

from .api import api_router
from .config import get_config, set_config


def _load_env_files(repo_root: Optional[str] = None):
    """Load .env files from repo root and user config.

    Uses override=True so .env file takes precedence over shell environment.
    """
    # Also try parent directories to find .env (load first, lower priority)
    current = Path(__file__).parent
    for _ in range(5):
        current = current.parent
        env_path = current / ".env"
        if env_path.exists():
            load_dotenv(env_path, override=True)
            break

    # Load from repo root if provided (highest priority)
    if repo_root:
        env_path = Path(repo_root) / ".env"
        if env_path.exists():
            load_dotenv(env_path, override=True)


def _shutdown_executors():
    """Shutdown all module-level thread pool executors and database connections."""
    from concurrent.futures import ThreadPoolExecutor

    # Import all modules with executors and shut them down
    executor_modules = [
        "emdash_core.api.index",
        "emdash_core.api.auth",
        "emdash_core.api.swarm",
        "emdash_core.api.tasks",
        "emdash_core.api.research",
        "emdash_core.api.spec",
        "emdash_core.api.team",
        "emdash_core.api.review",
        "emdash_core.api.agent",
        "emdash_core.api.projectmd",
        "emdash_core.agent.inprocess_subagent",
    ]

    for module_name in executor_modules:
        try:
            module = sys.modules.get(module_name)
            if module and hasattr(module, "_executor"):
                executor = getattr(module, "_executor")
                if executor and isinstance(executor, ThreadPoolExecutor):
                    executor.shutdown(wait=False)
        except Exception:
            pass  # Ignore errors during shutdown

    # Close database connections
    try:
        from .graph.connection import get_connection, _read_connection
        conn = get_connection()
        if conn:
            conn.close()
        if _read_connection:
            _read_connection.close()
    except Exception:
        pass  # Ignore errors during shutdown


@asynccontextmanager
async def lifespan(app: FastAPI):
    """Application lifespan handler."""
    config = get_config()

    # Startup
    print(f"EmDash Core starting on http://{config.host}:{config.port}")
    if config.repo_root:
        print(f"Repository root: {config.repo_root}")

    # Multiuser is lazily initialized on first /share or /join
    # Just check config to inform the user
    try:
        from .multiuser.config import is_multiuser_enabled, get_multiuser_config
        if is_multiuser_enabled():
            cfg = get_multiuser_config()
            print(f"Multiuser available (provider: {cfg.provider.value})")
        else:
            print("Multiuser disabled")
    except Exception as e:
        print(f"Multiuser config check: {e}")

    # Note: Port file management is handled by ServerManager (per-repo files)

    yield

    # Shutdown
    print("EmDash Core shutting down...")
    _shutdown_executors()


def create_app(
    repo_root: Optional[str] = None,
    host: str = "127.0.0.1",
    port: int = 8765,
) -> FastAPI:
    """Create and configure the FastAPI application."""
    # Load environment variables from .env files
    _load_env_files(repo_root)

    # Set configuration
    set_config(
        host=host,
        port=port,
        repo_root=repo_root,
    )

    app = FastAPI(
        title="EmDash Core",
        description="FastAPI server for code intelligence",
        version="0.1.0",
        lifespan=lifespan,
    )

    # CORS middleware for Electron app
    app.add_middleware(
        CORSMiddleware,
        allow_origins=["*"],  # Allow all origins for local development
        allow_credentials=True,
        allow_methods=["*"],
        allow_headers=["*"],
    )

    # Include API routes
    app.include_router(api_router)

    return app


def main():
    """Main entry point for the server."""
    parser = argparse.ArgumentParser(description="EmDash Core Server")
    parser.add_argument(
        "--host",
        default="127.0.0.1",
        help="Host to bind to (default: 127.0.0.1)"
    )
    parser.add_argument(
        "--port",
        type=int,
        default=8765,
        help="Port to bind to (default: 8765)"
    )
    parser.add_argument(
        "--repo-root",
        help="Repository root path"
    )
    parser.add_argument(
        "--reload",
        action="store_true",
        help="Enable auto-reload for development"
    )

    args = parser.parse_args()

    # Handle graceful shutdown
    def signal_handler(signum, frame):
        print("\nReceived shutdown signal...")
        sys.exit(0)

    signal.signal(signal.SIGINT, signal_handler)
    signal.signal(signal.SIGTERM, signal_handler)

    # Create app
    app = create_app(
        repo_root=args.repo_root,
        host=args.host,
        port=args.port,
    )

    # Run server
    uvicorn.run(
        app,
        host=args.host,
        port=args.port,
        reload=args.reload,
    )


if __name__ == "__main__":
    main()
