"""Backend manager for TUI application.

This module handles spawning and managing the local API server subprocess.
"""
import asyncio
import logging
import os
import socket
import subprocess  # nosec B404 - used to spawn internal API server
import sys
import time
from pathlib import Path
from typing import Optional

import httpx

from lineage.utils.env import load_env_file

logger = logging.getLogger(__name__)


class BackendManager:
    """Manages the local API server process."""

    def __init__(self):
        """Initialize the backend manager."""
        self.port: int = self._find_free_port()
        self.process: Optional[subprocess.Popen] = None
        self.log_fp: Optional[object] = None
        self.host = "localhost"
        self.base_url = f"http://{self.host}:{self.port}"
        
        # Setup log directory in ~/.typedef/logs (alongside client logs)
        self.log_dir = Path.home() / ".typedef" / "logs"
        self.log_dir.mkdir(parents=True, exist_ok=True)
        self.log_file = self.log_dir / "tui-backend.log"

    def _find_free_port(self) -> int:
        """Find a free port on localhost."""
        with socket.socket(socket.AF_INET, socket.SOCK_STREAM) as s:
            s.bind(("", 0))
            s.listen(1)
            return s.getsockname()[1]

    def start(self):
        """Start the API server subprocess."""
        if self.process:
            return

        load_env_file()
        env = os.environ.copy()
        env["PORT"] = str(self.port)
        # Use GIT_WORKING_DIR from env (set by typedef chat) or fallback to cwd
        if "GIT_WORKING_DIR" not in env:
            env["GIT_WORKING_DIR"] = os.getcwd()
        # Ensure output is unbuffered
        env["PYTHONUNBUFFERED"] = "1"
        
        # Set default config if not provided
        if "UNIFIED_CONFIG" not in env:
            config_path = Path.cwd() / "typedef_data_intelligence" / "config.cli.yml"
            if not config_path.exists():
                # Fallback to root config if not found
                config_path = Path.cwd() / "config.cli.yml"
            
            env["UNIFIED_CONFIG"] = str(config_path)
            logger.info(f"Setting UNIFIED_CONFIG={config_path}")
        
        # Pass project context to backend
        if "TYPEDEF_ACTIVE_PROJECT" in os.environ:
            env["TYPEDEF_ACTIVE_PROJECT"] = os.environ["TYPEDEF_ACTIVE_PROJECT"]
        
        if "TYPEDEF_GRAPH_NAME" in os.environ:
            env["TYPEDEF_GRAPH_NAME"] = os.environ["TYPEDEF_GRAPH_NAME"]

        # Command to run the API server module
        # We use sys.executable to ensure we use the same python environment
        cmd = [
            sys.executable,
            "-m",
            "lineage.api.pydantic",
        ]

        logger.info(f"Starting backend server on port {self.port}")
        logger.info(f"Backend logs -> {self.log_file.absolute()}")
        
        # Open log file for redirection
        self.log_fp = open(self.log_file, "w")
        
        try:
            self.process = subprocess.Popen(  # nosec B603 - cmd is hardcoded, runs internal module
                cmd,
                env=env,
                stdout=self.log_fp,
                stderr=subprocess.STDOUT,  # Redirect stderr to stdout
                text=True,
            )
        except Exception:
            # If Popen fails, close the log file handle to prevent leak
            self.log_fp.close()
            self.log_fp = None
            raise

    def stop(self):
        """Stop the API server subprocess."""
        if self.process:
            logger.info("Stopping backend server...")
            try:
                self.process.terminate()
                try:
                    self.process.wait(timeout=5)
                except subprocess.TimeoutExpired:
                    self.process.kill()
            except Exception as e:
                logger.error(f"Error stopping backend: {e}")
            finally:
                self.process = None
                if hasattr(self, 'log_fp') and self.log_fp:
                    self.log_fp.close()

    async def wait_for_health(self, timeout: int = 30) -> bool:
        """Wait for the server to become healthy."""
        start_time = time.time()
        async with httpx.AsyncClient() as client:
            while time.time() - start_time < timeout:
                try:
                    response = await client.get(f"{self.base_url}/health")
                    if response.status_code == 200:
                        return True
                except httpx.RequestError:
                    pass
                
                # Check if process died
                if self.process is not None and self.process.poll() is not None:
                    logger.error(f"Backend process died unexpectedly. Check logs at {self.log_file}")
                    return False

                await asyncio.sleep(0.5)
        
        return False
