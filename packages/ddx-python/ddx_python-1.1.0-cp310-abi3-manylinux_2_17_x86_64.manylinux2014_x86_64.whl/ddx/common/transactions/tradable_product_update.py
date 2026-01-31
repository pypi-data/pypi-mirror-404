"""
Tradable Product Update module
"""

from attrs import define, field
from ddx.common.transactions.event import Event
from ddx._rust.common.specs import SpecsKind
from ddx._rust.common.state import (DerivadexSMT, TradableProduct,
                                    TradableProductParameters)
from ddx._rust.common.state.keys import SpecsKey, TradableProductKey


@define
class TradableProductUpdate(Event):
    """
    Defines a Tradable Product Update

    A TradableProductUpdate is an update to a trader's strategy (such as depositing or withdrawing collateral).

    Attributes:
        additions (list[TradableProductKey]): List of tradable product keys that are marked tradable
        removals (list[TradableProductKey]): List of tradable product keys that are marked untradable
        request_index (int): Sequenced request index of transaction
    """

    additions: list[TradableProductKey]
    removals: list[TradableProductKey]
    request_index: int = field(default=-1, eq=False, hash=False)

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

        tradable_product_update_tx_event = raw_tx_log_event["event"]["c"]

        return cls(
            [
                TradableProductKey(
                    SpecsKey(
                        SpecsKind(tradable_product_key["specsKey"]["kind"]),
                        tradable_product_key["specsKey"]["name"],
                    ),
                    TradableProductParameters.from_dict(
                        tradable_product_key["parameters"]
                    ),
                )
                for tradable_product_key in tradable_product_update_tx_event[
                    "additions"
                ]
            ],
            [
                TradableProductKey(
                    SpecsKey(
                        SpecsKind(tradable_product_key["specsKey"]["kind"]),
                        tradable_product_key["specsKey"]["name"],
                    ),
                    TradableProductParameters.from_dict(
                        tradable_product_key["parameters"]
                    ),
                )
                for tradable_product_key in tradable_product_update_tx_event["removals"]
            ],
            raw_tx_log_event["requestIndex"],
        )

    def process_tx(
        self,
        smt: DerivadexSMT,
        **kwargs,
    ):
        """
        Process a TradableProductUpdate transaction. A TradableProductUpdate consists
        of information relating to updates of the list of tradable products.

        Parameters
        ----------
        smt: DerivadexSMT
            DerivaDEX Sparse Merkle Tree
        **kwargs
            Additional args specific to TradableProductUpdate transactions
        """

        for tradable_product_key in self.additions:
            smt.store_tradable_product(
                tradable_product_key,
                TradableProduct(),
            )

        for tradable_product_key in self.removals:
            smt.store_tradable_product(tradable_product_key, None)
