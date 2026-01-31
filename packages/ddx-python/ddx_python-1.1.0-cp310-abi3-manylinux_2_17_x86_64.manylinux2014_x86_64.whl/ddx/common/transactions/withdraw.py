"""
Withdraw module
"""

from attrs import define, field
from ddx.common.transactions.event import Event
from ddx._rust.common import TokenSymbol
from ddx._rust.common.state import DerivadexSMT, Strategy, Trader
from ddx._rust.common.state.keys import StrategyKey
from ddx._rust.decimal import Decimal


@define
class Withdraw(Event):
    """
    Defines a Withdraw Update

    A Withdraw Update is when a withdrawal of collateral is **signaled**.

    Attributes:
        recipient_address (str): Trader address DDX is being withdrawn to
        strategy_id_hash (str): Cross-margined strategy ID hash for which this withdrawal applies
        collateral_address (str): Collateral ERC-20 token address being withdrawn
        amount (Decimal): The amount of DDX being withdrawn
        request_index (int): Sequenced request index of transaction
    """

    recipient_address: str = field(eq=str.lower)
    strategy_id_hash: str = field(eq=str.lower)
    collateral_address: str = field(eq=str.lower)
    amount: Decimal
    request_index: int = field(default=-1, eq=False)

    @classmethod
    def decode_value_into_cls(cls, raw_tx_log_event: dict):
        """
        Decode a raw transaction log event (dict) into a Withdraw
        instance.

        Parameters
        ----------
        raw_tx_log_event : dict
            Raw transaction log event being processed
        """

        withdraw_tx_event = raw_tx_log_event["event"]["c"]

        return cls(
            withdraw_tx_event["recipientAddress"],
            withdraw_tx_event["strategy"],
            withdraw_tx_event["currency"],
            Decimal(withdraw_tx_event["amount"]),
            raw_tx_log_event["requestIndex"],
        )

    def process_tx(
        self,
        smt: DerivadexSMT,
        **kwargs,
    ):
        """
        Process a Withdraw transaction. A Withdraw event consists
        of consists of information relating to withdrawal of collateral.

        Parameters
        ----------
        smt: DerivadexSMT
            DerivaDEX Sparse Merkle Tree
        **kwargs
            Additional args specific to Withdraw transactions
        """

        strategy_key: StrategyKey = StrategyKey(
            self.recipient_address, self.strategy_id_hash
        )
        strategy: Strategy = smt.strategy(strategy_key)

        # Decrement the free balance by the withdrawn amount
        symbol = TokenSymbol.from_address(self.collateral_address)
        strategy.set_avail_collateral(
            symbol,
            strategy.avail_collateral[symbol] - self.amount,
        )
        # Increment the frozen balance by the withdrawn amount
        strategy.set_locked_collateral(
            symbol,
            strategy.locked_collateral[symbol] + self.amount,
        )

        smt.store_strategy(strategy_key, strategy)
