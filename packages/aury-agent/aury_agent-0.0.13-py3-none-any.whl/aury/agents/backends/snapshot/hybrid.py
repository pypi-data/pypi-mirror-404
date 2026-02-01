"""Git + S3 hybrid snapshot backend."""
from __future__ import annotations

import asyncio
from datetime import datetime
from pathlib import Path
from typing import Any

from .git import GitSnapshotBackend


class GitS3HybridBackend(GitSnapshotBackend):
    """Git + S3 hybrid snapshot backend.
    
    Combines local Git commits with S3 bundle uploads for remote persistence.
    """
    
    def __init__(
        self,
        worktree: str | Path,
        s3_bucket: str,
        session_id: str,
        snapshot_dir: str | Path | None = None,
        s3_client: Any | None = None,
    ):
        super().__init__(worktree, snapshot_dir)
        self.s3_bucket = s3_bucket
        self.session_id = session_id
        self._s3 = s3_client
        self._last_uploaded_commit: str | None = None
    
    @property
    def s3(self):
        if self._s3 is None:
            try:
                import boto3
                self._s3 = boto3.client('s3')
            except ImportError:
                raise ImportError("boto3 is required for GitS3HybridBackend")
        return self._s3
    
    async def track(self) -> str:
        import json
        commit_id = await super().track()
        bundle_path = self.snapshot_dir / f"{commit_id}.bundle"
        
        if self._last_uploaded_commit:
            await self._create_bundle(bundle_path, f"{self._last_uploaded_commit}..{commit_id}")
            bundle_type = "incremental"
        else:
            await self._create_bundle(bundle_path, commit_id)
            bundle_type = "full"
        
        s3_key = f"agents/{self.session_id}/snapshots/{commit_id}.bundle"
        loop = asyncio.get_event_loop()
        await loop.run_in_executor(None, lambda: self.s3.upload_file(str(bundle_path), self.s3_bucket, s3_key))
        
        meta = {
            "commit_id": commit_id,
            "parent_commit": self._last_uploaded_commit,
            "timestamp": datetime.now().isoformat(),
            "bundle_type": bundle_type,
        }
        meta_key = f"agents/{self.session_id}/snapshots/{commit_id}.meta.json"
        await loop.run_in_executor(None, lambda: self.s3.put_object(Bucket=self.s3_bucket, Key=meta_key, Body=json.dumps(meta)))
        
        if bundle_path.exists():
            bundle_path.unlink()
        
        self._last_uploaded_commit = commit_id
        return commit_id
    
    async def _create_bundle(self, path: Path, ref: str) -> None:
        proc = await asyncio.create_subprocess_exec(
            "git", "bundle", "create", str(path), ref,
            cwd=str(self.worktree),
            env={"GIT_DIR": str(self.snapshot_dir)},
            stdout=asyncio.subprocess.PIPE,
            stderr=asyncio.subprocess.PIPE,
        )
        await proc.wait()
    
    @classmethod
    async def restore_from_s3(
        cls,
        s3_bucket: str,
        session_id: str,
        local_dir: str | Path,
        s3_client: Any | None = None,
    ) -> "GitS3HybridBackend":
        import subprocess
        if s3_client is None:
            import boto3
            s3_client = boto3.client('s3')
        
        prefix = f"agents/{session_id}/snapshots/"
        response = s3_client.list_objects_v2(Bucket=s3_bucket, Prefix=prefix)
        bundles = sorted([obj['Key'] for obj in response.get('Contents', []) if obj['Key'].endswith('.bundle')])
        
        if not bundles:
            raise ValueError(f"No snapshots found for session: {session_id}")
        
        local_path = Path(local_dir)
        local_path.mkdir(parents=True, exist_ok=True)
        repo_path = local_path / "repo"
        
        for i, bundle_key in enumerate(bundles):
            bundle_file = local_path / "temp.bundle"
            s3_client.download_file(s3_bucket, bundle_key, str(bundle_file))
            if i == 0:
                subprocess.run(["git", "clone", str(bundle_file), str(repo_path)], check=True, capture_output=True)
            else:
                subprocess.run(["git", "fetch", str(bundle_file)], cwd=str(repo_path), check=True, capture_output=True)
            bundle_file.unlink()
        
        result = subprocess.run(["git", "rev-parse", "HEAD"], cwd=str(repo_path), capture_output=True, text=True)
        last_commit = result.stdout.strip()
        
        backend = cls(worktree=repo_path, s3_bucket=s3_bucket, session_id=session_id, snapshot_dir=repo_path / ".git", s3_client=s3_client)
        backend._last_uploaded_commit = last_commit
        backend._initialized = True
        return backend


__all__ = ["GitS3HybridBackend"]
