"""
Dominus SDK Endpoints

Gateway URL for authentication (JWT minting).
Orchestrator URL for all service calls.

Configuration:
    Set DOMINUS_GATEWAY_URL to override the gateway URL.
    Set DOMINUS_BASE_URL to override the orchestrator URL.
    Example: export DOMINUS_BASE_URL=http://localhost:5000

Usage:
    from dominus.config.endpoints import GATEWAY_URL, BASE_URL, get_gateway_url, get_base_url
"""
import os

# Default URLs
_DEFAULT_GATEWAY_URL = "https://dominus-gateway-production-775398158805.us-east4.run.app"
_DEFAULT_BASE_URL = "https://dominus-orchestrator-production-775398158805.us-east4.run.app"

# Gateway URL for JWT operations (can be overridden via DOMINUS_GATEWAY_URL)
GATEWAY_URL = os.environ.get("DOMINUS_GATEWAY_URL", _DEFAULT_GATEWAY_URL)

# Base URL for service calls (can be overridden via DOMINUS_BASE_URL environment variable)
BASE_URL = os.environ.get("DOMINUS_BASE_URL", _DEFAULT_BASE_URL)

# Legacy aliases (all point to orchestrator now) - DEPRECATED
SOVEREIGN_URL = BASE_URL
ARCHITECT_URL = BASE_URL
ORCHESTRATOR_URL = BASE_URL
WARDEN_URL = BASE_URL

# Proxy configuration (optional)
# DOMINUS_* variants take precedence over standard HTTP_PROXY/HTTPS_PROXY
HTTP_PROXY = os.environ.get("DOMINUS_HTTP_PROXY") or os.environ.get("HTTP_PROXY")
HTTPS_PROXY = os.environ.get("DOMINUS_HTTPS_PROXY") or os.environ.get("HTTPS_PROXY")


def get_proxy_config() -> dict | None:
    """
    Get proxy configuration for httpx clients.

    Returns a dict suitable for httpx's `proxies` parameter, or None if no proxy is configured.

    Environment variables (in order of precedence):
        - DOMINUS_HTTP_PROXY / DOMINUS_HTTPS_PROXY (SDK-specific)
        - HTTP_PROXY / HTTPS_PROXY (standard)

    Returns:
        Dict mapping protocol to proxy URL, or None if no proxies configured.
        Example: {"http://": "http://proxy:8080", "https://": "http://proxy:8080"}
    """
    proxies = {}
    if HTTP_PROXY:
        proxies["http://"] = HTTP_PROXY
    if HTTPS_PROXY:
        proxies["https://"] = HTTPS_PROXY
    return proxies if proxies else None


def get_gateway_url() -> str:
    """
    Get the dominus-gateway base URL for JWT operations.

    Returns the value of DOMINUS_GATEWAY_URL environment variable if set,
    otherwise returns the default production URL.
    """
    return os.environ.get("DOMINUS_GATEWAY_URL", _DEFAULT_GATEWAY_URL)


def get_base_url() -> str:
    """
    Get the dominus-orchestrator base URL for service calls.

    Returns the value of DOMINUS_BASE_URL environment variable if set,
    otherwise returns the default production URL.
    """
    return os.environ.get("DOMINUS_BASE_URL", _DEFAULT_BASE_URL)


# DEPRECATED - use get_base_url()
def get_sovereign_url(environment: str = None) -> str:
    """Deprecated: Use get_base_url() instead."""
    return BASE_URL


def get_architect_url(environment: str = None) -> str:
    """Deprecated: Use get_base_url() instead."""
    return BASE_URL


def get_service_url(service: str, environment: str = None) -> str:
    """Deprecated: Use get_base_url() instead. All services are now consolidated."""
    return BASE_URL
