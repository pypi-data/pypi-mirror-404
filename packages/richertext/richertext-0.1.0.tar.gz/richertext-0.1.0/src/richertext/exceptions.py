"""Custom exceptions for richertext."""


class RicherTextError(Exception):
    """Base exception for all richertext errors."""

    pass


class ConfigurationError(RicherTextError):
    """Raised when there's an error in configuration."""

    pass


class ProviderError(RicherTextError):
    """Raised when there's an error with an LLM provider."""

    pass
