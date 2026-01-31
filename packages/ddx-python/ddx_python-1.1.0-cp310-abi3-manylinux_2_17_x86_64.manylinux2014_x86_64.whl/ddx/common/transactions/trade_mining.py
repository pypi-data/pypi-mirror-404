"""
TradeMining module
"""

import logging

from attrs import define, field
from ddx.common.transactions.event import Event
from ddx._rust.common.state import DerivadexSMT, Stats
from ddx._rust.common.state.keys import TraderKey
from ddx._rust.decimal import Decimal

logger = logging.getLogger(__name__)


@define
class TradeMining(Event):
    """
    Defines a TradeMining

    A TradeMining is when a there is a trade mining distribution.

    Attributes:
        settlement_epoch_id (int): Settlement epoch id
        ddx_distributed (Decimal): The total DDX distributed in this interval.
        total_volume (Stats): The total maker and taker volume for this interval.
        request_index (int): Sequenced request index of transaction
    """

    settlement_epoch_id: int
    ddx_distributed: Decimal
    total_volume: Stats
    request_index: int = field(default=-1, eq=False)

    @classmethod
    def decode_value_into_cls(cls, raw_tx_log_event: dict):
        """
        Decode a raw transaction log event (dict) into a Funding
        instance.

        Parameters
        ----------
        raw_tx_log_event : dict
            Raw transaction log event being processed
        """

        trade_mining_tx_event = raw_tx_log_event["event"]["c"]

        return cls(
            trade_mining_tx_event["settlementEpochId"],
            Decimal(trade_mining_tx_event["ddxDistributed"]),
            Stats(
                Decimal(trade_mining_tx_event["totalVolume"]["makerVolume"]),
                Decimal(trade_mining_tx_event["totalVolume"]["takerVolume"]),
            ),
            raw_tx_log_event["requestIndex"],
        )

    def process_tx(
        self,
        smt: DerivadexSMT,
        **kwargs,
    ):
        """
        Process a TradeMining transaction. A TradeMining event consists
        of consists of information relating to the trade mining
        distribution, when DDX will be allocated to traders due to
        their maker and taker volume contributions as a proportion to
        the overall exchange volume.

        Parameters
        ----------
        smt: DerivadexSMT
            DerivaDEX Sparse Merkle Tree
        **kwargs
            Additional args specific to TradeMining transactions
        """

        if not kwargs["trade_mining_active"]:
            return

        # The overall trade mining allocation is 75% of the
        # liquidity mining supply (50mm DDX) issued over a 10-year
        # schedule, 3 times a day
        ddx_reward_per_epoch = kwargs["trade_mining_reward_per_epoch"]
        trade_mining_maker_reward_percentage = kwargs[
            "trade_mining_maker_reward_percentage"
        ]
        trade_mining_taker_reward_percentage = kwargs[
            "trade_mining_taker_reward_percentage"
        ]
        if self.ddx_distributed != Decimal("0"):
            # If trade mining did distribute DDX during the trade
            # mining period, we should handle DDX distributions,
            # otherwise we can gracefully skip

            # Loop through all the stats leaves
            for stats_key, stats in smt.all_stats():
                # Compute the DDX gained as a result of maker volume
                # for the trader (20% of the DDX rewards go to makers)
                ddx_accrued_as_maker = (
                    stats.maker_volume
                    / self.total_volume.maker_volume
                    * ddx_reward_per_epoch
                    * trade_mining_maker_reward_percentage
                    if self.total_volume.maker_volume != Decimal("0")
                    else Decimal("0")
                )

                # Compute the DDX gained as a result of taker volume
                # for the trader (80% of the DDX rewards go to takers)
                ddx_accrued_as_taker = (
                    stats.taker_volume
                    / self.total_volume.taker_volume
                    * ddx_reward_per_epoch
                    * trade_mining_taker_reward_percentage
                    if self.total_volume.taker_volume != Decimal("0")
                    else Decimal("0")
                )

                if ddx_accrued_as_maker != Decimal(
                    "0"
                ) or ddx_accrued_as_taker != Decimal("0"):
                    # If DDX accrued for trader is non-zero, handle
                    # distribution

                    # Derive TraderKey given the key
                    trader_key: TraderKey = stats_key.as_trader_key()

                    # Get Trader leaf given the key from above
                    trader = smt.trader(trader_key)

                    # Increment the Trader leaf's available balance by the
                    # DDX accrued (both maker and taker)
                    trader.avail_ddx_balance = (
                        trader.avail_ddx_balance
                        + ddx_accrued_as_maker
                        + ddx_accrued_as_taker
                    ).recorded_amount()

                    # Update the SMT with the H256 repr of the key and
                    # the Trader leaf
                    smt.store_trader(trader_key, trader)

                    # Update the SMT with the H256 repr of the key and
                    # the Stats leaf
                    smt.store_stats(stats_key, None)
