import logging
from typing import Any

from ddx.rest_client.http.http_client import HTTPClient


class BaseClient:
    """
    Base class for all API clients.

    Provides common functionality and attributes used by all client classes.
    """

    def __init__(self, http: HTTPClient, base_url: str):
        """
        Initialize the base client.

        Parameters
        ----------
        http : HTTPClient
            The HTTP client to use for requests
        base_url : str
            The base URL for API endpoints
        """

        self._http = http
        self._base_url = base_url
        self._logger = logging.getLogger(self.__class__.__name__)

    def _build_url(self, endpoint_template: str, **path_params: Any) -> str:
        """
        Build a complete URL from the base URL and endpoint template.

        Supports both simple endpoints and those with path parameters.

        Parameters
        ----------
        endpoint_template : str
            The API endpoint path template, potentially with format placeholders
        **path_params : Any
            Path parameters to substitute into the endpoint template

        Returns
        -------
        str
            The complete URL with path parameters substituted

        Examples
        --------
        >>> self._build_url(Account.GET_TRADER)
        'https://testnet.derivadex.io/stats/api/v1/account'

        >>> self._build_url(Account.GET_STRATEGY_FEE_HISTORY, trader='0x123', strategyId='main')
        'https://testnet.derivadex.io/stats/api/v1/account/0x123/strategy/main/fees'
        """

        # First join the base URL with the endpoint template
        url = f"{self._base_url}{endpoint_template}"

        return url if not path_params else url.format(**path_params)
