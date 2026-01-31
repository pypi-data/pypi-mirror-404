"""
Shared base Pydantic model enabling unified camel-case behaviour for
all realtime- and rest-client models.

Import `CamelModel` and inherit from it instead of `pydantic.BaseModel`.
"""

from pydantic import BaseModel, ConfigDict
from pydantic.alias_generators import to_camel

from enum import Enum
from pydantic.types import StringConstraints
from typing import Annotated

from ddx._rust.common.enums import (
    PositionSide as RustPositionSide,
    OrderSide as RustOrderSide,
)
from ddx._rust.decimal import Decimal


class CamelModel(BaseModel):
    model_config = ConfigDict(
        alias_generator=to_camel,
        validate_by_alias=True,
        validate_by_name=True,
        serialize_by_alias=True,
        extra="forbid",
    )


def validate_decimal_str(value: str, field_name: str, nonnegative: bool = True) -> str:
    try:
        d = Decimal(value)
    except Exception:
        raise ValueError(f"Invalid decimal value for {field_name}: {value}")
    if nonnegative and d < 0:
        raise ValueError(f"Value for {field_name} must be non-negative: {value}")
    return value


HexStr = Annotated[str, StringConstraints(pattern=r"^0x[0-9A-Fa-f]+$")]


class TradeSide(int, Enum):
    BID = 0
    ASK = 1

    def raw_order_side(self) -> RustOrderSide:
        if self == TradeSide.BID:
            return RustOrderSide.Bid
        else:
            return RustOrderSide.Ask


class OrderType(int, Enum):
    LIMIT = 0
    MARKET = 1
    STOP = 2
    LIMIT_POST_ONLY = 3


class OrderRejection(int, Enum):
    SELF_MATCH = 0
    SOLVENCY_GUARD = 1
    MAX_TAKER_PRICE_DEVIATION = 2
    NO_LIQUIDITY = 3
    INVALID_STRATEGY = 4
    POST_ONLY_VIOLATION = 5


class CancelRejection(int, Enum):
    INVALID_ORDER = 0


class OrderUpdateReason(int, Enum):
    POST = 0
    TRADE = 1
    LIQUIDATION = 2
    CANCELLATION = 3
    ORDER_REJECTION = 4
    CANCEL_REJECTION = 5


class WithdrawRejection(int, Enum):
    INVALID_STRATEGY = 0
    INVALID_INSURANCE_FUND_CONTRIBUTION = 1
    MAX_WITHDRAWAL_AMOUNT = 2
    INSUFFICIENT_INSURANCE_FUND_CONTRIBUTION = 3
    INSUFFICIENT_REMAINING_INSURANCE_FUND = 4


class StrategyUpdateReason(int, Enum):
    DEPOSIT = 0
    WITHDRAW = 1
    WITHDRAW_INTENT = 2
    FUNDING_PAYMENT = 3
    PNL_SETTLEMENT = 4
    TRADE = 5
    FEE = 6
    LIQUIDATION = 7
    ADL = 8
    WITHDRAW_REJECTION = 9


class WithdrawDDXRejection(int, Enum):
    INVALID_TRADER = 0
    INSUFFICIENT_DDX_BALANCE = 1


class TraderUpdateReason(int, Enum):
    DEPOSIT_DDX = 0
    WITHDRAW_DDX = 1
    WITHDRAW_DDX_INTENT = 2
    TRADE_MINING_REWARD = 3
    PROFILE_UPDATE = 4
    FEE_DISTRIBUTION = 5
    ADMISSION = 6
    DENIAL = 7
    FEE = 8
    WITHDRAW_DDX_REJECTION = 9


class PositionSide(int, Enum):
    LONG = 1
    SHORT = 2

    def raw_position_side(self) -> RustPositionSide:
        if self == PositionSide.LONG:
            return RustPositionSide.Long
        else:
            return RustPositionSide.Short
