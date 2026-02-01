"""
Custom exceptions for QuickSearch.
"""

class QuickSearchError(Exception):
    """Base exception for all QuickSearch errors."""
    pass


class ConnectionError(QuickSearchError):
    """Raised when MongoDB connection fails."""
    pass


class IndexError(QuickSearchError):
    """Raised when index operation fails."""
    pass


class CheckpointError(QuickSearchError):
    """Raised when checkpoint read/write fails."""
    pass


class SearchError(QuickSearchError):
    """Raised when search query fails."""
    pass


class ValidationError(QuickSearchError):
    """Raised when input validation fails."""
    pass
