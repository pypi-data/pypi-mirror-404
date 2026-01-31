"""
AdvanceSettlementEpoch module
"""

from attrs import define, field
from ddx.common.transactions.event import Event
from ddx._rust.common.state import DerivadexSMT


@define
class AdvanceSettlementEpoch(Event):
    """
    Defines a AdvanceSettlementEpoch

    A AdvanceSettlementEpoch is a non-transitioning transaction that indicates
    the start of a new settlement epoch.

    Attributes:
        request_index (int): Sequenced request index of transaction
    """

    request_index: int = field(default=-1, eq=False)

    @classmethod
    def decode_value_into_cls(cls, raw_tx_log_event: dict):
        """
        Decode a raw transaction log event (dict) into a AdvanceSettlementEpoch
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
        Process a AdvanceSettlementEpoch transaction.

        Parameters
        ----------
        smt: DerivadexSMT
            DerivaDEX Sparse Merkle Tree
        **kwargs
            Additional args specific to AdvanceSettlementEpoch transactions
        """

        latest_price_keys = {
            price_key for price_key, _ in kwargs["latest_price_leaves"].values()
        }
        for price_key, _ in smt.all_prices():
            if price_key in latest_price_keys:
                continue

            smt.store_price(price_key, None)
