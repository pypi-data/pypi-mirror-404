"""
FuturesExpiry module
"""

from typing import Optional

import numpy as np
from attrs import define, field
from ddx.common.logging import auditor_logger
from ddx.common.transaction_utils import get_prices_for_symbol_and_duration
from ddx.common.transactions.cancel import Cancel
from ddx.common.transactions.event import Event
from ddx.common.transactions.inner.adl_outcome import AdlOutcome
from ddx.common.transactions.inner.liquidated_position import LiquidatedPosition
from ddx.common.transactions.inner.liquidation_entry import LiquidationEntry
from ddx.common.transactions.inner.outcome import Outcome
from ddx.common.transactions.liquidation import Liquidation
from ddx._rust.common import ProductSymbol
from ddx._rust.common.enums import OrderSide
from ddx._rust.common.specs import Quarter
from ddx._rust.common.state import DerivadexSMT, Position
from ddx._rust.common.state.keys import PositionKey, StrategyKey
from ddx._rust.decimal import Decimal

logger = auditor_logger(__name__)


@define(hash=True)
class FuturesExpiry(Event):
    """
    Defines a FuturesExpiry

    A FuturesExpiry is when all futures of a fixed duration expire.
    This will result in a credit/debit for all strategies.

    Attributes:
        settlement_epoch_id (int): Settlement epoch id
        quarter (Quarter): Quarter of the futures expired
        time_value (int): Time value
        request_index (int): Sequenced request index of transaction
    """

    settlement_epoch_id: int
    quarter: Quarter
    time_value: int
    request_index: int = field(default=-1, eq=False, hash=False)

    @classmethod
    def decode_value_into_cls(cls, raw_tx_log_event: dict):
        """
        Decode a raw transaction log event (dict) into a FuturesExpiry
        instance.

        Parameters
        ----------
        raw_tx_log_event : dict
            Raw transaction log event being processed
        """

        futures_expiry_tx_event = raw_tx_log_event["event"]["c"]

        return cls(
            futures_expiry_tx_event["settlementEpochId"],
            Quarter(futures_expiry_tx_event["quarter"]),
            raw_tx_log_event["timeValue"],
            raw_tx_log_event["requestIndex"],
        )

    def process_tx(
        self,
        smt: DerivadexSMT,
        **kwargs,
    ):
        """
        Process a FuturesExpiry transaction. A FuturesExpiry event
        consists of information relating to when unrealized pnl is
        settled/realized for all traders' strategies. This will result
        in a credit/debit for all strategies. Furthermore, the
        average entry price for any open positions will be set to the
        current mark price.

        Parameters
        ----------
        smt: DerivadexSMT
            DerivaDEX Sparse Merkle Tree
        **kwargs
            Additional args specific to FuturesExpiry transactions
        """

        # Close all open orders
        book_order_leaves: list[tuple[BookOrderKey, BookOrder]] = [
            (book_order_key, book_order)
            for book_order_key, book_order in smt.all_book_orders()
            if (quarter := book_order_key.symbol.futures_quarter()) is not None
            and quarter == self.quarter
        ]

        for book_order_key, book_order in book_order_leaves:
            cancel = Cancel(
                book_order_key.symbol,
                book_order_key.order_hash,
                book_order.amount,
                self.request_index,
            )
            cancel.process_tx(smt)

        # Close all open positions for the expiring quarter
        relevant_positions: list[tuple[PositionKey, Position]] = [
            (position_key, position)
            for position_key, position in sorted(
                smt.all_positions(),
                key=lambda item: item[0].symbol,
            )
            if (quarter := position_key.symbol.futures_quarter()) is not None
            and quarter == self.quarter
        ]

        for position_key, position in relevant_positions:
            # Set position balances to zero
            position.balance = Decimal(0)

            # Store the position
            smt.store_position(position_key, position)
