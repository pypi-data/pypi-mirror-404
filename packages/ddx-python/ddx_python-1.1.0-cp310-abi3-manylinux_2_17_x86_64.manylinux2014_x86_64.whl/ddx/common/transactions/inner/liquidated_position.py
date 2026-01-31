"""
LiquidatedPosition module
"""

from attrs import define, field
from ddx.common.transactions.cancel import Cancel
from ddx.common.transactions.inner.adl_outcome import AdlOutcome
from ddx.common.transactions.inner.liquidation_fill import LiquidationFill
from ddx._rust.decimal import Decimal


@define
class LiquidatedPosition:
    """
    Defines a LiquidatedPosition

    A LiquidatedPosition has data pertaining to a liquidated position.

    Attributes:
        amount (Decimal): Liquidated balance amount
        trade_outcomes (list[LiquidationFill | Cancel]): A list of trade outcome objects
        adl_outcomes (list[AdlOutcome]): Positions that were ADL'd as a result of the liquidation
        new_insurance_fund_cap (Decimal): Insurance fund capitalization after the liquidation
        request_index (int): Sequenced request index of transaction
    """

    amount: Decimal
    trade_outcomes: list[LiquidationFill | Cancel] = field(eq=set)
    adl_outcomes: list[AdlOutcome] = field(eq=set)
    new_insurance_fund_cap: Decimal
    request_index: int = field(default=-1, eq=False)

    def __hash__(self):
        return hash(
            (
                self.amount,
                frozenset(self.trade_outcomes),
                frozenset(self.adl_outcomes),
                self.new_insurance_fund_cap,
            )
        )
