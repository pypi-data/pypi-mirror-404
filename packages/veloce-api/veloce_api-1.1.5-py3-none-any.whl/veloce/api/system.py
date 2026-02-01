"""
System API - System information and statistics
"""

from typing import Dict, Any, Optional, List


class SystemAPI:
    """System operations"""
    
    def __init__(self, client):
        self.client = client
    
    async def get_stats(self) -> Optional[Dict[str, Any]]:
        """
        Get system statistics
        
        Returns:
            {
                "total_user": int,
                "users_active": int,
                "incoming_bandwidth": int,
                "outgoing_bandwidth": int,
                "incoming_bandwidth_speed": int,
                "outgoing_bandwidth_speed": int
            }
        """
        status, data = await self.client._request("GET", "/system")
        return data if status == 200 else None
    
    async def get_inbounds(self) -> List[Dict[str, Any]]:
        """List all inbounds"""
        status, data = await self.client._request("GET", "/inbounds")
        return data if status == 200 else []
    
    async def get_hosts(self) -> List[Dict[str, Any]]:
        """Get hosts configuration"""
        status, data = await self.client._request("GET", "/hosts")
        return data if status == 200 else []
    
    async def restart_core(self) -> bool:
        """Restart Xray core"""
        status, _ = await self.client._request("POST", "/core/restart")
        return status == 200
    
    async def get_core_config(self) -> Optional[Dict[str, Any]]:
        """Get current core configuration"""
        status, data = await self.client._request("GET", "/core/config")
        return data if status == 200 else None
