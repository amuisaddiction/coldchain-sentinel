"""Tests for Local and Supabase Storage backends, SHA-256 integrity, and production safety guards."""

import pytest
import httpx
from app.core.config import settings
from app.core.storage import (
    compute_sha256,
    LocalStorageBackend,
    SupabaseStorageBackend,
    get_storage,
)


def test_local_storage_backend_sync_operations(tmp_path):
    """Verify local storage save, get, exists, and tamper detection."""
    backend = LocalStorageBackend(base_path=str(tmp_path))
    content = b"timestamp,temperature\n2026-11-01T00:00:00Z,4.5\n"
    expected_hash = compute_sha256(content)

    key, sha256_digest, size = backend.save_file_sync(content, "telemetry.csv", "evidence")
    assert sha256_digest == expected_hash
    assert size == len(content)
    assert backend.exists_sync(key) is True

    retrieved = backend.get_file_sync(key)
    assert retrieved == content
    assert compute_sha256(retrieved) == expected_hash

    # Missing file raises FileNotFoundError
    with pytest.raises(FileNotFoundError):
        backend.get_file_sync("evidence/non_existent.csv")


def test_supabase_storage_missing_credentials_guard():
    """Verify SupabaseStorageBackend raises ValueError if credentials are not configured."""
    with pytest.raises(ValueError, match="SUPABASE_URL and SUPABASE_KEY must be configured"):
        SupabaseStorageBackend(supabase_url="", supabase_key="")


def test_supabase_storage_sync_upload_and_download(monkeypatch):
    """Verify Supabase Storage upload, download, and exists checks via HTTPX mock transport."""
    mock_db = {}
    mock_url = "https://mock-test.supabase.co"
    mock_key = "mock-supabase-service-key"
    bucket = "evidence"

    def mock_handler(request: httpx.Request) -> httpx.Response:
        url_path = request.url.path
        # Auth header check
        assert request.headers.get("Authorization") == f"Bearer {mock_key}"
        assert request.headers.get("apikey") == mock_key

        if request.method == "POST" and f"/storage/v1/object/{bucket}/" in url_path:
            storage_key = url_path.split(f"/storage/v1/object/{bucket}/")[-1]
            mock_db[storage_key] = request.content
            return httpx.Response(200, json={"Key": storage_key})

        elif request.method == "GET" and f"/storage/v1/object/authenticated/{bucket}/" in url_path:
            storage_key = url_path.split(f"/storage/v1/object/authenticated/{bucket}/")[-1]
            if storage_key in mock_db:
                return httpx.Response(200, content=mock_db[storage_key])
            return httpx.Response(404, json={"error": "Not found"})

        elif request.method in ("GET", "HEAD") and f"/storage/v1/object/info/authenticated/{bucket}/" in url_path:
            storage_key = url_path.split(f"/storage/v1/object/info/authenticated/{bucket}/")[-1]
            if storage_key in mock_db:
                return httpx.Response(200, json={"name": storage_key})
            return httpx.Response(404, json={"error": "Not found"})

        return httpx.Response(400, json={"error": "Unhandled mock route"})

    transport = httpx.MockTransport(mock_handler)
    _real_client = httpx.Client
    monkeypatch.setattr(httpx, "Client", lambda *args, **kwargs: _real_client(transport=transport))

    supabase_backend = SupabaseStorageBackend(
        supabase_url=mock_url,
        supabase_key=mock_key,
        bucket=bucket,
    )

    test_content = b"sensor_id,temp\nSENSOR-01,3.8\n"
    expected_hash = compute_sha256(test_content)

    # 1. Save / Upload
    key, computed_hash, size = supabase_backend.save_file_sync(test_content, "sensor_readings.csv")
    assert computed_hash == expected_hash
    assert size == len(test_content)
    assert key.startswith("evidence/")

    # 2. Exists
    assert supabase_backend.exists_sync(key) is True
    assert supabase_backend.exists_sync("evidence/missing-file.csv") is False

    # 3. Retrieve
    retrieved_bytes = supabase_backend.get_file_sync(key)
    assert retrieved_bytes == test_content
    assert compute_sha256(retrieved_bytes) == expected_hash

    # 4. Missing file raises FileNotFoundError
    with pytest.raises(FileNotFoundError):
        supabase_backend.get_file_sync("evidence/missing-file.csv")


def test_production_ephemeral_storage_security_guard(monkeypatch):
    """Verify that using local ephemeral storage in production raises a security configuration error."""
    monkeypatch.setattr(settings, "APP_ENV", "production")
    monkeypatch.setattr(settings, "STORAGE_BACKEND", "local")
    monkeypatch.setattr(settings, "STORAGE_LOCAL_PATH", "backend/storage")

    with pytest.raises(ValueError, match="CRITICAL SECURITY CONFIGURATION ERROR: Ephemeral local storage"):
        get_storage()


def test_production_supabase_storage_selection(monkeypatch):
    """Verify that STORAGE_BACKEND='supabase' returns SupabaseStorageBackend."""
    monkeypatch.setattr(settings, "STORAGE_BACKEND", "supabase")
    monkeypatch.setattr(settings, "SUPABASE_URL", "https://xyz.supabase.co")
    monkeypatch.setattr(settings, "SUPABASE_KEY", "test-key-123")
    monkeypatch.setattr(settings, "SUPABASE_STORAGE_BUCKET", "evidence")

    backend = get_storage()
    assert isinstance(backend, SupabaseStorageBackend)
    assert backend.base_url == "https://xyz.supabase.co"
