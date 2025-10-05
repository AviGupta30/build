"""Errors for PexelsAPI"""

class PexelsError(Exception):
    """
    Base exception for this module
    """
class QuotaExceedError(PexelsError):
    """Raises when total request limit for the monthly period ends"""
    pass

class APIError(PexelsError):
    """Raises when an error occurs on the API"""
    pass

class InvalidTokenError(PexelsError):
    """Raises when given API Token is invalid"""
    pass