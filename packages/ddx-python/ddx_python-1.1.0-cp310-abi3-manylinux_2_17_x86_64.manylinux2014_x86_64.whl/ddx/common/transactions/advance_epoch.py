"""
AdvanceEpoch module
"""

from attrs import define, field
from ddx.common.transactions.event import Event
from ddx._rust.common import ProductSymbol, TokenSymbol
from ddx._rust.common.state import DerivadexSMT, EpochMetadata
from ddx._rust.common.state.keys import EpochMetadataKey
from ddx._rust.decimal import Decimal


@define
class AdvanceEpoch(Event):
    """
    Defines an AdvanceEpoch

    An AdvanceEpoch is a non-transitioning transaction that indicates
    the start of a new epoch.

    Attributes:
        next_book_ordinals (dict[ProductSymbol, int]): dictionary ({symbol: next_book_ordinal}) indicating the next book ordinal by symbol
        new_epoch_id (int): New epoch ID after epoch marker
        request_index (int): Sequenced request index of transaction
    """

    next_book_ordinals: dict[ProductSymbol, int]
    new_epoch_id: int
    request_index: int = field(default=-1, eq=False)

    @classmethod
    def decode_value_into_cls(cls, raw_tx_log_event: dict):
        """
        Decode a raw transaction log event (dict) into an AdvanceEpoch
        instance.

        Parameters
        ----------
        raw_tx_log_event : dict
            Raw transaction log event being processed
        """

        advance_epoch_tx_event = raw_tx_log_event["event"]["c"]

        return cls(
            {
                ProductSymbol(symbol): ordinal
                for symbol, ordinal in advance_epoch_tx_event[
                    "nextBookOrdinals"
                ].items()
            },
            advance_epoch_tx_event["newEpochId"],
            raw_tx_log_event["requestIndex"],
        )

    def process_tx(
        self,
        smt: DerivadexSMT,
        **kwargs,
    ):
        """
        Process an EpochMarker transaction of type AdvanceEpoch. This
        indicates the a new epoch in the transaction log, although
        it is not state-transitioning in the way typical transactions
        are.

        Parameters
        ----------
        smt: DerivadexSMT
            DerivaDEX Sparse Merkle Tree
        **kwargs
            Additional args specific to AdvanceEpoch transactions
        """

        # Update current epoch next book ordinals for closing
        old_epoch_metadata_key = EpochMetadataKey(self.new_epoch_id - 1)
        old_epoch_metadata = smt.epoch_metadata(old_epoch_metadata_key)
        old_epoch_metadata.next_book_ordinals = self.next_book_ordinals
        smt.store_epoch_metadata(old_epoch_metadata_key, old_epoch_metadata)

        # Create a new epoch metadata
        smt.store_epoch_metadata(
            EpochMetadataKey(self.new_epoch_id), EpochMetadata.default()
        )

        # Set the expected epoch ID to be the new epoch ID and the
        # expected tx ordinal to be -1, because we immediately increment
        # this by 1, thus setting it to 0, which will be the first
        # tx ordinal of the next epoch
        kwargs["expected_epoch_id"](kwargs["auditor_instance"], self.new_epoch_id)
        kwargs["expected_tx_ordinal"](kwargs["auditor_instance"], -1)
