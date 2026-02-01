"""
Main Veloce API Client
"""

import aiohttp
from typing import Dict, Any, Optional, Tuple

from .exceptions import (
    VeloceAPIError,
    VeloceAuthError,
    VeloceNotFoundError,
    VeloceValidationError,
    VeloceConflictError,
    VeloceServerError
)


class VeloceClient:
    """
    Main client for Veloce Panel API
    
    Usage:
        >>> client = VeloceClient("https://panel.com/api", "api_key")
        >>> await client.users.create_free("user123")
        >>> await client.nodes.list()
    """
    
    def __init__(self, base_url: str, api_key: str):
        """
        Initialize Veloce API client
        
        Args:
            base_url: Base URL of panel (e.g. https://panel.com/api)
            api_key: API key for authentication
        """
        self.base_url = base_url.rstrip("/")
        self.api_key = api_key
        
        # Lazy load API modules
        self._users_api = None
        self._admin_api = None
        self._nodes_api = None
        self._inbounds_api = None
        self._system_api = None
        self._api_keys_api = None
        self._core_api = None
    
    @property
    def users(self):
        """User management API"""
        if self._users_api is None:
            from .api.users import UsersAPI
            self._users_api = UsersAPI(self)
        return self._users_api
    
    @property
    def admin(self):
        """Admin operations API"""
        if self._admin_api is None:
            from .api.admin import AdminAPI
            self._admin_api = AdminAPI(self)
        return self._admin_api
    
    @property
    def nodes(self):
        """Node management API"""
        if self._nodes_api is None:
            from .api.nodes import NodesAPI
            self._nodes_api = NodesAPI(self)
        return self._nodes_api
    
    @property
    def inbounds(self):
        """Inbound configuration API"""
        if self._inbounds_api is None:
            from .api.inbounds import InboundsAPI
            self._inbounds_api = InboundsAPI(self)
        return self._inbounds_api
    
    @property
    def system(self):
        """System information API"""
        if self._system_api is None:
            from .api.system import SystemAPI
            self._system_api = SystemAPI(self)
        return self._system_api
    
    @property
    def api_keys(self):
        """API keys management"""
        if self._api_keys_api is None:
            from .api.api_keys import APIKeysAPI
            self._api_keys_api = APIKeysAPI(self)
        return self._api_keys_api
    
    @property
    def core(self):
        """Core statistics API"""
        if self._core_api is None:
            from .api.core import CoreAPI
            self._core_api = CoreAPI(self)
        return self._core_api
    
    def _get_headers(self) -> Dict[str, str]:
        """Get request headers with API key"""
        return {
            "X-API-Key": self.api_key,
            "Content-Type": "application/json"
        }
    
    async def _request(
        self,
        method: str,
        endpoint: str,
        json_data: Optional[Dict[str, Any]] = None,
        params: Optional[Dict[str, Any]] = None
    ) -> Tuple[int, Dict[str, Any]]:
        """
        Make HTTP request to API
        
        Args:
            method: HTTP method
            endpoint: API endpoint
            json_data: JSON body
            params: Query parameters
            
        Returns:
            Tuple of (status_code, response_data)
            
        Raises:
            VeloceAPIError: On API errors
        """
        url = f"{self.base_url}{endpoint}"
        headers = self._get_headers()
        
        try:
            async with aiohttp.ClientSession() as session:
                async with session.request(
                    method,
                    url,
                    json=json_data,
                    params=params,
                    headers=headers
                ) as resp:
                    try:
                        response_data = await resp.json()
                    except:
                        response_data = {}
                    
                    # Handle errors
                    if resp.status == 401:
                        raise VeloceAuthError(
                            "Authentication failed. Check API key.",
                            status_code=401,
                            response=response_data
                        )
                    elif resp.status == 403:
                        raise VeloceAuthError(
                            "Permission denied",
                            status_code=403,
                            response=response_data
                        )
                    elif resp.status == 404:
                        raise VeloceNotFoundError(
                            "Resource not found",
                            status_code=404,
                            response=response_data
                        )
                    elif resp.status == 409:
                        raise VeloceConflictError(
                            "Resource already exists",
                            status_code=409,
                            response=response_data
                        )
                    elif resp.status in (400, 422):
                        raise VeloceValidationError(
                            response_data.get("detail", "Validation error"),
                            status_code=resp.status,
                            response=response_data
                        )
                    elif resp.status >= 500:
                        raise VeloceServerError(
                            "Server error",
                            status_code=resp.status,
                            response=response_data
                        )
                    
                    return resp.status, response_data
        
        except (VeloceAuthError, VeloceNotFoundError, VeloceConflictError,
                VeloceValidationError, VeloceServerError):
            raise
        except Exception as e:
            raise VeloceAPIError(f"Request failed: {e}")
    
    async def health_check(self) -> bool:
        """
        Check if API is accessible
        
        Returns:
            True if healthy
        """
        try:
            await self._request("GET", "/admin")
            return True
        except VeloceAuthError:
            # Auth error means API is working
            return True
        except:
            return False
