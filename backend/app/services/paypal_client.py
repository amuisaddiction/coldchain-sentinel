"""PayPal REST API client supporting live Sandbox and deterministic local mock."""

import os
import uuid
import hashlib
import logging
from typing import Dict, Any, Optional
import httpx
from app.core.config import settings

logger = logging.getLogger(__name__)


class PayPalClientError(Exception):
    """Raised on PayPal API failures."""
    pass


class PayPalClient:
    def __init__(self):
        self.base_url = settings.PAYPAL_BASE_URL.rstrip("/")
        self.client_id = settings.PAYPAL_CLIENT_ID
        self.client_secret = settings.PAYPAL_CLIENT_SECRET
        self.is_live_sandbox = bool(self.client_id and self.client_secret)
        self._mock_captures: Dict[str, str] = {}

    def _get_access_token(self) -> str:
        """Fetch OAuth2 Bearer token from PayPal."""
        if not self.is_live_sandbox:
            return "mock-sandbox-token"

        resp = httpx.post(
            f"{self.base_url}/v1/oauth2/token",
            auth=(self.client_id, self.client_secret),
            data={"grant_type": "client_credentials"},
            timeout=10.0,
        )
        if resp.status_code != 200:
            raise PayPalClientError(f"PayPal OAuth failed: {resp.text}")
        return resp.json()["access_token"]

    def capture_authorization(
        self,
        authorization_id: str,
        amount_decimal: str,
        currency: str,
        idempotency_key: str,
    ) -> Dict[str, Any]:
        """Capture an authorized payment with server-side idempotency protection."""
        if not self.is_live_sandbox:
            # Deterministic simulation with idempotency key tracking
            if idempotency_key in self._mock_captures:
                capture_id = self._mock_captures[idempotency_key]
            else:
                seed = f"{authorization_id}:{idempotency_key}".encode()
                short_hash = hashlib.sha256(seed).hexdigest()[:12].upper()
                capture_id = f"SIMULATED-PAYPAL-CAP-{short_hash}"
                self._mock_captures[idempotency_key] = capture_id

            return {
                "id": capture_id,
                "status": "COMPLETED",
                "amount": {
                    "value": amount_decimal,
                    "currency_code": currency,
                },
                "final_capture": True,
            }

        token = self._get_access_token()
        headers = {
            "Authorization": f"Bearer {token}",
            "Content-Type": "application/json",
            "PayPal-Request-Id": idempotency_key,
        }
        body = {
            "amount": {
                "value": amount_decimal,
                "currency_code": currency,
            },
            "final_capture": True,
        }
        resp = httpx.post(
            f"{self.base_url}/v2/payments/authorizations/{authorization_id}/capture",
            headers=headers,
            json=body,
            timeout=15.0,
        )
        if resp.status_code not in (200, 201):
            raise PayPalClientError(f"PayPal capture failed: {resp.status_code} {resp.text}")
        return resp.json()

    def void_authorization(
        self,
        authorization_id: str,
        idempotency_key: str,
    ) -> Dict[str, Any]:
        """Void an authorized payment."""
        if not self.is_live_sandbox:
            return {
                "id": authorization_id,
                "status": "VOIDED",
            }

        token = self._get_access_token()
        headers = {
            "Authorization": f"Bearer {token}",
            "Content-Type": "application/json",
            "PayPal-Request-Id": idempotency_key,
        }
        resp = httpx.post(
            f"{self.base_url}/v2/payments/authorizations/{authorization_id}/void",
            headers=headers,
            timeout=15.0,
        )
        if resp.status_code != 204:
            raise PayPalClientError(f"PayPal void failed: {resp.status_code} {resp.text}")
        return {"id": authorization_id, "status": "VOIDED"}


paypal_client = PayPalClient()
