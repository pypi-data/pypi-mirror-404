"""
Veloce API - Python client library for Veloce VPN Panel

Copyright (c) 2026 Veloce VPN Panel
Licensed under the MIT License
"""

from .client import VeloceClient
from .exceptions import (
    VeloceAPIError,
    VeloceAuthError,
    VeloceNotFoundError,
    VeloceValidationError
)

__version__ = "1.0.0"
__author__ = "Veloce Team"
__license__ = "MIT"

__all__ = [
    "VeloceClient",
    "VeloceAPIError",
    "VeloceAuthError",
    "VeloceNotFoundError",
    "VeloceValidationError",
]
