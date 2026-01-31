"""
PartialFill module
"""

from attrs import define, field
from ddx.common.transactions.cancel import Cancel
from ddx.common.transactions.event import Event
from ddx.common.transactions.inner.outcome import Outcome
from ddx.common.transactions.inner.trade_fill import TradeFill
from ddx.common.transactions.post import Post
from ddx._rust.common import ProductSymbol
from ddx._rust.common.enums import OrderSide
from ddx._rust.common.state import DerivadexSMT
from ddx._rust.decimal import Decimal


@define
class PartialFill(Event):
    """
    Defines an PartialFill

    A PartialFill is a scenario where the taker order has been partially filled
    across 1 or more maker orders and thus has a remaining order that enters the
    book along with any canceled maker orders.

    Attributes:
        post (Post): A Post object
        trade_outcomes (list[TradeFill | Cancel]): A list of trade outcome objects
        request_index (int): Sequenced request index of transaction
    """

    post: Post
    trade_outcomes: list[TradeFill | Cancel] = field(eq=set)
    request_index: int = field(default=-1, eq=False)

    @classmethod
    def decode_value_into_cls(cls, raw_tx_log_event: dict):
        """
        Decode a raw transaction log event (dict) into a PartialFill
        instance.

        Parameters
        ----------
        raw_tx_log_event : dict
            Raw transaction log event being processed
        """

        event = raw_tx_log_event["event"]["c"]
        trade_outcomes_tx_event = event["tradeOutcomes"]

        return cls(
            Post(
                ProductSymbol(event["symbol"]),
                event["orderHash"],
                OrderSide(event["side"]),
                Decimal(event["amount"]),
                Decimal(event["price"]),
                event["traderAddress"],
                event["strategyIdHash"],
                event["bookOrdinal"],
                # NOTE 3503: This is logically identical to the time value in BookOrder, so not repeating it.
                raw_tx_log_event["timeValue"],
                raw_tx_log_event["requestIndex"],
            ),
            [
                (
                    TradeFill(
                        ProductSymbol(trade_outcome["Fill"]["symbol"]),
                        trade_outcome["Fill"]["takerOrderHash"],
                        trade_outcome["Fill"]["makerOrderHash"],
                        Decimal(trade_outcome["Fill"]["makerOrderRemainingAmount"]),
                        Decimal(trade_outcome["Fill"]["amount"]),
                        Decimal(trade_outcome["Fill"]["price"]),
                        OrderSide(trade_outcome["Fill"]["takerSide"]),
                        Outcome(
                            trade_outcome["Fill"]["makerOutcome"]["trader"],
                            trade_outcome["Fill"]["makerOutcome"]["strategyIdHash"],
                        ),
                        Outcome(
                            trade_outcome["Fill"]["takerOutcome"]["trader"],
                            trade_outcome["Fill"]["takerOutcome"]["strategyIdHash"],
                        ),
                        raw_tx_log_event["timeValue"],
                        raw_tx_log_event["requestIndex"],
                    )
                    if "Fill" in trade_outcome
                    else Cancel(
                        ProductSymbol(trade_outcome["Cancel"]["symbol"]),
                        trade_outcome["Cancel"]["orderHash"],
                        Decimal(trade_outcome["Cancel"]["amount"]),
                        raw_tx_log_event["requestIndex"],
                    )
                )
                for trade_outcome in trade_outcomes_tx_event
            ],
            raw_tx_log_event["requestIndex"],
        )

    def process_tx(
        self,
        smt: DerivadexSMT,
        **kwargs,
    ):
        """
        Process a PartialFill transaction. A PartialFill consists of
        Fill objects, which will adjust the maker BookOrder leaf in the
        SMT, while also adjusting the Strategy, Position, and Trader
        leaves corresponding to both the maker and the taker. It also
        consists of a Post object, which will be a BookOrder consisting
        of what's left of the partially matched order.

        Parameters
        ----------
        smt: DerivadexSMT
            DerivaDEX Sparse Merkle Tree
        **kwargs
            Additional args specific to PartialFill transactions
        """

        # Loop through each trade outcome event and process them individually
        for trade_outcome in self.trade_outcomes:
            trade_outcome.process_tx(smt, **kwargs)

        # Process the remaining post event
        self.post.process_tx(smt, **kwargs)
