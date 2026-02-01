"""
API Keys API - API key management
"""

from typing import Dict, Any, Optional, List


class APIKeysAPI:
    """API keys management"""
    
    def __init__(self, client):
        self.client = client
    
    async def list(self) -> List[Dict[str, Any]]:
        """List all API keys"""
        status, data = await self.client._request("GET", "/api-keys")
        return data if status == 200 else []
    
    async def create(self, name: str) -> Optional[Dict[str, Any]]:
        """
        Create new API key
        
        Args:
            name: Key name/description
            
        Returns:
            {"id": int, "name": str, "key": str, "created_at": datetime}
            
        Note:
            The "key" field is only shown once during creation!
        """
        payload = {"name": name}
        status, data = await self.client._request("POST", "/api-keys", payload)
        return data if status in (200, 201) else None
    
    async def delete(self, key_id: int) -> bool:
        """Delete API key"""
        status, _ = await self.client._request("DELETE", f"/api-keys/{key_id}")
        return status == 200
    
    async def toggle(self, key_id: int) -> bool:
        """Toggle API key active status"""
        status, _ = await self.client._request("PATCH", f"/api-keys/{key_id}/toggle")
        return status == 200
