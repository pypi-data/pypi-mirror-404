"""
Post module
"""

from attrs import define, field
from ddx.common.transactions.event import Event
from ddx._rust.common import ProductSymbol
from ddx._rust.common.enums import OrderSide
from ddx._rust.common.state import BookOrder, DerivadexSMT
from ddx._rust.common.state.keys import BookOrderKey, StrategyKey
from ddx._rust.decimal import Decimal


@define
class Post(Event):
    """
    Defines a Post

    A Post is an order that enters the order book.

    Attributes:
        symbol (ProductSymbol): The symbol for the market this order is for.
        order_hash (str): Hexstr representation of the EIP-712 hash of the order
        side (str): Side of order ('Bid', 'Ask')
        amount (Decimal): Amount/size of order
        price (Decimal): Price the order has been placed at
        trader_address (str): The order creator's Ethereum address
        strategy_id_hash (str): The cross-margined strategy ID for which this order belongs
        book_ordinal (int): The numerical sequence-identifying value for an order's insertion into the book
        time_value (int): Time value
        request_index (int): Sequenced request index of transaction
    """

    symbol: ProductSymbol
    order_hash: str = field(eq=str.lower)
    side: OrderSide
    amount: Decimal
    price: Decimal
    trader_address: str = field(eq=str.lower)
    strategy_id_hash: str = field(eq=str.lower)
    book_ordinal: int
    time_value: int
    request_index: int = field(default=-1, eq=False)

    def process_tx(
        self,
        smt: DerivadexSMT,
        **kwargs,
    ):
        """
        Process a Post transaction. We will need to create a new
        BookOrder leaf with this information.

        Parameters
        ----------
        smt: DerivadexSMT
            DerivaDEX Sparse Merkle Tree
        **kwargs
            Additional args specific to PostOrder transactions
        """

        book_order = BookOrder(
            self.side,
            self.amount,
            self.price,
            self.trader_address,
            self.strategy_id_hash,
            self.book_ordinal,
            self.time_value,
        )

        smt.store_book_order(BookOrderKey(self.symbol, self.order_hash), book_order)
