"""
PostOrder module
"""

from attrs import define, field
from ddx.common.transactions.cancel import Cancel
from ddx.common.transactions.event import Event
from ddx.common.transactions.post import Post
from ddx._rust.common import ProductSymbol
from ddx._rust.common.enums import OrderSide
from ddx._rust.common.state import DerivadexSMT
from ddx._rust.decimal import Decimal


@define
class PostOrder(Event):
    """
    Defines a PostOrder

    A PostOrder is an order that enters the order book along with any
    canceled maker orders.

    Attributes:
        post (Post): The posted order.
        canceled_orders (list[Cancel]): Canceled maker orders as a result of the posted order
        request_index (int): Sequenced request index of transaction
    """

    post: Post
    canceled_orders: list[Cancel] = field(eq=set)
    request_index: int = field(default=-1, eq=False)

    @classmethod
    def decode_value_into_cls(cls, raw_tx_log_event: dict):
        """
        Decode a raw transaction log event (dict) into a PostOrder
        instance.

        Parameters
        ----------
        raw_tx_log_event : dict
            Raw transaction log event being processed
        """

        post_tx_event = raw_tx_log_event["event"]["c"]
        cancel_orders_tx_event = post_tx_event["tradeOutcomes"]

        return cls(
            Post(
                ProductSymbol(post_tx_event["symbol"]),
                post_tx_event["orderHash"],
                OrderSide(post_tx_event["side"]),
                Decimal(post_tx_event["amount"]),
                Decimal(post_tx_event["price"]),
                post_tx_event["traderAddress"],
                post_tx_event["strategyIdHash"],
                post_tx_event["bookOrdinal"],
                raw_tx_log_event["timeValue"],
                raw_tx_log_event["requestIndex"],
            ),
            [
                Cancel(
                    ProductSymbol(canceled_order["Cancel"]["symbol"]),
                    canceled_order["Cancel"]["orderHash"],
                    Decimal(canceled_order["Cancel"]["amount"]),
                    raw_tx_log_event["requestIndex"],
                )
                for canceled_order in cancel_orders_tx_event
            ],
            raw_tx_log_event["requestIndex"],
        )

    def process_tx(
        self,
        smt: DerivadexSMT,
        **kwargs,
    ):
        """
        Process a PostOrder transaction. We will need to create a new
        BookOrder leaf with this information.

        Parameters
        ----------
        smt: DerivadexSMT
            DerivaDEX Sparse Merkle Tree
        **kwargs
            Additional args specific to PostOrder transactions
        """

        # Loop through each cancel event and process them individually
        for canceled_order in self.canceled_orders:
            canceled_order.process_tx(smt, **kwargs)

        # Process the post event
        self.post.process_tx(smt, **kwargs)
