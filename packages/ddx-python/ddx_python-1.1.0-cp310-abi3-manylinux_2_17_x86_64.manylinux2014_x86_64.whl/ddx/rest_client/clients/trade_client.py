from typing import Optional, AsyncIterator

from ddx.rest_client.clients.base_client import BaseClient
from ddx.rest_client.constants.endpoints import Trade
from ddx.rest_client.models.trade import (
    FeesHistoryResponse,
    Fee,
    PositionsResponse,
    Position,
    StrategyResponse,
    StrategyMetricsResponse,
    TraderResponse,
    StrategiesResponse,
)


class TradeClient(BaseClient):
    """
    Trade-related operations and data access.

    Provides access to strategy fees, positions, metrics, and trader information
    through the API endpoints.
    """

    async def get_strategy_fees_history_page(
        self,
        trader: str,
        strategy_id: str,
        limit: Optional[int] = None,
        epoch: Optional[int] = None,
        tx_ordinal: Optional[int] = None,
        ordinal: Optional[int] = None,
        symbol: Optional[str] = None,
        order: Optional[str] = None,
    ) -> FeesHistoryResponse:
        """
        Get a single page of maker/taker fee aggregates for a strategy.

        Parameters
        ----------
        trader : str
            The trader address
        strategy_id : str
            The strategy ID
        limit : Optional[int]
            The number of rows to return
        epoch : Optional[int]
            The epoch boundary used when fetching the next timeseries page
        tx_ordinal : Optional[int]
            The txOrdinal boundary used when fetching the next timeseries page.
            Must be passed along with epoch
        ordinal : Optional[int]
            The ordinal boundary used when fetching the next timeseries page.
            Must be passed along with epoch and txOrdinal
        symbol : Optional[str]
            The symbol
        order : Optional[str]
            The ordering of the results. Values: "asc", "desc"

        Returns
        -------
        FeesHistoryResponse
            Single page of strategy fees history data
        """

        params = {
            "trader": trader,
            "strategyId": strategy_id,
            "limit": limit,
            "epoch": epoch,
            "txOrdinal": tx_ordinal,
            "ordinal": ordinal,
            "symbol": symbol,
            "order": order,
        }
        params = {k: v for k, v in params.items() if v is not None}

        response = await self._http.get(
            self._build_url(Trade.GET_STRATEGY_FEES_HISTORY), params=params
        )

        return FeesHistoryResponse.model_validate(response)

    async def get_strategy_fees_history(
        self,
        trader: str,
        strategy_id: str,
        symbol: Optional[str] = None,
        order: Optional[str] = None,
        limit: Optional[int] = 100,
    ) -> AsyncIterator[Fee]:
        """
        Get all maker/taker fee aggregates for a strategy.

        Automatically handles pagination using epoch, tx_ordinal, and ordinal.

        Parameters
        ----------
        trader : str
            The trader address
        strategy_id : str
            The strategy ID
        symbol : Optional[str]
            The symbol
        order : Optional[str]
            The ordering of the results. Values: "asc", "desc"
        limit : Optional[int]
            The number of rows to return per page

        Yields
        ------
        Fee
            Strategy fee entries
        """

        epoch = None
        tx_ordinal = None
        ordinal = None

        while True:
            response = await self.get_strategy_fees_history_page(
                trader=trader,
                strategy_id=strategy_id,
                limit=limit,
                epoch=epoch,
                tx_ordinal=tx_ordinal,
                ordinal=ordinal,
                symbol=symbol,
                order=order,
            )

            if not response.value:
                break

            for item in response.value:
                yield item

            if response.next_epoch is None:
                break

            epoch = response.next_epoch
            tx_ordinal = response.next_tx_ordinal
            ordinal = response.next_ordinal

    async def get_strategy_positions_page(
        self,
        trader: str,
        strategy_id: str,
        limit: Optional[int] = None,
        offset: Optional[int] = None,
        symbol: Optional[str] = None,
    ) -> PositionsResponse:
        """
        Get a single page of current positions for a strategy.

        Parameters
        ----------
        trader : str
            The trader address
        strategy_id : str
            The strategy ID
        limit : Optional[int]
            The number of rows to return
        offset : Optional[int]
            The offset of returned rows
        symbol : Optional[str]
            The symbol

        Returns
        -------
        PositionsResponse
            Single page of strategy positions data
        """

        params = {
            "trader": trader,
            "strategyId": strategy_id,
            "limit": limit,
            "offset": offset,
            "symbol": symbol,
        }
        params = {k: v for k, v in params.items() if v is not None}

        response = await self._http.get(
            self._build_url(Trade.GET_STRATEGY_POSITIONS), params=params
        )

        return PositionsResponse.model_validate(response)

    async def get_strategy_positions(
        self,
        trader: str,
        strategy_id: str,
        symbol: Optional[str] = None,
        limit: Optional[int] = 100,
    ) -> AsyncIterator[Position]:
        """
        Get all current positions for a strategy.

        Automatically handles pagination using offset.

        Parameters
        ----------
        trader : str
            The trader address
        strategy_id : str
            The strategy ID
        symbol : Optional[str]
            The symbol
        limit : Optional[int]
            The number of rows to return per page

        Yields
        ------
        Position
            Strategy position entries
        """

        offset = 0

        while True:
            response = await self.get_strategy_positions_page(
                trader=trader,
                strategy_id=strategy_id,
                limit=limit,
                offset=offset,
                symbol=symbol,
            )

            if not response.value:
                break

            for item in response.value:
                yield item

            if len(response.value) < limit:
                break

            offset += len(response.value)

    async def get_strategy(
        self,
        trader: str,
        strategy_id: str,
    ) -> StrategyResponse:
        """
        Get current state of trader's strategy.

        Parameters
        ----------
        trader : str
            The trader address
        strategy_id : str
            The strategy ID

        Returns
        -------
        StrategyResponse
            Strategy information including trader address, strategy ID hash,
            max leverage, available collateral, locked collateral, and frozen status
        """

        params = {
            "trader": trader,
            "strategyId": strategy_id,
        }

        response = await self._http.get(self._build_url(Trade.GET_STRATEGY), params=params)

        return StrategyResponse.model_validate(response)

    async def get_strategies(
        self,
        trader: str,
    ) -> StrategiesResponse:
        """
        Get current state of trader's strategies.

        Parameters
        ----------
        trader : str
            The trader address

        Returns
        -------
        StrategiesResponse
            Strategies information including trader address, strategy ID hash,
            max leverage, available collateral, locked collateral, and frozen status
        """

        params = {
            "trader": trader,
        }

        response = await self._http.get(self._build_url(Trade.GET_STRATEGIES), params=params)

        return StrategiesResponse.model_validate(response)

    async def get_strategy_metrics(
        self,
        trader: str,
        strategy_id: str,
    ) -> StrategyMetricsResponse:
        """
        Get KPIs and risk metrics for a strategy.

        Includes margin fraction, maintenance margin ratio, leverage,
        strategy available collateral and strategy value.

        Parameters
        ----------
        trader : str
            The trader address
        strategy_id : str
            The strategy ID

        Returns
        -------
        StrategyMetricsResponse
            Strategy metrics including margin fraction, MMR, leverage,
            strategy margin, and strategy value
        """

        params = {
            "trader": trader,
            "strategyId": strategy_id,
        }

        response = await self._http.get(self._build_url(Trade.GET_STRATEGY_METRICS), params=params)

        return StrategyMetricsResponse.model_validate(response)

    async def get_trader(
        self,
        trader: str,
    ) -> TraderResponse:
        """
        Get current trader DDX balance and profile.

        Parameters
        ----------
        trader : str
            The trader address

        Returns
        -------
        TraderResponse
            Trader information including DDX balances and fee payment preferences
        """

        params = {
            "trader": trader,
        }

        response = await self._http.get(self._build_url(Trade.GET_TRADER), params=params)

        return TraderResponse.model_validate(response)
