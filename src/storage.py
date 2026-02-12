"""Storage abstraction for local and cloud object stores."""

from __future__ import annotations

from abc import ABC, abstractmethod
from pathlib import Path


class Storage(ABC):
    @abstractmethod
    def write_text(self, path: str, content: str) -> None:
        """Write text content to a target path."""

    @abstractmethod
    def exists(self, path: str) -> bool:
        """Check if a target path exists."""


class LocalStorage(Storage):
    """Filesystem-backed storage."""

    def __init__(self, base_path: Path) -> None:
        self.base_path = base_path

    def _resolve(self, path: str) -> Path:
        return self.base_path / path

    def write_text(self, path: str, content: str) -> None:
        target = self._resolve(path)
        target.parent.mkdir(parents=True, exist_ok=True)
        target.write_text(content)

    def exists(self, path: str) -> bool:
        return self._resolve(path).exists()


class S3Storage(Storage):
    """S3-ready stub for cloud deployments.

    This class intentionally does not perform network operations in local mode.
    Replace methods with boto3 implementation when cloud credentials are available.
    """

    def __init__(self, bucket: str, prefix: str = "") -> None:
        self.bucket = bucket
        self.prefix = prefix.strip("/")

    def write_text(self, path: str, content: str) -> None:
        raise NotImplementedError(
            "S3Storage is a stub in this repo. Implement boto3 put_object for production use."
        )

    def exists(self, path: str) -> bool:
        raise NotImplementedError(
            "S3Storage is a stub in this repo. Implement boto3 head_object for production use."
        )
