"""
Users API - User management endpoints
"""

from datetime import datetime, timedelta
from typing import Dict, Any, Optional, List


class UsersAPI:
    """User management operations"""
    
    def __init__(self, client):
        self.client = client
    
    async def get(self, username: str) -> Optional[Dict[str, Any]]:
        """
        Get user by username
        
        Args:
            username: Username to fetch
            
        Returns:
            User data or None if not found
        """
        try:
            status, data = await self.client._request("GET", f"/user/{username}")
            return data if status == 200 else None
        except:
            return None
    
    async def list(
        self,
        offset: int = 0,
        limit: int = 10,
        sort: str = "created_at",
        username: Optional[str] = None,
        status: Optional[str] = None
    ) -> Dict[str, Any]:
        """
        List users with pagination
        
        Args:
            offset: Skip first N users
            limit: Max users to return
            sort: Sort field
            username: Filter by username (contains)
            status: Filter by status
            
        Returns:
            {"users": [...], "total": N}
        """
        params = {"offset": offset, "limit": limit, "sort": sort}
        if username:
            params["username"] = username
        if status:
            params["status"] = status
        
        status_code, data = await self.client._request("GET", "/users", params=params)
        return data if status_code == 200 else {"users": [], "total": 0}
    
    async def create_free(self, username: str) -> Optional[str]:
        """
        Create free tier user
        
        Args:
            username: Username to create
            
        Returns:
            Subscription URL or None
        """
        # First check if user exists
        existing = await self.get(username)
        
        if existing:
            # User exists -> update to Free Tier settings
            try:
                # expire=1 marks free tier, status=free is the proper status
                await self.update(username, expire=1, data_limit=0, status="free")
            except:
                pass
            return await self.get_subscription_url(username)
        
        # User doesn't exist -> create new
        # Note: UserStatusCreate only allows active/on_hold, so we create as active
        # then immediately update to free status
        payload = {
            "username": str(username),
            "proxies": {"vless": {}},
            "inbounds": {},
            "expire": 1,
            "data_limit": 0,
            "status": "active"  # Create as active first
        }
        
        try:
            status, resp = await self.client._request("POST", "/user", payload)
            if status in (200, 201):
                # Now update to free status
                try:
                    await self.update(username, status="free")
                except:
                    pass
                return await self.get_subscription_url(username)
        except:
            pass
        
        return None
    
    async def create_paid(self, username: str, days: int) -> Optional[str]:
        """
        Create paid user with subscription
        
        Args:
            username: Username
            days: Subscription days
            
        Returns:
            Subscription URL
        """
        expire = int((datetime.now() + timedelta(days=days)).timestamp())
        
        payload = {
            "username": str(username),
            "proxies": {"vless": {}},
            "inbounds": {},
            "expire": expire,
            "data_limit": 0,
            "status": "active"
        }
        
        status, _ = await self.client._request("POST", "/user", payload)
        if status in (200, 201):
            return await self.get_subscription_url(username)
        return None
    
    async def update(self, username: str, **kwargs) -> bool:
        """
        Update user
        
        Args:
            username: Username
            **kwargs: Fields to update (expire, data_limit, status, etc.)
            
        Returns:
            True if successful
        """
        status, _ = await self.client._request("PUT", f"/user/{username}", kwargs)
        return status == 200
    
    async def extend_subscription(self, username: str, days: int) -> Optional[str]:
        """
        Extend user subscription
        
        Args:
            username: Username
            days: Days to add
            
        Returns:
            Subscription URL
        """
        user = await self.get(username)
        
        if not user:
            return await self.create_paid(username, days)
        
        current_expire = user.get("expire", 0)
        now_ts = int(datetime.now().timestamp())
        
        # Logic:
        # 1. Free Tier (expire == 1) -> Start from NOW
        # 2. Expired (expire < now) -> Start from NOW (don't extend in the past)
        # 3. Active (expire >= now) -> Extend from current expire
        
        if current_expire == 1 or current_expire < now_ts:
            # Start new paid subscription from now
            new_expire = int((datetime.now() + timedelta(days=days)).timestamp())
        else:
            # User has ACTIVE paid subscription -> extend it
            new_expire = current_expire + (days * 86400)
        
        payload = {"expire": new_expire, "status": "active"}
        status, _ = await self.client._request("PUT", f"/user/{username}", payload)
        
        if status == 200:
            return await self.get_subscription_url(username)
        return None
    
    async def delete(self, username: str) -> bool:
        """Delete user"""
        status, _ = await self.client._request("DELETE", f"/user/{username}")
        return status == 200
    
    async def ban(self, username: str) -> bool:
        """Ban (disable) user"""
        return await self.update(username, status="disabled")
    
    async def unban(self, username: str) -> bool:
        """Unban (enable) user"""
        return await self.update(username, status="active")
    
    async def reset_traffic(self, username: str) -> bool:
        """Reset user's used traffic"""
        status, _ = await self.client._request("POST", f"/user/{username}/reset")
        return status == 200
    
    async def revoke_subscription(self, username: str) -> bool:
        """Revoke subscription URL (generate new token)"""
        status, _ = await self.client._request("POST", f"/user/{username}/revoke_sub")
        return status == 200
    
    async def get_subscription_url(self, username: str) -> Optional[str]:
        """
        Get subscription URL
        
        Args:
            username: Username
            
        Returns:
            Full subscription URL
        """
        user = await self.get(username)
        if not user:
            return None
        
        sub_url = user.get("subscription_url", "")
        if sub_url and sub_url.startswith("/"):
            base = self.client.base_url.replace("/api", "")
            return f"{base.rstrip('/')}{sub_url}"
        
        return sub_url
    
    async def get_usage(self, username: str) -> Optional[Dict[str, Any]]:
        """
        Get user usage statistics
        
        Returns:
            {"used_traffic": bytes, "lifetime_used_traffic": bytes, ...}
        """
        user = await self.get(username)
        if not user:
            return None
        
        return {
            "used_traffic": user.get("used_traffic", 0),
            "lifetime_used_traffic": user.get("lifetime_used_traffic", 0),
            "data_limit": user.get("data_limit", 0),
            "expire": user.get("expire", 0),
            "status": user.get("status", "unknown"),
        }
