"""
Core API - Core statistics and operations
"""

from typing import Dict, Any, Optional


class CoreAPI:
    """Core statistics and operations"""
    
    def __init__(self, client):
        self.client = client
    
    async def get_stats(self) -> Optional[Dict[str, Any]]:
        """Get core statistics"""
        status, data = await self.client._request("GET", "/core/stats")
        return data if status == 200 else None
    
    async def restart(self) -> bool:
        """Restart core"""
        status, _ = await self.client._request("POST", "/core/restart")
        return status == 200
    
    async def get_config(self) -> Optional[Dict[str, Any]]:
        """Get core configuration"""
        status, data = await self.client._request("GET", "/core/config")
        return data if status == 200 else None
