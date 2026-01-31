"""
PnlRealization module
"""

from attrs import define, field
from ddx.common.logging import auditor_logger
from ddx.common.transactions.event import Event
from ddx._rust.common import TokenSymbol
from ddx._rust.common.state import DerivadexSMT, Position
from ddx._rust.common.state.keys import PositionKey, StrategyKey
from ddx._rust.decimal import Decimal

logger = auditor_logger(__name__)


@define
class PnlRealization(Event):
    """
    Defines a PnlRealization

    A PnlRealization is when unrealized pnl is settled/realized for all
    traders' strategies. This will result in a credit/debit for all
    strategies.

    Attributes:
        settlement_epoch_id (int): Settlement epoch id
        time_value (int): Time value
        request_index (int): Sequenced request index of transaction
    """

    settlement_epoch_id: int
    time_value: int
    request_index: int = field(default=-1, eq=False)

    @classmethod
    def decode_value_into_cls(cls, raw_tx_log_event: dict):
        """
        Decode a raw transaction log event (dict) into a PnlRealization
        instance.

        Parameters
        ----------
        raw_tx_log_event : dict
            Raw transaction log event being processed
        """

        event = raw_tx_log_event["event"]["c"]

        return cls(
            event["settlementEpochId"],
            raw_tx_log_event["timeValue"],
            raw_tx_log_event["requestIndex"],
        )

    def process_tx(
        self,
        smt: DerivadexSMT,
        **kwargs,
    ):
        """
        Process a PnlRealization transaction. A PnlRealization event
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
            Additional args specific to PnlRealization transactions
        """

        for (
            position_key,
            position,
        ) in sorted(
            smt.all_positions(),
            key=lambda item: item[0].symbol,
        ):
            mark_price = kwargs["latest_price_leaves"][position_key.symbol][
                1
            ].mark_price
            unrealized_pnl = position.unrealized_pnl(
                mark_price,
            )

            # Construct a StrategyKey and corresponding encoded
            # key
            strategy_key: StrategyKey = position_key.as_strategy_key()

            # Get the Strategy leaf given the key from above
            strategy = smt.strategy(strategy_key)

            old_balance = strategy.avail_collateral[TokenSymbol.USDC]
            # Credit/debit the trader's Strategy leaf by the
            # unrealized PNL to settle
            strategy.set_avail_collateral(
                TokenSymbol.USDC,
                strategy.avail_collateral[TokenSymbol.USDC] + unrealized_pnl,
            )
            logger.info(
                f"Calculated realized pnl:\n\told balance: {old_balance}\n\tnew balance: {strategy.avail_collateral[TokenSymbol.USDC]}\n\tpnl realized: {strategy.avail_collateral[TokenSymbol.USDC] - old_balance}"
            )

            smt.store_strategy(
                strategy_key,
                strategy,
            )

            # Set the Position's average entry price to the mark price
            # since settlement has just taken place
            position.avg_entry_price = mark_price

            smt.store_position(
                position_key,
                position,
            )
