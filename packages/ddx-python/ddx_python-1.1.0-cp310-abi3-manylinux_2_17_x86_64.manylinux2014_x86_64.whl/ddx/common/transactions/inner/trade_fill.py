"""
TradeFill module
"""

import asyncio

from attrs import define, field
from ddx.common.transactions.inner.fill import Fill
from ddx.common.transactions.inner.outcome import Outcome
from ddx._rust.common import ProductSymbol, TokenSymbol
from ddx._rust.common.enums import OrderSide
from ddx._rust.common.state import DerivadexSMT, Price
from ddx._rust.common.state.keys import (
    BookOrderKey,
    EpochMetadataKey,
    InsuranceFundKey,
    PriceKey,
    StrategyKey,
    TraderKey,
)
from ddx._rust.decimal import Decimal


AFFILIATE_STANDARD_L1 = Decimal("0.10")
AFFILIATE_STANDARD_L2 = Decimal("0.05")
AFFILIATE_STANDARD_REBATE = Decimal("0.10")
AFFILIATE_PREMIUM_L1 = Decimal("0.20")
AFFILIATE_PREMIUM_L2 = Decimal("0.10")
AFFILIATE_PREMIUM_REBATE = Decimal("0.20")
AFFILIATE_STANDARD_MIN_DDX = Decimal("1_000")
AFFILIATE_PREMIUM_MIN_DDX = Decimal("10_000")


def _affiliate_schedule_for(trader):
    if trader is None:
        return None
    stake = trader.avail_ddx_balance + trader.locked_ddx_balance
    if stake >= AFFILIATE_PREMIUM_MIN_DDX:
        return (AFFILIATE_PREMIUM_L1, AFFILIATE_PREMIUM_L2, AFFILIATE_PREMIUM_REBATE)
    if stake >= AFFILIATE_STANDARD_MIN_DDX:
        return (
            AFFILIATE_STANDARD_L1,
            AFFILIATE_STANDARD_L2,
            AFFILIATE_STANDARD_REBATE,
        )
    return None


def _resolve_affiliate_chain(smt: DerivadexSMT, taker_address: str):
    taker = smt.trader(TraderKey(taker_address))
    if taker is None:
        return (None, None, None, None)
    l1 = taker.referral_address
    l1_trader = smt.trader(TraderKey(l1)) if l1 is not None else None
    l2 = None
    l2_trader = None
    if l1_trader is not None and l1_trader.referral_address is not None:
        l2 = l1_trader.referral_address
        l2_trader = smt.trader(TraderKey(l2))
    return (l1, l1_trader, l2, l2_trader)


def _compute_affiliate_split(
    total_fee: Decimal,
    l1_schedule,
    l2_schedule,
    l1_exists: bool,
    l2_exists: bool,
    taker_schedule,
):
    if total_fee == Decimal("0"):
        return {
            "platform": Decimal("0"),
            "l1": Decimal("0"),
            "l2": Decimal("0"),
            "rebate": Decimal("0"),
        }
    l1 = total_fee * l1_schedule[0] if l1_exists and l1_schedule else Decimal("0")
    l2 = total_fee * l2_schedule[1] if l2_exists and l2_schedule else Decimal("0")
    # TODO: in alpha1 where there are 100 traders, they always get the taker rebate
    if l1_exists and l1_schedule:
        rebate = total_fee * l1_schedule[2]
    elif taker_schedule:
        rebate = total_fee * taker_schedule[2]
    else:
        rebate = Decimal("0")
    platform = total_fee - (l1 + l2 + rebate)
    return {"platform": platform, "l1": l1, "l2": l2, "rebate": rebate}


def _credit_affiliate_usdc(smt: DerivadexSMT, trader_address: str, amount: Decimal):
    if amount == Decimal("0"):
        return
    strategy_key = StrategyKey(
        trader_address, StrategyKey.generate_strategy_id_hash("main")
    )
    strategy = smt.strategy(strategy_key)
    if strategy is None:
        return
    strategy.set_avail_collateral(
        TokenSymbol.USDC,
        (strategy.avail_collateral[TokenSymbol.USDC] + amount).recorded_amount(),
    )
    smt.store_strategy(strategy_key, strategy)


def _credit_affiliate_ddx(smt: DerivadexSMT, trader_address: str, amount: Decimal):
    if amount == Decimal("0"):
        return
    trader = smt.trader(TraderKey(trader_address))
    if trader is None:
        return
    trader.avail_ddx_balance = (
        trader.avail_ddx_balance + amount
    ).recorded_amount()
    smt.store_trader(TraderKey(trader_address), trader)


@define(hash=True)
class TradeFill(Fill):
    """
    Defines a TradeFill
    """

    maker_order_hash: str = field(eq=str.lower)
    maker_outcome: Outcome = field(hash=False)
    maker_order_remaining_amount: Decimal = field(hash=False)
    taker_order_hash: str = field(eq=str.lower)
    taker_outcome: Outcome = field(hash=False)
    request_index: int = field(default=-1, eq=False, hash=False)

    def __init__(
        self,
        symbol: ProductSymbol,
        taker_order_hash: str,
        maker_order_hash: str,
        maker_order_remaining_amount: Decimal,
        amount: Decimal,
        price: Decimal,
        taker_side: OrderSide,
        maker_outcome: Outcome,
        taker_outcome: Outcome,
        time_value: int,
        request_index: int = -1,
    ):
        """
        Initialize a TradeFill instance
        Parameters
        ----------
        symbol : ProductSymbol
            Product symbol
        taker_order_hash : str
            Taker order hash
        maker_order_hash : str
            Maker order hash
        maker_order_remaining_amount : Decimal
            Maker order remaining amount
        amount : Decimal
            Amount
        price : Decimal
            Price
        taker_side : OrderSide
            Taker side
        maker_outcome : Outcome
            Maker outcome
        taker_outcome : Outcome
            Taker outcome
        time_value : int
            Time value
        request_index : int
            Request index
        """
        super().__init__(
            symbol,
            amount,
            price,
            taker_side,
            time_value,
            request_index,
        )
        self.maker_order_hash = maker_order_hash
        self.maker_outcome = maker_outcome
        self.maker_order_remaining_amount = maker_order_remaining_amount
        self.taker_order_hash = taker_order_hash
        self.taker_outcome = taker_outcome

    def process_tx(
        self,
        smt: DerivadexSMT,
        **kwargs,
    ):
        """
        Process a TradeFill transaction. These are Fill transactions
        that have risen from either a CompleteFill or a PartialFill
        transaction.

        Parameters
        ----------
        smt: DerivadexSMT
            DerivaDEX Sparse Merkle Tree
        **kwargs
            Additional args specific to CompleteFill/PartialFill transactions
        """

        maker_book_order_key: BookOrderKey = BookOrderKey(
            self.symbol, self.maker_order_hash
        )
        maker_book_order = smt.book_order(maker_book_order_key)
        maker_book_order_time_value = maker_book_order.time_value

        maker_book_order.amount = self.maker_order_remaining_amount
        smt.store_book_order(maker_book_order_key, maker_book_order)

        # Make the appropriate adjustments for both the maker and taker
        # components of the Trade
        self.adjust_for_maker(
            smt,
            kwargs["epoch_id"],
            kwargs["trade_mining_active"],
            maker_book_order_time_value,
            reconcile_fees=False,
        )
        self.adjust_for_taker(
            smt,
            kwargs["epoch_id"],
            kwargs["trade_mining_active"],
            maker_book_order_time_value,
            reconcile_fees=False,
        )
        self._reconcile_fees(
            smt,
            kwargs["epoch_id"],
        )

    def _reconcile_fees(self, smt: DerivadexSMT, epoch_id: int):
        fees_default, fees_ddx = Decimal("0"), Decimal("0")
        for outcome in (self.maker_outcome, self.taker_outcome):
            if outcome.fee > Decimal("0"):
                if outcome.pay_fee_in_ddx:
                    fees_ddx += outcome.fee
                else:
                    fees_default += outcome.fee

        l1 = l2 = l1_trader = l2_trader = None
        if self.taker_outcome is not None:
            l1, l1_trader, l2, l2_trader = _resolve_affiliate_chain(
                smt, self.taker_outcome.trader
            )
        l1_schedule = _affiliate_schedule_for(l1_trader)
        l2_schedule = _affiliate_schedule_for(l2_trader)
        taker = smt.trader(TraderKey(self.taker_outcome.trader))
        taker_schedule = _affiliate_schedule_for(taker)

        if fees_default > Decimal("0"):
            split = _compute_affiliate_split(
                fees_default, l1_schedule, l2_schedule, l1 is not None, l2 is not None, taker_schedule
            )
            if l1 is not None:
                _credit_affiliate_usdc(smt, l1, split["l1"])
            if l2 is not None:
                _credit_affiliate_usdc(smt, l2, split["l2"])
            if self.taker_outcome is not None:
                _credit_affiliate_usdc(
                    smt, self.taker_outcome.trader, split["rebate"]
                )

            insurance_fund_key = InsuranceFundKey()
            insurance_fund = smt.insurance_fund(insurance_fund_key)
            insurance_fund[TokenSymbol.USDC] = (
                insurance_fund[TokenSymbol.USDC] + split["platform"]
            ).recorded_amount()
            smt.store_insurance_fund(insurance_fund_key, insurance_fund)

        if fees_ddx > Decimal("0"):
            split = _compute_affiliate_split(
                fees_ddx, l1_schedule, l2_schedule, l1 is not None, l2 is not None, taker_schedule
            )
            if l1 is not None:
                _credit_affiliate_ddx(smt, l1, split["l1"])
            if l2 is not None:
                _credit_affiliate_ddx(smt, l2, split["l2"])
            if self.taker_outcome is not None:
                _credit_affiliate_ddx(
                    smt, self.taker_outcome.trader, split["rebate"]
                )

            epoch_metadata_key = EpochMetadataKey(epoch_id)
            epoch_metadata = smt.epoch_metadata(epoch_metadata_key)
            epoch_metadata.ddx_fee_pool = (
                epoch_metadata.ddx_fee_pool + split["platform"]
            ).recorded_amount()
            smt.store_epoch_metadata(epoch_metadata_key, epoch_metadata)
