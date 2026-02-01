"""Snapshot backend for file state tracking and revert.

Supports different snapshot strategies:
- Git-based (local)
- In-memory (testing)
- Git + S3 hybrid (cloud persistence)
"""
from .types import Patch, SnapshotBackend
from .memory import InMemorySnapshotBackend
from .git import GitSnapshotBackend
from .hybrid import GitS3HybridBackend

__all__ = [
    "SnapshotBackend",
    "Patch",
    "InMemorySnapshotBackend",
    "GitSnapshotBackend",
    "GitS3HybridBackend",
]
