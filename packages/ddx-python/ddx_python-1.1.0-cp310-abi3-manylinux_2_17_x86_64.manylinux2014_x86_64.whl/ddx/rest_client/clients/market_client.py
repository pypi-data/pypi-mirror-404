from typing import Optional, AsyncIterator, Dict

from ddx.rest_client.constants.endpoints import System, Market
from ddx.rest_client.clients.base_client import BaseClient
from ddx.rest_client.models.market import (
    MarkPriceHistoryResponse,
    MarkPrice,
    OrderBookL3Response,
    OrderUpdateHistoryResponse,
    OrderUpdate,
    StrategyUpdateHistoryResponse,
    StrategyUpdate,
    TickersResponse,
    TraderUpdateHistoryResponse,
    TraderUpdate,
    BalanceAggregationResponse,
    FeesAggregationResponse,
    FeesAggregation,
    FundingRateComparisonResponse,
    TopTradersAggregationResponse,
    TopTrader,
    VolumeAggregationResponse,
    VolumeAggregation,
    FundingRateHistoryResponse,
    FundingRateHistory,
    OpenInterestHistoryResponse,
    OrderBook,
    OrderBookL2Response,
    PriceCheckpointHistoryResponse,
    PriceCheckpoint,
)


class MarketClient(BaseClient):
    """
    System-related operations and data access.

    Provides access to exchange configuration, system status, and other
    system-related information through the API endpoints.
    """

    async def get_mark_price_history_page(
        self,
        limit: Optional[int] = None,
        epoch: Optional[int] = None,
        symbol: Optional[str] = None,
        order: Optional[str] = None,
        global_ordinal: Optional[int] = None,
    ) -> MarkPriceHistoryResponse:
        """
        Get a single page of mark prices over time.

        Parameters
        ----------
        limit : Optional[int]
            The number of rows to return
        epoch : Optional[int]
            The epoch boundary used when fetching the next timeseries page
        symbol : Optional[str]
            The symbol
        order : Optional[str]
            The ordering of the results. Values: "asc", "desc"
        global_ordinal : Optional[int]
            The global ordinal boundary used when fetching the next timeseries page

        Returns
        -------
        MarkPriceHistoryResponse
            Single page of mark price history data
        """

        params = {
            "limit": limit,
            "epoch": epoch,
            "symbol": symbol,
            "order": order,
            "globalOrdinal": global_ordinal,
        }
        params = {k: v for k, v in params.items() if v is not None}

        response = await self._http.get(
            self._build_url(Market.GET_MARK_PRICE_HISTORY), params=params
        )

        return MarkPriceHistoryResponse.model_validate(response)

    async def get_mark_price_history(
        self,
        epoch: Optional[int] = None,
        symbol: Optional[str] = None,
        order: Optional[str] = None,
        limit: Optional[int] = 100,
    ) -> AsyncIterator[MarkPrice]:
        """
        Get all mark price history data.

        Automatically handles pagination using global_ordinal.

        Parameters
        ----------
        epoch : Optional[int]
            The epoch boundary used when fetching the next timeseries page
        symbol : Optional[str]
            The symbol
        order : Optional[str]
            The ordering of the results. Values: "asc", "desc"
        limit : Optional[int]
            The number of rows to return per page

        Yields
        ------
        MarkPrice
            Mark price history entries
        """

        global_ordinal = None

        while True:
            response = await self.get_mark_price_history_page(
                limit=limit,
                epoch=epoch,
                symbol=symbol,
                order=order,
                global_ordinal=global_ordinal,
            )

            if not response.value:
                break

            for item in response.value:
                yield item

            if response.next_global_ordinal is None:
                break

            global_ordinal = response.next_global_ordinal

    async def get_order_book_l3(
        self,
        trader: Optional[str] = None,
        strategy_id_hash: Optional[str] = None,
        depth: Optional[int] = None,
        symbol: Optional[str] = None,
        side: Optional[int] = None,
    ) -> OrderBookL3Response:
        """
        Get current L3 order book.

        Parameters
        ----------
        trader : Optional[str]
            The trader address, with the discriminant prefix
        strategy_id_hash : Optional[str]
            The strategy id hash
        depth : Optional[int]
            The best N bids and asks to return, where N = depth
        symbol : Optional[str]
            The symbol
        side : Optional[int]
            The side of the order. Values: 0 (Bid), 1 (Ask)

        Returns
        -------
        OrderBookL3Response
            L3 order book data with individual orders
        """

        params = {
            "trader": trader,
            "strategyIdHash": strategy_id_hash,
            "depth": depth,
            "symbol": symbol,
            "side": side,
        }
        params = {k: v for k, v in params.items() if v is not None}

        response = await self._http.get(
            self._build_url(Market.GET_ORDER_BOOK_L3), params=params
        )

        return OrderBookL3Response.model_validate(response)

    async def get_order_update_history_page(
        self,
        trader: Optional[str] = None,
        strategy_id_hash: Optional[str] = None,
        limit: Optional[int] = None,
        global_ordinal: Optional[int] = None,
        order: Optional[str] = None,
        symbol: Optional[str] = None,
        order_hash: Optional[str] = None,
        reason: Optional[int] = None,
        since: Optional[int] = None,
    ) -> OrderUpdateHistoryResponse:
        """
        Get a single page of order updates (trades, liquidations, cancels).

        Parameters
        ----------
        trader : Optional[str]
            The trader address, with the discriminant prefix
        strategy_id_hash : Optional[str]
            The strategy id hash
        limit : Optional[int]
            The number of rows to return
        global_ordinal : Optional[int]
            The global ordinal boundary used when fetching the next timeseries page
        order : Optional[str]
            The ordering of the results. Values: "asc", "desc"
        symbol : Optional[str]
            The symbol
        order_hash : Optional[str]
            The order hash of the order intent. Multiple order hash values can be provided
        reason : Optional[int]
            The reason for the creation of this row. Multiple reason values can be provided.
            Values: 0 (Trade), 1 (Liquidation), 2 (Cancel), 3 (Order Rejection), 4 (Cancel Rejection)
        since : Optional[int]
            The earliest time in seconds to fetch rows for. This param cannot be used together with param order = 'desc'

        Returns
        -------
        OrderUpdateHistoryResponse
            Single page of order update history data
        """

        params = {
            "trader": trader,
            "strategyIdHash": strategy_id_hash,
            "limit": limit,
            "globalOrdinal": global_ordinal,
            "order": order,
            "symbol": symbol,
            "orderHash": order_hash,
            "reason": reason,
            "since": since,
        }
        params = {k: v for k, v in params.items() if v is not None}

        response = await self._http.get(
            self._build_url(Market.GET_ORDER_UPDATE_HISTORY), params=params
        )

        return OrderUpdateHistoryResponse.model_validate(response)

    async def get_order_update_history(
        self,
        trader: Optional[str] = None,
        strategy_id_hash: Optional[str] = None,
        order: Optional[str] = None,
        symbol: Optional[str] = None,
        order_hash: Optional[str] = None,
        reason: Optional[int] = None,
        since: Optional[int] = None,
        limit: Optional[int] = 100,
    ) -> AsyncIterator[OrderUpdate]:
        """
        Get all order updates (trades, liquidations, cancels).

        Automatically handles pagination using global_ordinal.

        Parameters
        ----------
        trader : Optional[str]
            The trader address, with the discriminant prefix
        strategy_id_hash : Optional[str]
            The strategy id hash
        order : Optional[str]
            The ordering of the results. Values: "asc", "desc"
        symbol : Optional[str]
            The symbol
        order_hash : Optional[str]
            The order hash of the order intent. Multiple order hash values can be provided
        reason : Optional[int]
            The reason for the creation of this row. Multiple reason values can be provided.
            Values: 0 (Trade), 1 (Liquidation), 2 (Cancel), 3 (Order Rejection), 4 (Cancel Rejection)
        since : Optional[int]
            The earliest time in seconds to fetch rows for. This param cannot be used together with param order = 'desc'
        limit : Optional[int]
            The number of rows to return per page

        Yields
        ------
        OrderUpdate
            Order update entries
        """

        global_ordinal = None

        while True:
            response = await self.get_order_update_history_page(
                trader=trader,
                strategy_id_hash=strategy_id_hash,
                limit=limit,
                global_ordinal=global_ordinal,
                order=order,
                symbol=symbol,
                order_hash=order_hash,
                reason=reason,
                since=since,
            )

            if not response.value:
                break

            for item in response.value:
                yield item

            if response.next_global_ordinal is None:
                break

            global_ordinal = response.next_global_ordinal

    async def get_strategy_update_history_page(
        self,
        trader: Optional[str] = None,
        strategy_id_hash: Optional[str] = None,
        reason: Optional[int] = None,
        limit: Optional[int] = None,
        global_ordinal: Optional[int] = None,
        order: Optional[str] = None,
    ) -> StrategyUpdateHistoryResponse:
        """
        Get a single page of strategy updates over time.

        Parameters
        ----------
        trader : Optional[str]
            The trader address, with the discriminant prefix
        strategy_id_hash : Optional[str]
            The strategy id hash
        reason : Optional[int]
            The type of strategy update. Multiple strategy update values can be provided.
            Values: 0 (Deposit), 1 (Withdraw), 2 (WithdrawIntent), 3 (FundingPayment),
            4 (RealizedPnl), 5 (Liquidation), 6 (ADL), 7 (Withdraw Rejection)
        limit : Optional[int]
            The number of rows to return
        global_ordinal : Optional[int]
            The global ordinal boundary used when fetching the next timeseries page
        order : Optional[str]
            The ordering of the results. Values: "asc", "desc"

        Returns
        -------
        StrategyUpdateHistoryResponse
            Single page of strategy update history data
        """

        params = {
            "trader": trader,
            "strategyIdHash": strategy_id_hash,
            "reason": reason,
            "limit": limit,
            "globalOrdinal": global_ordinal,
            "order": order,
        }
        params = {k: v for k, v in params.items() if v is not None}

        response = await self._http.get(
            self._build_url(Market.GET_STRATEGY_UPDATE_HISTORY), params=params
        )

        return StrategyUpdateHistoryResponse.model_validate(response)

    async def get_strategy_update_history(
        self,
        trader: Optional[str] = None,
        strategy_id_hash: Optional[str] = None,
        reason: Optional[int] = None,
        order: Optional[str] = None,
        limit: Optional[int] = 100,
    ) -> AsyncIterator[StrategyUpdate]:
        """
        Get all strategy updates over time.

        Automatically handles pagination using global_ordinal.

        Parameters
        ----------
        trader : Optional[str]
            The trader address, with the discriminant prefix
        strategy_id_hash : Optional[str]
            The strategy id hash
        reason : Optional[int]
            The type of strategy update. Multiple strategy update values can be provided.
            Values: 0 (Deposit), 1 (Withdraw), 2 (WithdrawIntent), 3 (FundingPayment),
            4 (RealizedPnl), 5 (Liquidation), 6 (ADL), 7 (Withdraw Rejection)
        order : Optional[str]
            The ordering of the results. Values: "asc", "desc"
        limit : Optional[int]
            The number of rows to return per page

        Yields
        ------
        StrategyUpdate
            Strategy update entries
        """

        global_ordinal = None

        while True:
            response = await self.get_strategy_update_history_page(
                trader=trader,
                strategy_id_hash=strategy_id_hash,
                reason=reason,
                limit=limit,
                global_ordinal=global_ordinal,
                order=order,
            )

            if not response.value:
                break

            for item in response.value:
                yield item

            if response.next_global_ordinal is None:
                break

            global_ordinal = response.next_global_ordinal

    async def get_tickers(
        self,
        symbol: Optional[str] = None,
        market_kind: Optional[int] = None,
    ) -> TickersResponse:
        """
        Get convenient market tickers data.

        Includes funding rate and open interest data, price related data,
        and trading volume in the last 24 hours.

        Parameters
        ----------
        symbol : Optional[str]
            The symbol
        market_kind : Optional[int]
            The type of markets to return data for. Values: 0 (SingleNamePerpetual),
            2 (IndexFundPerpetual), 4 (FixedExpiryFuture).

        Returns
        -------
        TickersResponse
            Market ticker data for requested symbols and market kinds
        """

        params = {
            "symbol": symbol,
            "marketKind": market_kind,
        }
        params = {k: v for k, v in params.items() if v is not None}

        response = await self._http.get(
            self._build_url(Market.GET_TICKERS), params=params
        )

        return TickersResponse.model_validate(response)

    async def get_trader_update_history_page(
        self,
        trader: Optional[str] = None,
        reason: Optional[int] = None,
        limit: Optional[int] = None,
        global_ordinal: Optional[int] = None,
        order: Optional[str] = None,
    ) -> TraderUpdateHistoryResponse:
        """
        Get a single page of trader DDX balance and profile updates over time.

        Parameters
        ----------
        trader : Optional[str]
            The trader address, with the discriminant prefix
        reason : Optional[int]
            The type of trader update. Multiple trader update values can be provided.
            Values: 0 (Deposit), 1 (WithdrawDDX), 2 (WithdrawDDXIntent),
            3 (TradeMiningReward), 4 (ProfileUpdate), 5 (FeeDistribution),
            6 (Admission), 7 (Denial), 8 (Fee),
            9 (WithdrawDDXRejection)
        limit : Optional[int]
            The number of rows to return
        global_ordinal : Optional[int]
            The global ordinal boundary used when fetching the next timeseries page
        order : Optional[str]
            The ordering of the results. Values: "asc", "desc"

        Returns
        -------
        TraderUpdateHistoryResponse
            Single page of trader update history data
        """

        params = {
            "trader": trader,
            "reason": reason,
            "limit": limit,
            "globalOrdinal": global_ordinal,
            "order": order,
        }
        params = {k: v for k, v in params.items() if v is not None}

        response = await self._http.get(
            self._build_url(Market.GET_TRADER_UPDATE_HISTORY), params=params
        )

        return TraderUpdateHistoryResponse.model_validate(response)

    async def get_trader_update_history(
        self,
        trader: Optional[str] = None,
        reason: Optional[int] = None,
        order: Optional[str] = None,
        limit: Optional[int] = 100,
    ) -> AsyncIterator[TraderUpdate]:
        """
        Get all trader DDX balance and profile updates over time.

        Automatically handles pagination using global_ordinal.

        Parameters
        ----------
        trader : Optional[str]
            The trader address, with the discriminant prefix
        reason : Optional[int]
            The type of trader update. Multiple trader update values can be provided.
            Values: 0 (Deposit), 1 (WithdrawDDX), 2 (WithdrawDDXIntent),
            3 (TradeMiningReward), 4 (ProfileUpdate), 5 (FeeDistribution),
            6 (Admission), 7 (Denial), 8 (Fee),
            9 (WithdrawDDXRejection)
        order : Optional[str]
            The ordering of the results. Values: "asc", "desc"
        limit : Optional[int]
            The number of rows to return per page

        Yields
        ------
        TraderUpdate
            Trader update history entries
        """

        global_ordinal = None

        while True:
            response = await self.get_trader_update_history_page(
                trader=trader,
                reason=reason,
                limit=limit,
                global_ordinal=global_ordinal,
                order=order,
            )

            if not response.value:
                break

            for item in response.value:
                yield item

            if response.next_global_ordinal is None:
                break

            global_ordinal = response.next_global_ordinal

    async def get_balance_aggregation(
        self,
        trader: Optional[str] = None,
        strategy_id: Optional[str] = None,
        limit: Optional[int] = None,
        aggregation_period: Optional[str] = None,
        lookback_count: Optional[int] = None,
    ) -> BalanceAggregationResponse:
        """
        Get the change of trader's balance for a specific strategy over a specific time period.

        Returns the change of trader's balance for a specific strategy over a specific
        time period, looking back from the present.

        Parameters
        ----------
        trader : Optional[str]
            The trader address, with the discriminant prefix
        strategy_id : Optional[str]
            The strategy ID
        limit : Optional[int]
            The number of rows to return
        aggregation_period : Optional[str]
            The period for the aggregation. Values: "week", "day", "hour", "minute"
        lookback_count : Optional[int]
            The number of periods to look back from present

        Returns
        -------
        BalanceAggregationResponse
            Balance aggregation data showing trader balance changes over time
        """

        params = {
            "trader": trader,
            "strategyId": strategy_id,
            "limit": limit,
            "aggregationPeriod": aggregation_period,
            "lookbackCount": lookback_count,
        }
        params = {k: v for k, v in params.items() if v is not None}

        response = await self._http.get(
            self._build_url(Market.GET_BALANCE_AGGREGATION), params=params
        )

        return BalanceAggregationResponse.model_validate(response)

    async def get_fees_aggregation_page(
        self,
        group: str,
        symbol: Optional[str] = None,
        fee_symbol: Optional[str] = None,
        aggregation_period: Optional[str] = None,
        lookback_count: Optional[int] = None,
        lookback_timestamp: Optional[int] = None,
    ) -> FeesAggregationResponse:
        """
        Get a single page of fees aggregation data.

        Returns fees per time period looking back from the present.

        Parameters
        ----------
        group : str
            The grouping for the aggregation. Values: "symbol", "feeSymbol"
        symbol : Optional[str]
            The symbol
        fee_symbol : Optional[str]
            The fee symbol. Values: "USDC", "DDX"
        aggregation_period : Optional[str]
            The period for the aggregation. Values: "week", "day", "hour", "minute"
        lookback_count : Optional[int]
            The number of periods to look back from present
        lookback_timestamp : Optional[int]
            The timestamp of the when to begin the lookback from. Each lookback query
            will return nextLookbackTimestamp in the response, which can be passed as
            a query parameter here to get the next page of results

        Returns
        -------
        FeesAggregationResponse
            Single page of fees aggregation data
        """

        params = {
            "group": group,
            "symbol": symbol,
            "feeSymbol": fee_symbol,
            "aggregationPeriod": aggregation_period,
            "lookbackCount": lookback_count,
            "lookbackTimestamp": lookback_timestamp,
        }
        params = {k: v for k, v in params.items() if v is not None}

        response = await self._http.get(
            self._build_url(Market.GET_FEES_AGGREGATION), params=params
        )

        return FeesAggregationResponse.model_validate(response)

    async def get_fees_aggregation(
        self,
        group: str,
        symbol: Optional[str] = None,
        fee_symbol: Optional[str] = None,
        aggregation_period: Optional[str] = None,
        lookback_count: Optional[int] = None,
    ) -> AsyncIterator[FeesAggregation]:
        """
        Get all fees aggregation data.

        Automatically handles pagination using lookback_timestamp.

        Parameters
        ----------
        group : str
            The grouping for the aggregation. Values: "symbol", "feeSymbol"
        symbol : Optional[str]
            The symbol
        fee_symbol : Optional[str]
            The fee symbol. Values: "USDC", "DDX"
        aggregation_period : Optional[str]
            The period for the aggregation. Values: "week", "day", "hour", "minute"
        lookback_count : Optional[int]
            The number of periods to look back from present

        Yields
        ------
        FeesAggregation
            Fees aggregation entries
        """

        lookback_timestamp = None

        while True:
            response = await self.get_fees_aggregation_page(
                group=group,
                symbol=symbol,
                fee_symbol=fee_symbol,
                aggregation_period=aggregation_period,
                lookback_count=lookback_count,
                lookback_timestamp=lookback_timestamp,
            )

            if not response.value:
                break

            for item in response.value:
                yield item

            if response.next_lookback_timestamp is None:
                break

            lookback_timestamp = response.next_lookback_timestamp

    async def get_funding_rate_comparison_aggregation(
        self,
        symbol: Optional[str] = None,
    ) -> FundingRateComparisonResponse:
        """
        Get funding rate comparison data between DerivaDEX and major exchanges.

        Parameters
        ----------
        symbol : Optional[str]
            The symbol

        Returns
        -------
        FundingRateComparisonResponse
            Funding rate comparison data showing rates and arbitrage opportunities
            between DerivaDEX and other major exchanges (Binance, Bybit, Hyperliquid)
        """

        params = {
            "symbol": symbol,
        }
        params = {k: v for k, v in params.items() if v is not None}

        response = await self._http.get(
            self._build_url(Market.GET_FUNDING_RATE_COMPARISON_AGGREGATION),
            params=params,
        )

        return FundingRateComparisonResponse.model_validate(response)

    async def get_top_traders_aggregation_page(
        self,
        trader: Optional[str] = None,
        limit: Optional[int] = None,
        cursor: Optional[int] = None,
        top_traders_ordering: Optional[str] = None,
        order: Optional[str] = None,
    ) -> TopTradersAggregationResponse:
        """
        Get a single page of top N traders by volume.

        Parameters
        ----------
        trader : Optional[str]
            The trader address, with the discriminant prefix
        limit : Optional[int]
            The number of rows to return
        cursor : Optional[int]
            The cursor for the beginning of the next page of top traders to fetch
        top_traders_ordering : Optional[str]
            The order by which to fetch top traders. Values: "volume", "pnl", "accountValue"
        order : Optional[str]
            The ordering of the results. Values: "asc", "desc"

        Returns
        -------
        TopTradersAggregationResponse
            Single page of top traders aggregation data
        """

        params = {
            "trader": trader,
            "limit": limit,
            "cursor": cursor,
            "topTradersOrdering": top_traders_ordering,
            "order": order,
        }
        params = {k: v for k, v in params.items() if v is not None}

        response = await self._http.get(
            self._build_url(Market.GET_TOP_TRADERS_AGGREGATION), params=params
        )

        return TopTradersAggregationResponse.model_validate(response)

    async def get_top_traders_aggregation(
        self,
        trader: Optional[str] = None,
        top_traders_ordering: Optional[str] = None,
        order: Optional[str] = None,
        limit: Optional[int] = 100,
    ) -> AsyncIterator[TopTrader]:
        """
        Get all top traders data.

        Automatically handles pagination using cursor.

        Parameters
        ----------
        trader : Optional[str]
            The trader address, with the discriminant prefix
        top_traders_ordering : Optional[str]
            The order by which to fetch top traders. Values: "volume", "pnl", "accountValue"
        order : Optional[str]
            The ordering of the results. Values: "asc", "desc"
        limit : Optional[int]
            The number of rows to return per page

        Yields
        ------
        TopTrader
            Top trader entries
        """

        cursor = None

        while True:
            response = await self.get_top_traders_aggregation_page(
                trader=trader,
                limit=limit,
                cursor=cursor,
                top_traders_ordering=top_traders_ordering,
                order=order,
            )

            if not response.value:
                break

            for item in response.value:
                yield item

            if response.next_cursor is None:
                break

            cursor = response.next_cursor

    async def get_volume_aggregation_page(
        self,
        group: Optional[str] = None,
        symbol: Optional[str] = None,
        aggregation_period: Optional[str] = None,
        lookback_count: Optional[int] = None,
        lookback_timestamp: Optional[int] = None,
    ) -> VolumeAggregationResponse:
        """
        Get a single page of volume aggregation data.

        Returns volume per time period looking back from the present.

        Parameters
        ----------
        group : Optional[str]
            The grouping for the aggregation. Values: "symbol"
        symbol : Optional[str]
            The symbol
        aggregation_period : Optional[str]
            The period for the aggregation. Values: "week", "day", "hour", "minute"
        lookback_count : Optional[int]
            The number of periods to look back from present
        lookback_timestamp : Optional[int]
            The timestamp of the when to begin the lookback from. Each lookback query
            will return nextLookbackTimestamp in the response, which can be passed as
            a query parameter here to get the next page of results

        Returns
        -------
        VolumeAggregationResponse
            Single page of volume aggregation data
        """

        params = {
            "group": group,
            "symbol": symbol,
            "aggregationPeriod": aggregation_period,
            "lookbackCount": lookback_count,
            "lookbackTimestamp": lookback_timestamp,
        }
        params = {k: v for k, v in params.items() if v is not None}

        response = await self._http.get(
            self._build_url(Market.GET_VOLUME_AGGREGATION), params=params
        )

        return VolumeAggregationResponse.model_validate(response)

    async def get_volume_aggregation(
        self,
        group: Optional[str] = None,
        symbol: Optional[str] = None,
        aggregation_period: Optional[str] = None,
        lookback_count: Optional[int] = None,
    ) -> AsyncIterator[VolumeAggregation]:
        """
        Get all volume aggregation data.

        Automatically handles pagination using lookback_timestamp.

        Parameters
        ----------
        group : Optional[str]
            The grouping for the aggregation. Values: "symbol"
        symbol : Optional[str]
            The symbol
        aggregation_period : Optional[str]
            The period for the aggregation. Values: "week", "day", "hour", "minute"
        lookback_count : Optional[int]
            The number of periods to look back from present

        Yields
        ------
        VolumeAggregation
            Volume aggregation entries
        """

        lookback_timestamp = None

        while True:
            response = await self.get_volume_aggregation_page(
                group=group,
                symbol=symbol,
                aggregation_period=aggregation_period,
                lookback_count=lookback_count,
                lookback_timestamp=lookback_timestamp,
            )

            if not response.value:
                break

            for item in response.value:
                yield item

            if response.next_lookback_timestamp is None:
                break

            lookback_timestamp = response.next_lookback_timestamp

    async def get_funding_rate_history_page(
        self,
        limit: Optional[int] = None,
        epoch: Optional[int] = None,
        tx_ordinal: Optional[int] = None,
        order: Optional[str] = None,
        symbol: Optional[str] = None,
        since: Optional[int] = None,
    ) -> FundingRateHistoryResponse:
        """
        Get a single page of funding rates over time.

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
        since : Optional[int]
            The earliest time in seconds to fetch rows for.
            This param cannot be used together with param order = 'desc'

        Returns
        -------
        FundingRateHistoryResponse
            Single page of funding rate history data
        """

        params = {
            "limit": limit,
            "epoch": epoch,
            "txOrdinal": tx_ordinal,
            "order": order,
            "symbol": symbol,
            "since": since,
        }
        params = {k: v for k, v in params.items() if v is not None}

        response = await self._http.get(
            self._build_url(Market.GET_FUNDING_RATE_HISTORY), params=params
        )

        return FundingRateHistoryResponse.model_validate(response)

    async def get_funding_rate_history(
        self,
        order: Optional[str] = None,
        symbol: Optional[str] = None,
        since: Optional[int] = None,
        limit: Optional[int] = 100,
    ) -> AsyncIterator[FundingRateHistory]:
        """
        Get all funding rate history data.

        Automatically handles pagination using epoch and tx_ordinal.

        Parameters
        ----------
        order : Optional[str]
            The ordering of the results. Values: "asc", "desc"
        symbol : Optional[str]
            The symbol
        since : Optional[int]
            The earliest time in seconds to fetch rows for.
            This param cannot be used together with param order = 'desc'
        limit : Optional[int]
            The number of rows to return per page

        Yields
        ------
        FundingRateHistory
            Funding rate history entries
        """

        epoch = None
        tx_ordinal = None

        while True:
            response = await self.get_funding_rate_history_page(
                limit=limit,
                epoch=epoch,
                tx_ordinal=tx_ordinal,
                order=order,
                symbol=symbol,
                since=since,
            )

            if not response.value:
                break

            for item in response.value:
                yield item

            if response.next_epoch is None:
                break

            epoch = response.next_epoch
            tx_ordinal = response.next_tx_ordinal

    async def get_open_interest_history(
        self,
        limit: Optional[int] = None,
        order: Optional[str] = None,
        symbol: Optional[str] = None,
        interval: Optional[str] = None,
        since: Optional[int] = None,
    ) -> OpenInterestHistoryResponse:
        """
        Get open interest over time.

        Parameters
        ----------
        limit : Optional[int]
            The number of rows to return
        order : Optional[str]
            The ordering of the results. Values: "asc", "desc"
        symbol : Optional[str]
            The symbol
        interval : Optional[str]
            The interval for open interest history. Values: "5m", "1h", "1d"
        since : Optional[int]
            The earliest time in seconds to fetch rows for. This param cannot be
            used together with param order = 'desc'

        Returns
        -------
        OpenInterestHistoryResponse
            Open interest history data
        """

        params = {
            "limit": limit,
            "order": order,
            "symbol": symbol,
            "interval": interval,
            "since": since,
        }
        params = {k: v for k, v in params.items() if v is not None}

        response = await self._http.get(
            self._build_url(Market.GET_OPEN_INTEREST_HISTORY), params=params
        )

        return OpenInterestHistoryResponse.model_validate(response)

    async def get_order_book_l2(
        self,
        symbol: Optional[str] = None,
        depth: Optional[int] = None,
        side: Optional[int] = None,
        price_aggregation: Optional[float] = None,
    ) -> Dict[str, OrderBook]:
        """
        Get current L2 aggregated order book.

        Parameters
        ----------
        symbol : Optional[str]
            The symbol
        depth : Optional[int]
            The best N bids and asks to return, where N = depth
        side : Optional[int]
            The side of the order. Values: 0 (Bid), 1 (Ask)
        price_aggregation : Optional[float]
            The price aggregation to use for the L2 orderbook.
            Valid values for each symbol include: ETHP: 0.1, 1, 10; BTCP: 1, 10, 100

        Returns
        -------
        Dict[str, OrderBook]
            Dictionary mapping symbols to their respective order books
        """

        params = {
            "symbol": symbol,
            "depth": depth,
            "side": side,
            "priceAggregation": price_aggregation,
        }
        params = {k: v for k, v in params.items() if v is not None}

        response = await self._http.get(
            self._build_url(Market.GET_ORDER_BOOK_L2), params=params
        )

        order_book_response = OrderBookL2Response.model_validate(response)

        return OrderBook.from_response(order_book_response, symbol)

    async def get_price_checkpoint_history_page(
        self,
        limit: Optional[int] = None,
        epoch: Optional[int] = None,
        tx_ordinal: Optional[int] = None,
        order: Optional[str] = None,
        symbol: Optional[str] = None,
        price_hash: Optional[str] = None,
    ) -> PriceCheckpointHistoryResponse:
        """
        Get a single page of price checkpoints over time.

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
        price_hash : Optional[str]
            The index price hash of the mark price. Multiple price hash values can be provided

        Returns
        -------
        PriceCheckpointHistoryResponse
            Single page of price checkpoint history data
        """

        params = {
            "limit": limit,
            "epoch": epoch,
            "txOrdinal": tx_ordinal,
            "order": order,
            "symbol": symbol,
            "priceHash": price_hash,
        }
        params = {k: v for k, v in params.items() if v is not None}

        response = await self._http.get(
            self._build_url(Market.GET_PRICE_CHECKPOINT_HISTORY), params=params
        )

        return PriceCheckpointHistoryResponse.model_validate(response)

    async def get_price_checkpoint_history(
        self,
        order: Optional[str] = None,
        symbol: Optional[str] = None,
        price_hash: Optional[str] = None,
        limit: Optional[int] = 100,
    ) -> AsyncIterator[PriceCheckpoint]:
        """
        Get all price checkpoints over time.

        Automatically handles pagination using epoch and tx_ordinal.

        Parameters
        ----------
        order : Optional[str]
            The ordering of the results. Values: "asc", "desc"
        symbol : Optional[str]
            The symbol
        price_hash : Optional[str]
            The index price hash of the mark price. Multiple price hash values can be provided
        limit : Optional[int]
            The number of rows to return per page

        Yields
        ------
        PriceCheckpoint
            Price checkpoint entries
        """

        epoch = None
        tx_ordinal = None

        while True:
            response = await self.get_price_checkpoint_history_page(
                limit=limit,
                epoch=epoch,
                tx_ordinal=tx_ordinal,
                order=order,
                symbol=symbol,
                price_hash=price_hash,
            )

            if not response.value:
                break

            for item in response.value:
                yield item

            if response.next_epoch is None:
                break

            epoch = response.next_epoch
            tx_ordinal = response.next_tx_ordinal
