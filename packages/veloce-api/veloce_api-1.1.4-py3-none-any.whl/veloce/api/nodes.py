"""
Nodes API - Node management
"""

from typing import Dict, Any, Optional, List


class NodesAPI:
    """Node management operations"""
    
    def __init__(self, client):
        self.client = client
    
    async def list(self) -> List[Dict[str, Any]]:
        """List all nodes"""
        status, data = await self.client._request("GET", "/nodes")
        return data if status == 200 else []
    
    async def get(self, node_id: int) -> Optional[Dict[str, Any]]:
        """Get node by ID"""
        status, data = await self.client._request("GET", f"/node/{node_id}")
        return data if status == 200 else None
    
    async def create(self, node_data: Dict[str, Any]) -> Optional[Dict[str, Any]]:
        """
        Create new node
        
        Args:
            node_data: {name, address, port, api_port, usage_coefficient, ...}
        """
        status, data = await self.client._request("POST", "/node", node_data)
        return data if status in (200, 201) else None
    
    async def update(self, node_id: int, node_data: Dict[str, Any]) -> bool:
        """Update node"""
        status, _ = await self.client._request("PUT", f"/node/{node_id}", node_data)
        return status == 200
    
    async def delete(self, node_id: int) -> bool:
        """Delete node"""
        status, _ = await self.client._request("DELETE", f"/node/{node_id}")
        return status == 200
    
    async def reconnect(self, node_id: int) -> bool:
        """Reconnect to node"""
        status, _ = await self.client._request("POST", f"/node/{node_id}/reconnect")
        return status == 200
    
    async def get_usage(self, node_id: int) -> Optional[Dict[str, Any]]:
        """Get node usage statistics"""
        status, data = await self.client._request("GET", f"/node/{node_id}/usage")
        return data if status == 200 else None
