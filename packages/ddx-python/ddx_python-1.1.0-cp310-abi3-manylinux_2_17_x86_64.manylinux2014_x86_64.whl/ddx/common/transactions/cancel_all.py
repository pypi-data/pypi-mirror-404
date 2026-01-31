"""
CancelAll module
"""

from attrs import define, field
from ddx.common.transactions.cancel import Cancel
from ddx.common.transactions.event import Event
from ddx._rust.common import ProductSymbol
from ddx._rust.common.state import BookOrder, DerivadexSMT
from ddx._rust.common.state.keys import BookOrderKey
from ddx._rust.h256 import H256


@define
class CancelAll(Event):
    """
    Defines a CancelAll

    A CancelAll is when all existing orders are canceled and removed from the
    order book for a given trader, strategy, and symbol.

    Attributes:
        symbol (ProductSymbol): The symbol for the market to cancel all orders for.
        trader_address (str): The trader address component of the strategy key pertaining to the CancelAll tx.
        strategy_id_hash (str): The strategy id hash component of the strategy key pertaining to the CancelAll tx.
        request_index (int): Sequenced request index of transaction
    """

    symbol: ProductSymbol
    trader_address: str = field(eq=str.lower)
    strategy_id_hash: str = field(eq=str.lower)
    request_index: int = field(default=-1, eq=False)

    @classmethod
    def decode_value_into_cls(cls, raw_tx_log_event: dict):
        """
        Decode a raw transaction log event (dict) into a CancelAll
        instance.

        Parameters
        ----------
        raw_tx_log_event : dict
            Raw transaction log event being processed
        """

        cancel_tx_event = raw_tx_log_event["event"]["c"]

        return cls(
            ProductSymbol(cancel_tx_event["symbol"]),
            cancel_tx_event["strategyKey"]["traderAddress"],
            cancel_tx_event["strategyKey"]["strategyIdHash"],
            raw_tx_log_event["requestIndex"],
        )

    def process_tx(
        self,
        smt: DerivadexSMT,
        **kwargs,
    ):
        """
        Process a CancelAll transaction. We will need to delete a
        BookOrder leaf with this information.

        Parameters
        ----------
        smt: DerivadexSMT
            DerivaDEX Sparse Merkle Tree
        **kwargs
            Additional args specific to CancelAll transactions
        """

        book_order_leaves: list[tuple[BookOrderKey, BookOrder]] = [
            (book_order_key, book_order)
            for book_order_key, book_order in smt.all_book_orders_for_symbol(
                self.symbol
            )
            if book_order.trader_address == self.trader_address
            and book_order.strategy_id_hash == self.strategy_id_hash
        ]

        for book_order_key, book_order in book_order_leaves:
            cancel = Cancel(
                book_order_key.symbol,
                book_order_key.order_hash,
                book_order.amount,
                self.request_index,
            )
            cancel.process_tx(smt)
