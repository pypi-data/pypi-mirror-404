from typing import Optional, Dict, Any


class HTTPClientError(Exception):
    """Base exception for HTTP client errors."""

    def __init__(
        self,
        request: str,
        message: str,
        status_code: int,
        time: str,
        response: Optional[Dict[str, Any]] = None,
    ):
        self.request = request
        self.message = message
        self.status_code = status_code
        self.time = time
        self.response = response
        super().__init__(f"{message} (Status: {status_code}, Time: {time})")


class InvalidRequestError(HTTPClientError):
    """Exception raised for API-specific errors."""

    pass


class FailedRequestError(HTTPClientError):
    """Exception raised for HTTP request failures."""

    pass
