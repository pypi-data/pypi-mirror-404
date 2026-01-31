from datetime import datetime
from typing import List, Literal, Optional
from pydantic import Field, field_validator
from ddx.models.base import (
    CamelModel,
    HexStr,
    validate_decimal_str,
    PositionSide,
)

from ddx._rust.decimal import Decimal
from ddx._rust.common.state import (
    Strategy as SMTStrategy,
    Balance,
    Trader as SMTTrader,
    Position as SMTPosition,
)
from ddx._rust.common import TokenSymbol


# Strategy Fees History Models
class Fee(CamelModel):
    """Strategy fee data model."""

    epoch_id: int = Field(..., ge=0)
    tx_ordinal: int = Field(..., ge=0)
    ordinal: int = Field(..., ge=0)
    amount: str
    fee_symbol: str
    symbol: str
    created_at: datetime

    @field_validator("amount")
    @classmethod
    def validate_nonnegative_decimals(cls, v, info):
        return validate_decimal_str(v, f"StrategyFee.{info.field_name}", nonnegative=True)


class FeesHistoryResponse(CamelModel):
    """Response model for strategy fees history endpoint."""

    value: List[Fee]
    next_epoch: Optional[int] = Field(None, ge=0)
    next_tx_ordinal: Optional[int] = Field(None, ge=0)
    next_ordinal: Optional[int] = Field(None, ge=0)
    success: bool
    timestamp: int


# Strategy Positions Models
class Position(CamelModel):
    """Position data model."""

    trader: HexStr
    symbol: str
    strategy_id_hash: HexStr
    strategy_id: str
    side: PositionSide
    balance: str
    avg_entry_price: str
    last_modified_in_epoch: Optional[int] = Field(None, ge=0)

    @field_validator("balance", "avg_entry_price")
    @classmethod
    def validate_nonnegative_decimals(cls, v, info):
        return validate_decimal_str(v, f"Position.{info.field_name}", nonnegative=True)

    def raw_position(self) -> SMTPosition:
        return SMTPosition(
            self.side.raw_position_side(),
            Decimal(self.balance),
            Decimal(self.avg_entry_price),
        )


class PositionsResponse(CamelModel):
    """Response model for strategy positions endpoint."""

    value: List[Position]
    success: bool
    timestamp: int


# Strategy Models
class Strategy(CamelModel):
    """Srategy data model."""

    trader: HexStr
    strategy_id_hash: HexStr
    strategy_id: str
    max_leverage: int = Field(..., ge=1)
    avail_collateral: str
    locked_collateral: str
    frozen: bool

    @field_validator("avail_collateral", "locked_collateral")
    @classmethod
    def validate_nonnegative_decimals(cls, v, info):
        return validate_decimal_str(v, f"Strategy.{info.field_name}", nonnegative=True)

    def raw_strategy(self) -> SMTStrategy:
        return SMTStrategy(
            Balance(
                Decimal(self.avail_collateral),
                TokenSymbol.USDC,
            ),
            Balance(
                Decimal(self.locked_collateral),
                TokenSymbol.USDC,
            ),
            self.max_leverage,
            self.frozen,
        )


class StrategyResponse(CamelModel):
    """Response model for strategy endpoint."""

    value: Optional[Strategy] = None
    success: bool
    timestamp: int


# Strategies Models
class StrategiesResponse(CamelModel):
    """Response model for strategies endpoint."""

    value: List[Strategy]
    success: bool
    timestamp: int


# Strategy Metrics Models
class StrategyMetrics(CamelModel):
    """Strategy metrics data model."""

    margin_fraction: str
    mmr: str
    leverage: str
    strategy_margin: str
    strategy_value: str

    @field_validator("margin_fraction", "mmr", "leverage", "strategy_margin", "strategy_value")
    @classmethod
    def validate_nonnegative_decimals(cls, v, info):
        return validate_decimal_str(v, f"StrategyMetrics.{info.field_name}", nonnegative=True)


class StrategyMetricsResponse(CamelModel):
    """Response model for strategy metrics endpoint."""

    value: StrategyMetrics
    success: bool
    timestamp: int


# Trader Models
class Trader(CamelModel):
    """Trader data model."""

    trader: str
    avail_ddx: str
    locked_ddx: str
    pay_fees_in_ddx: bool
    referral_address: Optional[HexStr] = None

    @field_validator("avail_ddx", "locked_ddx")
    @classmethod
    def validate_nonnegative_decimals(cls, v, info):
        return validate_decimal_str(v, f"TraderProfile.{info.field_name}", nonnegative=True)

    def raw_trader(self) -> SMTTrader:
        return SMTTrader(
            Decimal(self.avail_ddx),
            Decimal(self.locked_ddx),
            self.pay_fees_in_ddx,
        )


class TraderResponse(CamelModel):
    """Response model for trader profile endpoint."""

    value: Optional[Trader] = None
    success: bool
    timestamp: int
