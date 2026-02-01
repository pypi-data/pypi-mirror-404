"""
Inbounds API - Inbound configuration management
"""

from typing import Dict, Any, Optional, List


class InboundsAPI:
    """Inbound management operations"""
    
    def __init__(self, client):
        self.client = client
    
    async def list(self) -> List[Dict[str, Any]]:
        """List all inbounds"""
        status, data = await self.client._request("GET", "/inbounds")
        return data if status == 200 else []
    
    async def get(self, inbound_tag: str) -> Optional[Dict[str, Any]]:
        """Get inbound by tag"""
        status, data = await self.client._request("GET", f"/inbound/{inbound_tag}")
        return data if status == 200 else None
    
    async def create(self, inbound_data: Dict[str, Any]) -> Optional[Dict[str, Any]]:
        """Create inbound"""
        status, data = await self.client._request("POST", "/inbound", inbound_data)
        return data if status in (200, 201) else None
    
    async def update(self, inbound_tag: str, inbound_data: Dict[str, Any]) -> bool:
        """Update inbound"""
        status, _ = await self.client._request("PUT", f"/inbound/{inbound_tag}", inbound_data)
        return status == 200
    
    async def delete(self, inbound_tag: str) -> bool:
        """Delete inbound"""
        status, _ = await self.client._request("DELETE", f"/inbound/{inbound_tag}")
        return status == 200
