"""Remote API-based sandbox implementation."""
from __future__ import annotations

import base64
from pathlib import Path
from typing import Any, Literal

from .types import ExecutionResult, SandboxConfig


class RemoteSandbox:
    """Remote sandbox accessed via HTTP API.
    
    Connects to a sandbox service for SaaS deployments.
    """
    
    def __init__(
        self,
        client: Any,  # httpx.AsyncClient
        api_url: str,
        sandbox_id: str,
        api_key: str,
        config: SandboxConfig,
    ) -> None:
        self._client = client
        self._api_url = api_url
        self._sandbox_id = sandbox_id
        self._api_key = api_key
        self._config = config
        self._status: Literal["creating", "running", "stopped", "failed"] = "running"
    
    @property
    def id(self) -> str:
        return self._sandbox_id
    
    @property
    def status(self) -> Literal["creating", "running", "stopped", "failed"]:
        return self._status
    
    def _headers(self) -> dict[str, str]:
        return {"Authorization": f"Bearer {self._api_key}"}
    
    async def execute(
        self,
        command: str | list[str],
        *,
        timeout: int | None = None,
        stdin: str | None = None,
        env: dict[str, str] | None = None,
        workdir: str | None = None,
    ) -> ExecutionResult:
        """Execute command via API."""
        response = await self._client.post(
            f"{self._api_url}/sandboxes/{self._sandbox_id}/exec",
            headers=self._headers(),
            json={
                "command": command if isinstance(command, str) else " ".join(command),
                "timeout": timeout or self._config.timeout,
                "stdin": stdin,
                "env": env,
                "workdir": workdir or self._config.workdir,
            },
            timeout=timeout or self._config.timeout + 10,
        )
        response.raise_for_status()
        data = response.json()
        
        return ExecutionResult(
            exit_code=data.get("exit_code", 0),
            stdout=data.get("stdout", ""),
            stderr=data.get("stderr", ""),
            duration_ms=data.get("duration_ms", 0),
            timed_out=data.get("timed_out", False),
        )
    
    async def write_file(self, path: str, content: str | bytes) -> None:
        """Write file via API."""
        if isinstance(content, str):
            content = content.encode("utf-8")
        
        response = await self._client.post(
            f"{self._api_url}/sandboxes/{self._sandbox_id}/files",
            headers=self._headers(),
            json={
                "path": path,
                "content": base64.b64encode(content).decode("ascii"),
            },
        )
        response.raise_for_status()
    
    async def read_file(self, path: str) -> bytes:
        """Read file via API."""
        response = await self._client.get(
            f"{self._api_url}/sandboxes/{self._sandbox_id}/files",
            headers=self._headers(),
            params={"path": path},
        )
        response.raise_for_status()
        data = response.json()
        return base64.b64decode(data.get("content", ""))
    
    async def upload(self, local_path: Path, remote_path: str) -> None:
        """Upload file via API."""
        content = local_path.read_bytes()
        await self.write_file(remote_path, content)
    
    async def download(self, remote_path: str, local_path: Path) -> None:
        """Download file via API."""
        content = await self.read_file(remote_path)
        local_path.write_bytes(content)
    
    async def stop(self) -> None:
        """Stop sandbox via API."""
        response = await self._client.post(
            f"{self._api_url}/sandboxes/{self._sandbox_id}/stop",
            headers=self._headers(),
        )
        response.raise_for_status()
        self._status = "stopped"
    
    async def destroy(self) -> None:
        """Destroy sandbox via API."""
        response = await self._client.delete(
            f"{self._api_url}/sandboxes/{self._sandbox_id}",
            headers=self._headers(),
        )
        response.raise_for_status()
        self._status = "stopped"


class RemoteSandboxProvider:
    """Remote sandbox provider via HTTP API.
    
    Creates sandboxes by calling a remote sandbox service.
    Suitable for SaaS deployments with multi-tenancy.
    
    Requires: httpx package (`pip install httpx`)
    """
    
    def __init__(
        self,
        api_url: str,
        api_key: str,
        default_config: SandboxConfig | None = None,
    ) -> None:
        self.api_url = api_url.rstrip("/")
        self.api_key = api_key
        self.default_config = default_config or SandboxConfig()
        self._client: Any = None
    
    async def _get_client(self) -> Any:
        """Lazy-load httpx client."""
        if self._client is None:
            try:
                import httpx
                self._client = httpx.AsyncClient()
            except ImportError:
                raise ImportError(
                    "httpx package required for RemoteSandboxProvider. "
                    "Install with: pip install httpx"
                )
        return self._client
    
    async def create(self, config: SandboxConfig | None = None) -> RemoteSandbox:
        """Create a new remote sandbox."""
        cfg = config or self.default_config
        client = await self._get_client()
        
        response = await client.post(
            f"{self.api_url}/sandboxes",
            headers={"Authorization": f"Bearer {self.api_key}"},
            json={
                "image": cfg.image,
                "timeout": cfg.timeout,
                "memory_limit": cfg.memory_limit,
                "cpu_limit": cfg.cpu_limit,
                "network": cfg.network,
                "env": cfg.env,
                "workdir": cfg.workdir,
            },
        )
        response.raise_for_status()
        data = response.json()
        
        return RemoteSandbox(
            client=client,
            api_url=self.api_url,
            sandbox_id=data["id"],
            api_key=self.api_key,
            config=cfg,
        )
    
    async def close(self) -> None:
        """Close the HTTP client."""
        if self._client:
            await self._client.aclose()
            self._client = None


__all__ = ["RemoteSandbox", "RemoteSandboxProvider"]
