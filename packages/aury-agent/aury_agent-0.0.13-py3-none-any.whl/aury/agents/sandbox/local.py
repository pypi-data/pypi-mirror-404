"""Local Docker-based sandbox implementation."""
from __future__ import annotations

import asyncio
import os
import tarfile
import time
from io import BytesIO
from pathlib import Path
from typing import Any, Literal

from .types import ExecutionResult, SandboxConfig


class LocalSandbox:
    """Local Docker-based sandbox implementation.
    
    Uses Docker containers for isolation. Requires Docker to be installed
    and accessible via the Docker socket.
    """
    
    def __init__(self, container: Any, config: SandboxConfig) -> None:
        self._container = container
        self._config = config
        self._status: Literal["creating", "running", "stopped", "failed"] = "running"
    
    @property
    def id(self) -> str:
        return self._container.id
    
    @property
    def status(self) -> Literal["creating", "running", "stopped", "failed"]:
        return self._status
    
    async def execute(
        self,
        command: str | list[str],
        *,
        timeout: int | None = None,
        stdin: str | None = None,
        env: dict[str, str] | None = None,
        workdir: str | None = None,
    ) -> ExecutionResult:
        """Execute command in Docker container."""
        if isinstance(command, list):
            cmd = command
        else:
            cmd = ["/bin/sh", "-c", command]
        
        work_dir = workdir or self._config.workdir
        effective_timeout = timeout or self._config.timeout
        start_time = time.time()
        
        def _exec() -> tuple[int, bytes]:
            exec_result = self._container.exec_run(
                cmd=cmd,
                environment=env,
                workdir=work_dir,
                stdin=stdin is not None,
                demux=True,
            )
            return exec_result.exit_code, exec_result.output
        
        try:
            loop = asyncio.get_event_loop()
            exit_code, output = await asyncio.wait_for(
                loop.run_in_executor(None, _exec),
                timeout=effective_timeout,
            )
            
            stdout = ""
            stderr = ""
            if output:
                if isinstance(output, tuple):
                    stdout = (output[0] or b"").decode("utf-8", errors="replace")
                    stderr = (output[1] or b"").decode("utf-8", errors="replace")
                else:
                    stdout = output.decode("utf-8", errors="replace")
            
            return ExecutionResult(
                exit_code=exit_code or 0,
                stdout=stdout,
                stderr=stderr,
                duration_ms=int((time.time() - start_time) * 1000),
            )
            
        except asyncio.TimeoutError:
            return ExecutionResult(
                exit_code=-1,
                stdout="",
                stderr=f"Command timed out after {effective_timeout}s",
                duration_ms=effective_timeout * 1000,
                timed_out=True,
            )
    
    async def write_file(self, path: str, content: str | bytes) -> None:
        """Write file to container using tar archive."""
        if isinstance(content, str):
            content = content.encode("utf-8")
        
        def _write() -> None:
            tar_stream = BytesIO()
            with tarfile.open(fileobj=tar_stream, mode="w") as tar:
                file_info = tarfile.TarInfo(name=os.path.basename(path))
                file_info.size = len(content)
                tar.addfile(file_info, BytesIO(content))
            tar_stream.seek(0)
            self._container.put_archive(os.path.dirname(path) or "/", tar_stream)
        
        loop = asyncio.get_event_loop()
        await loop.run_in_executor(None, _write)
    
    async def read_file(self, path: str) -> bytes:
        """Read file from container using tar archive."""
        def _read() -> bytes:
            bits, _ = self._container.get_archive(path)
            tar_stream = BytesIO()
            for chunk in bits:
                tar_stream.write(chunk)
            tar_stream.seek(0)
            
            with tarfile.open(fileobj=tar_stream, mode="r") as tar:
                member = tar.getmembers()[0]
                f = tar.extractfile(member)
                if f:
                    return f.read()
                return b""
        
        loop = asyncio.get_event_loop()
        return await loop.run_in_executor(None, _read)
    
    async def upload(self, local_path: Path, remote_path: str) -> None:
        """Upload file/directory to container."""
        def _upload() -> None:
            tar_stream = BytesIO()
            with tarfile.open(fileobj=tar_stream, mode="w") as tar:
                tar.add(str(local_path), arcname=os.path.basename(remote_path))
            tar_stream.seek(0)
            dest_dir = os.path.dirname(remote_path) or "/"
            self._container.put_archive(dest_dir, tar_stream)
        
        loop = asyncio.get_event_loop()
        await loop.run_in_executor(None, _upload)
    
    async def download(self, remote_path: str, local_path: Path) -> None:
        """Download file/directory from container."""
        def _download() -> None:
            bits, _ = self._container.get_archive(remote_path)
            tar_stream = BytesIO()
            for chunk in bits:
                tar_stream.write(chunk)
            tar_stream.seek(0)
            with tarfile.open(fileobj=tar_stream, mode="r") as tar:
                tar.extractall(str(local_path.parent))
        
        loop = asyncio.get_event_loop()
        await loop.run_in_executor(None, _download)
    
    async def stop(self) -> None:
        """Stop container."""
        def _stop() -> None:
            self._container.stop()
        
        loop = asyncio.get_event_loop()
        await loop.run_in_executor(None, _stop)
        self._status = "stopped"
    
    async def destroy(self) -> None:
        """Remove container."""
        def _remove() -> None:
            self._container.remove(force=True)
        
        loop = asyncio.get_event_loop()
        await loop.run_in_executor(None, _remove)
        self._status = "stopped"


class LocalSandboxProvider:
    """Local Docker-based sandbox provider.
    
    Creates sandboxes using local Docker installation.
    Suitable for CLI usage and development.
    
    Requires: docker package (`pip install docker`)
    """
    
    def __init__(
        self,
        docker_socket: str = "unix:///var/run/docker.sock",
        default_config: SandboxConfig | None = None,
    ) -> None:
        self.docker_socket = docker_socket
        self.default_config = default_config or SandboxConfig()
        self._client: Any = None
    
    def _get_client(self) -> Any:
        """Lazy-load Docker client."""
        if self._client is None:
            try:
                import docker
                self._client = docker.DockerClient(base_url=self.docker_socket)
            except ImportError:
                raise ImportError(
                    "docker package required for LocalSandboxProvider. "
                    "Install with: pip install docker"
                )
        return self._client
    
    async def create(self, config: SandboxConfig | None = None) -> LocalSandbox:
        """Create a new Docker-based sandbox."""
        cfg = config or self.default_config
        client = self._get_client()
        
        def _create() -> Any:
            volumes = {}
            for host, container in cfg.volumes.items():
                volumes[host] = {"bind": container, "mode": "rw"}
            
            container = client.containers.run(
                image=cfg.image,
                detach=True,
                mem_limit=cfg.memory_limit,
                cpu_period=100000,
                cpu_quota=int(cfg.cpu_limit * 100000),
                network_disabled=not cfg.network,
                volumes=volumes or None,
                environment=cfg.env or None,
                working_dir=cfg.workdir,
                command="sleep infinity",
            )
            return container
        
        loop = asyncio.get_event_loop()
        container = await loop.run_in_executor(None, _create)
        
        return LocalSandbox(container, cfg)


__all__ = ["LocalSandbox", "LocalSandboxProvider"]
