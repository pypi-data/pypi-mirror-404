from __future__ import annotations


class CPZError(Exception):
    """Base SDK error."""


class CPZBrokerError(CPZError):
    """Broker-specific error mapped into CPZ domain."""


class BrokerNotRegistered(CPZError):
    def __init__(self, name: str) -> None:
        super().__init__(
            f"Broker '{name}' is not registered. Register an adapter or use a supported name (e.g., 'alpaca')."
        )


class CPZAuthenticationError(CPZError):
    """Authentication failed - invalid or expired credentials.
    
    Raised when API credentials are invalid, expired, or have been revoked.
    """


class CPZAuthorizationError(CPZError):
    """Authorization failed - insufficient permissions.
    
    Raised when the user doesn't have permission to access a resource (403).
    """


class CPZCredentialMissingError(CPZError):
    """Required credentials are missing.
    
    Raised when required API keys or broker credentials are not configured.
    Provides actionable guidance on how to configure credentials.
    """


class CPZDataProviderError(CPZError):
    """Error from a data provider (market data, SEC filings, etc.).
    
    Raised when there's an issue fetching data from external providers.
    """


class CPZConfigurationError(CPZError):
    """SDK configuration error.
    
    Raised when the SDK is misconfigured (invalid URLs, incompatible settings, etc.).
    """


class CPZRateLimitError(CPZError):
    """Rate limit exceeded.
    
    Raised when API rate limits are hit. Includes retry guidance.
    """
    
    def __init__(self, message: str, retry_after: float | None = None) -> None:
        super().__init__(message)
        self.retry_after = retry_after
