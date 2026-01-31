"""
AdlOutcome module
"""

from attrs import define, field
from ddx._rust.decimal import Decimal


@define(hash=True)
class AdlOutcome:
    """
    Defines an AdlOutcome

    An AdlOutcome is a scenario where a strategy has been auto-deleveraged
    due to a liquidation.

    Attributes:
        trader_address (str): Auto-deleveraged trader's ethereum address
        strategy_id_hash (str): Auto-deleveraged strategy ID hash
        request_index (int): Sequenced request index of transaction
    """

    trader_address: str = field(eq=str.lower)
    strategy_id_hash: str = field(eq=str.lower)
    request_index: int = field(default=-1, eq=False, hash=False)
