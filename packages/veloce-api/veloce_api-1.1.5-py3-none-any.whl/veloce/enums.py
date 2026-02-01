"""
Shared enums and constants
"""

from enum import Enum


class UserStatus(str, Enum):
    """User status enum"""
    ACTIVE = "active"
    DISABLED = "disabled"
    LIMITED = "limited"
    EXPIRED = "expired"
    FREE = "free"
    ON_HOLD = "on_hold"


class UserStatusCreate(str, Enum):
    """Allowed statuses for user creation"""
    ACTIVE = "active"
    ON_HOLD = "on_hold"


class UserStatusModify(str, Enum):
    """Allowed statuses for user modification"""
    ACTIVE = "active"
    DISABLED = "disabled"
    ON_HOLD = "on_hold"


class DataLimitResetStrategy(str, Enum):
    """Data limit reset strategy"""
    NO_RESET = "no_reset"
    DAY = "day"
    WEEK = "week"
    MONTH = "month"
    YEAR = "year"


class ProxyType(str, Enum):
    """Proxy protocols"""
    VMESS = "vmess"
    VLESS = "vless"
    TROJAN = "trojan"
    SHADOWSOCKS = "shadowsocks"


class SortOrder(str, Enum):
    """Sort order for list queries"""
    ASC = "asc"
    DESC = "desc"
