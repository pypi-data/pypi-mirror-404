from datetime import datetime
from typing import List, Literal, Optional, Dict
from ddx._rust.common.state import BookOrder
from pydantic import Field, ConfigDict, field_validator
from ddx.models.base import (
    CamelModel,
    CancelRejection,
    HexStr,
    OrderRejection,
    OrderUpdateReason,
    PositionSide,
    StrategyUpdateReason,
    TraderUpdateReason,
    WithdrawDDXRejection,
    WithdrawRejection,
    validate_decimal_str,
    TradeSide,
    OrderType,
)
from dataclasses import dataclass
from itertools import groupby
from operator import attrgetter

from ddx._rust.decimal import Decimal


# Mark Price History Models
class MarkPrice(CamelModel):
    """Mark price data model."""

    global_ordinal: int = Field(..., ge=0)
    epoch_id: int = Field(..., ge=0)
    symbol: str
    price: str
    funding_rate: str
    created_at: datetime

    @field_validator("price")
    @classmethod
    def validate_nonnegative_decimals(cls, v, info):
        return validate_decimal_str(v, f"MarkPrice.{info.field_name}", nonnegative=True)

    @field_validator("funding_rate")
    @classmethod
    def validate_decimals(cls, v, info):
        return validate_decimal_str(
            v, f"MarkPrice.{info.field_name}", nonnegative=False
        )


class MarkPriceHistoryResponse(CamelModel):
    """Response model for mark price history endpoint."""

    next_global_ordinal: Optional[int] = Field(None, ge=0)
    value: List[MarkPrice]
    success: bool
    timestamp: int


# Order Book L3 Models
class OrderBookL3Entry(CamelModel):
    """L3 order book entry model."""

    book_ordinal: int = Field(..., ge=0)
    order_hash: HexStr
    symbol: str
    side: TradeSide
    original_amount: str
    amount: str
    price: str
    trader_address: HexStr
    strategy_id_hash: HexStr

    def raw_book_order(self) -> BookOrder:
        return BookOrder(
            self.side.raw_order_side(),
            Decimal(self.amount),
            Decimal(self.price),
            self.trader_address,
            self.strategy_id_hash,
            self.book_ordinal,
            0,
        )

    @field_validator("original_amount", "amount", "price")
    @classmethod
    def validate_nonnegative_decimals(cls, v, info):
        return validate_decimal_str(
            v, f"OrderBookL3.{info.field_name}", nonnegative=True
        )


class OrderBookL3Response(CamelModel):
    """Response model for L3 order book endpoint."""

    value: List[OrderBookL3Entry]
    success: bool
    timestamp: int


# Order Update History Models
class OrderIntent(CamelModel):
    """Order intent data model."""

    epoch_id: int = Field(..., ge=0)
    order_hash: HexStr
    symbol: str
    side: TradeSide
    amount: str
    price: str
    trader_address: HexStr
    strategy_id_hash: HexStr
    order_type: OrderType
    stop_price: str
    nonce: str
    signature: HexStr
    created_at: datetime

    @field_validator("amount", "price", "stop_price")
    @classmethod
    def validate_nonnegative_decimals(cls, v, info):
        return validate_decimal_str(
            v, f"OrderIntent.{info.field_name}", nonnegative=True
        )


class OrderUpdate(CamelModel):
    """Order update data model."""

    global_ordinal: int = Field(..., ge=0)
    epoch_id: int = Field(..., ge=0)
    tx_ordinal: int = Field(..., ge=0)
    ordinal: int = Field(..., ge=0)
    order_rejection: Optional[OrderRejection] = None
    cancel_rejection: Optional[CancelRejection] = None
    reason: OrderUpdateReason
    amount: Optional[str] = None
    quote_asset_amount: Optional[str] = None
    symbol: str
    price: Optional[str] = None
    maker_fee_collateral: Optional[str] = None
    maker_fee_ddx: Optional[str] = Field(default=None, alias="makerFeeDDX")
    maker_realized_pnl: Optional[str] = None
    taker_order_intent: Optional[OrderIntent] = None
    taker_fee_collateral: Optional[str] = None
    taker_fee_ddx: Optional[str] = Field(default=None, alias="takerFeeDDX")
    taker_realized_pnl: Optional[str] = None
    liquidated_trader_address: Optional[HexStr] = None
    liquidated_strategy_id_hash: Optional[HexStr] = None
    maker_order_intent: OrderIntent
    created_at: datetime

    @field_validator(
        "amount",
        "quote_asset_amount",
        "price",
        "maker_fee_collateral",
        "maker_fee_ddx",
        "taker_fee_collateral",
        "taker_fee_ddx",
    )
    @classmethod
    def validate_nonnegative_optional_decimals(cls, v, info):
        if v is None:
            return v
        return validate_decimal_str(
            v, f"OrderUpdate.{info.field_name}", nonnegative=True
        )

    @field_validator("maker_realized_pnl", "taker_realized_pnl")
    @classmethod
    def validate_optional_decimals(cls, v, info):
        if v is None:
            return v
        return validate_decimal_str(
            v, f"OrderUpdate.{info.field_name}", nonnegative=False
        )


class OrderUpdateHistoryResponse(CamelModel):
    """Response model for order update history endpoint."""

    next_global_ordinal: Optional[int] = Field(None, ge=0)
    value: List[OrderUpdate]
    success: bool
    timestamp: int


# Strategy Update History Models
class StrategyPositionUpdate(CamelModel):
    """Strategy position update data within a strategy update."""

    symbol: str
    side: Optional[PositionSide] = None
    avg_entry_price: Optional[str] = Field(
        None, description="New average entry price after RealizedPnl strategy update"
    )
    realized_pnl: str = Field(
        ..., description="Realized PnL after RealizedPnl or ADL strategy update"
    )

    @field_validator("avg_entry_price")
    @classmethod
    def validate_nonnegative_decimals(cls, v, info):
        return validate_decimal_str(
            v, f"StrategyPositionUpdate.{info.field_name}", nonnegative=True
        )

    @field_validator("realized_pnl")
    @classmethod
    def validate_decimals(cls, v, info):
        return validate_decimal_str(
            v, f"StrategyPositionUpdate.{info.field_name}", nonnegative=False
        )


class StrategyUpdate(CamelModel):
    """Strategy update data model."""

    global_ordinal: int = Field(..., ge=0)
    epoch_id: int = Field(..., ge=0)
    tx_ordinal: int = Field(..., ge=0)
    ordinal: int = Field(..., ge=0)
    withdraw_rejection: Optional[WithdrawRejection] = None
    reason: StrategyUpdateReason
    trader_address: HexStr
    strategy_id_hash: HexStr
    collateral_address: HexStr
    collateral_symbol: Literal["USDC"]
    amount: Optional[str] = None
    new_avail_collateral: Optional[str] = None
    new_locked_collateral: Optional[str] = None
    block_number: Optional[int] = Field(None, ge=0)
    positions: Optional[List[StrategyPositionUpdate]] = None
    created_at: datetime

    @field_validator("amount", "new_avail_collateral", "new_locked_collateral")
    @classmethod
    def validate_nonnegative_optional_decimals(cls, v, info):
        if v is None:
            return v
        return validate_decimal_str(
            v, f"StrategyUpdate.{info.field_name}", nonnegative=True
        )


class StrategyUpdateHistoryResponse(CamelModel):
    """Response model for strategy update history endpoint."""

    next_global_ordinal: Optional[int] = Field(None, ge=0)
    value: List[StrategyUpdate]
    success: bool
    timestamp: int


# Ticker Models
class Ticker(CamelModel):
    """Market ticker data model."""

    symbol: str
    high_price_24h: str
    low_price_24h: str
    prev_price_24h: str
    last_price: str
    mark_price: str
    index_price: str
    next_funding_time: datetime
    volume_24h: str
    amount_24h: Optional[str] = None
    funding_rate: str
    open_interest: str
    open_interest_value: str


class TickersResponse(CamelModel):
    """Response model for tickers endpoint."""

    value: List[Ticker]
    success: bool
    timestamp: int


# Trader Update History Models
class TraderUpdate(CamelModel):
    """Trader update data model."""

    global_ordinal: int = Field(..., ge=0)
    epoch_id: int = Field(..., ge=0)
    tx_ordinal: int = Field(..., ge=0)
    ordinal: int = Field(..., ge=0)
    withdraw_ddx_rejection: Optional[WithdrawDDXRejection] = Field(
        default=None, alias="withdrawDDXRejection"
    )
    reason: TraderUpdateReason
    trader_address: HexStr
    amount: Optional[str] = None
    new_avail_ddx_balance: Optional[str] = Field(
        default=None, alias="newAvailDDXBalance"
    )
    new_locked_ddx_balance: Optional[str] = Field(
        default=None, alias="newLockedDDXBalance"
    )
    pay_fees_in_ddx: Optional[bool] = Field(default=None, alias="payFeesInDDX")
    block_number: Optional[int] = None
    created_at: datetime

    @field_validator("new_avail_ddx_balance", "new_locked_ddx_balance")
    @classmethod
    def validate_nonnegative_optional_decimals(cls, v, info):
        if v is None:
            return v
        return validate_decimal_str(
            v, f"TraderUpdate.{info.field_name}", nonnegative=True
        )

    @field_validator("amount")
    @classmethod
    def validate_optional_decimals(cls, v, info):
        if v is None:
            return v
        return validate_decimal_str(
            v, f"TraderUpdate.{info.field_name}", nonnegative=False
        )


class TraderUpdateHistoryResponse(CamelModel):
    """Response model for trader update history endpoint."""

    next_global_ordinal: Optional[int] = Field(None, ge=0)
    value: List[TraderUpdate]
    success: bool
    timestamp: int


# Balance Aggregation Models
class BalanceAggregation(CamelModel):
    """Balance aggregation data model."""

    trader: HexStr
    strategy_id_hash: HexStr
    amount: str
    timestamp: int

    @field_validator("amount")
    @classmethod
    def validate_decimals(cls, v, info):
        return validate_decimal_str(
            v, f"BalanceAggregation.{info.field_name}", nonnegative=False
        )


class BalanceAggregationResponse(CamelModel):
    """Response model for balance aggregation endpoint."""

    value: List[BalanceAggregation]
    success: bool
    timestamp: int


# Fees Aggregation Models
class FeesAggregation(CamelModel):
    """Fees aggregation data model."""

    model_config = CamelModel.model_config | ConfigDict(extra="allow")

    timestamp: int

    def get_fees_value(self, fee_symbol: Optional[str] = None) -> Optional[str]:
        """Get fees value for a specific fee symbol (e.g., 'USDC', 'DDX')."""
        return getattr(self, f"fees_{fee_symbol}", None)


class FeesAggregationResponse(CamelModel):
    """Response model for fees aggregation endpoint."""

    next_lookback_timestamp: Optional[int] = Field(None, ge=0)
    value: List[FeesAggregation]
    success: bool
    timestamp: int


# Funding Rate Comparison Models
class FundingRateComparison(CamelModel):
    """Funding rate comparison data model."""

    symbol: str
    derivadex_funding_rate: str
    binance_funding_rate: str
    derivadex_binance_arbitrage: str
    bybit_funding_rate: str
    derivadex_bybit_arbitrage: str
    hyperliquid_funding_rate: str
    derivadex_hyperliquid_arbitrage: str

    @field_validator(
        "derivadex_funding_rate",
        "binance_funding_rate",
        "bybit_funding_rate",
        "derivadex_binance_arbitrage",
        "derivadex_bybit_arbitrage",
        "hyperliquid_funding_rate",
        "derivadex_hyperliquid_arbitrage",
    )
    @classmethod
    def validate_decimals(cls, v, info):
        return validate_decimal_str(
            v, f"FundingRateComparison.{info.field_name}", nonnegative=False
        )


class FundingRateComparisonResponse(CamelModel):
    """Response model for funding rate comparison aggregation endpoint."""

    value: List[FundingRateComparison]
    success: bool
    timestamp: int


# Top Traders Models
class TopTrader(CamelModel):
    """Top trader data model."""

    trader: HexStr
    volume: Optional[str] = None
    realized_pnl: Optional[str] = None
    account_value: Optional[str] = None

    @field_validator("volume", "account_value")
    @classmethod
    def validate_nonnegative_optional_decimals(cls, v, info):
        if v is None:
            return v
        return validate_decimal_str(v, f"TopTrader.{info.field_name}", nonnegative=True)

    @field_validator("realized_pnl")
    @classmethod
    def validate_optional_decimals(cls, v, info):
        if v is None:
            return v
        return validate_decimal_str(
            v, f"TopTrader.{info.field_name}", nonnegative=False
        )


class TopTradersAggregationResponse(CamelModel):
    """Response model for top traders endpoint."""

    value: List[TopTrader]
    next_cursor: Optional[int] = None
    success: bool
    timestamp: int


# Volume Aggregation Models
class VolumeAggregation(CamelModel):
    """Volume aggregation data model."""

    model_config = CamelModel.model_config | ConfigDict(extra="allow")

    timestamp: int

    def get_volume_value(self, field_name: str) -> Optional[str]:
        """Get value for a specific volume field."""
        return getattr(self, f"volume_{field_name}", None)


class VolumeAggregationResponse(CamelModel):
    """Response model for volume aggregation endpoint."""

    model_config = CamelModel.model_config | ConfigDict(extra="allow")

    next_lookback_timestamp: Optional[int] = Field(None, ge=0)
    value: List[VolumeAggregation]
    success: bool
    timestamp: int


# Funding Rate History Models
class FundingRateHistory(CamelModel):
    """Funding rate history data model."""

    epoch_id: int = Field(..., ge=0)
    tx_ordinal: int = Field(..., ge=0)
    symbol: str
    funding_rate: str
    created_at: datetime

    @field_validator("funding_rate")
    @classmethod
    def validate_decimals(cls, v, info):
        return validate_decimal_str(
            v, f"FundingRateHistory.{info.field_name}", nonnegative=False
        )


class FundingRateHistoryResponse(CamelModel):
    """Response model for funding rate history endpoint."""

    value: List[FundingRateHistory]
    next_epoch: Optional[int] = Field(None, ge=0)
    next_tx_ordinal: Optional[int] = Field(None, ge=0)
    next_ordinal: Optional[int] = Field(None, ge=0)
    success: bool
    timestamp: int


# Open Interest History Models
class OpenInterestHistory(CamelModel):
    """Open interest history data model."""

    symbol: str
    amount: str
    created_at: datetime

    @field_validator("amount")
    @classmethod
    def validate_nonnegative_decimals(cls, v, info):
        return validate_decimal_str(
            v, f"OpenInterestHistory.{info.field_name}", nonnegative=True
        )


class OpenInterestHistoryResponse(CamelModel):
    """Response model for open interest history endpoint."""

    value: List[OpenInterestHistory]
    success: bool
    timestamp: int


# Order Book L2 Models
class OrderBookL2Entry(CamelModel):
    """L2 order book item model."""

    symbol: str
    amount: str
    price: str
    side: TradeSide

    @field_validator("amount", "price")
    @classmethod
    def validate_nonnegative_decimals(cls, v, info):
        return validate_decimal_str(
            v, f"OrderBookL2.{info.field_name}", nonnegative=True
        )


class OrderBookL2Response(CamelModel):
    """Response model for L2 order book endpoint."""

    value: List[OrderBookL2Entry]
    success: bool
    timestamp: int


@dataclass
class OrderBook:
    """
    Complete order book for a single market.

    Attributes
    ----------
    symbol : str
        The symbol of the market
    bids : List[OrderBookL2Item]
        List of bid orders, sorted by price (descending)
    asks : List[OrderBookL2Item]
        List of ask orders, sorted by price (ascending)
    timestamp : int
        Timestamp of the order book snapshot
    """

    symbol: str
    bids: List[OrderBookL2Entry]
    asks: List[OrderBookL2Entry]
    timestamp: int

    @classmethod
    def from_order_book_l2_items(
        cls, symbol: str, order_book_l2_items: List[OrderBookL2Entry], timestamp: int
    ) -> "OrderBook":
        """
        Create instance from a list of entries for a single symbol.

        Parameters
        ----------
        symbol : str
            The market symbol
        order_book_l2_items : List[OrderBookL2Item]
            List of order book entries for this symbol
        timestamp : int
            Timestamp of the order book snapshot

        Returns
        -------
        OrderBook
            Initialized instance
        """
        # Filter and sort bids (descending)
        bids = [e for e in order_book_l2_items if e.side == TradeSide.BID]
        bids.sort(key=lambda x: Decimal(x.price), reverse=True)

        # Filter and sort asks (ascending)
        asks = [e for e in order_book_l2_items if e.side == TradeSide.ASK]
        asks.sort(key=lambda x: Decimal(x.price))

        return cls(symbol=symbol, bids=bids, asks=asks, timestamp=timestamp)

    @classmethod
    def from_response(
        cls, response: OrderBookL2Response, symbol: Optional[str] = None
    ) -> Dict[str, "OrderBook"]:
        """
        Create OrderBook instance(s) from response data.

        Parameters
        ----------
        response : OrderBookL2Response
            Parsed response from the API
        symbol : Optional[str]
            If provided, only return order book for this symbol

        Returns
        -------
        Dict[str, OrderBook]
            Dictionary mapping symbols to their respective order books
        """
        if not response.value:
            return {}

        # If specific symbol requested, filter first
        items = response.value
        if symbol:
            items = [item for item in items if item.symbol == symbol]
            if not items:
                return {}

        # Group entries by symbol
        items_sorted = sorted(items, key=attrgetter("symbol"))
        grouped = groupby(items_sorted, key=attrgetter("symbol"))

        # Create order books for each symbol
        order_books = {}
        for sym, entries in grouped:
            entry_list = list(entries)
            if entry_list:  # Only create order book if there are entries
                order_books[sym] = cls.from_order_book_l2_items(
                    sym, entry_list, response.timestamp
                )

        return order_books


class PriceCheckpoint(CamelModel):
    """Price checkpoint data model."""

    epoch_id: int = Field(..., ge=0)
    tx_ordinal: int = Field(..., ge=0)
    index_price_hash: HexStr
    symbol: str
    index_price: str
    mark_price: str
    time: int = Field(..., ge=0)
    ema: Optional[str] = None
    price_ordinal: int = Field(..., ge=0)
    created_at: datetime

    @field_validator("index_price", "mark_price")
    @classmethod
    def validate_nonnegative_decimals(cls, v, info):
        return validate_decimal_str(
            v, f"PriceCheckpoint.{info.field_name}", nonnegative=True
        )

    @field_validator("ema")
    @classmethod
    def validate_optional_decimals(cls, v, info):
        if v is None:
            return v
        return validate_decimal_str(
            v, f"PriceCheckpoint.{info.field_name}", nonnegative=False
        )


class PriceCheckpointHistoryResponse(CamelModel):
    """Response model for price checkpoint history endpoint."""

    value: List[PriceCheckpoint]
    next_epoch: Optional[int] = Field(None, ge=0)
    next_tx_ordinal: Optional[int] = Field(None, ge=0)
    next_ordinal: Optional[int] = Field(None, ge=0)
    success: bool
    timestamp: int
