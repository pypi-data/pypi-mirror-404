"""File backend for file system operations.

Supports different file systems:
- Local file system
- Sandbox file system
- S3/Cloud storage
"""
from .types import FileBackend
from .local import LocalFileBackend

__all__ = ["FileBackend", "LocalFileBackend"]
