"""
FeeDistribution
"""

from attrs import define, field
from ddx.common.transactions.event import Event
from ddx._rust.common import TokenSymbol
from ddx._rust.common.state import DerivadexSMT, EpochMetadata, Trader
from ddx._rust.common.state.keys import EpochMetadataKey, TraderKey
from ddx._rust.decimal import Decimal


@define
class FeeDistribution(Event):
    """
    Defines a FeeDistribution

    A FeeDistribution is an update to a set of custodians' DDX
    balances.

    Attributes:
        custodians (list[str]): Operator custodians
        bonds (list[Decimal]): Operator bonds
        submitter (str): Checkpoint submitter address
        epoch_id (int): Epoch id
        request_index (int): Sequenced request index of transaction
    """

    custodians: list[str] = field(eq=lambda x: set(map(str.lower, x)))
    bonds: list[Decimal] = field(eq=set)
    submitter: str = field(eq=str.lower)
    epoch_id: int
    request_index: int = field(default=-1, eq=False)

    @classmethod
    def decode_value_into_cls(cls, raw_tx_log_event: dict):
        """
        Decode a raw transaction log event (dict) into a
        FeeDistribution instance.

        Parameters
        ----------
        raw_tx_log_event : dict
            Raw transaction log event being processed
        """

        fee_distribution_event = raw_tx_log_event["event"]["c"]

        return cls(
            fee_distribution_event["custodians"],
            [Decimal(bond) for bond in fee_distribution_event["bonds"]],
            fee_distribution_event["submitter"],
            fee_distribution_event["epochId"],
            raw_tx_log_event["requestIndex"],
        )

    def process_tx(
        self,
        smt: DerivadexSMT,
        **kwargs,
    ):
        """
        Process a FeeDistribution transaction - there shouldn't be any changes to the SMT

        Parameters
        ----------
        smt: DerivadexSMT
            DerivaDEX Sparse Merkle Tree
        **kwargs
            Additional args specific to FeeDistribution transactions
        """

        # Sum and delete all epoch metadatas up to the last checkpoint/fee distribution
        epoch_metadatas = sorted(
            filter(
                lambda epoch_metadata_key: epoch_metadata_key[0].epoch_id
                <= self.epoch_id,
                smt.all_epoch_metadatas(),
            ),
            key=lambda epoch_metadata_key: epoch_metadata_key[0].epoch_id,
        )
        accumulated_ddx = Decimal("0")
        for epoch_metadata_key, epoch_metadata in epoch_metadatas:
            accumulated_ddx += epoch_metadata.ddx_fee_pool
            smt.store_epoch_metadata(epoch_metadata_key, None)

        if accumulated_ddx != Decimal("0"):
            total_distributed_fees = Decimal("0")
            distro_per_custodian = accumulated_ddx / Decimal(str(len(self.custodians)))

            for custodian in self.custodians:
                trader_key: TraderKey = TraderKey(custodian)
                trader = smt.trader(trader_key)
                if trader is None:
                    # Initialize a new Trader Leaf
                    trader = Trader.default()

                old_balance = trader.avail_ddx_balance
                trader.avail_ddx_balance = (
                    old_balance + distro_per_custodian
                ).recorded_amount()
                if trader.avail_ddx_balance != old_balance:
                    smt.store_trader(trader_key, trader)

                    total_distributed_fees += trader.avail_ddx_balance - old_balance

            dust = accumulated_ddx - total_distributed_fees

            trader_key: TraderKey = TraderKey(self.submitter)
            trader = smt.trader(trader_key)
            if trader is None:
                # Initialize a new Trader Leaf
                trader = Trader.default()

            old_balance = trader.avail_ddx_balance
            trader.avail_ddx_balance += dust

            if trader.avail_ddx_balance != old_balance:
                smt.store_trader(trader_key, trader)
