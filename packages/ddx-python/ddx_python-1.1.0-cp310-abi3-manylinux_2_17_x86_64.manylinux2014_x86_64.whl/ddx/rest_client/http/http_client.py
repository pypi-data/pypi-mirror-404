import asyncio
import json
from datetime import datetime
from typing import Optional, Dict, Any
import logging
from httpx import AsyncClient, Limits, RequestError

from ddx.rest_client.exceptions.exceptions import (
    InvalidRequestError,
    FailedRequestError,
)


class HTTPClient:
    """
    HTTP client for DerivaDEX API.

    Handles request preparation and response processing.
    """

    def __init__(
        self,
        timeout: int = 10,
        max_retries: int = 3,
        retry_delay: int = 1,
        max_connections: int = 100,
        max_keepalive: int = 20,
        keepalive_expiry: int = 5,
        logger: Optional[logging.Logger] = None,
    ):
        """
        Initialize the HTTP client.

        Parameters
        ----------
        timeout : int
            Request timeout in seconds
        max_retries : int
            Maximum number of retry attempts
        retry_delay : int
            Delay between retries in seconds
        max_connections : int, default=100
            Max concurrent connections allowed
        max_keepalive : int, optional
            Max allowable keep-alive connections, None means always allow
        keepalive_expiry: int, default=5
            Time in seconds to keep HTTP connection alive. None means connection never expires
        logger : Optional[logging.Logger]
            Logger instance
        """

        self.timeout = timeout
        self.max_retries = max_retries
        self.retry_delay = retry_delay
        self.max_connections = max_connections
        self.max_keepalive = max_keepalive
        self.keepalive_expiry = keepalive_expiry

        # Setup logging
        self.logger = logger or logging.getLogger(__name__)

        # Initialize client to None - will be created in __aenter__
        self.client: Optional[AsyncClient] = None

        # Define retry status codes
        self.retry_codes = {408, 429, 500, 502, 503, 504}

    async def __aenter__(self):
        """
        Context manager entry point. Initializes the HTTP client.

        Returns
        -------
        BaseHTTPClient
            The client instance
        """

        self.client = AsyncClient(
            timeout=self.timeout,
            follow_redirects=True,
            headers={"Content-Type": "application/json"},
            limits=Limits(
                max_keepalive_connections=self.max_keepalive,
                max_connections=self.max_connections,
                keepalive_expiry=self.keepalive_expiry
            )
        )
        self.logger.debug("HTTP client initialized")

        return self

    async def __aexit__(self, exc_type, exc_val, exc_tb):
        """
        Context manager exit point. Ensures proper cleanup of resources.

        Parameters
        ----------
        exc_type : Type[Exception], optional
            The exception type if an exception was raised
        exc_val : Exception, optional
            The exception value if an exception was raised
        exc_tb : TracebackType, optional
            The traceback if an exception was raised
        """

        if self.client:
            await self.client.aclose()
            self.client = None
            self.logger.debug("HTTP client closed")

    async def get(
        self,
        url: str,
        params: Optional[Dict[str, Any]] = None,
        headers: Optional[Dict[str, str]] = None,
    ) -> Dict[str, Any]:
        """
        Send a GET request.

        Parameters
        ----------
        url : str
            The URL to send the request to
        params : Optional[Dict[str, Any]]
            Query parameters
        headers : Optional[Dict[str, str]]
            Additional headers

        Returns
        -------
        Dict[str, Any]
            The response data

        Raises
        ------
        FailedRequestError
            If the request fails after retries
        InvalidRequestError
            If the API returns an error response
        """

        return await self._request("GET", url, params=params, headers=headers)

    async def post(
        self,
        url: str,
        data: Any = None,
        json_data: Optional[Dict[str, Any]] = None,
        headers: Optional[Dict[str, str]] = None,
    ) -> Dict[str, Any]:
        """
        Send a POST request.

        Parameters
        ----------
        url : str
            The URL to send the request to
        data : Any
            Raw request body
        json_data : Optional[Dict[str, Any]]
            JSON data to serialize
        headers : Optional[Dict[str, str]]
            Additional headers

        Returns
        -------
        Dict[str, Any]
            The response data

        Raises
        ------
        FailedRequestError
            If the request fails after retries
        InvalidRequestError
            If the API returns an error response
        """

        return await self._request(
            "POST", url, data=data, json_data=json_data, headers=headers
        )

    def _parse_json_or_failed(self, response, request_info) -> Dict[str, Any]:
        try:
            return response.json()
        except json.JSONDecodeError:
            raise FailedRequestError(
                request=request_info,
                message="Failed to parse JSON response",
                status_code=response.status_code,
                time=datetime.now().strftime("%H:%M:%S"),
                response={"text": response.text},
            )

    def _raise_from_response(self, response, request_info) -> None:
        try:
            body = response.json()
        except json.JSONDecodeError:
            raise FailedRequestError(
                request=request_info,
                message=f"Request failed with status {response.status_code}",
                status_code=response.status_code,
                time=datetime.now().strftime("%H:%M:%S"),
                response={"text": response.text},
            )
        if isinstance(body, dict):
            reason = body.get("error_reason")
            safety = body.get("safety_failure")
            message = body.get("message") or f"Request failed with status {response.status_code}"
            details = f"{reason}: {message}" if reason else message
            if safety:
                details = f"{details} (safety_failure={safety})"
            exc_cls = FailedRequestError if response.status_code >= 500 else InvalidRequestError
            raise exc_cls(
                request=request_info,
                message=details,
                status_code=response.status_code,
                time=datetime.now().strftime("%H:%M:%S"),
                response=body,
            )
        exc_cls = FailedRequestError if response.status_code >= 500 else InvalidRequestError
        raise exc_cls(
            request=request_info,
            message=f"Request failed with status {response.status_code}",
            status_code=response.status_code,
            time=datetime.now().strftime("%H:%M:%S"),
            response={"text": response.text},
        )

    async def _request(
        self,
        method: str,
        url: str,
        params: Optional[Dict[str, Any]] = None,
        data: Any = None,
        json_data: Optional[Dict[str, Any]] = None,
        headers: Optional[Dict[str, str]] = None,
    ) -> Dict[str, Any]:
        """
        Execute HTTP request with retries and error handling.

        Parameters
        ----------
        method : str
            HTTP method (GET, POST, etc.)
        url : str
            The URL to send the request to
        params : Optional[Dict[str, Any]]
            Query parameters
        data : Any
            Raw request body
        json_data : Optional[Dict[str, Any]]
            JSON data to serialize
        headers : Optional[Dict[str, str]]
            Additional headers

        Returns
        -------
        Dict[str, Any]
            The response data

        Raises
        ------
        FailedRequestError
            If the request fails after retries
        InvalidRequestError
            If the API returns an error response
        RuntimeError
            If the client is not initialized
        """

        if self.client is None:
            raise RuntimeError(
                "HTTP client not initialized. Use 'async with' context manager."
            )

        request_info = (
            f"{method} {url}; params: {params}; json: {json_data}; data: {data}"
        )

        self.logger.debug(f"Request: {request_info}")

        retries = 0
        while retries <= self.max_retries:
            try:
                response = await self.client.request(
                    method=method,
                    url=url,
                    params=params,
                    content=data,
                    json=json_data,
                    headers=headers,
                )

                # Log response status
                self.logger.debug(f"Response status: {response.status_code}")

                # Check if the request was successful
                if response.status_code == 200:
                    return self._parse_json_or_failed(response, request_info)

                # Handle retry-able status codes
                if (
                    response.status_code in self.retry_codes
                    and retries < self.max_retries
                ):
                    wait_time = self.retry_delay * (2**retries)
                    self.logger.warning(
                        f"Request failed with status {response.status_code}. "
                        f"Retrying in {wait_time}s ({retries+1}/{self.max_retries})"
                    )
                    await asyncio.sleep(wait_time)
                    retries += 1
                    continue

                # Non-retryable error or max retries reached
                self._raise_from_response(response, request_info)

            except RequestError as e:
                # Network-related errors
                if retries < self.max_retries:
                    wait_time = self.retry_delay * (2**retries)
                    self.logger.warning(
                        f"Request error: {str(e)}. "
                        f"Retrying in {wait_time}s ({retries+1}/{self.max_retries})"
                    )
                    await asyncio.sleep(wait_time)
                    retries += 1
                    continue

                raise FailedRequestError(
                    request=request_info,
                    message=f"Request error: {str(e)}",
                    status_code=0,
                    time=datetime.now().strftime("%H:%M:%S"),
                    response=None,
                )
