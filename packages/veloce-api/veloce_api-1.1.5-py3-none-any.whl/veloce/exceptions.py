"""
Custom exceptions for Veloce API
"""


class VeloceAPIError(Exception):
    """Base exception for all Veloce API errors"""
    
    def __init__(self, message: str, status_code: int = None, response: dict = None):
        self.message = message
        self.status_code = status_code
        self.response = response or {}
        super().__init__(self.message)
    
    def __str__(self):
        if self.status_code:
            return f"[{self.status_code}] {self.message}"
        return self.message


class VeloceAuthError(VeloceAPIError):
    """Authentication/authorization failed (401/403)"""
    pass


class VeloceNotFoundError(VeloceAPIError):
    """Resource not found (404)"""
    pass


class VeloceValidationError(VeloceAPIError):
    """Request validation failed (400/422)"""
    pass


class VeloceConflictError(VeloceAPIError):
    """Resource already exists (409)"""
    pass


class VeloceServerError(VeloceAPIError):
    """Server error (500+)"""
    pass
