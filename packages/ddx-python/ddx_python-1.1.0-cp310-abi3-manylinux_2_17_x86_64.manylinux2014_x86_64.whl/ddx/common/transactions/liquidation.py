"""
Liquidation module
"""

from attrs import define, field
from ddx.common.transactions.cancel import Cancel
from ddx.common.transactions.event import Event
from ddx.common.transactions.inner.adl_outcome import AdlOutcome
from ddx.common.transactions.inner.liquidated_position import LiquidatedPosition
from ddx.common.transactions.inner.liquidation_entry import LiquidationEntry
from ddx.common.transactions.inner.liquidation_fill import LiquidationFill
from ddx.common.transactions.inner.outcome import Outcome
from ddx._rust.common import ProductSymbol, TokenSymbol
from ddx._rust.common.enums import OrderSide, PositionSide
from ddx._rust.common.state import (DerivadexSMT, InsuranceFund, Position,
                                     Price, Strategy)
from ddx._rust.common.state.keys import (InsuranceFundKey, PositionKey,
                                          PriceKey, StrategyKey)
from ddx._rust.decimal import Decimal


def compute_strategy_total_value(
    strategy: Strategy,
    position_leaves: dict[ProductSymbol, Position],
    prices: dict[ProductSymbol, tuple[PriceKey, Price]],
):
    # Compute Strategy total value prior to liquidation
    strategy_total_value = strategy.avail_collateral[TokenSymbol.USDC]

    for symbol in position_leaves:
        # Obtain latest mark price for the symbol
        mark_price = prices[symbol][1].mark_price

        # Compute unrealized PNL for Position
        unrealized_pnl = position_leaves[symbol].unrealized_pnl(mark_price)

        # Adjust the Strategy's total value to account for
        # the Position's unrealized pnl
        strategy_total_value += unrealized_pnl

    return strategy_total_value


@define
class Liquidation(Event):
    """
    Defines an Liquidation

    A Liquidation contains a list of LiquidationEntry objects.

    Attributes:
        liquidation_entries (list[LiquidationEntry]): A list of LiquidationEntry objects
        request_index (int): Sequenced request index of transaction
    """

    liquidation_entries: list[LiquidationEntry] = field(eq=set)
    request_index: int = field(default=-1, eq=False)

    @classmethod
    def decode_value_into_cls(cls, raw_tx_log_event: dict):
        """
        Decode a raw transaction log event (dict) into a Liquidation
        instance.

        Parameters
        ----------
        raw_tx_log_event : dict
            Raw transaction log event being processed
        """

        event = raw_tx_log_event["event"]["c"]
        liquidation_tx_event = event["strategies"]

        return cls(
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
                                            Decimal(trade_outcome["Fill"]["amount"]),
                                            Decimal(trade_outcome["Fill"]["price"]),
                                            OrderSide(
                                                trade_outcome["Fill"]["takerSide"]
                                            ),
                                            Outcome(
                                                trade_outcome["Fill"]["makerOutcome"][
                                                    "trader"
                                                ],
                                                trade_outcome["Fill"]["makerOutcome"][
                                                    "strategyIdHash"
                                                ],
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
                                            Decimal(trade_outcome["Cancel"]["amount"]),
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
                                Decimal(liquidated_position_val["newInsuranceFundCap"]),
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
        )

    def process_tx(
        self,
        smt: DerivadexSMT,
        **kwargs,
    ):
        """
        Process a Liquidation transaction. A Liquidation is when a
        trader's account is under-collateralized and forcibly closed.
        Their collateral is removed and positions are closed, either
        against the order book with other market participants, or if
        the insurance fund is insufficiently-capitalized, ADL'd vs
        winning traders. A liquidated trader's open orders are canceled
        and the insurance fund is adjusted, along with the relevant
        Stats leaves for the maker traders taking on the liquidated
        position.

        Parameters
        ----------
        smt: DerivadexSMT
            DerivaDEX Sparse Merkle Tree
        **kwargs
            Additional args specific to Liquidation transactions
        """

        # Loop through each liquidation entry and process the cancels
        for liquidation_entry in self.liquidation_entries:
            # Loop through the canceled orders to remove them from the
            # SMT
            for cancel_tx in liquidation_entry.canceled_orders:
                cancel_tx.process_tx(smt, **kwargs)

        # Loop through each liquidation entry and process them individually
        for liquidation_entry in self.liquidation_entries:
            liquidated_strategy_key: StrategyKey = StrategyKey(
                liquidation_entry.trader_address, liquidation_entry.strategy_id_hash
            )
            liquidated_strategy: Strategy = smt.strategy(liquidated_strategy_key)

            position_leaves_by_symbol = {}
            for symbol, liquidated_position in liquidation_entry.positions:
                liquidated_position_key: PositionKey = PositionKey(
                    liquidation_entry.trader_address,
                    liquidation_entry.strategy_id_hash,
                    symbol,
                )

                liquidated_position: Position = smt.position(liquidated_position_key)

                # Store position in dict
                position_leaves_by_symbol[symbol] = liquidated_position

            # Loop through the positions of the liquidated Strategy
            for symbol, liquidated_position in liquidation_entry.positions:
                # Get collateral for liquidated strategy
                collateral = liquidated_strategy.avail_collateral[TokenSymbol.USDC]

                liquidated_position_key: PositionKey = PositionKey(
                    liquidation_entry.trader_address,
                    liquidation_entry.strategy_id_hash,
                    symbol,
                )
                liquidated_position_leaf: Position = smt.position(
                    liquidated_position_key
                )

                # Obtain latest mark price
                mark_price = kwargs["latest_price_leaves"][symbol][1].mark_price

                liquidated_strategy_total_value = compute_strategy_total_value(
                    liquidated_strategy,
                    position_leaves_by_symbol,
                    kwargs["latest_price_leaves"],
                )

                # Compute the bankruptcy price for the liquidated Position
                bankruptcy_price = mark_price - (
                    Decimal("1")
                    if liquidated_position_leaf.side == PositionSide.Long
                    else Decimal("-1")
                ) * (liquidated_strategy_total_value / liquidated_position_leaf.balance)

                # Loop through each trade outcome event and process them individually
                for trade_outcome in liquidated_position.trade_outcomes:
                    trade_outcome.process_tx(smt, **kwargs)

                    # If we're dealing with a Liquidation fill vs.
                    # a cancel...
                    if isinstance(trade_outcome, LiquidationFill):
                        # Update the collateral's intermediate value
                        collateral += (
                            trade_outcome.amount
                            * liquidated_position_leaf.avg_pnl(bankruptcy_price)
                        )

                        # Update liquidated Position's balance by the
                        # liquidated amount
                        liquidated_position_leaf.balance -= trade_outcome.amount

                # Loop through each ADL outcome and process them individually
                for adl_outcome in liquidated_position.adl_outcomes:
                    adl_position_key: PositionKey = PositionKey(
                        adl_outcome.trader_address,
                        adl_outcome.strategy_id_hash,
                        symbol,
                    )
                    adl_position: Position = smt.position(adl_position_key)

                    adl_strategy_key: StrategyKey = adl_position_key.as_strategy_key()
                    adl_strategy: Strategy = smt.strategy(adl_strategy_key)

                    # Compute ADL amount
                    adl_amount = min(
                        liquidated_position_leaf.balance, adl_position.balance
                    )

                    # Compute ADL'd realized PNL
                    adl_realized_pnl = adl_amount * adl_position.avg_pnl(
                        bankruptcy_price,
                    )

                    # Adjust ADL'd Strategy's free collateral
                    adl_strategy.set_avail_collateral(
                        TokenSymbol.USDC,
                        adl_strategy.avail_collateral[TokenSymbol.USDC]
                        + adl_realized_pnl,
                    )

                    # Store ADL'd Strategy in the SMT
                    smt.store_strategy(
                        adl_strategy_key,
                        adl_strategy,
                    )

                    # Adjust and store ADL'd Position in the SMT
                    adl_position.balance -= adl_amount
                    smt.store_position(
                        adl_position_key,
                        adl_position,
                    )

                    # Compute liquidated Strategy's realized pnl
                    liquidated_realized_pnl = (
                        adl_amount
                        * liquidated_position_leaf.avg_pnl(
                            bankruptcy_price,
                        )
                    )

                    # Update the collateral's intermediate value
                    collateral += liquidated_realized_pnl

                    # Adjust liquidated Position's balance by the
                    # ADL'd amount
                    liquidated_position_leaf.balance -= adl_amount

                # Update liquidated Strategy's free collateral
                # with the realized PNL from liquidation fills and ADL's
                liquidated_strategy.set_avail_collateral(
                    TokenSymbol.USDC,
                    collateral,
                )

                # Remove Position from the SMT
                smt.store_position(
                    liquidated_position_key,
                    None,
                )

                insurance_fund_key: InsuranceFundKey = InsuranceFundKey()
                insurance_fund: InsuranceFund = smt.insurance_fund(insurance_fund_key)

                # Overwrite the insurance fund with the new insurance fund
                # capitalization.
                insurance_fund[TokenSymbol.USDC] = (
                    liquidated_position.new_insurance_fund_cap
                )

                smt.store_insurance_fund(insurance_fund_key, insurance_fund)

                # Delete symbol/Position from dict
                del position_leaves_by_symbol[symbol]

            # Clear out the liquidated Strategy's free collateral and
            # store in the SMT
            liquidated_strategy.set_avail_collateral(
                TokenSymbol.USDC,
                Decimal("0"),
            )
            smt.store_strategy(
                liquidated_strategy_key,
                liquidated_strategy,
            )
