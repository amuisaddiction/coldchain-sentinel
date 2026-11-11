"""Phase 1 baseline health and foundation test suite."""

import pytest
import httpx
from app.main import app
from app.core.config import settings
from app.core.storage import compute_sha256, LocalStorageBackend
from app.core.idempotency import generate_payment_idempotency_key


@pytest.mark.asyncio
async def test_root_endpoint():
    """Verify application root banner returns valid JSON and status."""
    transport = httpx.ASGITransport(app=app)
    async with httpx.AsyncClient(transport=transport, base_url="http://testserver") as client:
        response = await client.get("/")
        assert response.status_code == 200
        data = response.json()
        assert data["platform"] == "ColdChain Sentinel"
        assert data["status"] == "operational"
        assert "version" in data


@pytest.mark.asyncio
async def test_health_check_endpoint():
    """Verify system health endpoint validates database connectivity and returns runtime info."""
    transport = httpx.ASGITransport(app=app)
    async with httpx.AsyncClient(transport=transport, base_url="http://testserver") as client:
        response = await client.get(f"{settings.API_V1_PREFIX}/health")
        assert response.status_code == 200
        data = response.json()
        assert data["status"] == "healthy"
        assert data["database_connected"] is True
        assert "python_runtime" in data
        assert data["storage_backend"] in ("local", "s3", "supabase")
        assert data["paypal_mode"] in ("SANDBOX", "DEMO")


def test_sha256_computation():
    """Verify deterministic SHA-256 computation."""
    sample_bytes = b"timestamp,temperature,sensor_id\n2026-11-01T08:00:00Z,4.2,LOGGER-001\n"
    expected_hash = "19e11749d06d83e68bad44773cc4a900f715ffb6b0e7a12c4f4cb0b6a6360381"
    computed_hash = compute_sha256(sample_bytes)
    assert computed_hash == expected_hash
    # Confirm byte changes alter the hash
    modified_hash = compute_sha256(sample_bytes + b"tampered")
    assert modified_hash != computed_hash


def test_payment_idempotency_key_generation():
    """Verify stable unique payment idempotency key generation."""
    key1 = generate_payment_idempotency_key(
        shipment_ref="CCS-DEMO-001",
        action="CAPTURE",
        authorization_id="AUTH-999-XYZ",
        nonce="op-1"
    )
    key2 = generate_payment_idempotency_key(
        shipment_ref="CCS-DEMO-001",
        action="CAPTURE",
        authorization_id="AUTH-999-XYZ",
        nonce="op-1"
    )
    # Repeated calls with identical parameters produce identical keys
    assert key1 == key2
    assert key1.startswith("IDEMP-CCS-DEMO-001-CAPTURE-")

    # Different action produces different key
    key_void = generate_payment_idempotency_key(
        shipment_ref="CCS-DEMO-001",
        action="VOID",
        authorization_id="AUTH-999-XYZ",
        nonce="op-1"
    )
    assert key_void != key1
    assert "VOID" in key_void


@pytest.mark.asyncio
async def test_local_storage_backend(tmp_path):
    """Verify local storage backend saves file and calculates correct SHA-256."""
    storage = LocalStorageBackend(base_path=str(tmp_path))
    content = b"test temperature csv payload"
    storage_key, sha256_hash, size_bytes = await storage.save_file(
        content=content,
        original_filename="sample_log.csv",
        subfolder="evidence"
    )
    assert size_bytes == len(content)
    assert sha256_hash == compute_sha256(content)
    assert await storage.exists(storage_key) is True
    retrieved = await storage.get_file(storage_key)
    assert retrieved == content
