from typing import Optional, AsyncIterator

from ddx.rest_client.clients.base_client import BaseClient
from ddx.rest_client.constants.endpoints import System
from ddx.rest_client.models.system import (
    ExchangeInfoResponse,
    PingResponse,
    SymbolsResponse,
    Symbol,
    ServerTimeResponse,
    CollateralAggregationResponse,
    CollateralAggregation,
    DDXAggregationResponse,
    DDXAggregation,
    InsuranceFundAggregationResponse,
    InsuranceFundAggregation,
    EpochHistoryResponse,
    Epoch,
    InsuranceFundHistoryResponse,
    InsuranceFund,
    SpecsResponse,
    Spec,
    ExchangeStatusResponse,
    DDXSupplyResponse,
    TradableProductsResponse,
    TradableProduct,
    DeploymentInfo,
)


class SystemClient(BaseClient):
    """
    System-related operations and data access.

    Provides access to exchange configuration, system status, and other
    system-related information through the API endpoints.
    """

    async def get_exchange_info(self) -> ExchangeInfoResponse:
        """
        Get global exchange configuration.

        Returns
        -------
        ExchangeInfoResponse
            Exchange configuration information including settlement info,
            supported assets, and trading symbols
        """

        response = await self._http.get(self._build_url(System.GET_EXCHANGE_INFO))

        return ExchangeInfoResponse.model_validate(response)

    async def get_connection_info(self) -> PingResponse:
        """
        Simple connectivity test.

        Returns
        -------
        PingResponse
            Empty response indicating successful connection
        """

        response = await self._http.get(self._build_url(System.GET_CONNECTION_INFO))

        return PingResponse.model_validate(response)

    async def get_symbols_page(
        self,
        kind: Optional[int] = None,
        is_active: Optional[bool] = None,
        limit: Optional[int] = None,
        offset: Optional[int] = None,
    ) -> SymbolsResponse:
        """
        Get a single page of SEO-friendly alias for tradable products.

        Parameters
        ----------
        kind : Optional[int]
            The type of spec update. Values: 0 (Market), 1 (SpotGateway)
        is_active : Optional[bool]
            Checks for the active state of the tradable product
        limit : Optional[int]
            The number of rows to return
        offset : Optional[int]
            The offset of returned rows

        Returns
        -------
        SymbolsResponse
            Single page of symbols data
        """

        params = {
            "kind": kind,
            "isActive": is_active,
            "limit": limit,
            "offset": offset,
        }
        params = {k: v for k, v in params.items() if v is not None}

        response = await self._http.get(
            self._build_url(System.GET_SYMBOLS), params=params
        )

        return SymbolsResponse.model_validate(response)

    async def get_symbols(
        self,
        kind: Optional[int] = None,
        is_active: Optional[bool] = None,
        limit: Optional[int] = 100,
    ) -> AsyncIterator[Symbol]:
        """
        Get all symbols.

        Automatically handles pagination using offset.

        Parameters
        ----------
        kind : Optional[int]
            The type of spec update. Values: 0 (Market), 1 (SpotGateway)
        is_active : Optional[bool]
            Checks for the active state of the tradable product
        limit : Optional[int]
            The number of rows to return per page

        Yields
        ------
        Symbol
            Symbol entries
        """

        offset = 0

        while True:
            response = await self.get_symbols_page(
                kind=kind,
                is_active=is_active,
                limit=limit,
                offset=offset,
            )

            if not response.value:
                break

            for item in response.value:
                yield item

            if len(response.value) < limit:
                break

            offset += len(response.value)

    async def get_server_time(self) -> ServerTimeResponse:
        """
        Get server time for clock synchronization.

        Returns
        -------
        ServerTimeResponse
            Server time in milliseconds
        """

        response = await self._http.get(self._build_url(System.GET_SERVER_TIME))

        return ServerTimeResponse.model_validate(response)

    async def get_collateral_aggregation_page(
        self,
        aggregation_period: Optional[str] = None,
        starting_value: Optional[float] = None,
        from_epoch: Optional[int] = None,
        to_epoch: Optional[int] = None,
    ) -> CollateralAggregationResponse:
        """
        Get a single page of collateral aggregation data.

        Returns a rolling sum of collateral per time period grouped by
        the inflow and outflow types.

        Parameters
        ----------
        aggregation_period : Optional[str]
            The period for the aggregation. Values: "week", "day", "hour", "minute"
        starting_value : Optional[float]
            The partial total of this aggregation, used for rolling aggregation paging
        from_epoch : Optional[int]
            The from epoch
        to_epoch : Optional[int]
            The to epoch

        Returns
        -------
        CollateralAggregationResponse
            Single page of collateral aggregation data
        """

        params = {
            "aggregationPeriod": aggregation_period,
            "startingValue": starting_value,
            "fromEpoch": from_epoch,
            "toEpoch": to_epoch,
        }
        params = {k: v for k, v in params.items() if v is not None}

        response = await self._http.get(
            self._build_url(System.GET_COLLATERAL_AGGREGATION), params=params
        )

        return CollateralAggregationResponse.model_validate(response)

    async def get_collateral_aggregation(
        self,
        aggregation_period: Optional[str] = None,
        from_epoch: Optional[int] = None,
        to_epoch: Optional[int] = None,
    ) -> AsyncIterator[CollateralAggregation]:
        """
        Get all collateral aggregation data.

        Automatically handles pagination using starting_value.

        Parameters
        ----------
        aggregation_period : Optional[str]
            The period for the aggregation. Values: "week", "day", "hour", "minute"
        from_epoch : Optional[int]
            The from epoch
        to_epoch : Optional[int]
            The to epoch

        Yields
        ------
        CollateralAggregation
            Collateral aggregation entries
        """

        starting_value = None

        while True:
            response = await self.get_collateral_aggregation_page(
                aggregation_period=aggregation_period,
                starting_value=starting_value,
                from_epoch=from_epoch,
                to_epoch=to_epoch,
            )

            if not response.value:
                break

            for item in response.value:
                yield item

            if response.next_starting_value is None:
                break

            starting_value = float(response.next_starting_value)

    async def get_ddx_aggregation_page(
        self,
        aggregation_period: Optional[str] = None,
        starting_value: Optional[float] = None,
        from_epoch: Optional[int] = None,
        to_epoch: Optional[int] = None,
    ) -> DDXAggregationResponse:
        """
        Get a single page of DDX aggregation data.

        Returns a rolling sum of DDX per time period grouped by
        the inflow and outflow types.

        Parameters
        ----------
        aggregation_period : Optional[str]
            The period for the aggregation. Values: "week", "day", "hour", "minute"
        starting_value : Optional[float]
            The partial total of this aggregation, used for rolling aggregation paging
        from_epoch : Optional[int]
            The from epoch
        to_epoch : Optional[int]
            The to epoch

        Returns
        -------
        DDXAggregationResponse
            Single page of DDX aggregation data
        """

        params = {
            "aggregationPeriod": aggregation_period,
            "startingValue": starting_value,
            "fromEpoch": from_epoch,
            "toEpoch": to_epoch,
        }
        params = {k: v for k, v in params.items() if v is not None}

        response = await self._http.get(
            self._build_url(System.GET_DDX_AGGREGATION), params=params
        )

        return DDXAggregationResponse.model_validate(response)

    async def get_ddx_aggregation(
        self,
        aggregation_period: Optional[str] = None,
        from_epoch: Optional[int] = None,
        to_epoch: Optional[int] = None,
    ) -> AsyncIterator[DDXAggregation]:
        """
        Get all DDX aggregation data.

        Automatically handles pagination using starting_value.

        Parameters
        ----------
        aggregation_period : Optional[str]
            The period for the aggregation. Values: "week", "day", "hour", "minute"
        from_epoch : Optional[int]
            The from epoch
        to_epoch : Optional[int]
            The to epoch

        Yields
        ------
        DDXAggregation
            DDX aggregation entries
        """

        starting_value = None

        while True:
            response = await self.get_ddx_aggregation_page(
                aggregation_period=aggregation_period,
                starting_value=starting_value,
                from_epoch=from_epoch,
                to_epoch=to_epoch,
            )

            if not response.value:
                break

            for item in response.value:
                yield item

            if response.next_starting_value is None:
                break

            starting_value = float(response.next_starting_value)

    async def get_insurance_fund_aggregation_page(
        self,
        aggregation_period: Optional[str] = None,
        starting_value: Optional[float] = None,
        from_epoch: Optional[int] = None,
        to_epoch: Optional[int] = None,
    ) -> InsuranceFundAggregationResponse:
        """
        Get a single page of insurance fund aggregation data.

        Returns a rolling sum of insurance fund value per time period
        grouped by the inflow and outflow types.

        Parameters
        ----------
        aggregation_period : Optional[str]
            The period for the aggregation. Values: "week", "day", "hour", "minute"
        starting_value : Optional[float]
            The partial total of this aggregation, used for rolling aggregation paging
        from_epoch : Optional[int]
            The from epoch
        to_epoch : Optional[int]
            The to epoch

        Returns
        -------
        InsuranceFundAggregationResponse
            Single page of insurance fund aggregation data
        """

        params = {
            "aggregationPeriod": aggregation_period,
            "startingValue": starting_value,
            "fromEpoch": from_epoch,
            "toEpoch": to_epoch,
        }
        params = {k: v for k, v in params.items() if v is not None}

        response = await self._http.get(
            self._build_url(System.GET_INSURANCE_FUND_AGGREGATION), params=params
        )

        return InsuranceFundAggregationResponse.model_validate(response)

    async def get_insurance_fund_aggregation(
        self,
        aggregation_period: Optional[str] = None,
        from_epoch: Optional[int] = None,
        to_epoch: Optional[int] = None,
    ) -> AsyncIterator[InsuranceFundAggregation]:
        """
        Get all insurance fund aggregation data.

        Automatically handles pagination using starting_value.

        Parameters
        ----------
        aggregation_period : Optional[str]
            The period for the aggregation. Values: "week", "day", "hour", "minute"
        from_epoch : Optional[int]
            The from epoch
        to_epoch : Optional[int]
            The to epoch

        Yields
        ------
        InsuranceFundAggregation
            Insurance fund aggregation entries
        """

        starting_value = None

        while True:
            response = await self.get_insurance_fund_aggregation_page(
                aggregation_period=aggregation_period,
                starting_value=starting_value,
                from_epoch=from_epoch,
                to_epoch=to_epoch,
            )

            if not response.value:
                break

            for item in response.value:
                yield item

            if response.next_starting_value is None:
                break

            starting_value = float(response.next_starting_value)

    async def get_epoch_history_page(
        self,
        epoch: Optional[int] = None,
        limit: Optional[int] = None,
        offset: Optional[int] = None,
    ) -> EpochHistoryResponse:
        """
        Get a single page of epoch timetable and paging cursors.

        Parameters
        ----------
        epoch : Optional[int]
            The epoch boundary used when fetching the next timeseries page
        limit : Optional[int]
            The number of rows to return
        offset : Optional[int]
            The offset of returned rows

        Returns
        -------
        EpochHistoryResponse
            Single page of epoch history data
        """

        params = {
            "epoch": epoch,
            "limit": limit,
            "offset": offset,
        }
        params = {k: v for k, v in params.items() if v is not None}

        response = await self._http.get(
            self._build_url(System.GET_EPOCH_HISTORY), params=params
        )

        return EpochHistoryResponse.model_validate(response)

    async def get_epoch_history(
        self,
        epoch: Optional[int] = None,
        limit: Optional[int] = 100,
    ) -> AsyncIterator[Epoch]:
        """
        Get all epoch history data.

        Automatically handles pagination using offset.

        Parameters
        ----------
        epoch : Optional[int]
            The epoch boundary used when fetching the next timeseries page
        limit : Optional[int]
            The number of rows to return per page

        Yields
        ------
        Epoch
            Epoch entries
        """

        offset = 0

        while True:
            response = await self.get_epoch_history_page(
                epoch=epoch,
                limit=limit,
                offset=offset,
            )

            if not response.value:
                break

            for item in response.value:
                yield item

            if len(response.value) < limit:
                break

            offset += len(response.value)

    async def get_insurance_fund_history_page(
        self,
        limit: Optional[int] = None,
        epoch: Optional[int] = None,
        tx_ordinal: Optional[int] = None,
        order: Optional[str] = None,
        symbol: Optional[str] = None,
    ) -> InsuranceFundHistoryResponse:
        """
        Get a single page of insurance fund balance history.

        Parameters
        ----------
        limit : Optional[int]
            The number of rows to return
        epoch : Optional[int]
            The epoch boundary used when fetching the next timeseries page
        tx_ordinal : Optional[int]
            The txOrdinal boundary used when fetching the next timeseries page.
            Must be passed along with epoch
        order : Optional[str]
            The ordering of the results. Values: "asc", "desc"
        symbol : Optional[str]
            The symbol

        Returns
        -------
        InsuranceFundHistoryResponse
            Single page of insurance fund history data
        """

        params = {
            "limit": limit,
            "epoch": epoch,
            "txOrdinal": tx_ordinal,
            "order": order,
            "symbol": symbol,
        }
        params = {k: v for k, v in params.items() if v is not None}

        response = await self._http.get(
            self._build_url(System.GET_INSURANCE_FUND_HISTORY), params=params
        )

        return InsuranceFundHistoryResponse.model_validate(response)

    async def get_insurance_fund_history(
        self,
        order: Optional[str] = None,
        symbol: Optional[str] = None,
        limit: Optional[int] = 100,
    ) -> AsyncIterator[InsuranceFund]:
        """
        Get all insurance fund history data.

        Automatically handles pagination using epoch and tx_ordinal.

        Parameters
        ----------
        order : Optional[str]
            The ordering of the results. Values: "asc", "desc"
        symbol : Optional[str]
            The symbol
        limit : Optional[int]
            The number of rows to return per page

        Yields
        ------
        InsuranceFund
            Insurance fund history entries
        """

        epoch = None
        tx_ordinal = None

        while True:
            response = await self.get_insurance_fund_history_page(
                limit=limit,
                epoch=epoch,
                tx_ordinal=tx_ordinal,
                order=order,
                symbol=symbol,
            )

            if not response.value:
                break

            for item in response.value:
                yield item

            if response.next_epoch is None:
                break

            epoch = response.next_epoch
            tx_ordinal = response.next_tx_ordinal

    async def get_specs_page(
        self,
        kind: Optional[int] = None,
        limit: Optional[int] = None,
        offset: Optional[int] = None,
    ) -> SpecsResponse:
        """
        Get a single page of current operator configuration settings.

        Parameters
        ----------
        kind : Optional[int]
            The type of spec update. Values: 0 (Market), 1 (SpotGateway)
        limit : Optional[int]
            The number of rows to return
        offset : Optional[int]
            The offset of returned rows

        Returns
        -------
        SpecsResponse
            Single page of specs data
        """

        params = {
            "kind": kind,
            "limit": limit,
            "offset": offset,
        }
        params = {k: v for k, v in params.items() if v is not None}

        response = await self._http.get(
            self._build_url(System.GET_SPECS), params=params
        )

        return SpecsResponse.model_validate(response)

    async def get_specs(
        self,
        kind: Optional[int] = None,
        limit: Optional[int] = 100,
    ) -> AsyncIterator[Spec]:
        """
        Get all operator configuration settings.

        Automatically handles pagination using offset.

        Parameters
        ----------
        kind : Optional[int]
            The type of spec update. Values: 0 (Market), 1 (SpotGateway)
        limit : Optional[int]
            The number of rows to return per page

        Yields
        ------
        Spec
            Spec entries
        """

        offset = 0

        while True:
            response = await self.get_specs_page(
                kind=kind,
                limit=limit,
                offset=offset,
            )

            if not response.value:
                break

            for item in response.value:
                yield item

            if len(response.value) < limit:
                break

            offset += len(response.value)

    async def get_exchange_status(self) -> ExchangeStatusResponse:
        """
        Get high-level exchange status information.

        Returns
        -------
        ExchangeStatusResponse
            Exchange status information including current epoch,
            latest on-chain checkpoint, and active addresses
        """

        response = await self._http.get(self._build_url(System.GET_EXCHANGE_STATUS))

        return ExchangeStatusResponse.model_validate(response)

    async def get_ddx_supply(self) -> DDXSupplyResponse:
        """
        Get total DDX circulation information.

        Returns
        -------
        DDXSupplyResponse
            DDX supply information including circulating supply
        """

        response = await self._http.get(self._build_url(System.GET_DDX_SUPPLY))

        return DDXSupplyResponse.model_validate(response)

    async def get_tradable_products_page(
        self,
        kind: Optional[int] = None,
        is_active: Optional[bool] = None,
        limit: Optional[int] = None,
        offset: Optional[int] = None,
    ) -> TradableProductsResponse:
        """
        Get a single page of available trading products.

        Parameters
        ----------
        kind : Optional[int]
            The type of spec update. Values: 0 (Market), 1 (SpotGateway)
        is_active : Optional[bool]
            Checks for the active state of the tradable product
        limit : Optional[int]
            The number of rows to return
        offset : Optional[int]
            The offset of returned rows

        Returns
        -------
        TradableProductsResponse
            Single page of tradable products data
        """

        params = {
            "kind": kind,
            "isActive": is_active,
            "limit": limit,
            "offset": offset,
        }
        params = {k: v for k, v in params.items() if v is not None}

        response = await self._http.get(
            self._build_url(System.GET_TRADABLE_PRODUCTS), params=params
        )

        return TradableProductsResponse.model_validate(response)

    async def get_tradable_products(
        self,
        kind: Optional[int] = None,
        is_active: Optional[bool] = None,
        limit: Optional[int] = 100,
    ) -> AsyncIterator[TradableProduct]:
        """
        Get all available trading products.

        Automatically handles pagination using offset.

        Parameters
        ----------
        kind : Optional[int]
            The type of spec update. Values: 0 (Market), 1 (SpotGateway)
        is_active : Optional[bool]
            Checks for the active state of the tradable product
        limit : Optional[int]
            The number of rows to return per page

        Yields
        ------
        TradableProduct
            Tradable product entries
        """

        offset = 0

        while True:
            response = await self.get_tradable_products_page(
                kind=kind,
                is_active=is_active,
                limit=limit,
                offset=offset,
            )

            if not response.value:
                break

            for item in response.value:
                yield item

            if len(response.value) < limit:
                break

            offset += len(response.value)

    async def get_deployment_info(self, contract_deployment: str) -> DeploymentInfo:
        """
        Get deployment information including contract addresses.

        Parameters
        ----------
        contract_deployment : str, default="testnet"
            The deployment environment to get information for

        Returns
        -------
        DeploymentInfo
            Deployment information including contract addresses

        Raises
        ------
        HTTPError
            If the request fails
        """

        params = {"contractDeployment": contract_deployment}

        # Make the request
        response = await self._http.get(
            self._build_url(System.GET_DEPLOYMENT_INFO), params=params
        )

        return DeploymentInfo.model_validate(response)
