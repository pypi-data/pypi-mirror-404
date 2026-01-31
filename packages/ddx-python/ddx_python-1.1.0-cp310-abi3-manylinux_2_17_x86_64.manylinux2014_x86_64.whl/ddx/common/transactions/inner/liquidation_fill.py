"""
LiquidationFill module
"""

import logging

from attrs import define, field
from ddx.common.transactions.inner.fill import Fill
from ddx.common.transactions.inner.outcome import Outcome
from ddx._rust.common import ProductSymbol
from ddx._rust.common.enums import OrderSide
from ddx._rust.common.state import DerivadexSMT
from ddx._rust.common.state.keys import BookOrderKey
from ddx._rust.decimal import Decimal

logger = logging.getLogger(__name__)


@define(hash=True)
class LiquidationFill(Fill):
    """
    Defines a LiquidationFill
    """

    maker_order_hash: str = field(eq=str.lower)
    maker_outcome: Outcome = field(hash=False)
    maker_order_remaining_amount: Decimal = field(hash=False)
    index_price_hash: str = field(eq=str.lower)
    request_index: int = field(default=-1, eq=False, hash=False)

    def __init__(
        self,
        symbol: ProductSymbol,
        index_price_hash: str,
        maker_order_hash: str,
        maker_order_remaining_amount: Decimal,
        amount: Decimal,
        price: Decimal,
        taker_side: OrderSide,
        maker_outcome: Outcome,
        time_value: int,
        request_index: int = -1,
    ):
        """
        Initialize a LiquidationFill instance
        Parameters
        ----------
        symbol : ProductSymbol
            Product symbol
        index_price_hash : str
            Index price hash
        maker_order_hash : str
            Maker order hash
        maker_order_remaining_amount : Decimal
            Maker order remaining amount
        amount : Decimal
            Amount
        price : Decimal
            Price
        taker_side : OrderSide
            Taker side
        maker_outcome : Outcome
            Maker outcome
        time_value : int
            Time value
        request_index : int
            Request index
        """
        super().__init__(
            symbol,
            amount,
            price,
            taker_side,
            time_value,
            request_index,
        )
        self.maker_order_hash = maker_order_hash
        self.maker_outcome = maker_outcome
        self.maker_order_remaining_amount = maker_order_remaining_amount
        self.index_price_hash = index_price_hash

    def process_tx(
        self,
        smt: DerivadexSMT,
        **kwargs,
    ):
        """
        Process a LiquidationFill transaction. These are Fill
        transactions that have risen from either a Liquidation.

        Parameters
        ----------
        smt: DerivadexSMT
            DerivaDEX Sparse Merkle Tree
        **kwargs
            Additional args specific to Liquidation transactions
        """

        maker_book_order_key: BookOrderKey = BookOrderKey(
            self.symbol, self.maker_order_hash
        )

        maker_book_order = smt.book_order(maker_book_order_key)
        maker_book_order_time_value = maker_book_order.time_value

        maker_book_order.amount = self.maker_order_remaining_amount
        smt.store_book_order(maker_book_order_key, maker_book_order)

        # Adjust the maker-related position. Take note that
        # in a liquidation, there is no taker component, so
        # unlike its counterpart (TradeFill), a
        # LiquidationFill only considers the maker
        self.adjust_for_maker(
            smt,
            kwargs["epoch_id"],
            kwargs["trade_mining_active"],
            maker_book_order_time_value,
        )
