"""
SpecsUpdate module
"""

from attrs import define, field
from ddx.common.transactions.event import Event
from ddx._rust.common import ProductSymbol
from ddx._rust.common.specs import SpecsKind
from ddx._rust.common.state import Specs
from ddx._rust.common.state.keys import SpecsKey
from ddx._rust.decimal import Decimal


# TODO: test usage
@define
class SpecsUpdate(Event):
    """
    Defines an SpecsUpdate

    An SpecsUpdate is a transaction that updates the market specs

    Attributes:
        key (SpecsKey): The key of the specs being updated
        expr (Specs): The expression of the specs being updated
        block_number (int): Block number of transaction
        tx_hash (str): Transaction hash of on-chain action
        request_index (int): Sequenced request index of transaction
    """

    key: SpecsKey
    expr: Specs
    block_number: int
    tx_hash: str = field(eq=str.lower)
    request_index: int = field(default=-1, eq=False)

    @classmethod
    def decode_value_into_cls(cls, raw_tx_log_event: dict):
        """
        Decode a raw transaction log event (dict) into a
        SpecsUpdate instance.

        Parameters
        ----------
        raw_tx_log_event : dict
            Raw transaction log event being processed
        """

        specs_update_tx_event = raw_tx_log_event["event"]["c"]

        return cls(
            SpecsKey(
                SpecsKind(specs_update_tx_event["key"]["kind"]),
                specs_update_tx_event["key"]["name"],
            ),
            Specs(specs_update_tx_event["expr"]),
            specs_update_tx_event["blockNumber"],
            specs_update_tx_event["txHash"],
            raw_tx_log_event["requestIndex"],
        )

    # TODO: process_tx
