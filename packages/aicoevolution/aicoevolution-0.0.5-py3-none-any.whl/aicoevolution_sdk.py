"""
AICoevolution SDK (thin client)

This PyPI distribution intentionally ships ONLY an HTTP client. All metrics are
computed by the hosted SDK service (or your self-hosted deployment).

Primary service endpoints (Paper 03 release):
- POST /v0/ingest
- GET  /v0/snapshot/{conversation_id}
- POST /v0/transducer
- POST /v0/transducer/batch

Auth:
- External callers: Authorization: Bearer aic_...
- Internal service-to-service: X-SDK-API-Key: <SDK_SERVICE_API_KEY>
"""

from __future__ import annotations

from dataclasses import dataclass
from typing import Any, Dict, Iterable, List, Optional, Union
import os

import requests


Json = Dict[str, Any]


class AICoevolutionError(RuntimeError):
    """Raised for HTTP / protocol errors when calling the SDK service."""


@dataclass(frozen=True)
class SDKAuth:
    """
    Authentication configuration.

    - user_api_key: public API key for external users (aic_...).
    - sdk_service_api_key: internal secret for service-to-service calls (X-SDK-API-Key).
    """

    user_api_key: str = ""
    sdk_service_api_key: str = ""

    @staticmethod
    def from_env() -> "SDKAuth":
        return SDKAuth(
            user_api_key=os.getenv("AIC_SDK_API_KEY", ""),
            sdk_service_api_key=os.getenv("SDK_SERVICE_API_KEY", ""),
        )


class AICoevolutionClient:
    """
    Thin HTTP client for the AICoevolution SDK service.

    Environment variables:
    - AIC_SDK_URL: base URL for the SDK service (default: https://sdk.aicoevolution.com)
    - AIC_SDK_API_KEY: user API key (aic_...)
    - SDK_SERVICE_API_KEY: internal service-to-service key (optional)
    """

    def __init__(
        self,
        *,
        base_url: Optional[str] = None,
        auth: Optional[SDKAuth] = None,
        timeout_s: float = 30.0,
        session: Optional[requests.Session] = None,
    ):
        self.base_url = (base_url or os.getenv("AIC_SDK_URL", "https://sdk.aicoevolution.com")).rstrip("/")
        self.auth = auth or SDKAuth.from_env()
        self.timeout_s = timeout_s
        self._session = session or requests.Session()

    def _headers(self, *, internal: bool = False) -> Dict[str, str]:
        headers: Dict[str, str] = {"Content-Type": "application/json"}

        if internal and self.auth.sdk_service_api_key:
            headers["X-SDK-API-Key"] = self.auth.sdk_service_api_key
            return headers

        if self.auth.user_api_key:
            headers["Authorization"] = f"Bearer {self.auth.user_api_key}"
        return headers

    def _request(self, method: str, path: str, *, internal: bool = False, json: Optional[Json] = None) -> Json:
        url = f"{self.base_url}{path}"
        try:
            resp = self._session.request(
                method=method,
                url=url,
                json=json,
                headers=self._headers(internal=internal),
                timeout=self.timeout_s,
            )
        except requests.RequestException as e:
            raise AICoevolutionError(f"SDK request failed: {method} {url}: {e}") from e

        if not resp.ok:
            detail = resp.text.strip()
            raise AICoevolutionError(f"SDK error: {method} {url}: HTTP {resp.status_code}: {detail}")

        try:
            return resp.json()
        except ValueError as e:
            raise AICoevolutionError(f"SDK error: {method} {url}: invalid JSON response") from e

    # -------------------------------------------------------------------------
    # Paper 03: Real-time telemetry
    # -------------------------------------------------------------------------
    def ingest(
        self,
        *,
        conversation_id: str,
        role: str,
        text: str,
        timestamp_ms: Optional[int] = None,
    ) -> Json:
        """
        POST /v0/ingest

        Ingest a single message and return updated telemetry (SGI, angular velocity, etc.).
        """
        payload: Json = {
            "conversation_id": conversation_id,
            "role": role,
            "text": text,
        }
        if timestamp_ms is not None:
            payload["timestamp_ms"] = timestamp_ms
        return self._request("POST", "/v0/ingest", json=payload)

    def snapshot(self, *, conversation_id: str) -> Json:
        """GET /v0/snapshot/{conversation_id}"""
        return self._request("GET", f"/v0/snapshot/{conversation_id}")

    # -------------------------------------------------------------------------
    # Paper 03: Semantic transducer
    # -------------------------------------------------------------------------
    def transducer(self, *, text: str, backend: Optional[str] = None) -> Json:
        """POST /v0/transducer"""
        payload: Json = {"text": text}
        if backend is not None:
            payload["backend"] = backend
        return self._request("POST", "/v0/transducer", json=payload)

    def transducer_batch(self, *, texts: Union[List[str], Iterable[str]], backend: Optional[str] = None) -> Json:
        """POST /v0/transducer/batch"""
        payload: Json = {"texts": list(texts)}
        if backend is not None:
            payload["backend"] = backend
        return self._request("POST", "/v0/transducer/batch", json=payload)

    # -------------------------------------------------------------------------
    # Internal: Batch runs (primarily for platform backend use)
    # -------------------------------------------------------------------------
    def create_run(self, *, body: Json) -> Json:
        """
        POST /v1/runs (internal)

        Requires SDK_SERVICE_API_KEY to be set (sent as X-SDK-API-Key).
        """
        if not self.auth.sdk_service_api_key:
            raise AICoevolutionError("SDK_SERVICE_API_KEY is required for /v1/runs (internal)")
        return self._request("POST", "/v1/runs", internal=True, json=body)

    def get_run(self, *, run_id: str) -> Json:
        """GET /v1/runs/{run_id} (internal)"""
        if not self.auth.sdk_service_api_key:
            raise AICoevolutionError("SDK_SERVICE_API_KEY is required for /v1/runs/* (internal)")
        return self._request("GET", f"/v1/runs/{run_id}", internal=True)


__all__ = [
    "AICoevolutionClient",
    "AICoevolutionError",
    "SDKAuth",
]


