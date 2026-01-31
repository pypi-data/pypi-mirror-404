"""
Fill module.
"""

import logging
from typing import Optional

from attrs import define, field
from ddx.common.transactions.inner.outcome import Outcome
from ddx._rust.common import TokenSymbol
from ddx._rust.common.enums import OrderSide, PositionSide, TradeSide
from ddx._rust.common.state import Position, Strategy, Trader
from ddx._rust.decimal import Decimal

logger = logging.getLogger(__name__)

MAX_DDX_PRICE_CHECKPOINT_AGE_IN_TICKS = 40000
DDX_FEE_DISCOUNT = 0.5


def apply_trade(
    position: Position, amount: Decimal, price: Decimal, side: OrderSide
) -> (Position, Decimal):
    logger.debug(
        f"Applying trade of {amount} at {price} on {side} to position {position}"
    )
    if side == OrderSide.Bid:
        if position.side == PositionSide.Long:
            logger.info("Trade side matches position side, increasing position balance")
            return position.increase(price, amount)
        if position.side == PositionSide.Short:
            logger.info(
                "Trade side does not match position side, decreasing position balance"
            )
            if amount > position.balance:
                return position.cross_over(price, amount)
            return position.decrease(price, amount)
        logger.info(
            "Position side not set, setting to Long and increasing position balance"
        )
        position.side = PositionSide.Long
        return position.increase(price, amount)
    else:
        if position.side == PositionSide.Short:
            logger.info("Trade side matches position side, increasing position balance")
            return position.increase(price, amount)
        if position.side == PositionSide.Long:
            logger.info(
                "Trade side does not match position side, decreasing position balance"
            )
            if amount > position.balance:
                return position.cross_over(price, amount)
            return position.decrease(price, amount)
        logger.info(
            "Position side not set, setting to Short and increasing position balance"
        )
        position.side = PositionSide.Short
        return position.increase(price, amount)


@define
class FillContext:
    """
    Defines a FillContext.
    """

    outcome: Outcome
    realized_pnl: Optional[Decimal] = field(init=False)

    def apply_fill(
        self,
        position: Optional[Position],
        side: OrderSide,
        trade_side: TradeSide,
        fill_amount: Decimal,
        fill_price: Decimal,
    ) -> Position:
        if position is None:
            position = Position(
                PositionSide.Long if side == OrderSide.Bid else PositionSide.Short,
                Decimal("0"),
                Decimal("0"),
            )
            logger.info(f"New {position.side} position")
        old_balance = position.balance

        fee = trade_side.trading_fee(fill_amount, fill_price)
        updated_position, realized_pnl = apply_trade(
            position, fill_amount, fill_price, side
        )

        self.realized_pnl = realized_pnl
        logger.info(f"Realized pnl: {self.realized_pnl}")
        logger.info(f"Fee: {fee}")

        # Note that, again, we're never reading the fee from the txlog, and instead
        # we calulate it from the fill amount and price and set it in the outcome.
        self.outcome.fee = fee

        return updated_position

    def apply_ddx_fee_and_mutate_trader(
        self,
        trader: Trader,
        ddx_price: Decimal,
    ) -> bool:
        if self.outcome.fee == Decimal("0"):
            logger.info("Base fee of 0, no fees to pay")
            return False
        fee_in_ddx = (self.outcome.fee / ddx_price) * (Decimal("1") - DDX_FEE_DISCOUNT)
        if fee_in_ddx.recorded_amount() == Decimal("0"):
            logger.info(
                "Fee in DDX is 0 after conversion and discount, no fees to pay in DDX"
            )
            return False
        if trader.avail_ddx_balance < fee_in_ddx:
            # TODO 3825: this should be caught by the sequencer
            logger.warn("Not enough DDX to pay fee")
            return False
        old_balance = trader.avail_ddx_balance
        trader.avail_ddx_balance = (old_balance - fee_in_ddx).recorded_amount()
        self.outcome.fee = (old_balance - trader.avail_ddx_balance).recorded_amount()
        self.outcome.pay_fee_in_ddx = True
        return True

    def realize_trade_and_mutate_strategy(self, strategy: Strategy):
        if strategy.frozen:
            raise Exception("Cannot realize pnl from a frozen strategy")
        strategy.set_avail_collateral(
            TokenSymbol.USDC,
            strategy.avail_collateral[TokenSymbol.USDC] + self.realized_pnl,
        )
        if not self.outcome.pay_fee_in_ddx and self.outcome.fee > Decimal("0"):
            old_balance = strategy.avail_collateral[TokenSymbol.USDC]
            strategy.set_avail_collateral(
                TokenSymbol.USDC,
                strategy.avail_collateral[TokenSymbol.USDC] - self.outcome.fee,
            )
            self.outcome.fee = (
                old_balance - strategy.avail_collateral[TokenSymbol.USDC]
            ).recorded_amount()
