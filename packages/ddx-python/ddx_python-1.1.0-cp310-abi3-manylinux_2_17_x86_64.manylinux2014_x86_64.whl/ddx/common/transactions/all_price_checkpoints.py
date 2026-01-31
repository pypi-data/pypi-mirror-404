"""
AllPriceCheckpoints module
"""

from attrs import define, field
from ddx.common.transactions.event import Event
from ddx.common.transactions.price_checkpoint import PriceCheckpoint
from ddx._rust.common import ProductSymbol
from ddx._rust.common.accounting import MarkPriceMetadata
from ddx._rust.common.state import DerivadexSMT
from ddx._rust.decimal import Decimal


@define
class AllPriceCheckpoints(Event):
    """
    Defines a AllPriceCheckpoints

    An AllPriceCheckpoints is when a market registers an update to the
    composite index price a perpetual is tracking along with the ema
    component for 1+ symbols.

    Attributes:
        price_checkpoints (list[PriceCheckpoint]): The price checkpoints that make up this transaction
        request_index (int): Sequenced request index of transaction
    """

    price_checkpoints: list[PriceCheckpoint] = field(eq=set)
    request_index: int = field(default=-1, eq=False)

    @classmethod
    def decode_value_into_cls(cls, raw_tx_log_event: dict):
        """
        Decode a raw transaction log event (dict) into an
        AllPriceCheckpoints instance.

        Parameters
        ----------
        raw_tx_log_event : dict
            Raw transaction log event being processed
        """

        all_price_checkpoint_tx_event = raw_tx_log_event["event"]["c"]

        return cls(
            [
                PriceCheckpoint(
                    ProductSymbol(all_price_checkpoints_key),
                    MarkPriceMetadata.from_dict(
                        all_price_checkpoints_val["markPriceMetadata"]
                    ),
                    all_price_checkpoints_val["indexPriceHash"],
                    Decimal(all_price_checkpoints_val["indexPrice"]),
                    all_price_checkpoints_val["ordinal"],
                    all_price_checkpoints_val["timeValue"],
                    raw_tx_log_event["requestIndex"],
                )
                for all_price_checkpoints_key, all_price_checkpoints_val in all_price_checkpoint_tx_event.items()
            ],
            raw_tx_log_event["requestIndex"],
        )

    def process_tx(
        self,
        smt: DerivadexSMT,
        **kwargs,
    ):
        """
        Process an AllPriceCheckpoints transaction. An
        AllPriceCheckpoints consists of information relating to a new
        price checkpoint for 1+ symbols.

        Parameters
        ----------
        smt: DerivadexSMT
            DerivaDEX Sparse Merkle Tree
        **kwargs
            Additional args specific to AllPriceCheckpoints transactions
        """

        # Loop through each price checkpoint event and process them
        # individually
        for price_checkpoint in self.price_checkpoints:
            price_checkpoint.process_tx(smt, **kwargs)
