"""
Strategy Update module
"""

from typing import Optional

from attrs import define, field
from ddx.common.transactions.event import Event
from ddx.common.utils import calculate_max_collateral
from ddx._rust.common import TokenSymbol
from ddx._rust.common.state import DerivadexSMT, Strategy, Trader
from ddx._rust.common.state.keys import StrategyKey, TraderKey
from ddx._rust.common.transactions import StrategyUpdateKind
from ddx._rust.decimal import Decimal


@define
class StrategyUpdate(Event):
    """
    Defines a Strategy Update

    A StrategyUpdate is an update to a trader's strategy (such as
    depositing or withdrawing collateral).

    Attributes:
        trader_address (str): Trader's Ethereum address this strategy belongs to
        collateral_address (str): Collateral's Ethereum address a deposit/withdrawal has been made with
        strategy_id_hash (str): Strategy ID hash for the given trader this event belongs to
        strategy_id (Optional[str]): Strategy ID for the given trader this event belongs to. Only deposits will fill this field
        amount (Decimal): The amount of collateral deposited or withdrawn
        update_kind (StrategyUpdateKind): Update kind (Deposit=0, Withdraw=1)
        tx_hash (str): The Ethereum transaction's hash
        request_index (int): Sequenced request index of transaction
    """

    trader_address: str = field(eq=str.lower)
    collateral_address: str = field(eq=str.lower)
    strategy_id_hash: str = field(eq=str.lower)
    strategy_id: Optional[str]
    amount: Decimal
    update_kind: StrategyUpdateKind
    tx_hash: str = field(eq=str.lower)
    request_index: int = field(default=-1, eq=False)

    @classmethod
    def decode_value_into_cls(cls, raw_tx_log_event: dict):
        """
        Decode a raw transaction log event (dict) into a StrategyUpdate
        instance.

        Parameters
        ----------
        raw_tx_log_event : dict
            Raw transaction log event being processed
        """

        strategy_update_tx_event = raw_tx_log_event["event"]["c"]

        return cls(
            strategy_update_tx_event["trader"],
            strategy_update_tx_event["collateralAddress"],
            strategy_update_tx_event["strategyIdHash"],
            strategy_update_tx_event.get("strategyId"),
            Decimal(strategy_update_tx_event["amount"]),
            StrategyUpdateKind(strategy_update_tx_event["updateKind"]),
            strategy_update_tx_event["txHash"],
            raw_tx_log_event["requestIndex"],
        )

    def process_tx(
        self,
        smt: DerivadexSMT,
        **kwargs,
    ):
        """
        Process a StrategyUpdate transaction. A StrategyUpdate consists
        of information relating to updates for a trader's strategy, such
        as when their free or frozen collateral has changed due to a
        deposit or withdrawal. This will update the Strategy leaf in the
        SMT.

        Parameters
        ----------
        smt: DerivadexSMT
            DerivaDEX Sparse Merkle Tree
        **kwargs
            Additional args specific to StrategyUpdate transactions
        """

        strategy_key: StrategyKey = StrategyKey(
            self.trader_address, self.strategy_id_hash
        )
        strategy = smt.strategy(strategy_key)

        symbol = TokenSymbol.from_address(self.collateral_address)
        if self.update_kind == StrategyUpdateKind.Deposit:
            # If StrategyUpdate is of deposit type

            trader_key: TraderKey = TraderKey(self.trader_address)
            trader = smt.trader(trader_key)

            if strategy is None:
                # If we haven't yet seen the Strategy leaf, create a new
                # one
                strategy = Strategy.default()

                if trader is None:
                    # Initialize a new Trader Leaf
                    trader = Trader.default()

                    smt.store_trader(trader_key, trader)

            # Compute max allowable deposit given the collateral guard
            # for the trader's DDX balance
            max_allowable_deposit = max(
                (
                    calculate_max_collateral(
                        kwargs["collateral_tranches"], trader.avail_ddx_balance
                    )
                    - strategy.avail_collateral.total_value()
                ),
                Decimal("0"),
            )

            # Compute how much of the attempted deposit will be added
            # to the Strategy's free collateral
            net = min(max_allowable_deposit, self.amount)

            # Increment the Strategy's free collateral
            strategy.set_avail_collateral(
                symbol,
                strategy.avail_collateral[symbol] + net,
            )

            # Compute how much of the attempted deposit will be added
            # to the Strategy's frozen collateral
            kickback = self.amount - net
            if kickback != Decimal("0"):
                # Increment the Strategy's frozen collateral
                strategy.set_locked_collateral(
                    symbol,
                    strategy.locked_collateral[symbol] + kickback,
                )
        elif self.update_kind == StrategyUpdateKind.Withdraw:
            # If StrategyUpdate is of withdrawal (claimed) type
            if strategy is None or strategy.locked_collateral[symbol] < self.amount:
                raise Exception(
                    "Strategy leaf either non-existent or insufficiently capitalized to facilitate withdrawal"
                )

            # Adjust the existing strategy leaf by decrementing the
            # free collateral by the amount in the withdrawal event
            strategy.set_locked_collateral(
                symbol,
                strategy.locked_collateral[symbol] - self.amount,
            )

        smt.store_strategy(strategy_key, strategy)
