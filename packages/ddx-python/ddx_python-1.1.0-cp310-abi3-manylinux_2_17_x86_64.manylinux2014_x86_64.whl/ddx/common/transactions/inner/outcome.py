"""
Outcome module
"""

from typing import Optional

from attrs import define, field
from ddx._rust.decimal import Decimal


@define(hash=True)
class Outcome:
    """
    Defines a Outcome

    An Outcome is a part of a Fill transaction. It holds information
    including the fees paid, the strategy ID and trader address, and
    whether fees are being paid in DDX or not (i.e. USDC).

    Attributes:
        trader (str): Trader's Ethereum address
        strategy_id_hash (str): Strategy ID hash
        fee (Decimal): Fees paid for filled trade
        pay_fee_in_ddx (bool): Whether the trader has elected to pay the fee in DDX
    """

    trader: str = field(eq=str.lower, default="")
    strategy_id_hash: str = field(eq=str.lower, default="")
    # The below fields do not exist in the txlog (and thus are not checked in transaction
    # equality), and are only used when executing/processing transactions.
    fee: Optional[Decimal] = field(eq=False, default=None)
    pay_fee_in_ddx: Optional[bool] = field(eq=False, default=None)
