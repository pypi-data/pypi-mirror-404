"""
ONTO API Client

Usage:
    from onto_standard import ONTOClient

    client = ONTOClient(api_key="onto_...")

    # Submit evaluation
    result = client.evaluate(
        model_name="my-model",
        predictions=[{"id": "q1", "label": "KNOWN", "confidence": 0.9}, ...]
    )

    # Check signal
    signal = client.get_signal()
"""

import json
import time
from typing import List, Dict, Optional, Any
from dataclasses import dataclass

try:
    import httpx

    HAS_HTTPX = True
except ImportError:
    HAS_HTTPX = False


# ============================================================
# CONFIGURATION
# ============================================================

DEFAULT_API_URL = "https://api.ontostandard.org"
DEFAULT_SIGNAL_URL = "https://signal.ontostandard.org"
DEFAULT_NOTARY_URL = "https://notary.ontostandard.org"


# ============================================================
# EXCEPTIONS
# ============================================================


class ONTOError(Exception):
    """Base exception for ONTO client"""

    pass


class AuthenticationError(ONTOError):
    """Invalid or missing API key"""

    pass


class RateLimitError(ONTOError):
    """Rate limit exceeded"""

    def __init__(self, message: str, retry_after: int = 60):
        super().__init__(message)
        self.retry_after = retry_after


class APIError(ONTOError):
    """API returned an error"""

    def __init__(self, message: str, status_code: int, detail: Any = None):
        super().__init__(message)
        self.status_code = status_code
        self.detail = detail


# ============================================================
# RESPONSE MODELS
# ============================================================


@dataclass
class SignalStatus:
    """Current entropy signal status"""

    status: str
    sigma_id: str
    timestamp: int
    age_seconds: int
    next_update_in: int
    entropy_preview: str

    @classmethod
    def from_dict(cls, data: dict) -> "SignalStatus":
        return cls(
            status=data.get("status", "unknown"),
            sigma_id=data.get("sigma_id", ""),
            timestamp=data.get("timestamp", 0),
            age_seconds=data.get("age_seconds", 0),
            next_update_in=data.get("next_update_in", 0),
            entropy_preview=data.get("entropy_preview", ""),
        )


@dataclass
class Evaluation:
    """Evaluation result"""

    id: str
    model_name: str
    model_version: Optional[str]
    status: str
    risk_score: Optional[float]
    metrics: Optional[dict]
    submitted_at: Optional[str]
    completed_at: Optional[str]

    @classmethod
    def from_dict(cls, data: dict) -> "Evaluation":
        return cls(
            id=data.get("id", ""),
            model_name=data.get("model_name", ""),
            model_version=data.get("model_version"),
            status=data.get("status", "unknown"),
            risk_score=data.get("risk_score"),
            metrics=data.get("metrics"),
            submitted_at=data.get("submitted_at"),
            completed_at=data.get("completed_at"),
        )


@dataclass
class Certificate:
    """ONTO Certificate"""

    id: str
    certificate_number: str
    model_name: str
    level: str
    status: str
    issued_at: Optional[str]
    expires_at: Optional[str]
    verify_url: Optional[str]

    @classmethod
    def from_dict(cls, data: dict) -> "Certificate":
        return cls(
            id=data.get("id", ""),
            certificate_number=data.get("certificate_number", ""),
            model_name=data.get("model_name", ""),
            level=data.get("level", ""),
            status=data.get("status", "unknown"),
            issued_at=data.get("issued_at"),
            expires_at=data.get("expires_at"),
            verify_url=data.get("verify_url"),
        )


@dataclass
class Organization:
    """Organization details"""

    id: str
    name: str
    slug: str
    tier: str
    rate_limit: int
    evaluations_count: int
    certificates_count: int

    @classmethod
    def from_dict(cls, data: dict) -> "Organization":
        return cls(
            id=data.get("id", ""),
            name=data.get("name", ""),
            slug=data.get("slug", ""),
            tier=data.get("tier", "pilot"),
            rate_limit=data.get("rate_limit", 30),
            evaluations_count=data.get("evaluations_count", 0),
            certificates_count=data.get("certificates_count", 0),
        )


# ============================================================
# CLIENT
# ============================================================


class ONTOClient:
    """
    ONTO API Client

    Args:
        api_key: Your ONTO API key (starts with 'onto_')
        api_url: API base URL (default: https://api.ontostandard.org)
        timeout: Request timeout in seconds

    Example:
        >>> client = ONTOClient(api_key="onto_abc123...")
        >>> signal = client.get_signal()
        >>> print(signal.sigma_id)
    """

    def __init__(
        self,
        api_key: Optional[str] = None,
        api_url: str = DEFAULT_API_URL,
        signal_url: str = DEFAULT_SIGNAL_URL,
        notary_url: str = DEFAULT_NOTARY_URL,
        timeout: float = 30.0,
    ):
        if not HAS_HTTPX:
            raise ImportError(
                "httpx is required for API client. " "Install with: pip install onto-standard[api]"
            )

        self.api_key = api_key
        self.api_url = api_url.rstrip("/")
        self.signal_url = signal_url.rstrip("/")
        self.notary_url = notary_url.rstrip("/")
        self.timeout = timeout

        self._client = httpx.Client(timeout=timeout)

    def _headers(self) -> Dict[str, str]:
        """Get request headers"""
        headers = {"Content-Type": "application/json"}
        if self.api_key:
            headers["X-API-Key"] = self.api_key
        return headers

    def _handle_response(self, response: httpx.Response) -> dict:
        """Handle API response"""
        if response.status_code == 401:
            raise AuthenticationError("Invalid or missing API key")

        if response.status_code == 429:
            retry_after = int(response.headers.get("Retry-After", 60))
            raise RateLimitError(
                f"Rate limit exceeded. Retry after {retry_after}s", retry_after=retry_after
            )

        if response.status_code >= 400:
            try:
                detail = response.json()
            except:
                detail = response.text
            raise APIError(
                f"API error: {response.status_code}",
                status_code=response.status_code,
                detail=detail,
            )

        return response.json()

    # --------------------------------------------------------
    # Public Endpoints (no auth required)
    # --------------------------------------------------------

    def health(self) -> dict:
        """Check API health"""
        resp = self._client.get(f"{self.api_url}/health")
        return self._handle_response(resp)

    def get_pricing(self) -> dict:
        """Get pricing tiers"""
        resp = self._client.get(f"{self.api_url}/v1/pricing")
        return self._handle_response(resp)

    def get_signal(self) -> SignalStatus:
        """Get current entropy signal status"""
        resp = self._client.get(f"{self.signal_url}/signal/status")
        data = self._handle_response(resp)
        return SignalStatus.from_dict(data)

    def get_signal_binary(self) -> bytes:
        """Get raw 104-byte signal packet"""
        resp = self._client.get(f"{self.signal_url}/signal/latest.bin")
        if resp.status_code != 200:
            raise APIError("Failed to get signal", resp.status_code)
        return resp.content

    def get_rate_limit(self) -> dict:
        """Get current rate limit status"""
        resp = self._client.get(f"{self.api_url}/v1/rate-limit", headers=self._headers())
        return self._handle_response(resp)

    # --------------------------------------------------------
    # Auth Endpoints
    # --------------------------------------------------------

    def register(self, name: str, email: str, company: str, password: str) -> dict:
        """
        Register a new organization

        Returns dict with api_key (save it!)
        """
        resp = self._client.post(
            f"{self.api_url}/v1/auth/register",
            json={
                "name": name,
                "email": email,
                "company": company,
                "password": password,
            },
        )
        return self._handle_response(resp)

    def login(self, email: str, password: str) -> dict:
        """Login and get token"""
        resp = self._client.post(
            f"{self.api_url}/v1/auth/login", json={"email": email, "password": password}
        )
        return self._handle_response(resp)

    # --------------------------------------------------------
    # Protected Endpoints (require api_key)
    # --------------------------------------------------------

    def get_organization(self) -> Organization:
        """Get current organization details"""
        resp = self._client.get(f"{self.api_url}/v1/organization", headers=self._headers())
        data = self._handle_response(resp)
        return Organization.from_dict(data)

    def create_api_key(self, name: str) -> dict:
        """Create a new API key"""
        resp = self._client.post(
            f"{self.api_url}/v1/auth/api-keys", headers=self._headers(), json={"name": name}
        )
        return self._handle_response(resp)

    def list_api_keys(self) -> List[dict]:
        """List all API keys"""
        resp = self._client.get(f"{self.api_url}/v1/auth/api-keys", headers=self._headers())
        data = self._handle_response(resp)
        return data.get("api_keys", [])

    def revoke_api_key(self, key_id: str) -> dict:
        """Revoke an API key"""
        resp = self._client.delete(
            f"{self.api_url}/v1/auth/api-keys/{key_id}", headers=self._headers()
        )
        return self._handle_response(resp)

    # --------------------------------------------------------
    # Evaluation Endpoints
    # --------------------------------------------------------

    def evaluate(
        self,
        model_name: str,
        predictions: List[Dict],
        model_version: Optional[str] = None,
    ) -> dict:
        """
        Submit model predictions for evaluation

        Args:
            model_name: Name of your model
            predictions: List of dicts with {id, label, confidence}
            model_version: Optional version string

        Returns:
            dict with evaluation_id and status

        Example:
            >>> result = client.evaluate(
            ...     model_name="gpt-4",
            ...     predictions=[
            ...         {"id": "q1", "label": "KNOWN", "confidence": 0.95},
            ...         {"id": "q2", "label": "UNKNOWN", "confidence": 0.3},
            ...     ]
            ... )
        """
        payload = {
            "model_name": model_name,
            "predictions": predictions,
        }
        if model_version:
            payload["model_version"] = model_version

        resp = self._client.post(
            f"{self.api_url}/v1/evaluate", headers=self._headers(), json=payload
        )
        return self._handle_response(resp)

    def get_evaluation(self, evaluation_id: str) -> Evaluation:
        """Get evaluation details"""
        resp = self._client.get(
            f"{self.api_url}/v1/evaluations/{evaluation_id}", headers=self._headers()
        )
        data = self._handle_response(resp)
        return Evaluation.from_dict(data)

    def list_evaluations(self, limit: int = 20) -> List[Evaluation]:
        """List recent evaluations"""
        resp = self._client.get(
            f"{self.api_url}/v1/evaluations", headers=self._headers(), params={"limit": limit}
        )
        data = self._handle_response(resp)
        return [Evaluation.from_dict(e) for e in data.get("evaluations", [])]

    def wait_for_evaluation(
        self, evaluation_id: str, timeout: int = 300, poll_interval: int = 5
    ) -> Evaluation:
        """
        Wait for evaluation to complete

        Args:
            evaluation_id: Evaluation ID
            timeout: Max wait time in seconds
            poll_interval: Time between status checks

        Returns:
            Completed Evaluation

        Raises:
            TimeoutError if evaluation doesn't complete
        """
        start = time.time()
        while time.time() - start < timeout:
            evaluation = self.get_evaluation(evaluation_id)
            if evaluation.status in ["completed", "failed", "error"]:
                return evaluation
            time.sleep(poll_interval)

        raise TimeoutError(f"Evaluation {evaluation_id} did not complete in {timeout}s")

    # --------------------------------------------------------
    # Certificate Endpoints
    # --------------------------------------------------------

    def list_certificates(self, limit: int = 20) -> List[Certificate]:
        """List certificates"""
        resp = self._client.get(
            f"{self.api_url}/v1/certificates", headers=self._headers(), params={"limit": limit}
        )
        data = self._handle_response(resp)
        return [Certificate.from_dict(c) for c in data.get("certificates", [])]

    def get_certificate(self, certificate_id: str) -> Certificate:
        """Get certificate details (public endpoint)"""
        resp = self._client.get(f"{self.api_url}/v1/certificates/{certificate_id}")
        data = self._handle_response(resp)
        return Certificate.from_dict(data)

    def verify_certificate(self, certificate_id: str) -> dict:
        """Verify certificate via notary"""
        resp = self._client.get(f"{self.notary_url}/registry/{certificate_id}")
        return self._handle_response(resp)

    # --------------------------------------------------------
    # Notary Endpoints
    # --------------------------------------------------------

    def get_notary_stats(self) -> dict:
        """Get notary statistics"""
        resp = self._client.get(f"{self.notary_url}/v1/stats")
        return self._handle_response(resp)

    # --------------------------------------------------------
    # Cleanup
    # --------------------------------------------------------

    def close(self):
        """Close the HTTP client"""
        self._client.close()

    def __enter__(self):
        return self

    def __exit__(self, *args):
        self.close()


# ============================================================
# ASYNC CLIENT
# ============================================================


class AsyncONTOClient:
    """
    Async ONTO API Client

    Example:
        >>> async with AsyncONTOClient(api_key="onto_...") as client:
        ...     signal = await client.get_signal()
    """

    def __init__(
        self,
        api_key: Optional[str] = None,
        api_url: str = DEFAULT_API_URL,
        signal_url: str = DEFAULT_SIGNAL_URL,
        notary_url: str = DEFAULT_NOTARY_URL,
        timeout: float = 30.0,
    ):
        if not HAS_HTTPX:
            raise ImportError(
                "httpx is required for API client. " "Install with: pip install onto-standard[api]"
            )

        self.api_key = api_key
        self.api_url = api_url.rstrip("/")
        self.signal_url = signal_url.rstrip("/")
        self.notary_url = notary_url.rstrip("/")
        self.timeout = timeout

        self._client = httpx.AsyncClient(timeout=timeout)

    def _headers(self) -> Dict[str, str]:
        headers = {"Content-Type": "application/json"}
        if self.api_key:
            headers["X-API-Key"] = self.api_key
        return headers

    def _handle_response(self, response: httpx.Response) -> dict:
        if response.status_code == 401:
            raise AuthenticationError("Invalid or missing API key")

        if response.status_code == 429:
            retry_after = int(response.headers.get("Retry-After", 60))
            raise RateLimitError(
                f"Rate limit exceeded. Retry after {retry_after}s", retry_after=retry_after
            )

        if response.status_code >= 400:
            try:
                detail = response.json()
            except:
                detail = response.text
            raise APIError(
                f"API error: {response.status_code}",
                status_code=response.status_code,
                detail=detail,
            )

        return response.json()

    async def get_signal(self) -> SignalStatus:
        """Get current entropy signal status"""
        resp = await self._client.get(f"{self.signal_url}/signal/status")
        data = self._handle_response(resp)
        return SignalStatus.from_dict(data)

    async def evaluate(
        self,
        model_name: str,
        predictions: List[Dict],
        model_version: Optional[str] = None,
    ) -> dict:
        """Submit evaluation"""
        payload = {
            "model_name": model_name,
            "predictions": predictions,
        }
        if model_version:
            payload["model_version"] = model_version

        resp = await self._client.post(
            f"{self.api_url}/v1/evaluate", headers=self._headers(), json=payload
        )
        return self._handle_response(resp)

    async def get_evaluation(self, evaluation_id: str) -> Evaluation:
        """Get evaluation details"""
        resp = await self._client.get(
            f"{self.api_url}/v1/evaluations/{evaluation_id}", headers=self._headers()
        )
        data = self._handle_response(resp)
        return Evaluation.from_dict(data)

    async def close(self):
        await self._client.aclose()

    async def __aenter__(self):
        return self

    async def __aexit__(self, *args):
        await self.close()
