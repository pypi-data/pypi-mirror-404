from pydantic import Field, conlist, field_validator, ConfigDict
from ddx.models.base import (
    CamelModel,
    HexStr,
    TradeSide,
    OrderType,
    OrderRejection,
    CancelRejection,
    OrderUpdateReason,
    WithdrawRejection,
    StrategyUpdateReason,
    WithdrawDDXRejection,
    TraderUpdateReason,
    PositionSide,
    validate_decimal_str,
)
from typing import Optional, Union, Annotated, Literal
from enum import Enum
from datetime import datetime


class Action(str, Enum):
    SUBSCRIBE = "SUBSCRIBE"
    UNSUBSCRIBE = "UNSUBSCRIBE"


class Feed(str, Enum):
    ORDER_BOOK_L2 = "ORDER_BOOK_L2"
    ORDER_BOOK_L3 = "ORDER_BOOK_L3"
    MARK_PRICE = "MARK_PRICE"
    ORDER_UPDATE = "ORDER_UPDATE"
    STRATEGY_UPDATE = "STRATEGY_UPDATE"
    TRADER_UPDATE = "TRADER_UPDATE"


class MessageType(str, Enum):
    PARTIAL = "PARTIAL"
    UPDATE = "UPDATE"


class OrderFilter(CamelModel):
    trader_address: HexStr
    strategy_id_hash: Optional[HexStr] = None
    symbol: Optional[str] = None
    reason: Optional[OrderUpdateReason] = None


class StrategyFilter(CamelModel):
    trader_address: HexStr
    strategy_id_hash: Optional[HexStr] = None
    reason: Optional[StrategyUpdateReason] = None


class TraderFilter(CamelModel):
    trader_address: HexStr
    reason: Optional[TraderUpdateReason] = None


class OrderBookL2Filter(CamelModel):
    symbol: str
    aggregation: float = Field(..., gt=0, description="Aggregation level for prices.")


class OrderBookL2Params(CamelModel):
    # Optional list of filters; when omitted, subscribe to all L2 book orders for all symbols/aggregations (be careful).
    order_book_l2_filters: Optional[list[OrderBookL2Filter]] = None


class OrderBookL3Params(CamelModel):
    # Optional list of symbols; when omitted, subscribe to all L3 book orders for all symbols (be careful).
    symbols: Optional[Annotated[list[str], conlist(str, min_length=1)]] = Field(
        default=None, description="Multiple product symbols for filtering."
    )


class MarkPriceParams(CamelModel):
    # Optional list of symbols; when omitted, subscribe to all mark prices for all symbols (be careful).
    symbols: Optional[Annotated[list[str], conlist(str, min_length=1)]] = Field(
        default=None,
        description="The product symbols for which to retrieve mark prices.",
    )


class OrderUpdateParams(CamelModel):
    order_filters: Optional[list[OrderFilter]] = None


class StrategyUpdateParams(CamelModel):
    strategy_filters: Optional[list[StrategyFilter]] = None


class TraderUpdateParams(CamelModel):
    trader_filters: Optional[list[TraderFilter]] = None


class FeedWithParams(CamelModel):
    feed: Feed
    # params must match one of the models used by the various feeds.
    params: Union[
        OrderBookL2Params,
        OrderBookL3Params,
        MarkPriceParams,
        OrderUpdateParams,
        StrategyUpdateParams,
        TraderUpdateParams,
    ]


class SubscribePayload(CamelModel):
    action: Literal[Action.SUBSCRIBE]
    nonce: str
    feeds: Annotated[list[FeedWithParams], conlist(FeedWithParams, min_length=1)]


class UnsubscribePayload(CamelModel):
    action: Literal[Action.UNSUBSCRIBE]
    nonce: str
    feeds: Annotated[list[Feed], conlist(Feed, min_length=1)]


class AcknowledgeResult(CamelModel):
    error: Optional[str] = None


class AcknowledgePayload(CamelModel):
    action: Optional[Action]
    nonce: Optional[str]
    result: AcknowledgeResult


class AggregatedOrder(CamelModel):
    symbol: str
    side: TradeSide = Field(..., description="Side of the order (BID=0, ASK=1).")
    amount: str = Field(
        ...,
        description="The aggregated amount for this price level. Stored as string to preserve decimal precision.",
    )
    price: str = Field(
        ...,
        description="The aggregated price level. Stored as string to preserve decimal precision.",
    )

    @field_validator("amount", "price")
    @classmethod
    def validate_nonnegative_decimals(cls, v, info):
        return validate_decimal_str(
            v, f"AggregatedOrder.{info.field_name}", nonnegative=True
        )


class OrderBookL2Contents(CamelModel):
    message_type: MessageType
    data: list[AggregatedOrder]


class OrderBookL2Payload(CamelModel):
    sequence: int = Field(..., ge=0)
    ordinal: int = Field(..., ge=0)
    feed: Literal[Feed.ORDER_BOOK_L2] = Field(default=Feed.ORDER_BOOK_L2)
    subscriptionKey: str
    contents: OrderBookL2Contents


class OrderBookL3Order(CamelModel):
    order_hash: HexStr
    symbol: str
    side: TradeSide
    original_amount: str = Field(..., description="Original order amount")
    amount: str = Field(..., description="Remaining order amount")
    price: str = Field(..., description="Order price")
    trader_address: HexStr
    strategy_id_hash: HexStr
    book_ordinal: int = Field(..., ge=0)

    @field_validator("original_amount", "amount", "price")
    @classmethod
    def validate_nonnegative_decimals(cls, v, info):
        return validate_decimal_str(
            v, f"OrderBookL3Order.{info.field_name}", nonnegative=True
        )


class OrderBookL3Contents(CamelModel):
    message_type: MessageType
    data: list[OrderBookL3Order]


class OrderBookL3Payload(CamelModel):
    sequence: int = Field(..., ge=0)
    ordinal: int = Field(..., ge=0)
    feed: Literal[Feed.ORDER_BOOK_L3] = Field(default=Feed.ORDER_BOOK_L3)
    subscriptionKey: str
    contents: OrderBookL3Contents


class MarkPriceEntry(CamelModel):
    global_ordinal: int = Field(..., ge=0)
    epoch_id: int = Field(..., ge=0)
    price: str = Field(
        ...,
        description="The mark price, stored as a string to preserve decimal precision.",
    )
    funding_rate: str = Field(
        ...,
        description="The new funding rate for this symbol. Stored as a string to preserve decimal precision.",
    )
    symbol: str
    created_at: datetime

    @field_validator("price")
    @classmethod
    def validate_nonnegative_decimals(cls, v, info):
        return validate_decimal_str(
            v, f"MarkPriceEntry.{info.field_name}", nonnegative=True
        )

    @field_validator("funding_rate")
    @classmethod
    def validate_decimals(cls, v, info):
        return validate_decimal_str(
            v, f"MarkPriceEntry.{info.field_name}", nonnegative=False
        )


class MarkPriceContents(CamelModel):
    message_type: MessageType
    data: list[MarkPriceEntry]


class MarkPricePayload(CamelModel):
    sequence: int = Field(..., ge=0)
    ordinal: int = Field(..., ge=0)
    feed: Literal[Feed.MARK_PRICE] = Field(default=Feed.MARK_PRICE)
    subscriptionKey: str
    contents: MarkPriceContents


class OrderIntent(CamelModel):
    epoch_id: int = Field(..., ge=0)
    order_hash: HexStr
    symbol: str
    side: TradeSide
    amount: str = Field(
        ..., description="Amount stored as string to preserve decimal precision."
    )
    price: str = Field(
        ..., description="Price stored as string to preserve decimal precision."
    )
    trader_address: HexStr
    strategy_id_hash: HexStr
    order_type: OrderType
    stop_price: str = Field(
        ..., description="Stop price stored as string to preserve decimal precision."
    )
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
    global_ordinal: int = Field(..., ge=0)
    epoch_id: int = Field(..., ge=0)
    order_rejection: Optional[OrderRejection] = None
    cancel_rejection: Optional[CancelRejection] = None
    reason: OrderUpdateReason
    amount: Optional[str] = Field(
        default=None,
        description="The filled amount for the update, as a string preserving decimal precision.",
    )
    quote_asset_amount: Optional[str] = Field(
        default=None,
        description="The quote asset transacted amount for this update, as a string preserving decimal precision.",
    )
    symbol: str
    price: Optional[str] = Field(
        default=None,
        description="The fill price for the update, as a string preserving decimal precision.",
    )
    order_match_ordinal: Optional[int] = Field(
        default=None,
        ge=0,
        description="Ordinal representing the order match outcome for this update.",
    )
    ordinal: int = Field(..., ge=0)
    last_executed_amount: Optional[str] = Field(
        default=None,
        description="The last executed amount from the update, as a string preserving decimal precision.",
    )
    last_executed_price: Optional[str] = Field(
        default=None,
        description="The last executed price from the update, as a string preserving decimal precision.",
    )
    cumulative_filled_amount: Optional[str] = Field(
        default=None,
        description="The cumulative filled amount up to this update, as a string preserving decimal precision.",
    )
    cumulative_quote_asset_transacted_amount: Optional[str] = Field(
        default=None,
        description="The cumulative quote asset transacted amount up to this update, as a string preserving decimal precision.",
    )
    last_quote_asset_transacted_amount: Optional[str] = Field(
        default=None,
        description="The last quote asset transacted amount from this update, as a string preserving decimal precision.",
    )
    maker_fee_collateral: Optional[str] = Field(
        default=None,
        description="The maker fee in collateral, as a string preserving decimal precision.",
    )
    maker_fee_ddx: Optional[str] = Field(
        default=None,
        alias="makerFeeDDX",
        description="The maker fee in DDX, as a string preserving decimal precision.",
    )
    maker_realized_pnl: Optional[str] = Field(
        default=None,
        description="The realized PnL for the maker trade in the collateral currency, stored as string to preserve decimal precision.",
    )
    taker_order_intent: Optional[OrderIntent] = None
    taker_fee_collateral: Optional[str] = Field(
        default=None,
        description="The taker fee in collateral, as a string preserving decimal precision.",
    )
    taker_fee_ddx: Optional[str] = Field(
        default=None,
        alias="takerFeeDDX",
        description="The taker fee in DDX, as a string preserving decimal precision.",
    )
    taker_realized_pnl: Optional[str] = None
    liquidated_trader_address: Optional[HexStr] = None
    liquidated_strategy_id_hash: Optional[HexStr] = None
    maker_order_intent: OrderIntent
    created_at: datetime

    @field_validator(
        "amount",
        "quote_asset_amount",
        "price",
        "last_executed_amount",
        "last_executed_price",
        "cumulative_filled_amount",
        "cumulative_quote_asset_transacted_amount",
        "last_quote_asset_transacted_amount",
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


class OrderUpdateContents(CamelModel):
    message_type: MessageType
    data: list[OrderUpdate]


class OrderUpdatePayload(CamelModel):
    sequence: int = Field(..., ge=0)
    ordinal: int = Field(..., ge=0)
    feed: Literal[Feed.ORDER_UPDATE] = Field(default=Feed.ORDER_UPDATE)
    subscriptionKey: str
    contents: OrderUpdateContents


class Position(CamelModel):
    symbol: str
    balance: str = Field(
        ...,
        description="Position balance (after PnL was realized), stored as string to preserve decimal precision",
    )
    side: PositionSide
    avg_entry_price: str = Field(
        ...,
        description="Average entry price, stored as string to preserve decimal precision",
    )
    realized_pnl: str = Field(
        ..., description="Realized PnL, stored as string to preserve decimal precision"
    )

    @field_validator("balance", "avg_entry_price")
    @classmethod
    def validate_nonnegative_decimals(cls, v, info):
        return validate_decimal_str(v, f"Position.{info.field_name}", nonnegative=True)

    @field_validator("realized_pnl")
    @classmethod
    def validate_decimals(cls, v, info):
        return validate_decimal_str(v, f"Position.{info.field_name}", nonnegative=False)


class StrategyUpdate(CamelModel):
    global_ordinal: int = Field(..., ge=0)
    epoch_id: int = Field(..., ge=0)
    withdraw_rejection: Optional[WithdrawRejection] = None
    reason: StrategyUpdateReason
    trader_address: HexStr
    strategy_id_hash: HexStr
    collateral_address: HexStr
    collateral_symbol: Literal["USDC"]
    amount: Optional[str] = Field(
        default=None,
        description="The amount added to the strategy (may be negative). Stored as string to preserve decimal precision.",
    )
    new_avail_collateral: Optional[str] = Field(
        default=None,
        description="The available collateral after the update, as a string preserving decimal precision.",
    )
    new_locked_collateral: Optional[str] = Field(
        default=None,
        description="The locked collateral after the update, as a string preserving decimal precision.",
    )
    block_number: Optional[int] = Field(
        default=None,
        ge=0,
        description="The block number when this update was processed.",
    )
    positions: Optional[list[Position]] = Field(
        default=None,
        description="The updated positions after a PnL realization, as an array of positions. Null if not applicable.",
    )
    created_at: datetime

    @field_validator("new_avail_collateral", "new_locked_collateral")
    @classmethod
    def validate_nonnegative_optional_decimals(cls, v, info):
        if v is None:
            return v
        return validate_decimal_str(
            v, f"StrategyUpdate.{info.field_name}", nonnegative=True
        )

    @field_validator("amount")
    @classmethod
    def validate_optional_decimals(cls, v, info):
        if v is None:
            return v
        return validate_decimal_str(
            v, f"StrategyUpdate.{info.field_name}", nonnegative=False
        )


class StrategyUpdateContents(CamelModel):
    message_type: MessageType
    data: list[StrategyUpdate]


class StrategyUpdatePayload(CamelModel):
    sequence: int = Field(..., ge=0)
    ordinal: int = Field(..., ge=0)
    feed: Literal[Feed.STRATEGY_UPDATE] = Field(default=Feed.STRATEGY_UPDATE)
    subscriptionKey: str
    contents: StrategyUpdateContents


class TraderUpdate(CamelModel):
    global_ordinal: int = Field(..., ge=0)
    epoch_id: int = Field(..., ge=0)
    withdraw_ddx_rejection: Optional[WithdrawDDXRejection] = Field(
        default=None,
        alias="withdrawDDXRejection",
    )
    reason: TraderUpdateReason
    trader_address: HexStr
    amount: Optional[str] = Field(
        default=None,
        description="The change in trader amount (may be negative), stored as string to preserve decimal precision.",
    )
    new_avail_ddx_balance: Optional[str] = Field(
        default=None,
        alias="newAvailDDXBalance",
        description="The new available DDX balance after the update, as a string preserving decimal precision.",
    )
    new_locked_ddx_balance: Optional[str] = Field(
        default=None,
        alias="newLockedDDXBalance",
        description="The new locked DDX balance after the update, as a string preserving decimal precision.",
    )
    pay_fees_in_ddx: Optional[bool] = Field(default=None, alias="payFeesInDDX")
    block_number: Optional[int] = Field(
        default=None,
        ge=0,
        description="The block number when this trader update was processed.",
    )
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


class TraderUpdateContents(CamelModel):
    message_type: MessageType
    data: list[TraderUpdate]


class TraderUpdatePayload(CamelModel):
    sequence: int = Field(..., ge=0)
    ordinal: int = Field(..., ge=0)
    feed: Literal[Feed.TRADER_UPDATE] = Field(default=Feed.TRADER_UPDATE)
    subscriptionKey: str
    contents: TraderUpdateContents


FeedPayload = (
    OrderBookL2Payload
    | OrderBookL3Payload
    | MarkPricePayload
    | OrderUpdatePayload
    | StrategyUpdatePayload
    | TraderUpdatePayload
)

SubscriptionPayload = SubscribePayload | UnsubscribePayload | AcknowledgePayload

Contents = (
    OrderBookL2Contents
    | OrderBookL3Contents
    | MarkPriceContents
    | OrderUpdateContents
    | StrategyUpdateContents
    | TraderUpdateContents
)

__all__ = [
    "Action",
    "Feed",
    "MessageType",
    "TradeSide",
    "OrderType",
    "OrderRejection",
    "CancelRejection",
    "OrderUpdateReason",
    "WithdrawRejection",
    "StrategyUpdateReason",
    "WithdrawDDXRejection",
    "TraderUpdateReason",
    "OrderBookL2Filter",
    "OrderBookL2Params",
    "OrderBookL3Params",
    "MarkPriceParams",
    "OrderUpdateParams",
    "StrategyUpdateParams",
    "TraderUpdateParams",
    "FeedWithParams",
    "SubscribePayload",
    "UnsubscribePayload",
    "AcknowledgeResult",
    "AcknowledgePayload",
    "AggregatedOrder",
    "OrderBookL2Contents",
    "OrderBookL2Payload",
    "OrderBookL3Order",
    "OrderBookL3Contents",
    "OrderBookL3Payload",
    "MarkPriceEntry",
    "MarkPriceContents",
    "MarkPricePayload",
    "OrderIntent",
    "OrderUpdate",
    "OrderUpdateContents",
    "OrderUpdatePayload",
    "Position",
    "StrategyUpdate",
    "StrategyUpdateContents",
    "StrategyUpdatePayload",
    "TraderUpdate",
    "TraderUpdateContents",
    "TraderUpdatePayload",
    "PositionSide",
    "OrderFilter",
    "StrategyFilter",
    "TraderFilter",
    "FeedPayload",
    "SubscriptionPayload",
    "Contents",
]
