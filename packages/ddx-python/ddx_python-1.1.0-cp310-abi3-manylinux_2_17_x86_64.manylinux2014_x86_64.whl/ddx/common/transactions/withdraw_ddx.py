"""
WithdrawDDX module
"""

from attrs import define, field
from ddx.common.transactions.event import Event
from ddx._rust.common.state import DerivadexSMT
from ddx._rust.common.state.keys import TraderKey
from ddx._rust.decimal import Decimal


@define
class WithdrawDDX(Event):
    """
    Defines a WithdrawDDX Update

    A WithdrawDDX is when a withdrawal of DDX is signaled.

    Attributes:
        recipient_address (str): Ethereum address DDX is being withdrawn to
        amount (Decimal): The amount of DDX being withdrawn
        request_index (int): Sequenced request index of transaction
    """

    recipient_address: str = field(eq=str.lower)
    amount: Decimal
    request_index: int = field(default=-1, eq=False)

    @classmethod
    def decode_value_into_cls(cls, raw_tx_log_event: dict):
        """
        Decode a raw transaction log event (dict) into a WithdrawDDX
        instance.

        Parameters
        ----------
        raw_tx_log_event : dict
            Raw transaction log event being processed
        """

        withdraw_ddx_tx_event = raw_tx_log_event["event"]["c"]

        return cls(
            withdraw_ddx_tx_event["recipientAddress"],
            Decimal(withdraw_ddx_tx_event["amount"]),
            raw_tx_log_event["requestIndex"],
        )

    def process_tx(
        self,
        smt: DerivadexSMT,
        **kwargs,
    ):
        """
        Process a WithdrawDDX transaction. A WithdrawDDX event consists
        of consists of information relating to withdrawal of DDX.

        Parameters
        ----------
        smt: DerivadexSMT
            DerivaDEX Sparse Merkle Tree
        **kwargs
            Additional args specific to WithdrawDDX transactions
        """

        trader_key: TraderKey = TraderKey(self.recipient_address)
        trader = smt.trader(trader_key)

        # Decrement the free balance by the withdrawn amount
        trader.avail_ddx_balance -= self.amount
        # Increment the frozen balance by the withdrawn amount
        trader.locked_ddx_balance += self.amount

        smt.store_trader(trader_key, trader)
