"""
LiquidationEntry module
"""

from attrs import define, field
from ddx.common.transactions.cancel import Cancel
from ddx.common.transactions.inner.liquidated_position import LiquidatedPosition
from ddx._rust.common import ProductSymbol


@define
class LiquidationEntry:
    """
    Defines a LiquidationEntry

    A LiquidationEntry contains data pertaining to individual trader and
    strategy liquidations.

    Attributes:
        trader_address (str): Liquidated trader's Ethereum address
        strategy_id_hash (str): Liquidated strategy ID hash
        canceled_orders (list[Cancel]): Canceled orders for liquidated trader
        positions (list[tuple[str, LiquidatedPosition]]): Contains information pertaining to individual liquidated positions by symbol
        request_index (int): Sequenced request index of transaction
    """

    trader_address: str = field(eq=str.lower)
    strategy_id_hash: str = field(eq=str.lower)
    canceled_orders: list[Cancel] = field(eq=set)
    positions: list[tuple[ProductSymbol, LiquidatedPosition]] = field(eq=set)
    request_index: int = field(default=-1, eq=False)

    def __hash__(self):
        return hash(
            (
                self.trader_address,
                self.strategy_id_hash,
                frozenset(self.canceled_orders),
                frozenset(self.positions),
            )
        )
