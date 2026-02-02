"""
FastAPI Namespace - Decorators for route authentication.

Provides decorator-style auth for FastAPI routes:

    from dominus import dominus

    @router.get("/protected")
    @dominus.fastapi.jwt
    async def route(claims: dict):
        # claims contains JWT payload
        ...

    @router.get("/scoped")
    @dominus.fastapi.scopes(["api:read", "data:read"])
    async def route(claims: dict):
        # claims validated to have at least one scope
        ...

    @router.get("/psk-protected")
    @dominus.fastapi.psk
    async def route(client: dict):
        # client contains {id, name, tenant_id, scopes, roles, status}
        ...

Parameter naming conventions:
- @jwt and @scopes: function must have a 'claims' parameter
- @psk: function must have a 'client' parameter
"""
from functools import wraps
from typing import Any, Callable, Dict, List, Optional, TYPE_CHECKING
import inspect

if TYPE_CHECKING:
    from ..start import Dominus


class FastAPINamespace:
    """
    FastAPI authentication decorators namespace.

    Usage:
        from dominus import dominus

        @router.get("/protected")
        @dominus.fastapi.jwt
        async def my_route(claims: dict):
            return {"user": claims.get("sub")}
    """

    def __init__(self, client: "Dominus"):
        self._client = client

    def jwt(self, func: Callable) -> Callable:
        """
        Decorator: Require valid JWT in Authorization header.

        Injects JWT claims into the 'claims' parameter.

        Usage:
            @router.get("/protected")
            @dominus.fastapi.jwt
            async def route(claims: dict):
                return {"user": claims.get("sub")}

        Raises:
            HTTPException 401: Missing/invalid Authorization header or token
        """
        return self._create_auth_decorator(func, auth_type="jwt")

    def psk(self, func: Callable) -> Callable:
        """
        Decorator: Require valid PSK in Authorization: Bearer header.

        Injects client info into the 'client' parameter.

        Usage:
            @router.get("/protected")
            @dominus.fastapi.psk
            async def route(client: dict):
                return {"client_name": client.get("name")}

        Raises:
            HTTPException 401: Missing/invalid Authorization header or PSK
        """
        return self._create_auth_decorator(func, auth_type="psk")

    def scopes(self, allowed_scopes: List[str]) -> Callable:
        """
        Decorator factory: Require JWT with specific scopes.

        Access granted if client has ANY of the allowed scopes.
        Injects JWT claims into the 'claims' parameter.

        Usage:
            @router.get("/admin")
            @dominus.fastapi.scopes(["admin:read", "admin:write"])
            async def route(claims: dict):
                return {"admin": True}

        Args:
            allowed_scopes: List of scope strings, any one grants access

        Raises:
            HTTPException 401: Missing/invalid Authorization header or token
            HTTPException 403: Token valid but missing required scopes
        """
        def decorator(func: Callable) -> Callable:
            return self._create_auth_decorator(func, auth_type="jwt", required_scopes=allowed_scopes)
        return decorator

    def _create_auth_decorator(
        self,
        func: Callable,
        auth_type: str,
        required_scopes: Optional[List[str]] = None
    ) -> Callable:
        """
        Internal: Create an auth decorator for the given function.

        Args:
            func: The route function to wrap
            auth_type: "jwt" or "psk"
            required_scopes: Optional list of scopes to require (jwt only)
        """
        # Import here to avoid circular imports and make fastapi optional
        from fastapi import Header, HTTPException

        # Determine the parameter name to inject
        param_name = "claims" if auth_type == "jwt" else "client"

        # Validate the function has the required parameter
        sig = inspect.signature(func)
        if param_name not in sig.parameters:
            raise ValueError(
                f"@dominus.fastapi.{auth_type} requires a '{param_name}' parameter. "
                f"Add '{param_name}: dict' to your function signature."
            )

        @wraps(func)
        async def wrapper(*args, **kwargs):
            # Get Authorization header from the request
            # FastAPI injects this via the wrapper's signature
            authorization = kwargs.pop("_dominus_authorization", None)

            if not authorization:
                raise HTTPException(
                    status_code=401,
                    detail="Missing Authorization header",
                    headers={"WWW-Authenticate": "Bearer"}
                )

            # Extract Bearer token
            token = self._extract_bearer(authorization)
            if not token:
                raise HTTPException(
                    status_code=401,
                    detail="Invalid Authorization header format. Expected: Bearer <token>",
                    headers={"WWW-Authenticate": "Bearer"}
                )

            # Validate based on auth type
            if auth_type == "jwt":
                auth_data = await self._validate_jwt(token)
                if not auth_data:
                    raise HTTPException(
                        status_code=401,
                        detail="Invalid or expired token",
                        headers={"WWW-Authenticate": "Bearer"}
                    )

                # Check scopes if required
                if required_scopes:
                    client_scopes = auth_data.get("scopes", [])
                    if not any(scope in client_scopes for scope in required_scopes):
                        raise HTTPException(
                            status_code=403,
                            detail=f"Missing required scope. Need one of: {required_scopes}"
                        )
            else:  # psk
                auth_data = await self._validate_psk(token)
                if not auth_data:
                    raise HTTPException(
                        status_code=401,
                        detail="Invalid API key",
                        headers={"WWW-Authenticate": "Bearer"}
                    )

            # Inject the auth data into the function
            kwargs[param_name] = auth_data

            # Call the original function
            return await func(*args, **kwargs)

        # Modify the wrapper signature to include Authorization header
        # This allows FastAPI to inject it automatically
        old_sig = inspect.signature(func)
        old_params = list(old_sig.parameters.values())

        # Remove the claims/client param (we'll inject it manually)
        new_params = [p for p in old_params if p.name != param_name]

        # Add the Authorization header param
        auth_param = inspect.Parameter(
            "_dominus_authorization",
            inspect.Parameter.KEYWORD_ONLY,
            default=Header(None, alias="Authorization"),
            annotation=Optional[str]
        )
        new_params.append(auth_param)

        # Create new signature
        wrapper.__signature__ = old_sig.replace(parameters=new_params)

        return wrapper

    def _extract_bearer(self, auth_header: str) -> Optional[str]:
        """Extract token from Authorization: Bearer <token> header."""
        if not auth_header or not auth_header.startswith("Bearer "):
            return None
        return auth_header[7:]

    async def _validate_jwt(self, token: str) -> Optional[Dict[str, Any]]:
        """Validate JWT and return claims."""
        try:
            return await self._client.validate_jwt(token)
        except (ValueError, Exception):
            return None

    async def _validate_psk(self, psk: str) -> Optional[Dict[str, Any]]:
        """
        Validate PSK and return client info with scopes/roles.

        Uses portal.login_client to exchange PSK for JWT, then decodes
        the JWT to get the client's claims (scopes, roles, tenants, etc.).
        """
        try:
            # Exchange PSK for JWT via portal.login_client
            # This uses the SDK's project JWT + the subsidiary client's PSK
            result = await self._client.portal.login_client(psk=psk)
            if not result:
                return None

            jwt = result.get("access_token")
            if not jwt:
                return None

            # Decode JWT to get claims (includes scopes, roles, tenants, etc.)
            claims = await self._client.validate_jwt(jwt)
            return claims
        except Exception:
            return None
