"""
Admin API - Admin authentication and management
"""

from typing import Dict, Any, Optional


class AdminAPI:
    """Admin operations"""
    
    def __init__(self, client):
        self.client = client
    
    async def login(self, username: str, password: str) -> Optional[str]:
        """
        Authenticate admin and get token
        
        Args:
            username: Admin username
            password: Admin password
            
        Returns:
            Access token or None
        """
        payload = {"username": username, "password": password}
        status, data = await self.client._request("POST", "/admin/token", payload)
        
        if status == 200:
            return data.get("access_token")
        return None
    
    async def get_current(self) -> Optional[Dict[str, Any]]:
        """Get current authenticated admin info"""
        status, data = await self.client._request("GET", "/admin")
        return data if status == 200 else None
    
    async def create(self, username: str, password: str, is_sudo: bool = False) -> bool:
        """
        Create new admin
        
        Args:
            username: Admin username
            password: Admin password
            is_sudo: Grant sudo privileges
        """
        payload = {
            "username": username,
            "password": password,
            "is_sudo": is_sudo
        }
        status, _ = await self.client._request("POST", "/admin", payload)
        return status in (200, 201)
    
    async def delete(self, username: str) -> bool:
        """Delete admin"""
        status, _ = await self.client._request("DELETE", f"/admin/{username}")
        return status == 200
    
    async def modify(self, username: str, **kwargs) -> bool:
        """
        Modify admin
        
        Args:
            username: Admin to modify
            **kwargs: password, is_sudo, etc.
        """
        status, _ = await self.client._request("PUT", f"/admin/{username}", kwargs)
        return status == 200
