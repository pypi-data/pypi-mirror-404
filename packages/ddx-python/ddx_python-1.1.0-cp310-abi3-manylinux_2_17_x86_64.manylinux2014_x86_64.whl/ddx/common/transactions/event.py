"""
Event module
"""

from abc import ABC, abstractmethod

from ddx._rust.common.state import DerivadexSMT


class Event(ABC):
    """
    An Event class from which all Transaction classes inherit
    """

    @classmethod
    def decode_value_into_cls(cls, raw_tx_log_event: dict):
        """
        Decode a raw transaction log event (dict) into an instance of
        the class.

        Parameters
        ----------
        raw_tx_log_event : dict
            Raw transaction log event being processed
        """

        raise NotImplementedError()

    @abstractmethod
    def process_tx(self, smt: DerivadexSMT, **kwargs):
        """
        Process transaction log event by modifying the SMT state
        and emitting any corresponding events to the Trader when
        appropriate.

        Parameters
        ----------
        smt: DerivadexSMT
            DerivaDEX Sparse Merkle Tree
        trader_auditor_queue : asyncio.Queue
            Queue for sending events from the Auditor to the Trader
        suppress_trader_queue: bool
            Suppress trader queue messages
        **kwargs
            Additional args specific to various transaction types
        """

        raise NotImplementedError()
