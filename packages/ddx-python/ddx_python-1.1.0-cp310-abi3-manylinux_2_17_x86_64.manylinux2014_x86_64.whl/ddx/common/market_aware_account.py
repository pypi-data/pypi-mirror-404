"""
MarketAwareAccount module.
"""

import copy
import logging

from attrs import define
from ddx.common.transactions.price_checkpoint import PriceCheckpoint
from ddx._rust.common import ProductSymbol, TokenSymbol
from ddx._rust.common.enums import OrderSide, PositionSide
from ddx._rust.common.state import Position, Strategy
from ddx._rust.decimal import Decimal

logger = logging.getLogger(__name__)

MMR_FRACTION = Decimal("0.15")


# Designed to mimic ddxenclave::StrategyMetrics
@define
class MarketAwareAccount:
    avail_collateral: Decimal
    max_leverage: int
    positions: dict[ProductSymbol, tuple[Position, Decimal]]

    # must be initialize with a nonempty strategy
    def __init__(
        self,
        strategy: Strategy,
        positions: dict[ProductSymbol, tuple[Position, Decimal]],
    ):
        return self.__attrs_init__(
            strategy.avail_collateral[TokenSymbol.USDC],
            strategy.max_leverage,
            positions,
        )

    @property
    def notional_value(self):
        notional = Decimal("0")
        for symbol, (position, mark_price) in self.positions.items():
            notional += position.balance * mark_price
        logger.debug(f"Notional value: {notional}")
        return notional

    @property
    def unrealized_pnl(self):
        unrealized_pnl = Decimal("0")
        for symbol, (position, mark_price) in self.positions.items():
            unrealized_pnl += position.unrealized_pnl(mark_price)
        logger.debug(f"Unrealized pnl: {unrealized_pnl}")
        return unrealized_pnl

    @property
    def total_value(self):
        res = self.avail_collateral + self.unrealized_pnl
        logger.debug(f"Total value: {res}")
        return res

    @property
    def margin_fraction(self):
        total_value = self.total_value
        notional_value = self.notional_value
        if notional_value == Decimal("0"):
            if total_value < Decimal("0"):
                return Decimal("-1_000_000")
            return Decimal("1_000_000")

        mf = total_value / notional_value
        logger.debug(f"Margin fraction: {mf}")
        return mf

    @property
    def maintenance_margin_fraction(self):
        mmf = MMR_FRACTION / self.max_leverage
        logger.debug(f"Maintenance margin fraction: {mmf}")
        return mmf

    @property
    def maximum_withdrawal_amount(self):
        res = self.total_value - self.maintenance_margin_fraction * self.notional_value
        logger.debug(f"Max withdrawal amount: {res}")
        return res

    def maximum_fill_amount_increasing(
        self,
        fee_percentage: Decimal,
        mark_price: Decimal,
        side: OrderSide,
        price: Decimal,
        amount: Decimal,
    ):
        logger.debug(
            f"Max fill amount increasing current position {self.avail_collateral} {self.notional_value}"
        )
        if self.avail_collateral == Decimal("0") and self.notional_value == Decimal(
            "0"
        ):
            return Decimal("0")

        side = Decimal("1") if side == OrderSide.Bid else Decimal("-1")
        gamma = Decimal("1") / self.max_leverage
        if self.margin_fraction <= gamma:
            derivative_numerator = (
                self.notional_value
                * (side * (mark_price - price) - fee_percentage * price)
                - mark_price * self.total_value
            )
            return min(
                (
                    Decimal("0")
                    if derivative_numerator < Decimal("0")
                    else Decimal("1_000_000")
                ),
                amount,
            )
        else:
            denominator = (
                side * (price - mark_price)
                + fee_percentage * price
                + gamma * mark_price
            )
            return min(
                (
                    (self.total_value - gamma * self.notional_value) / denominator
                    if denominator > Decimal("0")
                    else Decimal("1_000_000")
                ),
                amount,
            )

    def maximum_fill_amount_decreasing(
        self,
        fee_percentage: Decimal,
        mark_price: Decimal,
        position: Position,
        side: OrderSide,
        price: Decimal,
        amount: Decimal,
    ):
        logger.debug(f"Max fill amount decreasing current position")
        side = Decimal("-1") if side == OrderSide.Bid else Decimal("1")
        gamma = Decimal("1") / self.max_leverage
        if self.margin_fraction <= gamma:
            derivative_numerator = (
                self.notional_value
                * (side * (price - mark_price) - fee_percentage * price)
                + mark_price * self.total_value
            )
            theoretical_fill_amount = (
                Decimal("0")
                if derivative_numerator < Decimal("0")
                else Decimal("1_000_000")
            )
        else:
            denominator = (
                side * (mark_price - price)
                + fee_percentage * price
                - gamma * mark_price
            )
            theoretical_fill_amount = (
                (self.total_value - gamma * self.notional_value) / denominator
                if denominator > Decimal("0")
                else Decimal("1_000_000")
            )

        return min(
            theoretical_fill_amount,
            amount,
            position.balance,
        )

    def maximum_fill_amount_cross_over(
        self,
        symbol: ProductSymbol,
        fee_percentage: Decimal,
        mark_price: Decimal,
        position: Position,
        side: OrderSide,
        price: Decimal,
        amount: Decimal,
    ):
        logger.debug(f"Max fill amount crossing over current position")
        decreasing_amount = self.maximum_fill_amount_decreasing(
            fee_percentage, mark_price, position, side, price, amount
        )

        if decreasing_amount == position.balance:
            # copy account so as to not modify anything
            copy_account = copy.deepcopy(self)
            copy_account.avail_collateral = (
                copy_account.avail_collateral
                + position.avg_pnl(price) * decreasing_amount
                - fee_percentage * price * decreasing_amount
            ).recorded_amount()
            del copy_account.positions[symbol]

            increasing_amount = copy_account.maximum_fill_amount_increasing(
                fee_percentage, mark_price, side, price, amount - decreasing_amount
            )
            return decreasing_amount + increasing_amount
        else:
            return decreasing_amount

    def maximum_fill_amount(
        self,
        symbol: ProductSymbol,
        fee_percentage: Decimal,
        mark_price: Decimal,
        side: OrderSide,
        price: Decimal,
        amount: Decimal,
        min_order_size: Decimal,
    ):
        logger.debug(f"Calculating max fill amount")
        if symbol in self.positions:
            logger.debug(f"Position already exists")
            p = self.positions[symbol][0]

            if (
                (p.side == PositionSide.Long and side == OrderSide.Bid)
                or (p.side == PositionSide.Short and side == OrderSide.Ask)
                or p.side == PositionSide.Empty
            ):
                fill_amount = self.maximum_fill_amount_increasing(
                    fee_percentage, mark_price, side, price, amount
                )
            else:
                fill_amount = self.maximum_fill_amount_cross_over(
                    symbol, fee_percentage, mark_price, p, side, price, amount
                )
        else:
            logger.debug(f"Position does not exist, auto increase")
            fill_amount = self.maximum_fill_amount_increasing(
                fee_percentage,
                mark_price,
                side,
                price,
                amount,
            )
        return (
            fill_amount
            if min_order_size == Decimal("0")
            else fill_amount - (fill_amount % min_order_size)
        )

    def assess_solvency(self):
        res = 0 if self.margin_fraction < self.maintenance_margin_fraction else 1
        logger.info(
            f"solvent? {bool(res)}; margin fraction is {self.margin_fraction} and maintenance margin fraction is {self.maintenance_margin_fraction}"
        )
        return res

    def sorted_positions_by_unrealized_pnl(self):
        return sorted(
            self.positions.items(),
            key=lambda item: item[1][0].unrealized_pnl(item[1][1]),
        )
