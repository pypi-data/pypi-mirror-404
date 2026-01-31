"""
Fill module
"""

import logging
from enum import Enum
from typing import Optional

from attrs import define, field
from ddx.common.fill_context import (MAX_DDX_PRICE_CHECKPOINT_AGE_IN_TICKS,
                                 FillContext, apply_trade)
from ddx.common.transaction_utils import get_most_recent_price
from ddx.common.transactions.event import Event
from ddx.common.transactions.inner.outcome import Outcome
from ddx._rust.common import ProductSymbol, TokenSymbol
from ddx._rust.common.enums import OrderSide, TradeSide
from ddx._rust.common.state import (DerivadexSMT, InsuranceFund, Position,
                                     Price, Stats)
from ddx._rust.common.state.keys import (EpochMetadataKey, InsuranceFundKey,
                                          PositionKey, PriceKey, StatsKey,
                                          StrategyKey, TraderKey)
from ddx._rust.decimal import Decimal

logger = logging.getLogger(__name__)


@define(hash=True)
class Fill(Event):
    """
    Defines a Fill
    """

    symbol: ProductSymbol
    amount: Decimal = field(hash=False)
    price: Decimal = field(hash=False)
    taker_side: OrderSide = field(hash=False)
    time_value: int
    request_index: int = field(eq=False, hash=False)

    def adjust_for_maker_taker(
        self,
        smt: DerivadexSMT,
        epoch_id: int,
        is_maker: bool,
        outcome: Outcome,
        trade_mining_active: bool = False,
        maker_book_order_time_value: Optional[int] = None,
        reconcile_fees: bool = True,
    ):
        """
        Make some adjustments to the SMT based on whether we are
        considering the maker or the taker component of the Trade.
        In this method, we will be adjusting the the Strategy,
        Position, and Stats leaves.

        Parameters
        ----------
        smt: DerivadexSMT
            DerivaDEX Sparse Merkle Tree
        epoch_id: int
            Epoch ID used for recording fees if any
        is_maker : bool
            Whether outcome is for the maker or taker
        outcome: Outcome
            Outcome to adjust
        trade_mining_active : bool
            Whether trade mining is active
        maker_book_order_time_value: Optional[int]
            Maker book order time value
        """

        context = FillContext(outcome)

        position_key: PositionKey = PositionKey(
            outcome.trader,
            outcome.strategy_id_hash,
            self.symbol,
        )

        position: Optional[Position] = smt.position(position_key)

        position = context.apply_fill(
            position,
            (
                (OrderSide.Ask if self.taker_side == OrderSide.Bid else OrderSide.Bid)
                if is_maker
                else self.taker_side
            ),
            (TradeSide.Maker if is_maker else TradeSide.Taker),
            self.amount,
            self.price,
        )
        smt.store_position(
            position_key,
            position,
        )

        trader_key: TraderKey = TraderKey(outcome.trader)
        trader = smt.trader(trader_key)

        if outcome.fee > Decimal("0") and trader.pay_fees_in_ddx:
            # Gets the most recent DDX price within MAX_DDX_PRICE_CHECKPOINT_AGE_IN_TICKS
            _, recent_ddx_price = get_most_recent_price(
                smt, ProductSymbol("DDXP"), self.time_value
            )
            if (
                recent_ddx_price.time_value
                >= self.time_value - MAX_DDX_PRICE_CHECKPOINT_AGE_IN_TICKS
            ):
                if context.apply_ddx_fee_and_mutate_trader(
                    trader, recent_ddx_price.index_price
                ):
                    smt.store_trader(trader_key, trader)
            else:
                raise Exception(
                    "DDX fee election enabled but no DDX price checkpoint within the max age was found, should have been caught by the operator"
                )

        strategy_key: StrategyKey = position_key.as_strategy_key()
        strategy = smt.strategy(strategy_key)
        context.realize_trade_and_mutate_strategy(strategy)
        smt.store_strategy(strategy_key, strategy)

        if reconcile_fees and outcome.fee > Decimal("0"):
            if outcome.pay_fee_in_ddx:
                logger.info(f"Fee of {outcome.fee} DDX to be paid")
                epoch_metadata_key: EpochMetadataKey = EpochMetadataKey(epoch_id)
                epoch_metadata = smt.epoch_metadata(epoch_metadata_key)
                epoch_metadata.ddx_fee_pool = (
                    epoch_metadata.ddx_fee_pool + outcome.fee
                ).recorded_amount()
                smt.store_epoch_metadata(epoch_metadata_key, epoch_metadata)
            else:
                logger.info(f"Fee of {outcome.fee} USDC to be paid")
                insurance_fund_key: InsuranceFundKey = InsuranceFundKey()
                insurance_fund = smt.insurance_fund(insurance_fund_key)
                insurance_fund[TokenSymbol.USDC] += outcome.fee
                smt.store_insurance_fund(insurance_fund_key, insurance_fund)

        if (
            trade_mining_active
            and maker_book_order_time_value
            and self.time_value > maker_book_order_time_value + 1
        ):
            stats_key: StatsKey = StatsKey(outcome.trader)
            stats = smt.stats(stats_key)
            notional_amount = self.amount * self.price
            if stats is None:
                # If Stats leaf doesn't exist in the tree, we need
                # to create/add a new one
                if is_maker:
                    # Initialize the trader's maker volume
                    stats = Stats(notional_amount, Decimal("0"))
                else:
                    # Initialize the trader's taker volume
                    stats = Stats(Decimal("0"), notional_amount)
            else:
                # If Stats leaf does exist, we update the existing leaf
                if is_maker:
                    # Increment the trader's maker volume
                    stats.maker_volume += notional_amount
                else:
                    # Increment the trader's taker volume
                    stats.taker_volume += notional_amount

            smt.store_stats(stats_key, stats)

    def adjust_for_maker(
        self,
        smt: DerivadexSMT,
        epoch_id: int,
        trade_mining_active: bool = False,
        maker_book_order_time_value: Optional[int] = None,
        reconcile_fees: bool = True,
    ):
        """
        Make some adjustments to the SMT based on the maker side
        of the Trade.

        Parameters
        ----------
        smt: DerivadexSMT
            DerivaDEX Sparse Merkle Tree
        epoch_id: int
            Epoch ID used for recording fees if any
        trade_mining_active : bool
            Whether trade mining is active
        maker_book_order_time_value: Optional[int]
            Maker book order time value
        """
        self.adjust_for_maker_taker(
            smt,
            epoch_id,
            True,
            self.maker_outcome,
            trade_mining_active,
            maker_book_order_time_value,
            reconcile_fees,
        )

    def adjust_for_taker(
        self,
        smt: DerivadexSMT,
        epoch_id: int,
        trade_mining_active: bool = False,
        maker_book_order_time_value: Optional[int] = None,
        reconcile_fees: bool = True,
    ):
        """
        Make some adjustments to the SMT based on the taker side
        of the Trade.

        Parameters
        ----------
        smt: DerivadexSMT
            DerivaDEX Sparse Merkle Tree
        epoch_id: int
            Epoch ID used for recording fees if any
        maker_book_order_time_value: int
            Maker book order time value
        trade_mining_active : bool
            Whether trade mining is active
        """
        self.adjust_for_maker_taker(
            smt,
            epoch_id,
            False,
            self.taker_outcome,
            trade_mining_active,
            maker_book_order_time_value,
            reconcile_fees,
        )
