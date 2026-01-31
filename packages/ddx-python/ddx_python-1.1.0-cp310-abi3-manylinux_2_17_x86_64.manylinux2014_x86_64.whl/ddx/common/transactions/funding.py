"""
Funding module
"""

import logging
from typing import Optional

import numpy as np
from attrs import define, field
from ddx.common.transaction_utils import get_prices_for_symbol_and_duration
from ddx.common.transactions.cancel import Cancel
from ddx.common.transactions.event import Event
from ddx.common.transactions.inner.adl_outcome import AdlOutcome
from ddx.common.transactions.inner.liquidated_position import LiquidatedPosition
from ddx.common.transactions.inner.liquidation_entry import LiquidationEntry
from ddx.common.transactions.inner.liquidation_fill import LiquidationFill
from ddx.common.transactions.inner.outcome import Outcome
from ddx.common.transactions.liquidation import Liquidation
from ddx._rust.common import ProductSymbol, TokenSymbol
from ddx._rust.common.enums import OrderSide, PositionSide
from ddx._rust.common.state import DerivadexSMT
from ddx._rust.common.state.keys import StrategyKey
from ddx._rust.decimal import Decimal

logger = logging.getLogger(__name__)


def get_funding_rate(
    smt: DerivadexSMT,
    funding_period: int,
    symbol: ProductSymbol,
) -> Optional[Decimal]:
    """
    Get the projected funding rate for the upcoming funding
    distribution pay period for a given symbol

    Parameters
    ----------
    smt: DerivadexSMT
        DerivaDEX Sparse Merkle Tree
    funding_period : int
        Funding period for retrieving price leaves
    symbol : str
        Market symbol
    """

    if not symbol.is_perpetual():
        return None

    # Get price leaves for symbol
    prices = get_prices_for_symbol_and_duration(smt, symbol, funding_period)
    logger.debug(f"Last {funding_period} price leaves: {prices}")

    # Compute average premium rate across all price checkpoints
    avg_premium_rate = np.mean(
        [
            price_value.mark_price_metadata.ema / price_value.index_price
            for _, price_value in prices
        ]
    )

    # Any values between [-0.0005, 0.0005] => 0
    unclamped_funding_rate = max(Decimal("0.0005"), avg_premium_rate) + min(
        Decimal("-0.0005"), avg_premium_rate
    )

    # Cap the funding rate bounds to [-0.005, 0.005]
    return min(Decimal("0.005"), max(Decimal("-0.005"), unclamped_funding_rate))


@define
class Funding(Event):
    """
    Defines a Funding

    A Funding is when a there is a funding rate distribution.

    Attributes:
        settlement_epoch_id (int): The epoch id for the funding event.
        liquidation (Liquidation): Liquidations
        time_value (int): Time value
        request_index (int): Sequenced request index of transaction
    """

    settlement_epoch_id: int
    liquidation: Liquidation
    time_value: int
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

        funding_tx_event = raw_tx_log_event["event"]["c"]
        liquidation_tx_event = funding_tx_event["liquidations"]

        return cls(
            funding_tx_event["settlementEpochId"],
            Liquidation(
                [
                    LiquidationEntry(
                        liquidation_entry["traderAddress"],
                        liquidation_entry["strategyIdHash"],
                        [
                            Cancel(
                                ProductSymbol(canceled_order["symbol"]),
                                canceled_order["orderHash"],
                                Decimal(canceled_order["amount"]),
                                raw_tx_log_event["requestIndex"],
                            )
                            for canceled_order in liquidation_entry["canceledOrders"]
                        ],
                        [
                            (
                                ProductSymbol(liquidated_position_key),
                                LiquidatedPosition(
                                    Decimal(liquidated_position_val["amount"]),
                                    [
                                        (
                                            LiquidationFill(
                                                ProductSymbol(
                                                    trade_outcome["Fill"]["symbol"]
                                                ),
                                                trade_outcome["Fill"]["indexPriceHash"],
                                                trade_outcome["Fill"]["makerOrderHash"],
                                                Decimal(
                                                    trade_outcome["Fill"][
                                                        "makerOrderRemainingAmount"
                                                    ]
                                                ),
                                                Decimal(
                                                    trade_outcome["Fill"]["amount"]
                                                ),
                                                Decimal(trade_outcome["Fill"]["price"]),
                                                OrderSide(
                                                    trade_outcome["Fill"]["takerSide"]
                                                ),
                                                Outcome(
                                                    trade_outcome["Fill"][
                                                        "makerOutcome"
                                                    ]["trader"],
                                                    trade_outcome["Fill"][
                                                        "makerOutcome"
                                                    ]["strategyIdHash"],
                                                ),
                                                raw_tx_log_event["timeValue"],
                                                raw_tx_log_event["requestIndex"],
                                            )
                                            if "Fill" in trade_outcome
                                            else Cancel(
                                                ProductSymbol(
                                                    trade_outcome["Cancel"]["symbol"]
                                                ),
                                                trade_outcome["Cancel"]["orderHash"],
                                                Decimal(
                                                    trade_outcome["Cancel"]["amount"]
                                                ),
                                                raw_tx_log_event["requestIndex"],
                                            )
                                        )
                                        for trade_outcome in liquidated_position_val[
                                            "tradeOutcomes"
                                        ]
                                    ],
                                    [
                                        AdlOutcome(
                                            adl_outcome["traderAddress"],
                                            adl_outcome["strategyIdHash"],
                                            raw_tx_log_event["requestIndex"],
                                        )
                                        for adl_outcome in liquidated_position_val[
                                            "adlOutcomes"
                                        ]
                                    ],
                                    Decimal(
                                        liquidated_position_val["newInsuranceFundCap"]
                                    ),
                                    raw_tx_log_event["requestIndex"],
                                ),
                            )
                            for (
                                liquidated_position_key,
                                liquidated_position_val,
                            ) in liquidation_entry["positions"]
                        ],
                        raw_tx_log_event["requestIndex"],
                    )
                    for liquidation_entry in liquidation_tx_event
                ],
                raw_tx_log_event["requestIndex"],
            ),
            raw_tx_log_event["timeValue"],
            raw_tx_log_event["requestIndex"],
        )

    def process_tx(
        self,
        smt: DerivadexSMT,
        **kwargs,
    ):
        """
        Process a Funding transaction. A Funding event consists of
        consists of information relating to funding rate-related
        distributions. All open positions will result in traders
        either paying or receiving a USDC debit/credit to their
        avaiable collateral as a function of the funding rate (given the
        Price leaves in the SMT at this time) and their
        position notional (given the latest mark price).

        Parameters
        ----------
        smt: DerivadexSMT
            DerivaDEX Sparse Merkle Tree
        **kwargs
            Additional args specific to Funding transactions
        """

        funding_strategies = {}

        # Loop through the funding rate symbols and values as specified
        # in the transaction
        for funding_rate_symbol in sorted(kwargs["latest_price_leaves"]):
            funding_rate = get_funding_rate(
                smt, kwargs["funding_period"], funding_rate_symbol
            )

            if funding_rate is not None and funding_rate != Decimal("0"):
                # If funding rate is non-zero, handle funding payments

                # Obtain latest mark price
                mark_price = kwargs["latest_price_leaves"][funding_rate_symbol][
                    1
                ].mark_price

                # Loop through each open position
                for (
                    position_key,
                    position,
                ) in smt.all_positions_for_symbol(funding_rate_symbol):
                    # Compute the funding payment for the trader. When
                    # the funding rate is positive, long traders will
                    # pay and short traders will receive payments. When
                    # the funding rate is negative, long traders will
                    # receive payments and short traders will pay.
                    funding_delta = (
                        (
                            Decimal("-1.0")
                            if position.side == PositionSide.Long
                            else Decimal("1.0")
                        )
                        * funding_rate
                        * position.balance
                        * mark_price
                    )

                    # Construct a StrategyKey and corresponding encoded
                    # key
                    strategy_key: StrategyKey = position_key.as_strategy_key()

                    funding_strategies[strategy_key] = (
                        funding_strategies[strategy_key] + funding_delta
                        if strategy_key in funding_strategies
                        else funding_delta
                    )

        for strategy_key, funding_delta in funding_strategies.items():
            strategy = smt.strategy(strategy_key)

            # Credit/debit the trader's Strategy leaf by the
            # funding delta from above
            strategy.set_avail_collateral(
                TokenSymbol.USDC,
                strategy.avail_collateral[TokenSymbol.USDC] + funding_delta,
            )

            # Update the SMT with the H256 repr of the key and
            # the Strategy leaf
            smt.store_strategy(
                strategy_key,
                strategy,
            )

        # Process liquidation
        self.liquidation.process_tx(smt, **kwargs)
