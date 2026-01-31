"""
DisasterRecovery module
"""

from attrs import define, field
from ddx.common.transactions.event import Event
from ddx._rust.common import TokenSymbol
from ddx._rust.common.state import DerivadexSMT
from ddx._rust.common.state.keys import StrategyKey
from ddx._rust.decimal import Decimal


@define
class DisasterRecovery(Event):
    """
    Defines a DisasterRecovery

    A DisasterRecovery is when the system is wound down in an extreme recovery scenario.

    Attributes:
        request_index (int): Sequenced request index of transaction
    """

    request_index: int = field(default=-1, eq=False)

    @classmethod
    def decode_value_into_cls(cls, raw_tx_log_event: dict):
        """
        Decode a raw transaction log event (dict) into a DisasterRecovery
        instance.

        Parameters
        ----------
        raw_tx_log_event : dict
            Raw transaction log event being processed
        """

        return cls(
            raw_tx_log_event["requestIndex"],
        )

    def process_tx(
        self,
        smt: DerivadexSMT,
        **kwargs,
    ):
        """
        Process a DisasterRecovery transaction.

        Parameters
        ----------
        smt: DerivadexSMT
            DerivaDEX Sparse Merkle Tree
        **kwargs
            Additional args specific to DisasterRecovery transactions
        """

        raise NotImplementedError()

        # sorted_positions = sorted(
        #     smt.all_positions(),
        #     key=lambda item: item[1].unrealized_pnl(
        #         kwargs["latest_price_leaves"][item[0].symbol][1].mark_price
        #     ),
        #     reverse=True,
        # )
        #
        # for position_key, position in sorted_positions:
        #     unrealized_pnl = position.unrealized_pnl(
        #         kwargs["latest_price_leaves"][position_key.symbol][1].mark_price
        #     )
        #
        #     strategy_key: StrategyKey = position_key.as_strategy_key()
        #     # Get the Strategy leaf given the key from above
        #     strategy = smt.strategy(strategy_key)
        #
        #     # Credit/debit the trader's Strategy leaf by the
        #     # unrealized PNL to settle
        #     update_avail_collateral(
        #         strategy,
        #         TokenSymbol.USDC,
        #         strategy.avail_collateral[TokenSymbol.USDC] + unrealized_pnl,
        #     )
        #
        #     smt.store_strategy(
        #         strategy_key,
        #         strategy,
        #     )
        #
        #     smt.store_position(
        #         position_key,
        #         None,
        #     )
        #
        # for book_order_key, _ in smt.all_book_orders():
        #     smt.store_book_order_by_key(book_order_key, None)
