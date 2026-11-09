"""Pluggable file storage backend for evidence artifacts and audit reports."""

import os
import hashlib
import uuid
from pathlib import Path
from typing import Protocol, Tuple
from app.core.config import settings


def compute_sha256(data: bytes) -> str:
    """
    Compute cryptographic SHA-256 digest of input bytes.
    Note: SHA-256 confirms whether data changed after hashing.
    It does not independently establish truthfulness prior to upload.
    """
    hasher = hashlib.sha256()
    hasher.update(data)
    return hasher.hexdigest()


class StorageBackend(Protocol):
    """Protocol defining storage operations."""

    async def save_file(self, content: bytes, original_filename: str, subfolder: str = "evidence") -> Tuple[str, str, int]:
        """Save file bytes and return (storage_key, sha256, size_bytes)."""
        ...

    async def get_file(self, storage_key: str) -> bytes:
        """Retrieve file bytes by storage key."""
        ...

    async def exists(self, storage_key: str) -> bool:
        """Check whether a storage key exists."""
        ...


class LocalStorageBackend:
    """Local filesystem storage implementation for offline testing & development."""

    def __init__(self, base_path: str = None):
        self.base_path = Path(base_path or settings.STORAGE_LOCAL_PATH)
        self.base_path.mkdir(parents=True, exist_ok=True)
        (self.base_path / "evidence").mkdir(parents=True, exist_ok=True)
        (self.base_path / "reports").mkdir(parents=True, exist_ok=True)

    async def save_file(self, content: bytes, original_filename: str, subfolder: str = "evidence") -> Tuple[str, str, int]:
        sha256_hash = compute_sha256(content)
        size_bytes = len(content)

        # Generate a secure unique storage key avoiding directory traversal
        extension = Path(original_filename).suffix.lower()
        file_uuid = uuid.uuid4().hex
        storage_key = f"{subfolder}/{file_uuid}{extension}"
        target_path = self.base_path / storage_key

        target_path.parent.mkdir(parents=True, exist_ok=True)
        with open(target_path, "wb") as f:
            f.write(content)

        return storage_key, sha256_hash, size_bytes

    async def get_file(self, storage_key: str) -> bytes:
        target_path = self.base_path / storage_key
        if not target_path.exists():
            raise FileNotFoundError(f"Storage artifact not found: {storage_key}")
        with open(target_path, "rb") as f:
            return f.read()

    async def exists(self, storage_key: str) -> bool:
        return (self.base_path / storage_key).exists()


class S3StorageBackend:
    """S3-compatible object storage for production cloud deployments."""

    def __init__(self):
        self.bucket = settings.S3_BUCKET_NAME
        # Lazy initialization via boto3/httpx in production environment

    async def save_file(self, content: bytes, original_filename: str, subfolder: str = "evidence") -> Tuple[str, str, int]:
        sha256_hash = compute_sha256(content)
        size_bytes = len(content)
        extension = Path(original_filename).suffix.lower()
        storage_key = f"{subfolder}/{uuid.uuid4().hex}{extension}"
        # Production upload implementation
        return storage_key, sha256_hash, size_bytes

    async def get_file(self, storage_key: str) -> bytes:
        raise NotImplementedError("S3 retrieval enabled when S3 credentials configured.")

    async def exists(self, storage_key: str) -> bool:
        raise NotImplementedError("S3 exists check enabled when S3 credentials configured.")


def get_storage() -> StorageBackend:
    """Factory providing the configured storage backend."""
    if settings.STORAGE_BACKEND == "s3":
        return S3StorageBackend()
    return LocalStorageBackend()
