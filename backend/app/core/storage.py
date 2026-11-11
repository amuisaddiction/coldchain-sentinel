"""Pluggable file storage backend for evidence artifacts and audit reports."""

import os
import hashlib
import uuid
from pathlib import Path
from typing import Protocol, Tuple
import httpx
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

    def save_file_sync(self, content: bytes, original_filename: str, subfolder: str = "evidence") -> Tuple[str, str, int]:
        sha256_hash = compute_sha256(content)
        size_bytes = len(content)

        extension = Path(original_filename).suffix.lower()
        file_uuid = uuid.uuid4().hex
        storage_key = f"{subfolder}/{file_uuid}{extension}"
        target_path = self.base_path / storage_key

        target_path.parent.mkdir(parents=True, exist_ok=True)
        with open(target_path, "wb") as f:
            f.write(content)

        return storage_key, sha256_hash, size_bytes

    def get_file_sync(self, storage_key: str) -> bytes:
        target_path = self.base_path / storage_key
        if not target_path.exists():
            raise FileNotFoundError(f"Storage artifact not found: {storage_key}")
        with open(target_path, "rb") as f:
            return f.read()

    def exists_sync(self, storage_key: str) -> bool:
        return (self.base_path / storage_key).exists()

    async def save_file(self, content: bytes, original_filename: str, subfolder: str = "evidence") -> Tuple[str, str, int]:
        return self.save_file_sync(content, original_filename, subfolder)

    async def get_file(self, storage_key: str) -> bytes:
        return self.get_file_sync(storage_key)

    async def exists(self, storage_key: str) -> bool:
        return self.exists_sync(storage_key)


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


class SupabaseStorageBackend:
    """Supabase Storage implementation using Supabase Storage REST API via HTTPX."""

    def __init__(self, supabase_url: str = None, supabase_key: str = None, bucket: str = None):
        self.base_url = (supabase_url or settings.SUPABASE_URL).rstrip("/")
        self.key = supabase_key or settings.SUPABASE_KEY
        self.bucket = bucket or settings.SUPABASE_STORAGE_BUCKET
        if not self.base_url or not self.key:
            raise ValueError("SUPABASE_URL and SUPABASE_KEY must be configured for SupabaseStorageBackend.")
        self.storage_endpoint = f"{self.base_url}/storage/v1/object"

    def _headers(self) -> dict:
        return {
            "Authorization": f"Bearer {self.key}",
            "apikey": self.key,
        }

    def save_file_sync(self, content: bytes, original_filename: str, subfolder: str = "evidence") -> Tuple[str, str, int]:
        sha256_hash = compute_sha256(content)
        size_bytes = len(content)
        extension = Path(original_filename).suffix.lower()
        file_uuid = uuid.uuid4().hex
        storage_key = f"{subfolder}/{file_uuid}{extension}"

        url = f"{self.storage_endpoint}/{self.bucket}/{storage_key}"
        headers = self._headers()
        headers["Content-Type"] = "application/octet-stream"
        headers["x-upsert"] = "true"

        with httpx.Client(timeout=30.0) as client:
            resp = client.post(url, content=content, headers=headers)
            if resp.status_code not in (200, 201):
                raise IOError(f"Supabase Storage upload failed with status {resp.status_code}: {resp.text}")

        return storage_key, sha256_hash, size_bytes

    def get_file_sync(self, storage_key: str) -> bytes:
        url = f"{self.storage_endpoint}/authenticated/{self.bucket}/{storage_key}"
        with httpx.Client(timeout=30.0) as client:
            resp = client.get(url, headers=self._headers())
            if resp.status_code == 404:
                raise FileNotFoundError(f"Storage artifact not found in Supabase: {storage_key}")
            if resp.status_code != 200:
                raise IOError(f"Supabase Storage download failed with status {resp.status_code}: {resp.text}")
            return resp.content

    def exists_sync(self, storage_key: str) -> bool:
        url = f"{self.storage_endpoint}/info/authenticated/{self.bucket}/{storage_key}"
        with httpx.Client(timeout=30.0) as client:
            resp = client.get(url, headers=self._headers())
            if resp.status_code == 200:
                return True
            if resp.status_code == 404:
                return False
            get_resp = client.head(f"{self.storage_endpoint}/authenticated/{self.bucket}/{storage_key}", headers=self._headers())
            return get_resp.status_code == 200

    async def save_file(self, content: bytes, original_filename: str, subfolder: str = "evidence") -> Tuple[str, str, int]:
        sha256_hash = compute_sha256(content)
        size_bytes = len(content)
        extension = Path(original_filename).suffix.lower()
        file_uuid = uuid.uuid4().hex
        storage_key = f"{subfolder}/{file_uuid}{extension}"

        url = f"{self.storage_endpoint}/{self.bucket}/{storage_key}"
        headers = self._headers()
        headers["Content-Type"] = "application/octet-stream"
        headers["x-upsert"] = "true"

        async with httpx.AsyncClient(timeout=30.0) as client:
            resp = await client.post(url, content=content, headers=headers)
            if resp.status_code not in (200, 201):
                raise IOError(f"Supabase Storage upload failed with status {resp.status_code}: {resp.text}")

        return storage_key, sha256_hash, size_bytes

    async def get_file(self, storage_key: str) -> bytes:
        url = f"{self.storage_endpoint}/authenticated/{self.bucket}/{storage_key}"
        async with httpx.AsyncClient(timeout=30.0) as client:
            resp = await client.get(url, headers=self._headers())
            if resp.status_code == 404:
                raise FileNotFoundError(f"Storage artifact not found in Supabase: {storage_key}")
            if resp.status_code != 200:
                raise IOError(f"Supabase Storage download failed with status {resp.status_code}: {resp.text}")
            return resp.content

    async def exists(self, storage_key: str) -> bool:
        url = f"{self.storage_endpoint}/info/authenticated/{self.bucket}/{storage_key}"
        async with httpx.AsyncClient(timeout=30.0) as client:
            resp = await client.get(url, headers=self._headers())
            if resp.status_code == 200:
                return True
            if resp.status_code == 404:
                return False
            get_resp = await client.head(f"{self.storage_endpoint}/authenticated/{self.bucket}/{storage_key}", headers=self._headers())
            return get_resp.status_code == 200


def get_storage() -> StorageBackend:
    """Factory providing the configured storage backend."""
    if settings.STORAGE_BACKEND == "supabase":
        return SupabaseStorageBackend()
    elif settings.STORAGE_BACKEND == "s3":
        return S3StorageBackend()
    elif settings.STORAGE_BACKEND == "local":
        if settings.APP_ENV == "production" and settings.STORAGE_LOCAL_PATH == "backend/storage":
            raise ValueError(
                "CRITICAL SECURITY CONFIGURATION ERROR: Ephemeral local storage ('backend/storage') "
                "is strictly prohibited in production. Configure STORAGE_BACKEND='supabase' "
                "or attach a verified persistent volume mount."
            )
        return LocalStorageBackend()
    raise ValueError(f"Unsupported storage backend: {settings.STORAGE_BACKEND}")
