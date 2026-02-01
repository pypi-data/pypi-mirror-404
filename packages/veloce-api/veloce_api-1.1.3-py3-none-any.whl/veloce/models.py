"""
Pydantic models for type-safe API responses
"""

from typing import Optional, Dict, Any, List
from datetime import datetime
from pydantic import BaseModel, Field


class UserResponse(BaseModel):
    """User data response model"""
    username: str
    status: str
    expire: int = 0
    data_limit: int = 0
    data_limit_reset_strategy: str = "no_reset"
    used_traffic: int = 0
    lifetime_used_traffic: int = 0
    created_at: Optional[datetime] = None
    sub_updated_at: Optional[datetime] = None
    subscription_url: Optional[str] = None
    proxies: Dict[str, Any] = Field(default_factory=dict)
    inbounds: Dict[str, List[str]] = Field(default_factory=dict)
    note: Optional[str] = None
    online_at: Optional[datetime] = None


class NodeResponse(BaseModel):
    """Node data response model"""
    id: int
    name: str
    address: str
    port: int = 62050
    api_port: int = 62051
    usage_coefficient: float = 1.0
    status: str = "connected"
    message: Optional[str] = None


class SystemStats(BaseModel):
    """System statistics response"""
    total_user: int = 0
    users_active: int = 0
    incoming_bandwidth: int = 0
    outgoing_bandwidth: int = 0
    incoming_bandwidth_speed: int = 0
    outgoing_bandwidth_speed: int = 0


class APIKeyResponse(BaseModel):
    """API key response (for listing)"""
    id: int
    name: str
    created_at: datetime
    last_used_at: Optional[datetime] = None
    last_ip: Optional[str] = None
    is_active: bool = True


class APIKeyCreated(BaseModel):
    """API key response when created (includes actual key)"""
    id: int
    name: str
    key: str  # Only shown once!
    created_at: datetime
