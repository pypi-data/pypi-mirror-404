"""
Cancel module
"""

import logging

from attrs import define, field
from ddx.common.transactions.event import Event
from ddx._rust.common import ProductSymbol
from ddx._rust.common.state import DerivadexSMT
from ddx._rust.common.state.keys import BookOrderKey
from ddx._rust.decimal import Decimal

logger = logging.getLogger(__name__)


@define(hash=True)
class Cancel(Event):
    """
    Defines a Cancel

    A Cancel is when an existing order is canceled and removed from the
    order book.

    Attributes:
        symbol (ProductSymbol): The symbol for the market this order is for.
        order_hash (str): Hexstr representation of the EIP-712 hash of the order
        amount (Decimal): Amount/size of order
        request_index (int): Sequenced request index of transaction
    """

    symbol: ProductSymbol
    order_hash: str = field(eq=str.lower)
    amount: Decimal
    request_index: int = field(default=-1, eq=False, hash=False)

    @classmethod
    def decode_value_into_cls(cls, raw_tx_log_event: dict):
        """
        Decode a raw transaction log event (dict) into a Cancel
        instance.

        Parameters
        ----------
        raw_tx_log_event : dict
            Raw transaction log event being processed
        """

        cancel_tx_event = raw_tx_log_event["event"]["c"]

        return cls(
            ProductSymbol(cancel_tx_event["symbol"]),
            cancel_tx_event["orderHash"],
            Decimal(cancel_tx_event["amount"]),
            raw_tx_log_event["requestIndex"],
        )

    def process_tx(
        self,
        smt: DerivadexSMT,
        **kwargs,
    ):
        """
        Process a Cancel transaction. We will need to delete a
        BookOrder leaf with this information.

        Parameters
        ----------
        smt: DerivadexSMT
            DerivaDEX Sparse Merkle Tree
        **kwargs
            Additional args specific to Cancel transactions
        """

        logger.debug(f"Canceling {self.symbol} order {self.order_hash}")
        smt.store_book_order(BookOrderKey(self.symbol, self.order_hash), None)
