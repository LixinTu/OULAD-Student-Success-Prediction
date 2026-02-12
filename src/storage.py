"""Storage abstraction for local and cloud object stores."""

from __future__ import annotations

import mimetypes
from abc import ABC, abstractmethod
from pathlib import Path


class Storage(ABC):
    @abstractmethod
    def put_text(self, key: str, content: str, content_type: str = "text/plain") -> None:
        """Store text content by key."""

    @abstractmethod
    def put_file(self, local_path: Path | str, key: str, content_type: str | None = None) -> None:
        """Store a local file by key."""

    @abstractmethod
    def exists(self, key: str) -> bool:
        """Check if a target key exists."""


class LocalStorage(Storage):
    """Filesystem-backed storage."""

    def __init__(self, base_path: Path) -> None:
        self.base_path = base_path

    def _resolve(self, key: str) -> Path:
        return self.base_path / key

    def put_text(self, key: str, content: str, content_type: str = "text/plain") -> None:
        del content_type
        target = self._resolve(key)
        target.parent.mkdir(parents=True, exist_ok=True)
        target.write_text(content)

    def put_file(self, local_path: Path | str, key: str, content_type: str | None = None) -> None:
        del content_type
        src = Path(local_path)
        target = self._resolve(key)
        target.parent.mkdir(parents=True, exist_ok=True)
        target.write_bytes(src.read_bytes())

    def exists(self, key: str) -> bool:
        return self._resolve(key).exists()


class S3Storage(Storage):
    """boto3-backed S3 storage implementation."""

    def __init__(self, bucket: str, region: str, prefix: str = "") -> None:
        if not bucket:
            raise ValueError("S3 bucket must be provided when using STORAGE_BACKEND=s3")
        import boto3

        self.bucket = bucket
        self.prefix = prefix.strip("/")
        self.client = boto3.client("s3", region_name=region)

    def _object_key(self, key: str) -> str:
        key = key.lstrip("/")
        if not self.prefix:
            return key
        return f"{self.prefix}/{key}"

    def put_text(self, key: str, content: str, content_type: str = "text/plain") -> None:
        self.client.put_object(
            Bucket=self.bucket,
            Key=self._object_key(key),
            Body=content.encode("utf-8"),
            ContentType=content_type,
        )

    def put_file(self, local_path: Path | str, key: str, content_type: str | None = None) -> None:
        src = Path(local_path)
        extra_args: dict[str, str] = {}
        guessed = content_type or mimetypes.guess_type(src.name)[0]
        if guessed:
            extra_args["ContentType"] = guessed

        self.client.upload_file(
            str(src),
            self.bucket,
            self._object_key(key),
            ExtraArgs=extra_args or None,
        )

    def exists(self, key: str) -> bool:
        try:
            self.client.head_object(Bucket=self.bucket, Key=self._object_key(key))
            return True
        except Exception as exc:
            from botocore.exceptions import ClientError

            if not isinstance(exc, ClientError):
                raise
            error_code = exc.response.get("Error", {}).get("Code")
            if error_code in {"404", "NoSuchKey", "NotFound"}:
                return False
            raise
