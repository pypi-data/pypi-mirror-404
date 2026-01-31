"""
Signer Registered module
"""

from attrs import define, field
from ddx.common.transactions.event import Event
from ddx._rust.common.state import DerivadexSMT, Signer
from ddx._rust.common.state.keys import SignerKey


@define
class SignerRegistered(Event):
    """
    Defines a SignerRegistered

    A SignerRegistered is when a new enclave signer registers with the smart contract

    Attributes:
        signer_address (str): The signer address component of the signer key pertaining to the SignerRegistered tx.
        release_hash (str): The release hash component of the signer key pertaining to the SignerRegistered tx.
    """

    signer_address: str = field(eq=str.lower)
    release_hash: str = field(eq=str.lower)

    @classmethod
    def decode_value_into_cls(cls, raw_tx_log_event: dict):
        """
        Decode a raw transaction log event (dict) into a SignerRegistered
        instance.

        Parameters
        ----------
        raw_tx_log_event : dict
            Raw transaction log event being processed
        """

        event = raw_tx_log_event["event"]["c"]

        return cls(
            event["signerAddress"],
            event["releaseHash"],
        )

    def process_tx(
        self,
        smt: DerivadexSMT,
        **kwargs,
    ):
        """
        Process a SignerRegistered, inserting the signer into the tree

        Parameters
        ----------
        smt: DerivadexSMT
            DerivaDEX Sparse Merkle Tree
        **kwargs
            Additional args specific to SignerRegistered transactions
        """
        signer = Signer(self.release_hash)

        smt.store_signer(SignerKey(self.signer_address), signer)
