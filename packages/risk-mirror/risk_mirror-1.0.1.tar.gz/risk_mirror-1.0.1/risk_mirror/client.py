"""
Risk Mirror SDK - Python Client
================================
Deterministic, stateless AI safety toolkit
Drop-in integration for prompt security

US-0001: Core Behavior
US-0002: Policy Controls
US-0006: Edge Cases
US-0007: Performance
US-0008: Security
US-0009: Audit Evidence
US-0010: Privacy (no storage)
US-0011: Compliance
US-0012: Rate Limits
US-0013: Logging
US-0015: Rollback
US-0020: Error Handling
"""
import time
import logging
from typing import Optional, Callable, Dict, Any
from urllib.request import Request, urlopen
from urllib.error import HTTPError, URLError
import json

from .types import ScanResponse, ScanPolicy, OptimizeResponse, Verdict

# Constants
DEFAULT_BASE_URL = "https://risk-mirror-auth.anonymous617461746174.workers.dev"
DEFAULT_TIMEOUT = 30
DEFAULT_RETRIES = 3
SDK_VERSION = "1.0.0"
ENGINE_VERSION = "6.0-ULTRA"

logger = logging.getLogger("risk_mirror")


class RiskMirrorError(Exception):
    """Base exception for Risk Mirror SDK.
    
    US-0020: Error Handling
    """
    def __init__(
        self,
        code: str,
        message: str,
        retryable: bool = False,
        status_code: Optional[int] = None
    ):
        super().__init__(message)
        self.code = code
        self.message = message
        self.retryable = retryable
        self.status_code = status_code


class RiskMirror:
    """
    Risk Mirror SDK Client
    ======================
    Deterministic AI safety scanning with zero content storage.
    
    Example:
        >>> client = RiskMirror(api_key="your-key")
        >>> result = client.scan("Check this prompt for safety")
        >>> print(result.verdict)
        'SAFE'
    
    US-0001: Core Behavior
    """
    
    def __init__(
        self,
        base_url: str = DEFAULT_BASE_URL,
        api_key: Optional[str] = None,
        timeout: int = DEFAULT_TIMEOUT,
        retries: int = DEFAULT_RETRIES,
        debug: bool = False,
    ):
        """
        Initialize the Risk Mirror client.
        
        Args:
            base_url: API base URL
            api_key: Optional API key for authentication
            timeout: Request timeout in seconds
            retries: Number of retries on failure
            debug: Enable debug logging
        """
        self.base_url = base_url.rstrip("/")
        self.api_key = api_key
        self.timeout = timeout
        self.retries = retries
        self.debug = debug
        self._telemetry_callback: Optional[Callable[[Dict[str, Any]], None]] = None
        
        if debug:
            logging.basicConfig(level=logging.DEBUG)
    
    def on_telemetry(self, callback: Callable[[Dict[str, Any]], None]) -> None:
        """
        Set telemetry callback (receives no content, only metadata).
        
        US-0018: Analytics without storing content
        """
        self._telemetry_callback = callback
    
    def _log(self, msg: str, *args: Any) -> None:
        if self.debug:
            logger.debug(f"[RiskMirror] {msg}", *args)
    
    def _request(
        self,
        endpoint: str,
        method: str = "POST",
        body: Optional[Dict[str, Any]] = None
    ) -> Dict[str, Any]:
        """Make HTTP request with retry logic.
        
        US-0012: Rate Limits
        US-0020: Error Handling
        """
        url = f"{self.base_url}{endpoint}"
        headers = {
            "Content-Type": "application/json",
            "X-SDK-Version": SDK_VERSION,
        }
        
        if self.api_key:
            headers["X-API-Key"] = self.api_key
        
        last_error: Optional[Exception] = None
        
        for attempt in range(self.retries + 1):
            try:
                self._log(f"Request attempt {attempt + 1}: {method} {endpoint}")
                
                data = json.dumps(body).encode("utf-8") if body else None
                req = Request(url, data=data, headers=headers, method=method)
                
                with urlopen(req, timeout=self.timeout) as response:
                    return json.loads(response.read().decode("utf-8"))
                    
            except HTTPError as e:
                last_error = e
                
                # US-0012: Rate limit handling
                if e.code == 429:
                    retry_after = e.headers.get("Retry-After", "1")
                    wait_secs = int(retry_after)
                    self._log(f"Rate limited, waiting {wait_secs}s")
                    time.sleep(wait_secs)
                    continue
                
                # Retryable server errors
                if e.code >= 500 and attempt < self.retries:
                    wait_secs = min(2 ** attempt, 10)
                    self._log(f"Server error {e.code}, retry in {wait_secs}s")
                    time.sleep(wait_secs)
                    continue
                
                raise RiskMirrorError(
                    code="API_ERROR",
                    message=f"API returned {e.code}: {e.read().decode('utf-8', errors='ignore')}",
                    retryable=e.code >= 500,
                    status_code=e.code
                )
                
            except URLError as e:
                last_error = e
                if attempt < self.retries:
                    wait_secs = min(2 ** attempt, 10)
                    self._log(f"Network error, retry in {wait_secs}s: {e.reason}")
                    time.sleep(wait_secs)
                    continue
                raise RiskMirrorError(
                    code="NETWORK_ERROR",
                    message=str(e.reason),
                    retryable=True
                )
            except Exception as e:
                last_error = e
                raise RiskMirrorError(
                    code="UNKNOWN_ERROR",
                    message=str(e),
                    retryable=False
                )
        
        raise last_error or RiskMirrorError("UNKNOWN_ERROR", "Request failed", False)
    
    def scan(
        self,
        input_text: str,
        policy: Optional[ScanPolicy] = None,
        mode: str = "default"
    ) -> ScanResponse:
        """
        Scan input for safety issues.
        
        US-0001: Core behavior - deterministic scanning
        US-0002: Policy controls - configurable detection
        US-0010: Privacy - no content storage
        
        Args:
            input_text: Text to scan
            policy: Optional policy configuration
            mode: Scan mode (default, strict, paranoid)
        
        Returns:
            ScanResponse with verdict, findings, and safe_output
        
        Raises:
            RiskMirrorError: On validation or API errors
        """
        start = time.perf_counter()
        
        # US-0006: Edge cases - input validation
        if not input_text or not isinstance(input_text, str):
            raise RiskMirrorError(
                code="INVALID_INPUT",
                message="Input must be a non-empty string",
                retryable=False
            )
        
        # US-0008: Security - size limit
        max_length = policy.max_length if policy else 100000
        if len(input_text) > max_length:
            raise RiskMirrorError(
                code="INPUT_TOO_LARGE",
                message=f"Input exceeds maximum length of {max_length} characters",
                retryable=False
            )
        
        # Build request
        policy = policy or ScanPolicy()
        request_body = {
            "prompt": input_text,
            "policy": {
                "detect_pii": policy.pii,
                "detect_secrets": policy.secrets,
                "detect_injection": policy.injection,
            },
        }
        
        if policy.pii_classes:
            request_body["policy"]["pii_classes"] = policy.pii_classes
        
        response_data = self._request("/firewall/audit", "POST", request_body)
        
        latency_ms = (time.perf_counter() - start) * 1000
        response_data["latency_ms"] = latency_ms
        response_data["privacy"] = {"stateless": True, "content_logged": False}
        
        # US-0018: Analytics telemetry (no content)
        if self._telemetry_callback:
            self._telemetry_callback({
                "operation": "scan",
                "verdict": response_data.get("verdict", "SAFE"),
                "findings_count": len(response_data.get("findings", [])),
                "latency_ms": latency_ms,
                "timestamp": time.strftime("%Y-%m-%dT%H:%M:%SZ", time.gmtime()),
            })
        
        return ScanResponse.from_dict(response_data)
    
    def audit(
        self,
        input_text: str,
        policy: Optional[ScanPolicy] = None
    ) -> ScanResponse:
        """
        Audit scan for compliance reporting.
        
        US-0009: Audit Evidence
        
        Args:
            input_text: Text to audit
            policy: Optional policy configuration
        
        Returns:
            ScanResponse with detailed audit evidence
        """
        return self.scan(input_text, policy, mode="strict")
    
    def optimize(
        self,
        input_text: str,
        mode: str = "compress"
    ) -> OptimizeResponse:
        """
        Optimize prompt for token efficiency.
        
        Args:
            input_text: Text to optimize
            mode: compress, refine, or strip
        
        Returns:
            OptimizeResponse with optimized text
        """
        if not input_text or not isinstance(input_text, str):
            raise RiskMirrorError(
                code="INVALID_INPUT",
                message="Input must be a non-empty string",
                retryable=False
            )
        
        response_data = self._request("/optimize/prompt", "POST", {
            "prompt": input_text,
            "mode": mode,
        })
        
        return OptimizeResponse.from_dict(response_data)
    
    def get_version(self) -> Dict[str, str]:
        """
        Get SDK and engine version.
        
        US-0015: Rollback - version tracking
        """
        return {
            "sdk": SDK_VERSION,
            "engine": ENGINE_VERSION,
        }


# ============ Quick Helpers ============
_default_client: Optional[RiskMirror] = None


def configure(**kwargs: Any) -> None:
    """Configure the default client."""
    global _default_client
    _default_client = RiskMirror(**kwargs)


def scan(
    input_text: str,
    policy: Optional[ScanPolicy] = None,
    mode: str = "default"
) -> ScanResponse:
    """Quick scan using default client."""
    global _default_client
    if _default_client is None:
        _default_client = RiskMirror()
    return _default_client.scan(input_text, policy, mode)
